
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

import configparser
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, fields

# -------------------------------------- CLASS DEFINITIONS -------------------------------------------------------------

# Define your PacketCaptureMode Enum, if not already done

class PacketCaptureMode(Enum):
    """Enum class for packet capture mode
    """
    DISABLED = "disabled"
    ENABLED = "enabled"
    ENABLED_WITH_AUTOSAVE = "enabled-with-autosave"

    def __repr__(self)->str:
        """Return the string representation

        Returns:
            str: string representation
        """
        return self.__str__()

    def __str__(self)->str:
        """Return the string representation

        Returns:
            str: string representation
        """
        return self.value

@dataclass
class Config:
    """The data class containing the app config
    """
    telemetry_port: int
    server_port: int
    udp_custom_action_code: int
    packet_capture_mode: PacketCaptureMode
    post_race_data_autosave: bool
    refresh_interval: int
    num_adjacent_cars: int
    disable_browser_autoload: bool
    log_file: str
    log_file_size: int

    def __repr__(self) -> str:
        """Return the string representation, formatted one key-value pair per line

        Returns:
            str: string representation
        """
        return "\n".join(f"{field.name}: {getattr(self, field.name)}" for field in fields(self))

# -------------------------------------- GLOBALS -----------------------------------------------------------------------

_default_config = {
    'Network': {
        'telemetry_port': 20777,  # Integer
        'server_port': 5000,      # Integer
        'udp_custom_action_code': None,  # None (optional, not set by default)
    },
    'Capture': {
        'packet_capture_mode': PacketCaptureMode.DISABLED,  # Enum (which can be converted to string for INI storage)
        'post_race_data_autosave': True,  # Boolean
    },
    'Display': {
        'refresh_interval': 200,  # Integer
        'num_adjacent_cars': 2,   # Integer
        'disable_browser_autoload': False,  # Boolean
    },
    'Logging': {
        'log_file': 'png.log',  # String (empty if not set)
        'log_file_size': 1000000,  # Integer
    },
}

# -------------------------------------- FUNCTIONS ---------------------------------------------------------------------

def load_config(config_file: str = "config.ini") -> Config:
    """Load settings from an INI file or create it if missing, and add new keys.

    Args:
        config_file (str, optional): Path to the config file. Defaults to "config.ini".

    Returns:
        Config: The config data object
    """

    # Helper methods to fetch values
    def get_value_str(section: str, key: str) -> str:
        """Fetch string value from INI or use default from _default_config

        Args:
            section (str): Section name
            key (str): Key name

        Returns:
            str: Value as string for the given key under the given section
        """

        default_value = _default_config.get(section, {}).get(key, "")
        value = config.get(section, key, fallback=str(default_value))
        return value if value != '' else str(default_value)

    def get_value_int(section: str, key: str) -> int:
        """Fetch integer value from INI or use default from _default_config.

        Args:
            section (str): Section name
            key (str): Key name

        Returns:
            int: Value as int for the given key under the given section
        """

        default_value = _default_config.get(section, {}).get(key, None)
        value = config.get(section, key, fallback=default_value)

        # Handle case where value is empty string or None
        return default_value if value == '' or value is None else int(value)

    def get_value_bool(section, key):
        """Fetch boolean value from INI or use default from _default_config.

        Args:
            section (str): Section name
            key (str): Key name

        Returns:
            int: Value as bool for the given key under the given section
        """

        default_value = _default_config.get(section, {}).get(key, False)
        value = config.get(section, key, fallback=str(default_value))

        # Handle case where value is empty string or None
        if value == '' or value is None:
            return default_value

        # Try converting to boolean
        return config.getboolean(section, key, fallback=default_value)

    config_path = Path(config_file)
    config = configparser.ConfigParser()

    # Check if the config file exists; if not, create an empty file
    if not config_path.exists():
        print(f"Config file {config_file} not found. Creating an empty config file.")
        config_path.touch()  # Creates an empty file

    # Read the configuration from the file
    config.read(config_file)

    # Populate missing sections and keys with default values from _default_config
    should_write = False
    for section, options in _default_config.items():
        if section not in config:
            config.add_section(section)
        for key, default_value in options.items():
            if key not in config[section]:
                # Convert non-string values to string before writing them into the config
                config[section][key] = str(default_value) if default_value is not None else ''
                print(f"Missing config key {section}:{key}. Using default value: {str(default_value)}")
                should_write = True

    # Save the updated config back to the file
    if should_write:
        with open(config_file, 'w') as f:
            config.write(f)

    # Create and return the Config object with values from INI file
    return Config(
        telemetry_port=get_value_int("Network", "telemetry_port"),
        server_port=get_value_int("Network", "server_port"),
        udp_custom_action_code=get_value_int("Network", "udp_custom_action_code"),

        packet_capture_mode=PacketCaptureMode(get_value_str("Capture", "packet_capture_mode")),
        post_race_data_autosave=get_value_bool("Capture", "post_race_data_autosave"),

        refresh_interval=get_value_int("Display", "refresh_interval"),
        num_adjacent_cars=get_value_int("Display", "num_adjacent_cars"),
        disable_browser_autoload=get_value_bool("Display", "disable_browser_autoload"),

        log_file=get_value_str("Logging", "log_file"),
        log_file_size=get_value_int("Logging", "log_file_size"),
    )
