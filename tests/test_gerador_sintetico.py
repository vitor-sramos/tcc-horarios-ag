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


def test_todo_componente_tem_professor_habilitado_para_a_disciplina():
    instancia = gerar_instancia(seed=1, n_turmas=5, n_professores=6, n_disciplinas=4, disciplinas_por_professor=2)
    for componente in instancia.componentes:
        professor = instancia.professor(componente.professor_id)
        assert componente.disciplina_id in professor.disciplinas_habilitadas


def test_turnos_customizados_geram_slots_e_turmas_nos_turnos_certos():
    instancia = gerar_instancia(seed=1, n_turmas=6, turnos=["MATUTINO", "VESPERTINO"])

    turnos_das_turmas = {t.turno for t in instancia.turmas}
    turnos_dos_slots = {s.turno for s in instancia.slots_horario}

    assert turnos_das_turmas <= {"MATUTINO", "VESPERTINO"}
    assert turnos_dos_slots == {"MATUTINO", "VESPERTINO"}
    # ids de slot nao colidem entre turnos
    assert len({s.id for s in instancia.slots_horario}) == len(instancia.slots_horario)


def test_turno_padrao_preserva_comportamento_de_um_turno_so():
    instancia = gerar_instancia(seed=42)
    assert {t.turno for t in instancia.turmas} == {"MATUTINO"}
    assert {s.turno for s in instancia.slots_horario} == {"MATUTINO"}
