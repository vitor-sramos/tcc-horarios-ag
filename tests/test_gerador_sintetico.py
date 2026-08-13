from motor_horarios.gerador_sintetico import gerar_instancia


def test_mesma_seed_gera_instancia_identica():
    a = gerar_instancia(seed=42)
    b = gerar_instancia(seed=42)
    assert a.componentes == b.componentes
    assert a.disponibilidades == b.disponibilidades


def test_seeds_diferentes_geram_instancias_diferentes():
    a = gerar_instancia(seed=1)
    b = gerar_instancia(seed=2)
    assert a.componentes != b.componentes


def test_parametros_de_escala_sao_respeitados():
    instancia = gerar_instancia(seed=1, n_turmas=4, n_professores=6, n_disciplinas=3, n_salas=5)
    assert len(instancia.turmas) == 4
    assert len(instancia.professores) == 6
    assert len(instancia.disciplinas) == 3
    assert len(instancia.salas) == 5
