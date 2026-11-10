import pytest

from precos.extrator import PrecoNaoEncontrado, converter_preco, extrair_preco


@pytest.mark.parametrize("texto, esperado", [
    ("R$ 1.299,90", 1299.90),
    ("R$ 49,90", 49.90),
    ("1,299.90", 1299.90),
    ("£51.77", 51.77),
    ("1.299", 1299.0),
    ("12.99", 12.99),
    ("199", 199.0),
    (89.9, 89.9),
    ("Indisponível", None),
    (None, None),
])
def test_converter_preco(texto, esperado):
    assert converter_preco(texto) == esperado


def test_json_ld_com_oferta_simples():
    html = """
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "Product", "name": "Fone",
     "offers": {"@type": "Offer", "price": "249.90", "priceCurrency": "BRL"}}
    </script>"""
    assert extrair_preco(html) == 249.90


def test_json_ld_com_graph_e_lista_de_ofertas():
    html = """
    <script type="application/ld+json">
    {"@graph": [
        {"@type": "BreadcrumbList"},
        {"@type": ["Product"], "offers": [{"lowPrice": "1.099,00"}]}
    ]}
    </script>"""
    assert extrair_preco(html) == 1099.0


def test_ignora_json_ld_invalido_e_usa_meta_tag():
    html = """
    <script type="application/ld+json">{ isso não é json }</script>
    <meta property="product:price:amount" content="79.50">"""
    assert extrair_preco(html) == 79.50


def test_itemprop_price():
    html = '<span itemprop="price" content="1599.00">R$ 1.599,00</span>'
    assert extrair_preco(html) == 1599.0


def test_seletor_personalizado_tem_prioridade():
    html = """
    <meta property="product:price:amount" content="10.00">
    <p class="preco-final">R$ 8,49</p>"""
    assert extrair_preco(html, seletor=".preco-final") == 8.49


def test_sem_preco_gera_erro():
    with pytest.raises(PrecoNaoEncontrado):
        extrair_preco("<html><body>Produto esgotado</body></html>")
