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
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 6)
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


def _instancia_dominio_quase_lotado() -> InstanciaProblema:
    """10 componentes ocupam 10 dos 11 slots do dominio; so o slot 11 fica livre.

    Regressao do achado de 2026-09-02: com poucas tentativas (comportamento antigo, capado
    e com reposicao), o reparo tinha boa chance de nao experimentar o unico slot livre restante
    num dominio grande. Sem cap (tentativas=None, o padrao atual), o reparo percorre o dominio
    inteiro embaralhado e sempre acha o slot livre, se ele existir.
    """
    n = 10
    turmas = [Turma(1, "T1", "MATUTINO")]
    professores = [Professor(i, f"P{i}", 100_000) for i in range(1, n + 2)]
    disciplinas = [Disciplina(1, "D")]
    salas = [Sala(1, "S1")]
    componentes = [
        ComponenteCurricular(i, turma_id=1, professor_id=i, disciplina_id=1, sala_id=1, aulas_por_semana=1)
        for i in range(1, n + 1)
    ]
    # componente extra forcado no slot 1 (mesma sala/turma do componente 1) -> conflito de sala/turma
    componentes.append(
        ComponenteCurricular(n + 1, turma_id=1, professor_id=n + 1, disciplina_id=1, sala_id=1, aulas_por_semana=1)
    )
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, n + 2)
    ]
    return InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )


def test_reparar_sem_cap_de_tentativas_acha_unico_slot_livre_em_dominio_grande():
    instancia = _instancia_dominio_quase_lotado()
    genes = list(range(1, 11)) + [1]  # componente 11 forcado no slot 1, ja ocupado
    individuo = Individuo(genes)

    capado = reparar(individuo, instancia, random.Random(0), tentativas=1)
    assert avaliar(capado, instancia).violacoes_sala > 0  # 1 tentativa nao acha o unico slot livre

    sem_cap = reparar(individuo, instancia, random.Random(0), tentativas=None)
    relatorio = avaliar(sem_cap, instancia)
    assert relatorio.violacoes_sala == 0
    assert relatorio.violacoes_turma == 0


def test_mutar_reproducivel_com_mesma_seed():
    dominio_por_gene = [[1, 2, 3, 4, 5]] * 5
    individuo = Individuo([1, 1, 1, 1, 1])
    a = mutar(individuo, dominio_por_gene, random.Random(7), taxa=0.5)
    b = mutar(individuo, dominio_por_gene, random.Random(7), taxa=0.5)
    assert a.genes == b.genes


def test_mutar_e_reparar_nunca_saem_do_turno_da_turma():
    """Instancia multi-turno: cada componente esta preso ao turno da sua turma (ver InstanciaProblema.dominio_genes)."""
    turmas = [Turma(1, "Matutina", "MATUTINO"), Turma(2, "Vespertina", "VESPERTINO")]
    professores = [Professor(1, "Prof", 100_000)]
    disciplinas = [Disciplina(1, "Disc")]
    salas = [Sala(1, "Sala 1")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1),
        ComponenteCurricular(2, turma_id=2, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
        SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40), "MATUTINO"),
        SlotHorario(3, DiaSemana.SEGUNDA, 1, time(13, 0), time(13, 50), "VESPERTINO"),
        SlotHorario(4, DiaSemana.SEGUNDA, 2, time(13, 50), time(14, 40), "VESPERTINO"),
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    dominio_por_gene = instancia.dominio_genes()
    rng = random.Random(0)

    for _ in range(50):
        individuo = Individuo([rng.choice([1, 2, 3, 4]) for _ in range(2)])
        mutado = mutar(individuo, dominio_por_gene, rng, taxa=1.0)
        reparado = reparar(mutado, instancia, rng, tentativas=10)
        assert reparado.genes[0] in {1, 2}  # componente 1 (matutina) so pode usar slots 1/2
        assert reparado.genes[1] in {3, 4}  # componente 2 (vespertina) so pode usar slots 3/4
