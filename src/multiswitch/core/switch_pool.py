import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoAuthenticationException, NetMikoTimeoutException

from multiswitch.config.constants import INVENTORY_FILE, MAX_WORKERS
from multiswitch.models.switch_config import SwitchConfig
from multiswitch.models.switch_connection import SwitchConnection


class SwitchPool:
    def __init__(self, max_workers=MAX_WORKERS):
        self.switches = {}
        self.selected = set()
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sw")
        self.lock = threading.Lock()

    def add(self, config):
        cle = self._cle_switch(config.host, config.port)
        with self.lock:
            if cle in self.switches:
                return False
            self.switches[cle] = SwitchConnection(config=config)
        return True

    def _cle_switch(self, host, port):
        return f"{host}:{port}"

    def remove(self, host):
        with self.lock:
            if host not in self.switches:
                return False
            self.switches[host].disconnect()
            del self.switches[host]
            self.selected.discard(host)
            return True

    def connect_one(self, host):
        connexion = self.switches.get(host)
        if not connexion:
            return False, "Switch introuvable"
        try:
            connexion.handler = ConnectHandler(**connexion.config.to_netmiko_dict())
            connexion.connected = True
            connexion.error = ""
            connexion.last_seen = datetime.now()
            return True, "OK"
        except NetMikoAuthenticationException as erreur:
            connexion.error = str(erreur)
            return False, f"Auth echouee : {erreur}"
        except NetMikoTimeoutException as erreur:
            connexion.error = str(erreur)
            return False, f"Timeout : {erreur}"

    def connect_many(self, hosts):
        resultats = {}
        taches = {}
        for host in hosts:
            future = self.executor.submit(self.connect_one, host)
            taches[future] = host

        for future in as_completed(taches):
            host = taches[future]
            resultats[host] = future.result()
        return resultats

    def disconnect_many(self, hosts):
        for host in hosts:
            if host in self.switches:
                self.switches[host].disconnect()

    def resolve_host(self, spec):
        if spec in self.switches:
            return spec

        trouves = []
        for cle in self.switches:
            config = self.switches[cle].config
            if config.host == spec:
                trouves.append(cle)
        if len(trouves) == 1:
            return trouves[0]

        for host in self.switches:
            config = self.switches[host].config
            if config.alias == spec:
                return host
        return None

    def select(self, spec):
        texte = spec.strip()

        if texte in ("all", "*"):
            self.selected = set(self.switches.keys())
            return sorted(self.selected)

        if texte == "connected":
            hotes_selectionnes = set()
            for host in self.switches:
                if self.switches[host].connected:
                    hotes_selectionnes.add(host)
            self.selected = hotes_selectionnes
            return sorted(self.selected)

        if texte.startswith("@"):
            tag = texte[1:]
            hotes_selectionnes = set()
            for host in self.switches:
                config = self.switches[host].config
                for item in config.tags:
                    if item == tag:
                        hotes_selectionnes.add(host)
                        break
            self.selected = hotes_selectionnes
            return sorted(self.selected)

        alias_map = {}
        host_map = {}
        for host in self.switches:
            config = self.switches[host].config
            alias = config.alias
            if alias:
                alias_map[alias] = host
            if config.host not in host_map:
                host_map[config.host] = []
            host_map[config.host].append(host)

        hotes_selectionnes = set()
        for item in texte.split(","):
            valeur = item.strip()
            if valeur in self.switches:
                hotes_selectionnes.add(valeur)
                continue
            if valeur in alias_map:
                hotes_selectionnes.add(alias_map[valeur])
                continue
            if valeur in host_map and len(host_map[valeur]) == 1:
                hotes_selectionnes.add(host_map[valeur][0])

        self.selected = hotes_selectionnes
        return sorted(self.selected)

    def resolve_targets(self, spec):
        if spec is None:
            return sorted(self.switches.keys())
        if spec in ("all", "*"):
            return sorted(self.switches.keys())
        if spec in ("selected", "sel"):
            return sorted(self.selected)
        host = self.resolve_host(spec)
        if host:
            return [host]
        return []

    def run_command(self, command, hosts=None, config_mode=False):
        if hosts is None:
            cibles = sorted(self.selected)
        else:
            cibles = hosts

        resultats = {}
        if not cibles:
            return resultats

        taches = {}
        for host in cibles:
            future = self.executor.submit(self._run_command_on_host, host, command, config_mode)
            taches[future] = host

        for future in as_completed(taches):
            host, resultat = future.result()
            resultats[host] = resultat
        return resultats

    def _run_command_on_host(self, host, command, config_mode):
        connexion = self.switches.get(host)
        if not connexion:
            return host, (False, "Switch introuvable")
        if not connexion.connected:
            return host, (False, "Non connecte, lance connect d'abord")

        if config_mode:
            commandes = []
            for line in command.splitlines():
                line = line.strip()
                if line:
                    commandes.append(line)

            # Sur device_type linux, on evite send_config_set (privilege mode Netmiko).
            if connexion.config.device_type == "linux":
                sorties = []
                succes_global = True
                for commande in commandes:
                    succes, sortie = connexion.send_command(commande)
                    sorties.append(f"--- {commande} ---\n{sortie}")
                    if not succes:
                        succes_global = False
                return host, (succes_global, "\n".join(sorties))

            ok, out = connexion.send_config(commandes)
            return host, (ok, out)

        ok, out = connexion.send_command(command)
        return host, (ok, out)

    def run_script(self, script_path, hosts=None):
        if hosts is None:
            cibles = sorted(self.selected)
        else:
            cibles = hosts

        try:
            contenu = Path(script_path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as erreur:
            erreurs = {}
            for host in cibles:
                erreurs[host] = (False, str(erreur))
            return erreurs

        commandes = []
        for line in contenu.splitlines():
            valeur = line.strip()
            if not valeur:
                continue
            if valeur.startswith("#"):
                continue
            commandes.append(valeur)

        resultat_global = {}
        for commande in commandes:
            resultat_partiel = self.run_command(commande, hosts=cibles)
            for host in resultat_partiel:
                ok, sortie = resultat_partiel[host]
                if host not in resultat_global:
                    resultat_global[host] = (True, "")
                ancien_ok, ancienne_sortie = resultat_global[host]
                nouveau_ok = ancien_ok and ok
                nouvelle_sortie = ancienne_sortie + "\n--- " + commande + " ---\n" + sortie
                resultat_global[host] = (nouveau_ok, nouvelle_sortie)

        return resultat_global

    def save_inventory(self, path=INVENTORY_FILE):
        data = []
        for host in self.switches:
            data.append(self.switches[host].config.to_dict())
        texte = json.dumps(data, indent=2)
        Path(path).write_text(texte, encoding="utf-8")

    def load_inventory(self, path=INVENTORY_FILE):
        if not Path(path).exists():
            return 0

        contenu = Path(path).read_text(encoding="utf-8")
        data = json.loads(contenu)
        count = 0
        for item in data:
            config = SwitchConfig(**item)
            if self.add(config):
                count += 1
        return count
