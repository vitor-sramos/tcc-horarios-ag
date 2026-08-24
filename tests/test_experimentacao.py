from motor_horarios.experimentacao import (
    ConfiguracaoEscala,
    convergencia_para_linhas,
    resultados_para_linhas,
    rodar_execucao,
    rodar_grade,
)

ESCALA_PEQUENA = ConfiguracaoEscala(
    nome="pequena", n_turmas=3, n_professores=4, n_disciplinas=3, n_salas=3, disciplinas_por_turma=3
)


def test_rodar_execucao_produz_metricas_coerentes_com_o_piso():
    execucao = rodar_execucao(ESCALA_PEQUENA, seed=1, geracoes=80, tamanho_populacao=30)

    assert execucao.resultado.escala == "pequena"
    assert execucao.resultado.seed == 1
    assert execucao.resultado.tamanho_cromossomo > 0
    assert execucao.resultado.tempo_execucao_segundos > 0
    # fitness nunca pode ser melhor que o piso teórico permite (>=), mesmo que o AG bata o piso
    assert execucao.resultado.violacoes_professor >= execucao.resultado.piso_professor
    assert execucao.resultado.violacoes_sala >= execucao.resultado.piso_sala
    assert execucao.resultado.violacoes_turma >= execucao.resultado.piso_turma
    assert execucao.resultado.violacoes_disponibilidade >= execucao.resultado.piso_disponibilidade
    assert len(execucao.historico_melhor_fitness) == 80


def test_rodar_execucao_e_deterministico_pela_seed():
    a = rodar_execucao(ESCALA_PEQUENA, seed=5, geracoes=40, tamanho_populacao=20)
    b = rodar_execucao(ESCALA_PEQUENA, seed=5, geracoes=40, tamanho_populacao=20)

    assert a.resultado.fitness_final == b.resultado.fitness_final
    assert a.historico_melhor_fitness == b.historico_melhor_fitness


def test_rodar_grade_cobre_o_produto_cartesiano_de_escalas_e_seeds():
    escalas = [ESCALA_PEQUENA]
    seeds = [1, 2, 3]

    execucoes = rodar_grade(escalas, seeds, geracoes=10, tamanho_populacao=10)

    assert len(execucoes) == len(escalas) * len(seeds)
    assert {e.resultado.seed for e in execucoes} == set(seeds)
    assert all(e.resultado.escala == "pequena" for e in execucoes)


def test_resultados_para_linhas_gera_uma_linha_por_execucao():
    execucoes = rodar_grade([ESCALA_PEQUENA], [1, 2], geracoes=5, tamanho_populacao=10)

    linhas = resultados_para_linhas(execucoes)

    assert len(linhas) == 2
    assert {"escala", "seed", "fitness_final", "bateu_piso"} <= linhas[0].keys()


def test_convergencia_para_linhas_gera_uma_linha_por_geracao_por_execucao():
    geracoes = 7
    execucoes = rodar_grade([ESCALA_PEQUENA], [1, 2], geracoes=geracoes, tamanho_populacao=10)

    linhas = convergencia_para_linhas(execucoes)

    assert len(linhas) == geracoes * 2
    assert {"escala", "seed", "geracao", "melhor_fitness"} <= linhas[0].keys()
