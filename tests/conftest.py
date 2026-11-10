import sys
from pathlib import Path

# Permite importar monitor.py e o pacote precos a partir dos testes.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
