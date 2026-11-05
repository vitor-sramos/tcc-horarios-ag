"""Fluxograma do EXPERIMENTO (pipeline instâncias -> AG/piso -> comparação), horizontal e compacto, para o artigo.

Instâncias sintéticas -> (algoritmo genético -> melhor indivíduo) e (piso teórico) em paralelo -> comparação -> registro e análise.
O piso é calculado só dos dados, sem executar o AG; os dois ramos se encontram na comparação.
Sem título interno: a legenda fica no LaTeX.

Uso: python3 -m scripts.gerar_figura_fluxo_experimento
Saída: figuras/figura_fluxo_experimento.png e .pdf
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SAIDA = "figuras/figura_fluxo_experimento"
LARG = 1.75
CINZA, AZUL, AMARELO, VERDE = ("#F2F2F2", "#555555"), ("#DCE8FA", "#1F5FB0"), ("#FFF6DE", "#B7791F"), ("#E8F5E9", "#2E7D32")
BRANCO = ("white", "black")


def _caixa(ax, cx, cy, altura, titulo, corpo, cores):
    fundo, borda = cores
    ax.add_patch(
        FancyBboxPatch(
            (cx - LARG / 2, cy - altura / 2), LARG, altura, boxstyle="round,pad=0,rounding_size=0.07",
            linewidth=1.3, edgecolor=borda, facecolor=fundo,
        )
    )
    ax.text(cx, cy + altura / 2 - 0.14, titulo, ha="center", va="top", fontsize=7, fontweight="bold")
    ax.text(cx, cy - 0.12, corpo, ha="center", va="center", fontsize=6.3, linespacing=1.25)


def _linha(ax, pontos):
    xs, ys = zip(*pontos)
    ax.plot(xs, ys, color="black", linewidth=1.2, solid_capstyle="butt")


def _seta(ax, origem, destino):
    ax.annotate("", xy=destino, xytext=origem,
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black", shrinkA=0, shrinkB=0, mutation_scale=9))


def main() -> None:
    fig, ax = plt.subplots(figsize=(6.3, 2.5), dpi=250)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.97)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    y_cima, y_meio, y_baixo = 2.9, 1.98, 1.06
    cols = [1.0, 3.0, 5.0, 7.0, 9.0]
    meia = LARG / 2

    _caixa(ax, cols[0], y_meio, 1.7, "Instâncias",
           "sintéticas, geradas\npor seed: 3 escalas\n× 5 seeds\n= 15 execuções", CINZA)
    _caixa(ax, cols[1], y_cima, 1.45, "Algoritmo genético",
           "população de 60,\n300 gerações:\nfitness, operadores,\nreparo e elitismo", AZUL)
    _caixa(ax, cols[1], y_baixo - 0.2, 1.25, "Piso teórico",
           "5 dimensões,\ncalculado dos dados,\nsem executar o AG", AMARELO)
    _caixa(ax, cols[2], y_cima, 1.45, "Melhor indivíduo",
           "de cada execução:\num quadro de\nhorários completo", AZUL)
    _caixa(ax, cols[3], y_meio, 1.85, "Comparação",
           "violações × piso\nnas 5 dimensões;\ncontagem absoluta\ndos critérios sem piso", BRANCO)
    _caixa(ax, cols[4], y_meio, 1.85, "Registro e análise",
           "CSV por execução e\npor geração; tabelas,\nconvergência e teste\ncom 1500 gerações", VERDE)

    y_piso = y_baixo - 0.2

    # instâncias -> AG e piso (bifurcação)
    x_fork = (cols[0] + meia + cols[1] - meia) / 2
    _linha(ax, [(cols[0] + meia, y_meio), (x_fork, y_meio)])
    _linha(ax, [(x_fork, y_piso), (x_fork, y_cima)])
    _seta(ax, (x_fork, y_cima), (cols[1] - meia, y_cima))
    _seta(ax, (x_fork, y_piso), (cols[1] - meia, y_piso))

    # AG -> melhor indivíduo
    _seta(ax, (cols[1] + meia, y_cima), (cols[2] - meia, y_cima))

    # melhor indivíduo e piso -> comparação (junção)
    x_join = (cols[2] + meia + cols[3] - meia) / 2
    _linha(ax, [(cols[2] + meia, y_cima), (x_join, y_cima), (x_join, y_meio)])
    _linha(ax, [(cols[1] + meia, y_piso), (x_join, y_piso), (x_join, y_meio)])
    _seta(ax, (x_join, y_meio), (cols[3] - meia, y_meio))

    # comparação -> registro e análise
    _seta(ax, (cols[3] + meia, y_meio), (cols[4] - meia, y_meio))

    fig.savefig(f"{SAIDA}.png", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(f"{SAIDA}.pdf", bbox_inches="tight", pad_inches=0.02)
    print(f"Figura salva em {SAIDA}.png/.pdf")


if __name__ == "__main__":
    main()
