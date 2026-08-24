"""Harness de experimentação: roda o AG em várias escalas x seeds e salva CSVs + gráfico de convergência.

Uso: python3 -m scripts.rodar_experimentos
"""

import pandas as pd

from motor_horarios.experimentacao import (
    ConfiguracaoEscala,
    convergencia_para_linhas,
    resultados_para_linhas,
    rodar_grade,
)
from motor_horarios.visualizacao import plotar_convergencia

ESCALAS = [
    ConfiguracaoEscala(nome="pequena", n_turmas=3, n_professores=5, n_disciplinas=4, n_salas=4),
    ConfiguracaoEscala(nome="media", n_turmas=10, n_professores=15, n_disciplinas=8, n_salas=10),
    ConfiguracaoEscala(nome="grande", n_turmas=25, n_professores=35, n_disciplinas=12, n_salas=20),
]

SEEDS = [0, 1, 2, 3, 4]
GERACOES = 300
TAMANHO_POPULACAO = 60

CAMINHO_RESUMO = "resultados/experimentos_resumo.csv"
CAMINHO_CONVERGENCIA_CSV = "resultados/experimentos_convergencia.csv"
CAMINHO_CONVERGENCIA_PNG = "resultados/experimentos_convergencia.png"


def main() -> None:
    print(f"Rodando {len(ESCALAS)} escalas x {len(SEEDS)} seeds ({len(ESCALAS) * len(SEEDS)} execuções)...")
    execucoes = rodar_grade(ESCALAS, SEEDS, geracoes=GERACOES, tamanho_populacao=TAMANHO_POPULACAO)

    resumo = pd.DataFrame(resultados_para_linhas(execucoes))
    resumo.to_csv(CAMINHO_RESUMO, index=False)

    convergencia = pd.DataFrame(convergencia_para_linhas(execucoes))
    convergencia.to_csv(CAMINHO_CONVERGENCIA_CSV, index=False)

    plotar_convergencia(execucoes, CAMINHO_CONVERGENCIA_PNG)

    agregado = resumo.groupby("escala").agg(
        tamanho_cromossomo=("tamanho_cromossomo", "first"),
        fitness_final_medio=("fitness_final", "mean"),
        tempo_execucao_medio_s=("tempo_execucao_segundos", "mean"),
        taxa_bateu_piso=("bateu_piso", "mean"),
    )
    print(agregado.to_string())
    print(f"\nResumo salvo em {CAMINHO_RESUMO}")
    print(f"Convergência (long format) salva em {CAMINHO_CONVERGENCIA_CSV}")
    print(f"Gráfico de convergência salvo em {CAMINHO_CONVERGENCIA_PNG}")


if __name__ == "__main__":
    main()
