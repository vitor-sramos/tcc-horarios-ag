"""Repete a base do harness (3 escalas x 30 seeds, 300 gerações) registrando, a cada geração, as violações obrigatórias
do melhor indivíduo. Serve para o gráfico de convergência: violações obrigatórias acima do piso, por geração.

É só registro: o resultado final de cada execução deve ser idêntico ao de `resultados/experimentos_resumo.csv`
(o script confere). Roda em paralelo; os tempos desta rodada NÃO devem ser usados.

Uso: python3 -m scripts.rodar_convergencia_obrigatorias
Saída: resultados/convergencia_obrigatorias.csv
"""

from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.motor_ga import evoluir
from scripts.rodar_experimentos import ESCALAS, GERACOES, SEEDS, TAMANHO_POPULACAO

TRABALHADORES = 4
CAMINHO_RESUMO = "resultados/experimentos_resumo.csv"
CAMINHO_SAIDA = "resultados/convergencia_obrigatorias.csv"


def _executar(argumentos):
    escala, seed = argumentos
    instancia = gerar_instancia(
        seed=seed,
        n_turmas=escala.n_turmas,
        n_professores=escala.n_professores,
        n_disciplinas=escala.n_disciplinas,
        n_salas=escala.n_salas,
        disciplinas_por_turma=escala.disciplinas_por_turma,
        disciplinas_por_professor=escala.disciplinas_por_professor,
    )
    piso = calcular_limites_teoricos(instancia)
    piso_obrigatorias = (
        piso.minimo_conflitos_professor
        + piso.minimo_conflitos_sala
        + piso.minimo_conflitos_turma
        + piso.minimo_minutos_excedentes_carga_horaria / 60
    )
    registro: list[float] = []
    _, relatorio, historico = evoluir(
        instancia, geracoes=GERACOES, tamanho_populacao=TAMANHO_POPULACAO, seed=seed, registro_obrigatorias=registro
    )
    linhas = [
        {
            "escala": escala.nome,
            "seed": seed,
            "geracao": g,
            "melhor_fitness": historico[g],
            "violacoes_obrigatorias": registro[g],
            "piso_obrigatorias": piso_obrigatorias,
            "excesso_obrigatorias": registro[g] - piso_obrigatorias,
        }
        for g in range(len(registro))
    ]
    return escala.nome, seed, relatorio.valor, linhas


def main() -> None:
    tarefas = [(escala, seed) for escala in reversed(ESCALAS) for seed in SEEDS]  # grande primeiro (mais lenta)
    print(f"Rodando {len(tarefas)} execuções de {GERACOES} gerações ({TRABALHADORES} em paralelo)...", flush=True)
    with ProcessPoolExecutor(max_workers=TRABALHADORES) as pool:
        resultados = list(pool.map(_executar, tarefas))

    pd.DataFrame([linha for *_, linhas in resultados for linha in linhas]).to_csv(CAMINHO_SAIDA, index=False)

    base = pd.read_csv(CAMINHO_RESUMO).set_index(["escala", "seed"]).fitness_final
    divergentes = [(e, s) for e, s, valor, _ in resultados if abs(base.loc[(e, s)] - valor) > 1e-9]
    print(f"Salvo em {CAMINHO_SAIDA}")
    print(f"Fitness final idêntico ao da base em {len(resultados) - len(divergentes)} de {len(resultados)} execuções")
    if divergentes:
        print("DIVERGENTES:", divergentes)


if __name__ == "__main__":
    main()
