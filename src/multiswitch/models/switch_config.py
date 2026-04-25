from dataclasses import dataclass, field

from multiswitch.config.constants import CONNECT_TIMEOUT


@dataclass
class SwitchConfig:
    host: str
    username: str
    password: str
    device_type: str = "hp_procurve"
    port: int = 22
    secret: str = ""
    alias: str = ""
    tags: list = field(default_factory=list)

    @property
    def label(self):
        if self.alias:
            return self.alias
        return self.host

    def to_netmiko_dict(self):
        data = {
            "device_type": self.device_type,
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "port": self.port,
            "conn_timeout": CONNECT_TIMEOUT,
            "auth_timeout": CONNECT_TIMEOUT,
            "banner_timeout": CONNECT_TIMEOUT,
            "fast_cli": False,
        }
        if self.secret:
            data["secret"] = self.secret
        return data

    def to_dict(self):
        return {
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "device_type": self.device_type,
            "port": self.port,
            "secret": self.secret,
            "alias": self.alias,
            "tags": self.tags,
        }
