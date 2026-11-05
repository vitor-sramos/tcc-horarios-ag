"""Figura do ciclo do algoritmo genético implementado, em formato horizontal (duas fileiras) para o artigo.

Fileira de cima (esq -> dir): população inicial, avaliação, seleção, crossover, mutação.
Fileira de baixo (dir -> esq): reparo, elitismo, decisão de parada, resultado. O "não" da decisão volta à avaliação.
Sem título interno: a legenda fica no LaTeX.

Uso: python3 -m scripts.gerar_figura_ciclo_ag
Saída: figuras/figura_ciclo_algoritmo_genetico.png e .pdf
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

SAIDA = "figuras/figura_ciclo_algoritmo_genetico"
LARGURA, ALTURA = 0.80, 0.80  # tamanho das caixas, em unidades de coluna
Y_CIMA, Y_BAIXO = 1.80, 0.50
Y_FOLGA = (Y_CIMA + Y_BAIXO) / 2  # meio do espaço entre as fileiras (por onde passa o laço "não")
VERDE_BORDA, VERDE_FUNDO = "#2E7D32", "#E8F5E9"


def _caixa(ax, x, y, texto, verde=False):
    ax.add_patch(
        FancyBboxPatch(
            (x - LARGURA / 2, y - ALTURA / 2),
            LARGURA,
            ALTURA,
            boxstyle="round,pad=0,rounding_size=0.06",
            linewidth=1.3,
            edgecolor=VERDE_BORDA if verde else "black",
            facecolor=VERDE_FUNDO if verde else "white",
        )
    )
    ax.text(x, y, texto, ha="center", va="center", fontsize=6.9, linespacing=1.25)


def _seta(ax, origem, destino):
    ax.annotate(
        "",
        xy=destino,
        xytext=origem,
        arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black", shrinkA=0, shrinkB=0, mutation_scale=9),
    )


def main() -> None:
    fig, ax = plt.subplots(figsize=(6.3, 3.0), dpi=250)
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 2.3)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    coluna = [0.5, 1.5, 2.5, 3.5, 4.5]
    meia = LARGURA / 2

    # fileira de cima, da esquerda para a direita
    cima = [
        "Gerar população\ninicial aleatória\n(dentro do domínio\nde cada gene)",
        "Avaliar cada\nindivíduo\n(fitness)",
        "Selecionar\npor torneio",
        "Crossover",
        "Mutação",
    ]
    for x, texto in zip(coluna, cima):
        _caixa(ax, x, Y_CIMA, texto)
    for i in range(4):
        _seta(ax, (coluna[i] + meia, Y_CIMA), (coluna[i + 1] - meia, Y_CIMA))

    # desce da mutação para o reparo (extremidade direita)
    _seta(ax, (coluna[4], Y_CIMA - ALTURA / 2), (coluna[4], Y_BAIXO + ALTURA / 2))

    # fileira de baixo, da direita para a esquerda
    _caixa(ax, coluna[4], Y_BAIXO, "Reparo\n(conflitos hard →\ndisponibilidade →\nfragmentação)")
    _caixa(ax, coluna[3], Y_BAIXO, "Elitismo\n(melhores seguem\nsem alteração)")
    _seta(ax, (coluna[4] - meia, Y_BAIXO), (coluna[3] + meia, Y_BAIXO))

    # decisão de parada (losango) na terceira coluna
    x_dec, meia_dec, meia_alt_dec = coluna[2], LARGURA / 2, 0.45
    ax.add_patch(
        Polygon(
            [
                (x_dec - meia_dec, Y_BAIXO),
                (x_dec, Y_BAIXO + meia_alt_dec),
                (x_dec + meia_dec, Y_BAIXO),
                (x_dec, Y_BAIXO - meia_alt_dec),
            ],
            closed=True,
            linewidth=1.3,
            edgecolor="black",
            facecolor="white",
        )
    )
    ax.text(x_dec, Y_BAIXO, "Atingiu o nº\nde gerações?", ha="center", va="center", fontsize=6.6, linespacing=1.2)
    _seta(ax, (coluna[3] - meia, Y_BAIXO), (x_dec + meia_dec, Y_BAIXO))

    # "sim": segue para o resultado
    _caixa(ax, coluna[1], Y_BAIXO, "Retorna o melhor\nindivíduo\nencontrado em\nqualquer geração", verde=True)
    _seta(ax, (x_dec - meia_dec, Y_BAIXO), (coluna[1] + meia, Y_BAIXO))
    ax.text(x_dec - meia_dec - 0.10, Y_BAIXO + 0.07, "sim", ha="center", va="bottom", fontsize=6.4, fontweight="bold")

    # "não": sobe da decisão, passa pelo espaço entre as fileiras e volta à avaliação
    topo_dec = Y_BAIXO + meia_alt_dec
    ax.plot([x_dec, x_dec], [topo_dec, Y_FOLGA], color="black", linewidth=1.2, solid_capstyle="butt")
    ax.plot([x_dec, coluna[1]], [Y_FOLGA, Y_FOLGA], color="black", linewidth=1.2, solid_capstyle="butt")
    _seta(ax, (coluna[1], Y_FOLGA), (coluna[1], Y_CIMA - ALTURA / 2))
    ax.text(x_dec + 0.06, (topo_dec + Y_FOLGA) / 2, "não", ha="left", va="center", fontsize=6.6, fontweight="bold")

    fig.savefig(f"{SAIDA}.png", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(f"{SAIDA}.pdf", bbox_inches="tight", pad_inches=0.02)
    print(f"Figura salva em {SAIDA}.png/.pdf")


if __name__ == "__main__":
    main()
