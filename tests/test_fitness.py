from datetime import time

from motor_horarios.fitness import avaliar
from motor_horarios.individuo import Individuo
from motor_horarios.modelo import (
    ComponenteCurricular,
    DiaSemana,
    Disciplina,
    Disponibilidade,
    InstanciaProblema,
    Professor,
    Sala,
    SlotHorario,
    Turma,
)

SLOTS_SEGUNDA = [
    SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
    SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40), "MATUTINO"),
]

SLOTS_SEGUNDA_3_AULAS = [
    SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
    SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40), "MATUTINO"),
    SlotHorario(3, DiaSemana.SEGUNDA, 3, time(8, 40), time(9, 30), "MATUTINO"),
]


def _instancia_duas_turmas_mesmo_professor(carga_horaria_maxima_minutos: int = 1200) -> InstanciaProblema:
    turmas = [Turma(1, "A", "MATUTINO"), Turma(2, "B", "MATUTINO")]
    professores = [Professor(1, "Joao", carga_horaria_maxima_minutos)]
    disciplinas = [Disciplina(1, "Mat")]
    salas = [Sala(1, "Sala1"), Sala(2, "Sala2")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1),
        ComponenteCurricular(2, turma_id=2, professor_id=1, disciplina_id=1, sala_id=2, aulas_por_semana=1),
    ]
    return InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=SLOTS_SEGUNDA,
    )


def test_mesmo_professor_mesmo_slot_e_conflito():
    instancia = _instancia_duas_turmas_mesmo_professor()
    relatorio = avaliar(Individuo([1, 1]), instancia)
    assert relatorio.violacoes_professor == 1
    assert relatorio.violacoes_sala == 0
    assert relatorio.violacoes_turma == 0


def test_professor_em_slots_diferentes_nao_e_conflito():
    instancia = _instancia_duas_turmas_mesmo_professor()
    relatorio = avaliar(Individuo([1, 2]), instancia)
    assert relatorio.violacoes_professor == 0
    assert relatorio.valor == 0.0


def test_carga_horaria_excedente_e_detectada():
    # cada aula dura 50min; carga maxima de 60min so permite 1 aula
    instancia = _instancia_duas_turmas_mesmo_professor(carga_horaria_maxima_minutos=60)
    relatorio = avaliar(Individuo([1, 2]), instancia)
    assert relatorio.minutos_excedentes_carga_horaria == 40  # 2*50 - 60


def test_disponibilidade_fora_da_janela_e_penalizada_como_soft():
    instancia = _instancia_duas_turmas_mesmo_professor()
    instancia.disponibilidades.append(
        Disponibilidade(id=1, professor_id=1, dia_semana=DiaSemana.TERCA, hora_inicio=time(7, 0), hora_fim=time(12, 0))
    )
    # SLOTS_SEGUNDA sao todos na segunda-feira; professor so esta disponivel na terca
    relatorio = avaliar(Individuo([1, 2]), instancia)
    assert relatorio.violacoes_disponibilidade == 2
    # e uma soft constraint: nao deve contar como hard
    assert relatorio.violacoes_professor == 0
    assert relatorio.violacoes_sala == 0
    assert relatorio.violacoes_turma == 0


def test_buraco_na_grade_da_turma_e_contado():
    turma = Turma(1, "A", "MATUTINO")
    professor = Professor(1, "Prof", 1200)
    disciplina = Disciplina(1, "Matematica")
    sala = Sala(1, "Sala1")
    componente = ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=2)
    instancia = InstanciaProblema(
        turmas=[turma], professores=[professor], disciplinas=[disciplina], salas=[sala],
        componentes=[componente], slots_horario=SLOTS_SEGUNDA_3_AULAS,
    )

    # aula 1 e aula 3, pulando a aula 2 -> 1 buraco pra turma, e coincide com fragmentacao
    # da propria disciplina (so ela ocupa a segunda-feira nessa instancia)
    relatorio = avaliar(Individuo([1, 3]), instancia)

    assert relatorio.janelas_turma == 1
    assert relatorio.fragmentacao_disciplina == 1


