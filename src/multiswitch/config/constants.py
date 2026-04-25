import os

VERSION = "2.0.0"
HISTORY_FILE = os.path.expanduser("~/.multiswitch_history")
INVENTORY_FILE = "switches.json"
MAX_WORKERS = 20
CMD_TIMEOUT = 30
CONNECT_TIMEOUT = 15
RECONNECT_ATTEMPTS = 2

HP_DEVICE_TYPES = {
    "procurve": "hp_procurve",
    "comware": "hp_comware",
    "aruba": "aruba_os",
    "arubaos": "aruba_os",
    "linux": "linux",
    "cisco": "cisco_ios",
    "juniper": "juniper_junos",
}

COLORS = [
    "cyan",
    "green",
    "yellow",
    "magenta",
    "blue",
    "bright_cyan",
    "bright_green",
    "bright_yellow",
    "bright_magenta",
    "bright_blue",
    "bright_red",
]
