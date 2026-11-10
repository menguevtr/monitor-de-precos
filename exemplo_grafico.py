"""Gera o gráfico de exemplo usado no README (com dados fictícios)."""

from datetime import datetime, timedelta
from pathlib import Path

from precos.grafico import gerar_grafico

produto = {"id": "exemplo", "nome": "Fone de ouvido Bluetooth", "preco_alvo": 199.90}
precos = [279.90, 279.90, 259.90, 264.90, 249.90, 229.90, 239.90,
          219.90, 219.90, 209.90, 214.90, 199.00, 189.90, 194.90]
inicio = datetime(2026, 10, 27, 9)
historico = [{"data_hora": inicio + timedelta(days=i), "preco": p} for i, p in enumerate(precos)]

caminho = gerar_grafico(produto, historico, Path(__file__).parent / "docs")
print(f"Gráfico salvo em {caminho}")
