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
    SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50)),
    SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40)),
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
