import json
from pathlib import Path
from typing import Dict, List, Tuple


class ArubaProvisioning:
    """Construit des commandes Aruba a partir d'un profil JSON simple."""

    def load_profile(self, profile_path: str) -> Dict:
        content = Path(profile_path).read_text(encoding="utf-8")
        data = json.loads(content)
        return data

    def build_commands(self, profile: Dict) -> List[str]:
        commands: List[str] = []

        self._add_identity(commands, profile)
        self._add_dns(commands, profile)
        self._add_ntp(commands, profile)
        self._add_snmp(commands, profile)
        self._add_vlans(commands, profile)
        self._add_interfaces(commands, profile)
        self._add_default_gateway(commands, profile)
        self._add_security(commands, profile)
        self._add_banner(commands, profile)

        commands.append("write memory")
        return commands

    def _add_identity(self, commands: List[str], profile: Dict):
        hostname = profile.get("hostname", "")
        if hostname:
            commands.append(f"hostname {hostname}")

    def _add_dns(self, commands: List[str], profile: Dict):
        dns_servers = profile.get("dns_servers", [])
        for server in dns_servers:
            commands.append(f"ip dns server-address {server}")

        domain_name = profile.get("domain_name", "")
        if domain_name:
            commands.append(f"ip domain-name {domain_name}")

    def _add_ntp(self, commands: List[str], profile: Dict):
        ntp_servers = profile.get("ntp_servers", [])
        for server in ntp_servers:
            commands.append(f"ntp server {server}")
        if ntp_servers:
            commands.append("ntp enable")

    def _add_snmp(self, commands: List[str], profile: Dict):
        snmp = profile.get("snmp", {})
        community = snmp.get("community", "")
        location = snmp.get("location", "")
        contact = snmp.get("contact", "")

        if community:
            commands.append(f"snmp-server community {community} operator")
        if location:
            commands.append(f"snmp-server location {location}")
        if contact:
            commands.append(f"snmp-server contact {contact}")

    def _add_vlans(self, commands: List[str], profile: Dict):
        vlans = profile.get("vlans", [])
        for vlan in vlans:
            vlan_id = vlan.get("id")
            name = vlan.get("name", "")
            ip = vlan.get("ip", "")
            mask = vlan.get("mask", "")

            if vlan_id is None:
                continue

            commands.append(f"vlan {vlan_id}")
            if name:
                commands.append(f"name {name}")
            if ip and mask:
                commands.append(f"ip address {ip} {mask}")
            commands.append("exit")

    def _add_interfaces(self, commands: List[str], profile: Dict):
        access_ports = profile.get("access_ports", [])
        for item in access_ports:
            port = item.get("port", "")
            vlan = item.get("vlan")
            if not port:
                continue
            commands.append(f"interface {port}")
            if vlan is not None:
                commands.append(f"untagged vlan {vlan}")
            commands.append("exit")

        trunks = profile.get("trunks", [])
        for item in trunks:
            port = item.get("port", "")
            native_vlan = item.get("native_vlan")
            allowed_vlans = item.get("allowed_vlans", [])

            if not port:
                continue

            commands.append(f"interface {port}")
            if native_vlan is not None:
                commands.append(f"untagged vlan {native_vlan}")
            for vlan in allowed_vlans:
                commands.append(f"tagged vlan {vlan}")
            commands.append("exit")

    def _add_default_gateway(self, commands: List[str], profile: Dict):
        gateway = profile.get("default_gateway", "")
        if gateway:
            commands.append(f"ip default-gateway {gateway}")

    def _add_security(self, commands: List[str], profile: Dict):
        admins = profile.get("admins", [])
        for admin in admins:
            username = admin.get("username", "")
            password = admin.get("password", "")
            role = admin.get("role", "manager")

            if not username or not password:
                continue

            commands.append(f"password manager user-name {username} plaintext {password}")
            if role == "operator":
                commands.append(f"password operator user-name {username} plaintext {password}")

        ssh_enabled = profile.get("ssh_enabled", True)
        if ssh_enabled:
            commands.append("ip ssh")

    def _add_banner(self, commands: List[str], profile: Dict):
        banner = profile.get("banner", "")
        if not banner:
            return
        commands.append("banner motd")
        commands.append(banner)
        commands.append("end")

    def preview(self, profile_path: str) -> Tuple[bool, List[str], str]:
        try:
            profile = self.load_profile(profile_path)
            commands = self.build_commands(profile)
            return True, commands, "OK"
        except Exception as error:
            return False, [], str(error)
