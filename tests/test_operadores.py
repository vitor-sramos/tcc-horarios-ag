import random
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
from motor_horarios.operadores import mutar, reparar, reparar_disponibilidade


def _instancia_com_folga() -> InstanciaProblema:
    """3 turmas, 1 professor unico, slots suficientes para acomodar todo mundo sem conflito."""
    turmas = [Turma(i, f"Turma {i}", "MATUTINO") for i in range(1, 4)]
    professores = [Professor(1, "Prof", 100_000)]
    disciplinas = [Disciplina(1, "Disc")]
    salas = [Sala(i, f"Sala {i}") for i in range(1, 4)]
    componentes = [
        ComponenteCurricular(i, turma_id=i, professor_id=1, disciplina_id=1, sala_id=i, aulas_por_semana=1)
        for i in range(1, 4)
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50)) for i in range(1, 6)
    ]
    return InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )


def test_reparar_nao_piora_hard_constraints():
    instancia = _instancia_com_folga()
    rng = random.Random(0)
    # forca todo mundo no mesmo slot -> 2 conflitos de professor/sala/turma
    individuo = Individuo([1, 1, 1])
    antes = avaliar(individuo, instancia)
    reparado = reparar(individuo, instancia, rng, tentativas=10)
    depois = avaliar(reparado, instancia)
    assert depois.violacoes_professor <= antes.violacoes_professor
    assert depois.violacoes_sala <= antes.violacoes_sala
    assert depois.violacoes_turma <= antes.violacoes_turma


def test_reparar_zera_conflitos_quando_ha_folga_suficiente():
    instancia = _instancia_com_folga()
    rng = random.Random(0)
    individuo = Individuo([1, 1, 1])
    reparado = reparar(individuo, instancia, rng, tentativas=20)
    relatorio = avaliar(reparado, instancia)
    assert relatorio.violacoes_professor == 0
    assert relatorio.violacoes_sala == 0
    assert relatorio.violacoes_turma == 0


def test_reparar_disponibilidade_move_aula_para_janela_valida_sem_novo_conflito():
    instancia = _instancia_com_folga()
    # slots (ver _instancia_com_folga): 1=08:00 2=09:00 3=10:00 4=11:00 5=12:00
    # janela 09:00-12:00 cobre os slots 2, 3 e 4 -- espaco de sobra pra mover o slot 1 (fora da janela)
    instancia.disponibilidades.append(
        Disponibilidade(id=1, professor_id=1, dia_semana=DiaSemana.SEGUNDA, hora_inicio=time(9, 0), hora_fim=time(12, 0))
    )
    rng = random.Random(0)
    individuo = Individuo([1, 2, 3])  # componente 1 esta no slot 1, fora da janela
    antes = avaliar(individuo, instancia)
    assert antes.violacoes_disponibilidade == 1

    reparado = reparar_disponibilidade(individuo, instancia, rng, tentativas=10)
    depois = avaliar(reparado, instancia)
    assert depois.violacoes_disponibilidade == 0
    assert depois.violacoes_professor == 0
    assert depois.violacoes_sala == 0
    assert depois.violacoes_turma == 0


def test_mutar_reproducivel_com_mesma_seed():
    slot_ids = [1, 2, 3, 4, 5]
    individuo = Individuo([1, 1, 1, 1, 1])
    a = mutar(individuo, slot_ids, random.Random(7), taxa=0.5)
    b = mutar(individuo, slot_ids, random.Random(7), taxa=0.5)
    assert a.genes == b.genes
