from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.motor_ga import evoluir


def test_motor_ga_bate_o_piso_teorico_em_instancia_pequena():
    instancia = gerar_instancia(seed=1, n_turmas=3, n_professores=4, n_disciplinas=3, n_salas=3, disciplinas_por_turma=3)
    limites = calcular_limites_teoricos(instancia)

    _, relatorio, historico = evoluir(instancia, geracoes=80, tamanho_populacao=30, seed=1)

    assert relatorio.violacoes_professor == limites.minimo_conflitos_professor
    assert relatorio.violacoes_sala == limites.minimo_conflitos_sala
    assert relatorio.violacoes_turma == limites.minimo_conflitos_turma
    assert relatorio.violacoes_disponibilidade == limites.minimo_violacoes_disponibilidade
    assert historico[-1] <= historico[0]
