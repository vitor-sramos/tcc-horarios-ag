"""Teste de sensibilidade ao número de gerações: repete o harness principal com mais gerações, nas escalas média e grande.

Mesmas instâncias (mesmas seeds) e mesmos parâmetros do AG do harness principal; só `GERACOES` muda (300 -> 1500).
As execuções rodam em paralelo (um processo por execução), então `tempo_execucao_segundos` aqui NÃO é comparável
com o do harness principal (que roda em série).

Uso: python3 -m scripts.rodar_sensibilidade_geracoes
"""

from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from motor_horarios.experimentacao import convergencia_para_linhas, resultados_para_linhas, rodar_execucao
from scripts.rodar_experimentos import ESCALAS, SEEDS, TAMANHO_POPULACAO

GERACOES = 1500
TRABALHADORES = 4
ESCALAS_TESTADAS = [escala for escala in ESCALAS if escala.nome in ("media", "grande")]

CAMINHO_RESUMO = "resultados/sensibilidade_geracoes_resumo.csv"
CAMINHO_CONVERGENCIA_CSV = "resultados/sensibilidade_geracoes_convergencia.csv"


def _executar(argumentos):
    escala, seed = argumentos
    return rodar_execucao(escala, seed, GERACOES, TAMANHO_POPULACAO)


def main() -> None:
    # a escala grande vai primeiro: é a mais lenta, e assim os processos terminam mais juntos
    tarefas = [(escala, seed) for escala in reversed(ESCALAS_TESTADAS) for seed in SEEDS]
    print(f"Rodando {len(tarefas)} execuções de {GERACOES} gerações ({TRABALHADORES} em paralelo)...", flush=True)
    with ProcessPoolExecutor(max_workers=TRABALHADORES) as pool:
        execucoes = list(pool.map(_executar, tarefas))

    pd.DataFrame(resultados_para_linhas(execucoes)).to_csv(CAMINHO_RESUMO, index=False)
    pd.DataFrame(convergencia_para_linhas(execucoes)).to_csv(CAMINHO_CONVERGENCIA_CSV, index=False)
    print(f"Resumo salvo em {CAMINHO_RESUMO}")
    print(f"Convergência salva em {CAMINHO_CONVERGENCIA_CSV}")


if __name__ == "__main__":
    main()
