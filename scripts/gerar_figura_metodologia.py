"""Fluxograma das ETAPAS DO TRABALHO (como a pesquisa foi conduzida), horizontal e compacto, para o artigo.

Levantamento dos dados -> definição dos critérios -> definição da modelagem -> implementação do AG -> testes -> documentação.
Os testes devolvem achados que levaram a ajustes nas etapas anteriores (piso de disponibilidade, reparo, novos critérios no
fitness, remodelagem por turno e habilitação); por isso há uma volta dos testes para critérios, modelagem e implementação.
Sem título interno: a legenda fica no LaTeX.

Uso: python3 -m scripts.gerar_figura_metodologia
Saída: figuras/figura_fluxo_metodologia.png e .pdf
(O fluxo do experimento, instâncias -> AG/piso -> comparação, está em gerar_figura_fluxo_experimento.py.)
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SAIDA = "figuras/figura_fluxo_metodologia"
LARG, ALT = 1.38, 1.7
# sem cor: todas as caixas em branco com borda preta (versão para impressão em preto e branco)
CINZA = AZUL = AMARELO = VERDE = ("white", "black")

ETAPAS = [
    ("Levantamento\ndos dados", "instâncias\nsintéticas ou em\nJSON; parâmetros\nde tamanho", CINZA),
    ("Definição\ndos critérios", "restrições hard e\nsoft; pesos do\nfitness; piso teórico", CINZA),
    ("Definição\nda modelagem", "cromossomo e\ngenes; domínio por\nturno; indivíduo\ne população", CINZA),
    ("Implementação\ndo AG", "Python: seleção,\ncrossover, mutação,\nreparo e elitismo", AZUL),
    ("Testes", "testes\nautomatizados;\nexperimentos em 3\nescalas × 30 seeds", AMARELO),
    ("Documentação", "resultados em CSV,\ngráficos e\ndocumentação\ndo motor e artigo", VERDE),
]


def _caixa(ax, cx, cy, titulo, corpo, cores):
    fundo, borda = cores
    ax.add_patch(
        FancyBboxPatch(
            (cx - LARG / 2, cy - ALT / 2), LARG, ALT, boxstyle="round,pad=0,rounding_size=0.07",
            linewidth=1.3, edgecolor=borda, facecolor=fundo,
        )
    )
    ax.text(cx, cy + ALT / 2 - 0.12, titulo, ha="center", va="top", fontsize=6.9, fontweight="bold", linespacing=1.2)
    ax.text(cx, cy - 0.3, corpo, ha="center", va="center", fontsize=6.0, linespacing=1.25)


def _seta(ax, origem, destino):
    ax.annotate("", xy=destino, xytext=origem,
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black", shrinkA=0, shrinkB=0, mutation_scale=9))


def _linha(ax, pontos, estilo="-"):
    xs, ys = zip(*pontos)
    ax.plot(xs, ys, color="black", linewidth=1.1, linestyle=estilo, solid_capstyle="butt")


def main() -> None:
    fig, ax = plt.subplots(figsize=(6.3, 1.95), dpi=250)
    ax.set_xlim(0, 10)
    ax.set_ylim(0.95, 4.05)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    y = 2.9
    passo = (10 - 0.1 * 2 - LARG) / (len(ETAPAS) - 1)
    xs = [0.1 + LARG / 2 + i * passo for i in range(len(ETAPAS))]
    for x, (titulo, corpo, cores) in zip(xs, ETAPAS):
        _caixa(ax, x, y, titulo, corpo, cores)
    for i in range(len(ETAPAS) - 1):
        _seta(ax, (xs[i] + LARG / 2, y), (xs[i + 1] - LARG / 2, y))

    # volta: os testes geram ajustes em critérios, modelagem e implementação
    y_base = y - ALT / 2
    y_volta = 1.6
    _linha(ax, [(xs[4], y_base), (xs[4], y_volta), (xs[1], y_volta)])
    for i in (1, 2, 3):
        _seta(ax, (xs[i], y_volta), (xs[i], y_base))
    ax.text(
        (xs[1] + xs[4]) / 2, y_volta - 0.34,
        "os achados dos testes retornam às etapas anteriores como ajustes\nna definição dos critérios, na modelagem e na implementação",
        ha="center", va="center", fontsize=6.1, style="italic", linespacing=1.3,
    )

    fig.savefig(f"{SAIDA}.png", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(f"{SAIDA}.pdf", bbox_inches="tight", pad_inches=0.02)
    print(f"Figura salva em {SAIDA}.png/.pdf")


if __name__ == "__main__":
    main()
