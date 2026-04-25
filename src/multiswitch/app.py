import sys

from rich.console import Console

from multiswitch.config.constants import INVENTORY_FILE, VERSION
from multiswitch.shell.multiswitch_shell import MultiSwitchShell

console = Console()


def run():
    import argparse

    parser = argparse.ArgumentParser(
        description="MultiSwitch Shell - gestion parallele HP/Aruba",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--inventory",
        "-i",
        default=INVENTORY_FILE,
        help=f"Fichier d'inventaire JSON (defaut : {INVENTORY_FILE})",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"MultiSwitch Shell v{VERSION}",
    )
    args = parser.parse_args()

    try:
        import netmiko  # noqa: F401
    except ImportError:
        console.print("[red]netmiko n'est pas installe.[/red]")
        console.print("pip install netmiko")
        sys.exit(1)

    shell = MultiSwitchShell(inventory=args.inventory)
    shell.run()
