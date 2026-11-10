"""Monitor de preços — linha de comando.

Exemplos:
    python monitor.py adicionar "Fone JBL" https://loja.com/fone --alvo 199.90
    python monitor.py listar
    python monitor.py verificar
    python monitor.py grafico 1
    python monitor.py remover 1
"""

import argparse
import sys
import time

import requests

from precos.alertas import alertar, formatar_reais
from precos.armazenamento import Armazenamento
from precos.extrator import PrecoNaoEncontrado, buscar_preco
from precos.grafico import gerar_grafico

PAUSA_ENTRE_LOJAS = 3  # segundos, para não sobrecarregar os sites


def deve_alertar(produto, preco):
    """Alerta quando o preço chega no alvo pela primeira vez ou cai ainda mais."""
    if preco > produto["preco_alvo"]:
        return False
    anterior = produto["ultimo_preco"]
    return anterior is None or anterior > produto["preco_alvo"] or preco < anterior


def comando_adicionar(args, banco):
    print("Buscando o preço atual...")
    try:
        preco = buscar_preco(args.url, args.seletor)
    except PrecoNaoEncontrado as erro:
        print(f"Erro: {erro}")
        return 1
    except requests.RequestException as erro:
        print(f"Erro ao acessar a página: {erro}")
        return 1

    produto = banco.adicionar_produto(args.nome, args.url, args.alvo, args.seletor)
    banco.registrar_preco(produto, preco)
    print(f"✅ \"{produto['nome']}\" adicionado (id {produto['id']}). "
          f"Preço atual: {formatar_reais(preco)} | Alvo: {formatar_reais(args.alvo)}")
    if deve_alertar(produto, preco):
        alertar(produto, preco)
    banco.atualizar_preco(produto["id"], preco)
    return 0


def comando_listar(args, banco):
    produtos = banco.carregar_produtos()
    if not produtos:
        print("Nenhum produto monitorado ainda. Use o comando 'adicionar'.")
        return 0

    print(f"{'ID':<4}{'PRODUTO':<32}{'ATUAL':>14}{'MENOR':>14}{'ALVO':>14}")
    print("-" * 78)
    for p in produtos:
        atual = formatar_reais(p["ultimo_preco"]) if p["ultimo_preco"] else "—"
        menor = formatar_reais(p["menor_preco"]) if p["menor_preco"] else "—"
        marcador = " 🔔" if p["ultimo_preco"] and p["ultimo_preco"] <= p["preco_alvo"] else ""
        print(f"{p['id']:<4}{p['nome'][:30]:<32}{atual:>14}{menor:>14}"
              f"{formatar_reais(p['preco_alvo']):>14}{marcador}")
    return 0


def comando_verificar(args, banco):
    produtos = banco.carregar_produtos()
    if not produtos:
        print("Nenhum produto monitorado ainda.")
        return 0

    erros = 0
    for indice, produto in enumerate(produtos):
        if indice > 0:
            time.sleep(PAUSA_ENTRE_LOJAS)
        try:
            preco = buscar_preco(produto["url"], produto.get("seletor"))
        except (PrecoNaoEncontrado, requests.RequestException) as erro:
            print(f"⚠️  {produto['nome']}: {erro}")
            erros += 1
            continue

        anterior = produto["ultimo_preco"]
        variacao = ""
        if anterior:
            diferenca = preco - anterior
            if abs(diferenca) >= 0.01:
                seta = "▼" if diferenca < 0 else "▲"
                variacao = f" ({seta} {formatar_reais(abs(diferenca))})"
        print(f"• {produto['nome']}: {formatar_reais(preco)}{variacao}")

        banco.registrar_preco(produto, preco)
        if deve_alertar(produto, preco):
            alertar(produto, preco)
        banco.atualizar_preco(produto["id"], preco)

    return 1 if erros == len(produtos) else 0


def comando_grafico(args, banco):
    produto = next((p for p in banco.carregar_produtos() if p["id"] == args.id), None)
    if produto is None:
        print(f"Não existe produto com id {args.id}.")
        return 1
    try:
        caminho = gerar_grafico(produto, banco.historico(produto["id"]), banco.pasta / "graficos")
    except ValueError as erro:
        print(erro)
        return 1
    print(f"📈 Gráfico salvo em: {caminho}")
    return 0


def comando_remover(args, banco):
    try:
        banco.remover_produto(args.id)
    except ValueError as erro:
        print(erro)
        return 1
    print(f"Produto {args.id} removido.")
    return 0


def criar_parser():
    parser = argparse.ArgumentParser(
        description="Monitora preços de produtos e avisa quando baixam.")
    sub = parser.add_subparsers(dest="comando", required=True)

    adicionar = sub.add_parser("adicionar", help="começa a monitorar um produto")
    adicionar.add_argument("nome", help="nome para identificar o produto")
    adicionar.add_argument("url", help="link da página do produto")
    adicionar.add_argument("--alvo", type=float, required=True,
                           help="preço que você quer pagar (ex.: 199.90)")
    adicionar.add_argument("--seletor", help="seletor CSS do preço, se a loja precisar")
    adicionar.set_defaults(funcao=comando_adicionar)

    listar = sub.add_parser("listar", help="mostra os produtos monitorados")
    listar.set_defaults(funcao=comando_listar)

    verificar = sub.add_parser("verificar", help="consulta os preços agora")
    verificar.set_defaults(funcao=comando_verificar)

    grafico = sub.add_parser("grafico", help="gera o gráfico do histórico")
    grafico.add_argument("id", type=int)
    grafico.set_defaults(funcao=comando_grafico)

    remover = sub.add_parser("remover", help="para de monitorar um produto")
    remover.add_argument("id", type=int)
    remover.set_defaults(funcao=comando_remover)

    return parser


def main(argv=None):
    # Garante acentos e emojis no terminal do Windows.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = criar_parser().parse_args(argv)
    return args.funcao(args, Armazenamento())


if __name__ == "__main__":
    sys.exit(main())
