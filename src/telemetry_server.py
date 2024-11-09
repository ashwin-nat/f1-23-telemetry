# MIT License
#
# Copyright (c) [2024] [Ashwin Natarajan]
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -------------------------------------- IMPORTS -----------------------------------------------------------------------

from typing import Dict, Any, Optional, Callable, List, Tuple, Set
from http import HTTPStatus
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
# pylint: disable=unused-import
from engineio.async_drivers import gevent
import src.telemetry_data as TelData
import src.telemetry_web_api as TelWebAPI
from src.png_logger import getLogger
from lib.inter_thread_communicator import InterThreadCommunicator

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_web_server : Optional["TelemetryWebServer"] = None
png_logger = getLogger()
_race_table_clients : Set[str] = set()
_player_overlay_clients : Set[str] = set()

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

class TelemetryWebServer:
    def __init__(self,
        port: int,
        packet_capture_enabled: bool,
        client_update_interval_ms: int,
        debug_mode: bool,
        num_adjacent_cars: int,
        socketio_tasks: List[Tuple[Callable, Any]]):
        """
        Initialize TelemetryServer.

        Args:
            port (int): Port number for the server.
            packet_capture (bool) - True if packet capture is enabled
            client_update_interval_ms (int) - The interval at which the client should be updated with new data
            debug_mode (bool): Enable debug mode.
            num_adjacent_cars (int): The number of cars adjacent to player to be included in telemetry-info response
            socketio_tasks (List[Tuple[Callable, Any]]): List of tasks to be executed by the SocketIO server
        """

        self.m_app = Flask(__name__, template_folder='templates', static_folder='static')
        self.m_app.config['PROPAGATE_EXCEPTIONS'] = True
        self.m_port = port
        self.m_debug_mode = debug_mode
        self.m_packet_capture_enabled = packet_capture_enabled
        self.m_client_update_interval_ms = client_update_interval_ms
        self.m_num_adjacent_cars = num_adjacent_cars
        self.m_socketio = SocketIO(
            app=self.m_app,
            async_mode="gevent",
        )
        self.m_socketio_tasks = socketio_tasks

        # Define your endpoint
        @self.m_app.route('/favicon.ico')
        def favicon():
            """Return the favicon file

            Returns:
                file: Favicon file
            """
            return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

        @self.m_app.route('/telemetry-info')
        def telemetryInfo() -> Dict:
            """
            Endpoint for telemetry information.

            Returns:
                str: Telemetry data in JSON format.
            """

            return TelWebAPI.RaceInfoRsp().toJSON(), HTTPStatus.OK

        # Define your endpoint
        @self.m_app.route('/race-info')
        def overtakeInfo() -> Dict:
            """
            Endpoint for overtake information.

            Returns:
                str: Overtake data in JSON format.
            """

            return TelWebAPI.OverallRaceStatsRsp().toJSON(), HTTPStatus.OK

        @self.m_app.route('/save-telemetry-capture')
        def saveTelemetryCapture() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """
            return TelWebAPI.SavePacketCaptureRsp().toJSON()

        @self.m_app.route('/driver-info', methods=['GET'])
        def driverInfo() -> Dict:
            """
            Endpoint for saving telemetry packet capture.

            Returns:
                str: JSON response indicating success or failure.
            """

            # Access parameters using request.args
            index = request.args.get('index')

            # Validate the input
            error_response = self.validateIntGetRequestParam(index, 'index')
            if error_response:
                return error_response, HTTPStatus.BAD_REQUEST

            # Check if the given index is valid
            index = int(index)
            if not TelData.isDriverIndexValid(index):
                error_response = {
                    'error' : 'Invalid parameter value',
                    'message' : 'Invalid index'
                }
                return jsonify(error_response), HTTPStatus.BAD_REQUEST

            # Process parameters and generate response
            return TelWebAPI.DriverInfoRsp(index).toJSON(), HTTPStatus.OK

        # Render the HTML page
        @self.m_app.route('/')
        def index():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            return render_template('index.html',
                packet_capture_enabled=self.m_packet_capture_enabled,
                client_poll_interval_ms=0, # deprecated since we've moved to socketio
                num_adjacent_cars=self.m_num_adjacent_cars,
                live_data_mode=True)

        # Render the HTML page
        @self.m_app.route('/player-stream-overlay')
        def throttleBrakeOverlay():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            return render_template('player-stream-overlay.html')

        # Render the HTML page
        @self.m_app.route('/full')
        def fullTelemetryView():
            """
            Endpoint for the index page.

            Returns:
                str: HTML page content.
            """

            return render_template('index.html',
                packet_capture_enabled=self.m_packet_capture_enabled,
                client_poll_interval_ms=0, # deprecated since we've moved to socketio
                num_adjacent_cars=22,
                live_data_mode=True)

        # Socketio endpoints
        @self.m_socketio.on('connect')
        def handleConnect():
            """SocketIO endpoint for handling client connection
            """
            png_logger.debug("Client connected")

        @self.m_socketio.on('disconnect')
        def handleDisconnect():
            """SocketIO endpoint for handling client disconnection
            """
            png_logger.debug("Client disconnected")
            _player_overlay_clients.discard(request.sid)
            _race_table_clients.discard(request.sid)

        @self.m_socketio.on('race-info')
        # pylint: disable=unused-argument
        def handeRaceInfo(dummy_arg: Any):
            """SocketIO endpoint to handle race info request
            """
            emit("race-info-response", TelWebAPI.OverallRaceStatsRsp().toJSON(), broadcast=False)

        @self.m_socketio.on('driver-info')
        def handleDriverInfo(data: Dict[str, Any]):
            """SocketIO endpoint to handle driver info request

            Args:
                data (Dict[str, Any]): The JSON response. Will contain the key "error" in case of failure
            """
            response = None
            index = data.get("index", None)
            error_response = self.validateIntGetRequestParam(index, "index")
            if error_response:
                emit("driver-info-response", error_response, broadcast=False)
                response = error_response
            elif not TelData.isDriverIndexValid(index):
                response = {
                    'error' : 'Invalid parameter value',
                    'message' : 'Invalid index'
                }
            else:
                response = TelWebAPI.DriverInfoRsp(index).toJSON()
            emit("driver-info-response", response, broadcast=False)

        @self.m_socketio.on('register-client')
        def handleClientRegistration(data):
            """SocketIO endpoint to handle client registration
            """
            png_logger.debug('Client registered. SID = %s Type = %s', request.sid, data['type'])
            if data['type'] == 'player-stream-overlay':
                _player_overlay_clients.add(request.sid)
            elif data['type'] == 'race-table':
                _race_table_clients.add(request.sid)

    def validateIntGetRequestParam(self, param: Any, param_name: str) -> Optional[Dict[str, Any]]:
        """
        Validate integer get request parameter.

        Args:
            param (Any): The parameter to check.
            param_name (str) : The name of the parameter (used in response)

        Returns:
            Optional[Dict[str, Any]]: Error response if the parameter is invalid, else None
        """

        # Check if only one parameter is provided
        if param is None:
            return {
                'error': 'Invalid parameters',
                'message': f'Provide "{param_name}" parameter'
            }

        # Check if the provided value for index is numeric
        if not isinstance(param, int) and not param.isdigit():
            return {
                'error': 'Invalid parameter value',
                'message': f'"{param_name}" parameter must be numeric'
            }

        return None

    def run(self):
        """
        Run the TelemetryServer.
        """

        # Disable Werkzeug request logging
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('socketio').setLevel(logging.ERROR)
        logging.getLogger('engineio').setLevel(logging.ERROR)
        logging.getLogger('gevent').setLevel(logging.ERROR)
        logging.getLogger('websocket').setLevel(logging.ERROR)

        if self.m_socketio_tasks:
            for callback, arg in self.m_socketio_tasks:
                self.m_socketio.start_background_task(callback, arg)
        self.m_socketio.run(
            app=self.m_app,
            debug=False,
            port=self.m_port,
            use_reloader=False)

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def initTelemetryWebServer(
    port: int,
    packet_capture_enabled: bool,
    client_update_interval_ms: int,
    debug_mode: bool,
    num_adjacent_cars: int) -> None:
    """Initialize the web server

    Args:
        port (int): Port number
        packet_capture_enabled (bool): Should enable packet capture
        client_update_interval_ms (int): How often the client will be updated with new info
        debug_mode (bool): Debug enabled if true
        num_adjacent_cars (int): Number of adjacent cars to be displayed in the telemetry table
    """

    global _web_server
    _web_server = TelemetryWebServer(
        port=port,
        packet_capture_enabled=packet_capture_enabled,
        client_update_interval_ms=client_update_interval_ms,
        debug_mode=debug_mode,
        num_adjacent_cars=num_adjacent_cars,
        socketio_tasks=[
            (raceTableClientUpdaterTask, client_update_interval_ms),
            (playerTelemetryOverlayUpdaterTask, 60),
            (streamUpdaterTask, 1000)
        ]
    )
    _web_server.run()

def raceTableClientUpdaterTask(update_interval_ms: int) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
    """

    global _web_server
    global _race_table_clients
    sleep_duration = update_interval_ms / 1000
    while True:
        if len(_race_table_clients) > 0:
            _web_server.m_socketio.emit('race-table-update', TelWebAPI.RaceInfoRsp().toJSON())
        _web_server.m_socketio.sleep(sleep_duration)

def playerTelemetryOverlayUpdaterTask(update_interval_ms: int) -> None:
    """Task to update clients with player telemetry overlay data
    Args:
        update_interval_ms (int): Update interval in milliseconds
    """

    global _web_server
    global _player_overlay_clients
    sleep_duration = update_interval_ms / 1000
    while True:
        if len(_player_overlay_clients) > 0:
            _web_server.m_socketio.emit('player-overlay-update', TelWebAPI.PlayerTelemetryOverlayUpdate().toJSON())
        _web_server.m_socketio.sleep(sleep_duration)

def streamUpdaterTask(update_interval_ms: int) -> None:
    """Task to update clients with telemetry data

    Args:
        update_interval_ms (int): Update interval in milliseconds
    """

    sleep_duration = update_interval_ms / 1000
    while True:
        frame_id = InterThreadCommunicator().receive("stream-update")
        if frame_id is not None:
            png_logger.info(f"Received stream update button press {frame_id}")
        _web_server.m_socketio.sleep(sleep_duration)
