"""Figura de convergência para o artigo: proporção de execuções com as restrições obrigatórias no piso, por geração.

Uma linha por escala (30 execuções cada). Uma execução está "no piso" na geração g quando as violações obrigatórias do melhor
indivíduo até então (conflitos de professor, sala e turma + excesso de carga horária) são iguais ao mínimo inevitável da
instância. Dados: resultados/convergencia_obrigatorias.csv (gerado por scripts/rodar_convergencia_obrigatorias.py).
Sem título interno: a legenda fica no LaTeX.

Uso: python3 -m scripts.gerar_figura_convergencia
Saída: figuras/figura_convergencia.png e .pdf
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CAMINHO = "resultados/convergencia_obrigatorias.csv"
SAIDA = "figuras/figura_convergencia"

# Okabe-Ito (seguro para daltonismo) + estilo de linha distinto (o artigo pode ser impresso em preto e branco)
ESTILO = {
    "pequena": {"cor": "#0072B2", "linha": "-", "rotulo": "Pequena (3 turmas)"},
    "media": {"cor": "#D55E00", "linha": "--", "rotulo": "Média (10 turmas)"},
    "grande": {"cor": "#009E73", "linha": ":", "rotulo": "Grande (25 turmas)"},
}


def main() -> None:
    dados = pd.read_csv(CAMINHO)
    dados["no_piso"] = dados.excesso_obrigatorias.abs() < 1e-9
    proporcao = dados.groupby(["escala", "geracao"]).no_piso.mean().unstack(0) * 100

    fig, ax = plt.subplots(figsize=(6.3, 3.0), dpi=250)
    for escala, estilo in ESTILO.items():
        ax.plot(proporcao.index, proporcao[escala], color=estilo["cor"], linestyle=estilo["linha"],
                linewidth=2.0, label=estilo["rotulo"])

    ax.set_xlim(0, 299)
    ax.set_ylim(0, 103)
    ax.set_yticks(range(0, 101, 20))
    ax.set_xlabel("Geração", fontsize=9)
    ax.set_ylabel("Execuções com as obrigatórias\nno piso (%)", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(f"{SAIDA}.png", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(f"{SAIDA}.pdf", bbox_inches="tight", pad_inches=0.02)
    print(f"Figura salva em {SAIDA}.png/.pdf")


if __name__ == "__main__":
    main()
