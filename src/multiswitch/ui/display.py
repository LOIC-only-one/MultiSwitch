from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from multiswitch.config.constants import COLORS, VERSION

console = Console()


def host_color(host, switches):
    hosts = sorted(switches.keys())
    index = 0
    if host in hosts:
        index = hosts.index(host) % len(COLORS)
    return COLORS[index]


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]MultiSwitch Shell[/bold cyan]  [dim]v" + VERSION + "[/dim]\n"
            "[dim]Gestion parallele HP/Comware/Aruba via Netmiko[/dim]\n\n"
            "[dim]Tape [/dim][bold]help[/bold][dim] pour la liste des commandes[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )


def print_results(results, pool):
    if not results:
        console.print("[dim]Aucun resultat.[/dim]")
        return

    panneaux = []
    hotes = sorted(results.keys())
    for host in hotes:
        succes, sortie = results[host]
        connexion = pool.switches.get(host)
        etiquette = host
        if connexion:
            etiquette = connexion.config.label
        couleur = host_color(host, pool.switches)
        icone = "x"
        if succes:
            icone = "v"
        titre = f"[{couleur}]{icone} {etiquette}[/{couleur}] [dim]({host})[/dim]"
        style = "red"
        if succes:
            style = couleur
        corps = sortie.strip()
        if not corps:
            corps = "[dim](vide)[/dim]"
        panneaux.append(Panel(corps, title=titre, border_style=style, padding=(0, 1)))

    max_len = 0
    for host in results:
        _, sortie = results[host]
        if len(sortie) > max_len:
            max_len = len(sortie)

    if len(panneaux) > 1 and max_len < 120:
        cols = len(panneaux)
        if cols > 3:
            cols = 3
        i = 0
        while i < len(panneaux):
            console.print(Columns(panneaux[i:i + cols], equal=True, expand=True))
            i += cols
        return

    for panneau in panneaux:
        console.print(panneau)


def print_status_table(pool):
    table = Table(
        title="[bold]Switches[/bold]",
        box=box.ROUNDED,
        border_style="dim",
        header_style="bold dim",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Host", style="cyan")
    table.add_column("Alias", style="bright_cyan")
    table.add_column("Type", style="dim")
    table.add_column("Port", style="dim", justify="right")
    table.add_column("Etat", justify="center")
    table.add_column("Selectionne", justify="center")
    table.add_column("Tags", style="dim")
    table.add_column("Dernier contact", style="dim")

    index = 1
    for host, connexion in sorted(pool.switches.items()):
        config = connexion.config

        if connexion.connected:
            etat = "[green]connecte[/green]"
        elif connexion.error:
            etat = "[red]" + connexion.error[:30] + "[/red]"
        else:
            etat = "[dim]deconnecte[/dim]"

        selectionne = ""
        if host in pool.selected:
            selectionne = "*"

        dernier_contact = "-"
        if connexion.last_seen:
            dernier_contact = connexion.last_seen.strftime("%H:%M:%S")

        tags = "-"
        if config.tags:
            tags = ", ".join(config.tags)

        alias = config.alias
        if not alias:
            alias = "-"

        table.add_row(
            str(index),
            host,
            alias,
            config.device_type,
            str(config.port),
            etat,
            selectionne,
            tags,
            dernier_contact,
        )
        index += 1

    console.print(table)


def print_help():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("cmd", style="bold cyan", no_wrap=True)
    table.add_column("description", style="dim")

    rows = [
        ("add <host> <user> <pass> [type] [port] [alias]", "Ajoute un switch"),
        ("list / ls", "Liste les switches"),
        ("connect [host|alias|selected|all]", "Ouvre les connexions SSH"),
        ("disconnect [host|alias|selected|all]", "Ferme les connexions SSH"),
        ("select <spec>", "Selection all, connected, @tag, host1,host2"),
        ("<commande libre>", "Envoi sur selection"),
        ("conf <cmd1> ; <cmd2>", "Mode config"),
        ("script <fichier>", "Execute un fichier"),
        ("save [fichier]", "Sauvegarde inventaire"),
        ("load [fichier]", "Charge inventaire"),
        ("aruba-preview <profil.json>", "Affiche commandes Aruba generees"),
        ("aruba-apply <profil.json>", "Applique le profil Aruba sur selection"),
        ("exit", "Quitte le shell"),
    ]

    for cmd, desc in rows:
        table.add_row(Text(cmd), desc)

    console.print(Panel(table, title="[bold]Aide[/bold]", border_style="dim"))
