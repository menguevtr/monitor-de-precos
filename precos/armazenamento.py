"""Salva os produtos monitorados (JSON) e o histórico de preços (CSV)."""

import csv
import json
from datetime import datetime
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"
ARQUIVO_PRODUTOS = PASTA_DADOS / "produtos.json"
ARQUIVO_HISTORICO = PASTA_DADOS / "historico.csv"
COLUNAS_HISTORICO = ["data_hora", "produto_id", "nome", "preco"]


class Armazenamento:
    def __init__(self, pasta=PASTA_DADOS):
        self.pasta = Path(pasta)
        self.arquivo_produtos = self.pasta / "produtos.json"
        self.arquivo_historico = self.pasta / "historico.csv"
        self.pasta.mkdir(parents=True, exist_ok=True)

    # ---------- Produtos ----------

    def carregar_produtos(self):
        if not self.arquivo_produtos.exists():
            return []
        with open(self.arquivo_produtos, encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def salvar_produtos(self, produtos):
        with open(self.arquivo_produtos, "w", encoding="utf-8") as arquivo:
            json.dump(produtos, arquivo, ensure_ascii=False, indent=2)

    def adicionar_produto(self, nome, url, preco_alvo, seletor=None):
        produtos = self.carregar_produtos()
        if any(p["url"] == url for p in produtos):
            raise ValueError("Esse produto já está sendo monitorado.")
        novo_id = max((p["id"] for p in produtos), default=0) + 1
        produto = {
            "id": novo_id,
            "nome": nome,
            "url": url,
            "preco_alvo": preco_alvo,
            "seletor": seletor,
            "ultimo_preco": None,
            "menor_preco": None,
        }
        produtos.append(produto)
        self.salvar_produtos(produtos)
        return produto

    def remover_produto(self, produto_id):
        produtos = self.carregar_produtos()
        restantes = [p for p in produtos if p["id"] != produto_id]
        if len(restantes) == len(produtos):
            raise ValueError(f"Não existe produto com id {produto_id}.")
        self.salvar_produtos(restantes)

    def atualizar_preco(self, produto_id, preco):
        produtos = self.carregar_produtos()
        for produto in produtos:
            if produto["id"] == produto_id:
                produto["ultimo_preco"] = preco
                if produto["menor_preco"] is None or preco < produto["menor_preco"]:
                    produto["menor_preco"] = preco
        self.salvar_produtos(produtos)

    # ---------- Histórico ----------

    def registrar_preco(self, produto, preco, momento=None):
        momento = momento or datetime.now()
        novo_arquivo = not self.arquivo_historico.exists()
        with open(self.arquivo_historico, "a", newline="", encoding="utf-8") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_HISTORICO)
            if novo_arquivo:
                escritor.writeheader()
            escritor.writerow({
                "data_hora": momento.isoformat(timespec="seconds"),
                "produto_id": produto["id"],
                "nome": produto["nome"],
                "preco": f"{preco:.2f}",
            })

    def historico(self, produto_id):
        if not self.arquivo_historico.exists():
            return []
        with open(self.arquivo_historico, encoding="utf-8") as arquivo:
            return [
                {"data_hora": datetime.fromisoformat(linha["data_hora"]),
                 "preco": float(linha["preco"])}
                for linha in csv.DictReader(arquivo)
                if int(linha["produto_id"]) == produto_id
            ]
