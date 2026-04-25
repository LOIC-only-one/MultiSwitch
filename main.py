#!/usr/bin/env python3
"""Entry point du projet MultiSwitch."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from multiswitch.app import run  # noqa: E402


if __name__ == "__main__":
    run()
