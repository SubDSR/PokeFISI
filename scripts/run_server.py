"""Punto de entrada principal del proyecto PokeFISI.

Uso equivalente a: python -m backend.main

Ejemplos:
    python scripts/run_server.py --mode serve
    python scripts/run_server.py --mode battle --agent1 minimax --agent2 heuristic
    python scripts/run_server.py --mode experiment --battles 30
"""

import os
import sys

# Agregar la raíz del proyecto al path para que los imports de backend funcionen
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import main  # noqa: E402

if __name__ == "__main__":
    main()
