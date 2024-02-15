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

from telemetry_handler import F12023TelemetryHandler
from telemetry_server import TelemetryServer
import threading
import time
import sys

http_port = 5000
f1_telemetry_port = 20777


def http_server_task() -> None:
    """Entry to point to start the HTTP server
    """

    telemetry_server = TelemetryServer(http_port, debug_mode=False)
    print("Starting HTTP Server")
    telemetry_server.run()

def f1_telemetry_client_task():
    """Entry point to start the F1 23 telemetry client
    """

    telemetry_client = F12023TelemetryHandler(f1_telemetry_port)
    print("Starting F1 telemetry client. Open http://127.0.0.1:" + str(http_port))
    telemetry_client.run()

if __name__ == '__main__':

    # First init the telemetry client on  a main thread
    client_thread = threading.Thread(target=f1_telemetry_client_task)
    client_thread.daemon = True
    client_thread.start()

    # Run the HTTP server on the main thread. flask does not like running on separate threads
    http_server_task()

    # Set up a keyboard interrupt handler
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Ctrl+C pressed. Exiting...")
        sys.exit()