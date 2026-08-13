from datetime import time

import pytest

from motor_horarios.modelo import (
    ComponenteCurricular,
    DiaSemana,
    Disciplina,
    InstanciaProblema,
    Professor,
    Sala,
    SlotHorario,
    Turma,
)


def _instancia_minima(aulas_por_semana: int = 3) -> InstanciaProblema:
    turma = Turma(id=1, nome="Turma 1", turno="MATUTINO")
    professor = Professor(id=1, nome="Prof", carga_horaria_maxima_minutos=1200)
    disciplina = Disciplina(id=1, nome="Disciplina")
    sala = Sala(id=1, nome="Sala")
    componente = ComponenteCurricular(
        id=1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=aulas_por_semana
    )
    slot = SlotHorario(id=1, dia_semana=DiaSemana.SEGUNDA, numero_aula=1, hora_inicio=time(7, 0), hora_fim=time(7, 50))
    return InstanciaProblema(
        turmas=[turma], professores=[professor], disciplinas=[disciplina], salas=[sala],
        componentes=[componente], slots_horario=[slot],
    )


def test_aulas_pendentes_expande_pelo_aulas_por_semana():
    instancia = _instancia_minima(aulas_por_semana=5)
    assert len(instancia.aulas_pendentes()) == 5


def test_aulas_pendentes_referencia_o_componente_correto():
    instancia = _instancia_minima(aulas_por_semana=2)
    pendentes = instancia.aulas_pendentes()
    assert all(p.componente_id == 1 for p in pendentes)
    assert {p.indice for p in pendentes} == {0, 1}


def test_componente_curricular_rejeita_aulas_por_semana_zero():
    with pytest.raises(ValueError):
        ComponenteCurricular(id=1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=0)


def test_validar_detecta_referencia_invalida():
    instancia = _instancia_minima()
    componente_invalido = ComponenteCurricular(
        id=2, turma_id=999, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1
    )
    instancia.componentes.append(componente_invalido)
    with pytest.raises(ValueError):
        instancia.validar()
