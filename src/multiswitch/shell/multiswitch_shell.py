import os
import time
import traceback
from concurrent.futures import as_completed
from pathlib import Path

from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from multiswitch.config.constants import HISTORY_FILE, HP_DEVICE_TYPES, INVENTORY_FILE
from multiswitch.core.switch_pool import SwitchPool
from multiswitch.features.aruba.provisioning import ArubaProvisioning
from multiswitch.models.switch_config import SwitchConfig
from multiswitch.shell.readline_support import get_readline_module
from multiswitch.ui.display import console, print_banner, print_help, print_results, print_status_table


class MultiSwitchShell:
    def __init__(self, inventory=INVENTORY_FILE):
        self.pool = SwitchPool()
        self.inventory_path = inventory
        self.aruba = ArubaProvisioning()
        self.readline, self.readline_ok = get_readline_module()
        self.setup_readline()

    def setup_readline(self):
        if not self.readline_ok:
            console.print("[yellow]Auto-completion indisponible. Installe pyreadline3 sous Windows.[/yellow]")
            return

        try:
            self.readline.read_history_file(HISTORY_FILE)
        except FileNotFoundError:
            pass

        self.readline.set_history_length(500)

        commands = [
            "add", "remove", "list", "ls", "connect", "disconnect",
            "select", "deselect", "conf", "script", "save", "load",
            "alias", "tag", "untag", "ping", "clear", "help", "exit", "quit",
            "all", "connected", "selected", "aruba-preview", "aruba-apply",
        ]

        def completer(text, state):
            options = []

            for item in commands:
                if item.startswith(text):
                    options.append(item)

            for host in self.pool.switches:
                if host.startswith(text):
                    options.append(host)

            for host in self.pool.switches:
                alias = self.pool.switches[host].config.alias
                if alias and alias.startswith(text):
                    options.append(alias)

            if state < len(options):
                return options[state]
            return None

        self.readline.set_completer(completer)
        self.readline.parse_and_bind("tab: complete")

    def prompt(self):
        nb_selectionnes = len(self.pool.selected)
        nb_total = len(self.pool.switches)
        nb_connectes = 0

        for host in self.pool.switches:
            if self.pool.switches[host].connected:
                nb_connectes += 1

        return f"msw [{nb_selectionnes}/{nb_total}]({nb_connectes}v)> "

    def save_history(self):
        if not self.readline_ok:
            return
        self.readline.write_history_file(HISTORY_FILE)

    def print_connect_usage(self):
        console.print("Usage : connect [host|alias|selected|all]", style="dim", markup=False)

    def print_disconnect_usage(self):
        console.print("Usage : disconnect [host|alias|selected|all]", style="dim", markup=False)

    def _selection_est_linux(self):
        if not self.pool.selected:
            return False
        for host in self.pool.selected:
            if host not in self.pool.switches:
                continue
            type_switch = self.pool.switches[host].config.device_type
            if type_switch != "linux":
                return False
        return True

    def _traduire_commande_linux_lab(self, ligne):
        commande = ligne.strip().lower()
        if commande in ("show vl", "show vlan", "show vlan brief"):
            return "ip link"
        if commande in ("show int", "show interfaces", "show ip int brief"):
            return "ip -br a"
        if commande in ("show mac", "show mac-address", "show mac address-table"):
            return "ip neigh"
        return ligne

    def handle(self, line):
        line = line.strip()
        if not line:
            return True

        self.save_history()
        parts = line.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("exit", "quit"):
            console.print("[dim]Fermeture des connexions...[/dim]")
            all_hosts = sorted(self.pool.switches.keys())
            self.pool.disconnect_many(all_hosts)
            self.pool.executor.shutdown(wait=False)
            return False

        if cmd == "help":
            print_help()
            return True

        if cmd == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            return True

        if cmd in ("list", "ls"):
            print_status_table(self.pool)
            return True

        if cmd == "add":
            return self.handle_add(args)

        if cmd == "remove":
            return self.handle_remove(args)

        if cmd == "connect":
            return self.handle_connect(args)

        if cmd == "disconnect":
            return self.handle_disconnect(args)

        if cmd == "select":
            return self.handle_select(args)

        if cmd == "deselect":
            return self.handle_deselect(args)

        if cmd == "ping":
            return self.handle_ping()

        if cmd == "conf":
            return self.handle_conf(args)

        if cmd == "script":
            return self.handle_script(args)

        if cmd == "save":
            return self.handle_save(args)

        if cmd == "load":
            return self.handle_load(args)

        if cmd == "alias":
            return self.handle_alias(args)

        if cmd == "tag":
            return self.handle_tag(args)

        if cmd == "untag":
            return self.handle_untag(args)

        if cmd == "aruba-preview":
            return self.handle_aruba_preview(args)

        if cmd == "aruba-apply":
            return self.handle_aruba_apply(args)

        return self.handle_free_command(line)

    def handle_add(self, args):
        if len(args) < 3:
            console.print("[red]Usage : add <host> <user> <pass> [type] [port] [alias][/red]")
            return True

        host = args[0]
        utilisateur = args[1]
        mot_de_passe = args[2]

        if len(args) > 3:
            type_brut = args[3].lower()
            device_type = HP_DEVICE_TYPES.get(type_brut, args[3])
        else:
            device_type = "hp_procurve"

        port = 22
        if len(args) > 4:
            port = int(args[4])

        alias = ""
        if len(args) > 5:
            alias = args[5]

        config = SwitchConfig(
            host=host,
            username=utilisateur,
            password=mot_de_passe,
            device_type=device_type,
            port=port,
            alias=alias,
        )

        if self.pool.add(config):
            console.print(f"[green]+ {host}[/green] ajoute (type=[cyan]{device_type}[/cyan])")
        else:
            console.print(f"[yellow]{host} existe deja.[/yellow]")

        return True

    def handle_remove(self, args):
        if not args:
            console.print("[red]Usage : remove <host|alias>[/red]")
            return True

        host = self.pool.resolve_host(args[0])
        if host and self.pool.remove(host):
            console.print(f"[green]Supprime : {host}[/green]")
        else:
            console.print(f"[red]Switch introuvable : {args[0]}[/red]")
        return True

    def handle_connect(self, args):
        if args and args[0] in ("-h", "--help", "?"):
            self.print_connect_usage()
            return True

        if len(args) > 1:
            self.print_connect_usage()
            return True

        cible = None
        if args:
            cible = args[0]

        cibles = self.pool.resolve_targets(cible)

        if not cibles:
            console.print("[yellow]Aucun switch a connecter.[/yellow]")
            return True

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"Connexion a {len(cibles)} switch(es)...", total=len(cibles))
            futures = {}
            for host in cibles:
                future = self.pool.executor.submit(self.pool.connect_one, host)
                futures[future] = host

            results = {}
            for future in as_completed(futures):
                host = futures[future]
                succes, message = future.result()
                results[host] = (succes, message)
                progress.advance(task)

        for host in sorted(results.keys()):
            succes, message = results[host]
            etiquette = self.pool.switches[host].config.label
            if succes:
                console.print(f"  [green]v[/green] {etiquette} ({host})")
            else:
                console.print(f"  [red]x[/red] {etiquette} ({host}) - {message}")

        console.print("[dim]Astuce: tape `select all` puis une commande.[/dim]")

        return True

    def handle_disconnect(self, args):
        if args and args[0] in ("-h", "--help", "?"):
            self.print_disconnect_usage()
            return True

        if len(args) > 1:
            self.print_disconnect_usage()
            return True

        cible = None
        if args:
            cible = args[0]

        cibles = self.pool.resolve_targets(cible)
        if not cibles:
            console.print("[yellow]Aucun switch a deconnecter.[/yellow]")
            return True

        self.pool.disconnect_many(cibles)
        console.print(f"[green]{len(cibles)} session(s) fermee(s).[/green]")
        return True

    def handle_select(self, args):
        spec = "all"
        if args:
            spec = " ".join(args)
        selection = self.pool.select(spec)
        console.print(f"[yellow]* {len(selection)} switch(es) selectionne(s)[/yellow]")

        for host in selection:
            etiquette = self.pool.switches[host].config.label
            console.print(f"   [dim]-[/dim] {etiquette} ({host})")
        return True

    def handle_deselect(self, args):
        spec = "all"
        if args:
            spec = " ".join(args)

        if spec in ("all", "*"):
            self.pool.selected.clear()
            console.print("[dim]Selection videe.[/dim]")
            return True

        host = self.pool.resolve_host(spec)
        if host:
            self.pool.selected.discard(host)
            console.print(f"[dim]{host} retire de la selection.[/dim]")
            return True

        console.print(f"[red]Switch introuvable : {spec}[/red]")
        return True

    def handle_ping(self):
        if not self.pool.selected:
            console.print("[yellow]Aucun switch selectionne.[/yellow]")
            return True

        for host in sorted(self.pool.selected):
            if host not in self.pool.switches:
                continue
            vivant = self.pool.switches[host].is_alive()
            etiquette = self.pool.switches[host].config.label
            if vivant:
                console.print(f"  [green]alive[/green] {etiquette} ({host})")
            else:
                console.print(f"  [red]dead[/red] {etiquette} ({host})")
        return True

    def handle_conf(self, args):
        if not self.pool.selected:
            console.print("[yellow]Aucun switch selectionne. Lance select all d'abord.[/yellow]")
            return True

        text = " ".join(args)
        commands = []
        for item in text.split(";"):
            value = item.strip()
            if value:
                commands.append(value)

        if not commands:
            console.print("[red]Usage : conf <cmd1> ; <cmd2> ; ...[/red]")
            return True

        joined = "\n".join(commands)
        results = self.pool.run_command(joined, config_mode=True)
        print_results(results, self.pool)
        return True

    def handle_script(self, args):
        if not args:
            console.print("[red]Usage : script <fichier>[/red]")
            return True

        path = args[0]
        if not Path(path).exists():
            console.print(f"[red]Fichier introuvable : {path}[/red]")
            return True

        if not self.pool.selected:
            console.print("[yellow]Aucun switch selectionne.[/yellow]")
            return True

        results = self.pool.run_script(path)
        print_results(results, self.pool)
        return True

    def handle_save(self, args):
        path = self.inventory_path
        if args:
            path = args[0]
        self.pool.save_inventory(path)
        console.print(f"[green]Inventaire sauvegarde -> {path}[/green]")
        return True

    def handle_load(self, args):
        path = self.inventory_path
        if args:
            path = args[0]
        count = self.pool.load_inventory(path)
        console.print(f"[green]{count} switch(es) charge(s) depuis {path}[/green]")
        return True

    def handle_alias(self, args):
        if len(args) < 2:
            console.print("[red]Usage : alias <host> <alias>[/red]")
            return True

        host = self.pool.resolve_host(args[0])
        if not host:
            console.print(f"[red]Switch introuvable : {args[0]}[/red]")
            return True

        self.pool.switches[host].config.alias = args[1]
        console.print(f"[green]Alias defini : {host} -> {args[1]}[/green]")
        return True

    def handle_tag(self, args):
        if len(args) < 2:
            console.print("[red]Usage : tag <host> <tag>[/red]")
            return True

        host = self.pool.resolve_host(args[0])
        if not host:
            console.print(f"[red]Switch introuvable : {args[0]}[/red]")
            return True

        self.pool.switches[host].config.tags.append(args[1])
        console.print(f"[green]Tag ajoute : {host} @{args[1]}[/green]")
        return True

    def handle_untag(self, args):
        if len(args) < 2:
            console.print("[red]Usage : untag <host> <tag>[/red]")
            return True

        host = self.pool.resolve_host(args[0])
        if not host:
            console.print(f"[red]Switch introuvable : {args[0]}[/red]")
            return True

        try:
            self.pool.switches[host].config.tags.remove(args[1])
            console.print(f"[green]Tag retire : {host} @{args[1]}[/green]")
        except ValueError:
            console.print("[yellow]Tag introuvable.[/yellow]")
        return True

    def handle_aruba_preview(self, args):
        if not args:
            console.print("[red]Usage : aruba-preview <profil.json>[/red]")
            return True

        ok, commands, message = self.aruba.preview(args[0])
        if not ok:
            console.print(f"[red]Profil invalide : {message}[/red]")
            return True

        console.print(f"[green]{len(commands)} commande(s) generee(s).[/green]")
        for command in commands:
            console.print("  " + command)
        return True

    def handle_aruba_apply(self, args):
        if not args:
            console.print("[red]Usage : aruba-apply <profil.json>[/red]")
            return True

        if not self.pool.selected:
            console.print("[yellow]Aucun switch selectionne.[/yellow]")
            return True

        ok, commands, message = self.aruba.preview(args[0])
        if not ok:
            console.print(f"[red]Profil invalide : {message}[/red]")
            return True

        joined = "\n".join(commands)
        results = self.pool.run_command(joined, config_mode=True)
        print_results(results, self.pool)
        return True

    def handle_free_command(self, line):
        if not self.pool.selected:
            console.print("[yellow]Aucun switch selectionne. Utilise select all ou select <host>[/yellow]")
            return True

        ligne_a_executer = line
        if self._selection_est_linux():
            ligne_a_executer = self._traduire_commande_linux_lab(line)
            if ligne_a_executer != line:
                console.print(f"[dim]Traduction lab linux: {line} -> {ligne_a_executer}[/dim]")

        debut = time.time()
        resultats = self.pool.run_command(ligne_a_executer)
        duree = time.time() - debut
        print_results(resultats, self.pool)

        nb_ok = 0
        for host in resultats:
            succes, _ = resultats[host]
            if succes:
                nb_ok += 1

        total = len(resultats)
        console.print(f"[dim]{nb_ok}/{total} OK en {duree:.2f}s[/dim]")
        return True

    def run(self):
        print_banner()

        if Path(self.inventory_path).exists():
            count = self.pool.load_inventory(self.inventory_path)
            if count:
                console.print(f"[dim]Inventaire charge : {count} switch(es)[/dim]")

        console.print()

        while True:
            try:
                line = input(f"\033[1;36m{self.prompt()}\033[0m")
            except (EOFError, KeyboardInterrupt):
                console.print()
                console.print("[dim]^C - tape exit pour quitter.[/dim]")
                continue

            try:
                if not self.handle(line):
                    break
            except Exception as error:
                console.print(f"[red]Erreur inattendue : {error}[/red]")
                if os.getenv("MSSH_DEBUG"):
                    traceback.print_exc()
