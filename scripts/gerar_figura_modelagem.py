"""Figura da modelagem do problema para o artigo, na mesma ordem em que o texto a descreve:

1. componentes curriculares da turma (cada um com N aulas por semana);
2. cromossomo: um gene por aula semanal (4 aulas de Matemática geram 4 genes);
3. o valor de cada gene é um slot do turno da turma (aqui, matutino: 6 aulas por dia, 5 dias, slots 1 a 30);
4. indivíduo = cromossomo completo = um quadro de horários; população = conjunto de indivíduos.

Os slots são numerados por dia e depois por aula (como em `gerar_slots`): slot = (dia - 1) x 6 + aula.
Os valores dos genes são ilustrativos. Sem título interno: a legenda fica no LaTeX.

Uso: python3 -m scripts.gerar_figura_modelagem
Saída: figuras/figura_hierarquia_representacao.png e .pdf
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SAIDA = "figuras/figura_hierarquia_representacao"
VERDE, ROXO = "#CDEBC9", "#DDCDE4"
AZUL, AZUL_FUNDO = "#1F5FB0", "#DCE8FA"
CINZA_FUNDO = "#F2F2F2"
DIAS = ["SEG", "TER", "QUA", "QUI", "SEX"]
AULAS_POR_DIA = 6

# genes: (componente, valor do slot)
MATEMATICA = [8, 15, 3, 27]
PORTUGUES = [5, 19, 26]
COR_DO_SLOT = {**{s: VERDE for s in MATEMATICA}, **{s: ROXO for s in PORTUGUES}}


def _caixa(ax, x, y, w, h, texto="", borda="black", fundo="white", espessura=1.1, tamanho=6.6, bold=False):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.05",
            linewidth=espessura, edgecolor=borda, facecolor=fundo,
        )
    )
    if texto:
        ax.text(
            x + w / 2, y + h / 2, texto, ha="center", va="center",
            fontsize=tamanho, fontweight="bold" if bold else "normal", linespacing=1.2,
        )


def _passo(ax, x, y, numero, texto):
    ax.text(x, y, f"{numero}", fontsize=6.8, fontweight="bold", color="white", ha="center", va="center",
            bbox=dict(boxstyle="circle,pad=0.22", fc="#333333", ec="none"))
    ax.text(x + 0.2, y, texto, fontsize=6.9, fontweight="bold", va="center")


def _seta(ax, origem, destino):
    ax.annotate("", xy=destino, xytext=origem,
                arrowprops=dict(arrowstyle="-|>", lw=1.1, color="black", shrinkA=0, shrinkB=0, mutation_scale=8))


def main() -> None:
    fig, ax = plt.subplots(figsize=(6.3, 3.53), dpi=250)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    # ---------- 1. componentes curriculares ----------
    esquerda = 0.1
    larg_cel, passo_cel = 0.55, 0.6
    x_mat = esquerda
    larg_mat = (len(MATEMATICA) - 1) * passo_cel + larg_cel
    x_por = x_mat + larg_mat + 0.3
    larg_por = (len(PORTUGUES) - 1) * passo_cel + larg_cel

    _passo(ax, 0.2, 5.45, "1", "Componentes curriculares da turma")
    _caixa(ax, x_mat, 4.45, larg_mat, 0.7, "Matemática\n4 aulas por semana", fundo=VERDE)
    _caixa(ax, x_por, 4.45, larg_por, 0.7, "Português\n3 aulas por semana", fundo=ROXO)
    ax.text(x_por + larg_por + 0.3, 4.8, "...", fontsize=11, fontweight="bold", ha="center", va="center")

    # ---------- 2. cromossomo ----------
    y_cel, h_cel = 2.55, 0.72
    _seta(ax, (x_mat + larg_mat / 2, 4.45), (x_mat + larg_mat / 2, y_cel + h_cel + 0.02))
    ax.text(x_mat + larg_mat / 2 + 0.12, 4.0, "4 genes", fontsize=6.2, style="italic", va="center")
    _seta(ax, (x_por + larg_por / 2, 4.45), (x_por + larg_por / 2, y_cel + h_cel + 0.02))
    ax.text(x_por + larg_por / 2 + 0.12, 4.0, "3 genes", fontsize=6.2, style="italic", va="center")

    posicao = 0
    for grupo, x_ini, cor in ((MATEMATICA, x_mat, VERDE), (PORTUGUES, x_por, ROXO)):
        for i, valor in enumerate(grupo):
            x = x_ini + i * passo_cel
            _caixa(ax, x, y_cel, larg_cel, h_cel, str(valor), fundo=cor, tamanho=7.6)
            ax.text(x + larg_cel / 2, y_cel - 0.17, f"g{posicao}", ha="center", va="center", fontsize=5.8)
            posicao += 1
    x_ultimo = x_por + larg_por + 0.3
    ax.text(x_ultimo, y_cel + h_cel / 2, "...", fontsize=11, fontweight="bold", ha="center", va="center")
    _passo(ax, 0.2, 2.02, "2", "Cromossomo: um gene por aula semanal")
    ax.text(esquerda, 1.72, "cada posição do vetor é uma aula a alocar; o valor armazenado é o slot escolhido para ela",
            fontsize=6.1, style="italic", va="center")

    # ---------- 3. slots do turno ----------
    gx, gy_topo = 6.75, 4.95  # canto superior esquerdo da grade
    larg_c, alt_c, larg_rot = 0.62, 0.43, 0.0
    _passo(ax, 6.55, 5.45, "3", "Slots do turno (matutino: 1 a 30)")
    for d, nome in enumerate(DIAS):
        ax.text(gx + d * larg_c + larg_c / 2, gy_topo + 0.2, nome, ha="center", va="center", fontsize=6)
    for a in range(AULAS_POR_DIA):
        ax.text(gx - 0.1, gy_topo - a * alt_c - alt_c / 2, f"{a + 1}ª", ha="right", va="center", fontsize=5.8)
        for d in range(len(DIAS)):
            slot = d * AULAS_POR_DIA + a + 1
            cor = COR_DO_SLOT.get(slot, "white")
            _caixa(ax, gx + d * larg_c, gy_topo - (a + 1) * alt_c, larg_c, alt_c, str(slot), fundo=cor,
                   espessura=1.6 if slot == 8 else 0.7, borda=AZUL if slot == 8 else "#555555", tamanho=6.2)
    ax.text(gx - 0.05, gy_topo - AULAS_POR_DIA * alt_c - 0.28,
            "o gene de valor 8 é a terça, 2ª aula", fontsize=6.2, style="italic", va="center")

    # ---------- 4. indivíduo e população ----------
    _passo(ax, 0.2, 1.3, "4", "Indivíduo = cromossomo completo = um quadro de horários; população = conjunto de indivíduos")
    _caixa(ax, 0.05, 0.03, 9.9, 0.98, fundo=CINZA_FUNDO, espessura=1.2)
    nomes = [("Indivíduo 1", False), ("Indivíduo 2", True), ("Indivíduo 3", False)]
    for i, (nome, destaque) in enumerate(nomes):
        _caixa(ax, 0.3 + i * 2.35, 0.22, 2.05, 0.6, nome, borda=AZUL if destaque else "black",
               fundo=AZUL_FUNDO if destaque else "white", espessura=1.8 if destaque else 1.1, tamanho=7)
    ax.text(7.55, 0.52, "...", fontsize=11, fontweight="bold", ha="center", va="center")
    _caixa(ax, 7.9, 0.22, 1.85, 0.6, "Indivíduo N", tamanho=7)

    fig.savefig(f"{SAIDA}.png", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(f"{SAIDA}.pdf", bbox_inches="tight", pad_inches=0.02)
    print(f"Figura salva em {SAIDA}.png/.pdf")


if __name__ == "__main__":
    main()
