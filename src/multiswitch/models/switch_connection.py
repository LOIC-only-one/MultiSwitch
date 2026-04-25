import threading
import time
from dataclasses import dataclass, field
from datetime import datetime

from netmiko import ConnectHandler

from multiswitch.config.constants import CMD_TIMEOUT, RECONNECT_ATTEMPTS
from multiswitch.models.switch_config import SwitchConfig


@dataclass
class SwitchConnection:
    config: SwitchConfig
    handler: object = None
    connected: bool = False
    error: str = ""
    last_seen: object = None
    lock: object = field(default_factory=threading.Lock)

    def is_alive(self):
        if not self.handler:
            return False
        if not self.connected:
            return False
        try:
            return self.handler.is_alive()
        except Exception:
            return False

    def send_command(self, command):
        with self.lock:
            try:
                if not self.is_alive():
                    self.reconnect()
                output = self.handler.send_command(
                    command,
                    read_timeout=CMD_TIMEOUT,
                    strip_prompt=True,
                    strip_command=True,
                )
                self.last_seen = datetime.now()
                return True, output
            except Exception as error:
                self.connected = False
                self.error = str(error)
                return False, f"[ERROR] {error}"

    def send_config(self, commands):
        with self.lock:
            try:
                if not self.is_alive():
                    self.reconnect()
                output = self.handler.send_config_set(commands, read_timeout=CMD_TIMEOUT)
                self.last_seen = datetime.now()
                return True, output
            except Exception as error:
                self.connected = False
                self.error = str(error)
                return False, f"[ERROR] {error}"

    def reconnect(self):
        attempt = 0
        while attempt < RECONNECT_ATTEMPTS:
            try:
                if self.handler:
                    try:
                        self.handler.disconnect()
                    except Exception:
                        pass
                self.handler = ConnectHandler(**self.config.to_netmiko_dict())
                self.connected = True
                self.error = ""
                return
            except Exception as error:
                self.error = str(error)
                attempt += 1
                time.sleep(2)
        raise ConnectionError(f"Reconnexion echouee : {self.error}")

    def disconnect(self):
        with self.lock:
            if self.handler:
                try:
                    self.handler.disconnect()
                except Exception:
                    pass
            self.connected = False
            self.handler = None