def test_disciplina_fragmentada_conta_mesmo_sem_buraco_na_turma():
    """Turma sem nenhum buraco (todo periodo do dia ocupado), mas a mesma disciplina aparece
    em posicoes nao-consecutivas -- outra disciplina no meio (caso real observado na interface web)."""
    turma = Turma(1, "A", "MATUTINO")
    professor = Professor(1, "Prof", 1200)
    matematica = Disciplina(1, "Matematica")
    portugues = Disciplina(2, "Portugues")
    sala = Sala(1, "Sala1")
    componente_matematica = ComponenteCurricular(
        1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=2
    )
    componente_portugues = ComponenteCurricular(
        2, turma_id=1, professor_id=1, disciplina_id=2, sala_id=1, aulas_por_semana=1
    )
    instancia = InstanciaProblema(
        turmas=[turma], professores=[professor], disciplinas=[matematica, portugues], salas=[sala],
        componentes=[componente_matematica, componente_portugues], slots_horario=SLOTS_SEGUNDA_3_AULAS,
    )

    # aulas_pendentes(): matematica-ocorrencia0, matematica-ocorrencia1, portugues-ocorrencia0
    # genes: matematica na aula 1 e na aula 3, portugues na aula 2 (entre elas)
    relatorio = avaliar(Individuo([1, 3, 2]), instancia)

    assert relatorio.janelas_turma == 0  # aulas 1, 2 e 3 todas ocupadas -> sem vazio pra turma
    assert relatorio.fragmentacao_disciplina == 1  # matematica interrompida por portugues no meio


def test_aulas_geminadas_sem_janela_nem_fragmentacao():
    turma = Turma(1, "A", "MATUTINO")
    professor = Professor(1, "Prof", 1200)
    disciplina = Disciplina(1, "Matematica")
    sala = Sala(1, "Sala1")
    componente = ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=2)
    instancia = InstanciaProblema(
        turmas=[turma], professores=[professor], disciplinas=[disciplina], salas=[sala],
        componentes=[componente], slots_horario=SLOTS_SEGUNDA_3_AULAS,
    )

    relatorio = avaliar(Individuo([1, 2]), instancia)

    assert relatorio.janelas_turma == 0
    assert relatorio.fragmentacao_disciplina == 0


def test_buraco_na_grade_do_professor_e_contado_mesmo_sem_buraco_na_turma():
    """Mesmo professor dando aula pra 2 turmas diferentes no mesmo dia, com um horario vago
    entre elas -- nenhuma das turmas tem buraco (1 aula cada), mas o professor tem."""
    turmas = [Turma(1, "A", "MATUTINO"), Turma(2, "B", "MATUTINO")]
    professor = Professor(1, "Prof", 1200)
    disciplina = Disciplina(1, "Matematica")
    salas = [Sala(1, "Sala1"), Sala(2, "Sala2")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1),
        ComponenteCurricular(2, turma_id=2, professor_id=1, disciplina_id=1, sala_id=2, aulas_por_semana=1),
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=[professor], disciplinas=[disciplina], salas=salas,
        componentes=componentes, slots_horario=SLOTS_SEGUNDA_3_AULAS,
    )

    # turma 1 na aula 1, turma 2 na aula 3 -- professor pula a aula 2 (turma nenhuma tem 2+ aulas)
    relatorio = avaliar(Individuo([1, 3]), instancia)

    assert relatorio.janelas_turma == 0
    assert relatorio.janelas_professor == 1


SLOTS_TRES_DIAS = [
    SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
    SlotHorario(2, DiaSemana.TERCA, 1, time(7, 0), time(7, 50), "MATUTINO"),
    SlotHorario(3, DiaSemana.QUARTA, 1, time(7, 0), time(7, 50), "MATUTINO"),
]


def _instancia_disciplina_tres_aulas_semana() -> InstanciaProblema:
    turma = Turma(1, "A", "MATUTINO")
    professor = Professor(1, "Prof", 1200)
    disciplina = Disciplina(1, "Matematica")
    sala = Sala(1, "Sala1")
    componente = ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=3)
    return InstanciaProblema(
        turmas=[turma], professores=[professor], disciplinas=[disciplina], salas=[sala],
        componentes=[componente], slots_horario=SLOTS_TRES_DIAS,
    )


def test_disciplina_espalhada_pelos_dias_disponiveis_sem_deficit():
    instancia = _instancia_disciplina_tres_aulas_semana()

    # 3 aulas/semana, 3 dias letivos na instancia -- 1 aula por dia = ideal
    relatorio = avaliar(Individuo([1, 2, 3]), instancia)

    assert relatorio.distribuicao_semanal_disciplina == 0


def test_disciplina_concentrada_em_menos_dias_e_penalizada():
    instancia = _instancia_disciplina_tres_aulas_semana()

    # 3 aulas/semana, mas so 2 dias usados (2 aulas na segunda, 1 na terca) -- deficit de 1 dia
    relatorio = avaliar(Individuo([1, 1, 2]), instancia)

    assert relatorio.distribuicao_semanal_disciplina == 1
