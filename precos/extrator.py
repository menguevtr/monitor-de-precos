"""Busca uma página de produto e descobre o preço dela.

A extração tenta, nesta ordem:
1. Seletor CSS informado pelo usuário (quando a loja precisa de um ajuste manual)
2. Dados estruturados JSON-LD (schema.org/Product), usados pela maioria das lojas
3. Meta tags de preço (Open Graph, product:price, itemprop="price")
"""

import json
import re

import requests
from bs4 import BeautifulSoup

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


class PrecoNaoEncontrado(Exception):
    """A página foi baixada, mas nenhum preço foi encontrado nela."""


def converter_preco(texto):
    """Converte um texto de preço em número.

    Aceita formatos brasileiros e internacionais:
    "R$ 1.299,90" -> 1299.9 | "1,299.90" -> 1299.9 | "£51.77" -> 51.77
    """
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        return float(texto)

    limpo = re.sub(r"[^\d,.]", "", str(texto))
    if not limpo or not re.search(r"\d", limpo):
        return None

    if "," in limpo and "." in limpo:
        # O separador que aparece por último é o decimal.
        if limpo.rfind(",") > limpo.rfind("."):
            limpo = limpo.replace(".", "").replace(",", ".")
        else:
            limpo = limpo.replace(",", "")
    elif "," in limpo:
        # "1.299" não entra aqui; "49,90" vira 49.90 e "1,299" vira 1299.
        inteiro, _, decimal = limpo.rpartition(",")
        if len(decimal) == 3 and inteiro:
            limpo = limpo.replace(",", "")
        else:
            limpo = inteiro.replace(",", "") + "." + decimal
    elif "." in limpo:
        # Só pontos: "1.299" (milhar) ou "12.99" (decimal).
        inteiro, _, decimal = limpo.rpartition(".")
        if len(decimal) == 3:
            limpo = limpo.replace(".", "")
        else:
            limpo = inteiro.replace(".", "") + "." + decimal

    try:
        return float(limpo)
    except ValueError:
        return None


def _itens_json_ld(dados):
    """Percorre o JSON-LD (que pode ser lista, dicionário ou @graph)."""
    if isinstance(dados, list):
        for item in dados:
            yield from _itens_json_ld(item)
    elif isinstance(dados, dict):
        yield dados
        if "@graph" in dados:
            yield from _itens_json_ld(dados["@graph"])


def _eh_produto(item):
    tipo = item.get("@type", "")
    tipos = tipo if isinstance(tipo, list) else [tipo]
    return "Product" in tipos


def _preco_das_ofertas(ofertas):
    for oferta in ofertas if isinstance(ofertas, list) else [ofertas]:
        if not isinstance(oferta, dict):
            continue
        for campo in ("price", "lowPrice"):
            preco = converter_preco(oferta.get(campo))
            if preco is not None:
                return preco
        # Algumas lojas aninham o preço em priceSpecification.
        especificacao = oferta.get("priceSpecification")
        if isinstance(especificacao, dict):
            preco = converter_preco(especificacao.get("price"))
            if preco is not None:
                return preco
    return None


def preco_por_json_ld(sopa):
    for script in sopa.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for item in _itens_json_ld(dados):
            if _eh_produto(item) and "offers" in item:
                preco = _preco_das_ofertas(item["offers"])
                if preco is not None:
                    return preco
    return None


def preco_por_meta_tags(sopa):
    seletores = [
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
        '[itemprop="price"][content]',
    ]
    for seletor in seletores:
        tag = sopa.select_one(seletor)
        if tag and tag.get("content"):
            preco = converter_preco(tag["content"])
            if preco is not None:
                return preco
    return None


def preco_por_seletor(sopa, seletor):
    elemento = sopa.select_one(seletor)
    if elemento is None:
        return None
    return converter_preco(elemento.get("content") or elemento.get_text())


def extrair_preco(html, seletor=None):
    """Recebe o HTML da página e devolve o preço como float."""
    sopa = BeautifulSoup(html, "html.parser")

    if seletor:
        preco = preco_por_seletor(sopa, seletor)
        if preco is not None:
            return preco

    for estrategia in (preco_por_json_ld, preco_por_meta_tags):
        preco = estrategia(sopa)
        if preco is not None:
            return preco

    raise PrecoNaoEncontrado(
        "Não encontrei o preço nesta página. Tente informar um seletor CSS "
        "com --seletor (veja o README)."
    )


def baixar_pagina(url, tempo_limite=20):
    resposta = requests.get(url, headers=CABECALHOS, timeout=tempo_limite)
    resposta.raise_for_status()
    # Usa a codificação detectada no conteúdo quando o servidor não informa.
    if resposta.encoding is None or resposta.encoding.lower() == "iso-8859-1":
        resposta.encoding = resposta.apparent_encoding
    return resposta.text


def buscar_preco(url, seletor=None):
    """Baixa a página e devolve o preço encontrado."""
    return extrair_preco(baixar_pagina(url), seletor)
