from datetime import datetime

from monitor import deve_alertar
from precos.alertas import formatar_reais, montar_mensagem
from precos.armazenamento import Armazenamento
from precos.grafico import gerar_grafico


def produto_exemplo(ultimo_preco=None):
    return {"id": 1, "nome": "Fone", "url": "https://loja.com/fone",
            "preco_alvo": 200.0, "ultimo_preco": ultimo_preco, "menor_preco": None}


def test_alerta_quando_chega_no_alvo_pela_primeira_vez():
    assert deve_alertar(produto_exemplo(ultimo_preco=250.0), 199.0)


def test_nao_alerta_acima_do_alvo():
    assert not deve_alertar(produto_exemplo(ultimo_preco=250.0), 210.0)


def test_nao_repete_alerta_com_mesmo_preco():
    assert not deve_alertar(produto_exemplo(ultimo_preco=190.0), 190.0)


def test_alerta_de_novo_se_cair_mais():
    assert deve_alertar(produto_exemplo(ultimo_preco=190.0), 180.0)


def test_formatar_reais():
    assert formatar_reais(1299.9) == "R$ 1.299,90"
    assert "R$ 199,00" in montar_mensagem(produto_exemplo(), 199.0)


def test_armazenamento_e_historico(tmp_path):
    banco = Armazenamento(tmp_path)
    produto = banco.adicionar_produto("Fone", "https://loja.com/fone", 200.0)

    banco.registrar_preco(produto, 250.0, datetime(2026, 11, 1, 9))
    banco.registrar_preco(produto, 199.0, datetime(2026, 11, 2, 9))
    banco.atualizar_preco(produto["id"], 250.0)
    banco.atualizar_preco(produto["id"], 199.0)

    salvo = banco.carregar_produtos()[0]
    assert salvo["ultimo_preco"] == 199.0
    assert salvo["menor_preco"] == 199.0
    assert [h["preco"] for h in banco.historico(produto["id"])] == [250.0, 199.0]

    caminho = gerar_grafico(salvo, banco.historico(produto["id"]), tmp_path / "graficos")
    assert caminho.exists()


def test_nao_adiciona_url_repetida(tmp_path):
    banco = Armazenamento(tmp_path)
    banco.adicionar_produto("Fone", "https://loja.com/fone", 200.0)
    try:
        banco.adicionar_produto("Fone de novo", "https://loja.com/fone", 150.0)
    except ValueError:
        return
    raise AssertionError("Deveria ter recusado a URL repetida")
