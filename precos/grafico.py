"""Gera um gráfico com a evolução do preço de um produto."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera a imagem sem abrir janela
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from precos.alertas import formatar_reais  # noqa: E402


def gerar_grafico(produto, historico, pasta_saida):
    if not historico:
        raise ValueError("Ainda não há histórico para esse produto. Rode 'verificar' antes.")

    datas = [registro["data_hora"] for registro in historico]
    precos = [registro["preco"] for registro in historico]

    figura, eixo = plt.subplots(figsize=(9, 4.5))
    eixo.plot(datas, precos, marker="o", linewidth=2, color="#2563eb", label="Preço")
    eixo.axhline(produto["preco_alvo"], color="#16a34a", linestyle="--",
                 linewidth=1.5, label=f"Alvo ({formatar_reais(produto['preco_alvo'])})")

    menor = min(precos)
    indice_menor = precos.index(menor)
    eixo.annotate(f"Menor: {formatar_reais(menor)}", (datas[indice_menor], menor),
                  textcoords="offset points", xytext=(0, -16), ha="center",
                  fontsize=9, color="#475569")

    # Deixa uma folga em cima e embaixo para os rótulos não encostarem no eixo.
    valores = precos + [produto["preco_alvo"]]
    folga = max((max(valores) - min(valores)) * 0.15, max(valores) * 0.02)
    eixo.set_ylim(min(valores) - folga, max(valores) + folga)

    eixo.set_title(produto["nome"], fontsize=13, fontweight="bold", loc="left")
    eixo.set_ylabel("Preço (R$)")
    eixo.yaxis.set_major_formatter(lambda valor, _: formatar_reais(valor))
    localizador = mdates.AutoDateLocator(maxticks=8)
    eixo.xaxis.set_major_locator(localizador)
    if (max(datas) - min(datas)).days >= 2:
        eixo.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    else:
        # Período curto: o formatador conciso mostra horas/minutos sem repetir datas.
        eixo.xaxis.set_major_formatter(mdates.ConciseDateFormatter(localizador))
    eixo.grid(alpha=0.3)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.legend(frameon=False)
    figura.autofmt_xdate()
    figura.tight_layout()

    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho = pasta_saida / f"produto_{produto['id']}.png"
    figura.savefig(caminho, dpi=120)
    plt.close(figura)
    return caminho
