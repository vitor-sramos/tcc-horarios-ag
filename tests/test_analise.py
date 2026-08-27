from datetime import time

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
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


def test_detecta_sala_sobrecarregada():
    turmas = [Turma(1, "A", "MATUTINO"), Turma(2, "B", "MATUTINO")]
    professores = [Professor(1, "P1", 100_000), Professor(2, "P2", 100_000)]
    disciplinas = [Disciplina(1, "Disc")]
    salas = [Sala(1, "Sala unica")]
    # 2 slots disponiveis, mas a sala unica precisa acomodar 3 aulas -> 1 conflito inevitavel
    slots = [
        SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
        SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40), "MATUTINO"),
    ]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=2),
        ComponenteCurricular(2, turma_id=2, professor_id=2, disciplina_id=1, sala_id=1, aulas_por_semana=1),
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    limites = calcular_limites_teoricos(instancia)
    assert limites.minimo_conflitos_sala == 1
    assert limites.detalhes_sala == {1: 1}


def test_capacidade_de_turma_nao_vaza_entre_turnos():
    """Turma matutina sobrecarregada deve ser detectada mesmo com folga no turno vespertino de outra turma."""
    turmas = [Turma(1, "Matutina", "MATUTINO"), Turma(2, "Vespertina", "VESPERTINO")]
    professores = [Professor(1, "P1", 100_000), Professor(2, "P2", 100_000)]
    disciplinas = [Disciplina(1, "Disc")]
    salas = [Sala(1, "Sala 1"), Sala(2, "Sala 2")]
    slots = [
        SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
        SlotHorario(2, DiaSemana.SEGUNDA, 1, time(13, 0), time(13, 50), "VESPERTINO"),
        SlotHorario(3, DiaSemana.TERCA, 1, time(13, 0), time(13, 50), "VESPERTINO"),
        SlotHorario(4, DiaSemana.QUARTA, 1, time(13, 0), time(13, 50), "VESPERTINO"),
    ]
    # matutina tem so 1 slot no seu turno mas precisa de 2 aulas/semana -> 1 conflito inevitavel
    # vespertina tem 3 slots de folga no seu turno e so precisa de 1 aula/semana -> 0 conflito
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=2),
        ComponenteCurricular(2, turma_id=2, professor_id=2, disciplina_id=1, sala_id=2, aulas_por_semana=1),
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )

    limites = calcular_limites_teoricos(instancia)

    assert limites.detalhes_turma == {1: 1}
    assert limites.minimo_conflitos_turma == 1


def test_disponibilidade_nao_superestima_quando_professor_excede_total_de_slots():
    """Quando a demanda do professor ja excede o total de slots da semana, o conflito de professor
    (empilhamento no mesmo slot) e inevitavel de qualquer jeito -- e o empilhamento pode cair sobre
    um slot ja compativel, sem gerar violacao de disponibilidade extra por causa disso. A formula
    ingenua (demanda - compativeis) superestima o piso nesse caso, o que quebra a invariante de que
    nenhuma solucao do AG pode ficar abaixo do piso (bug real encontrado analisando resultados do
    harness em escala media)."""
    turma = Turma(1, "A", "MATUTINO")
    professor = Professor(1, "Sobrecarregado", 100_000)
    disciplina = Disciplina(1, "Disc")
    sala = Sala(1, "Sala")
    slots = [
        SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
        SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40), "MATUTINO"),
        SlotHorario(3, DiaSemana.TERCA, 1, time(7, 0), time(7, 50), "MATUTINO"),
    ]
    # 4 aulas/semana, so 3 slots no total -> ja estoura o total (1 conflito de professor inevitavel);
    # desses 3 slots, so 2 sao compativeis com a disponibilidade dele
    componente = ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=4)
    disponibilidade = Disponibilidade(
        id=1, professor_id=1, dia_semana=DiaSemana.SEGUNDA, hora_inicio=time(7, 0), hora_fim=time(9, 0)
    )
    instancia = InstanciaProblema(
        turmas=[turma], professores=[professor], disciplinas=[disciplina], salas=[sala],
        componentes=[componente], disponibilidades=[disponibilidade], slots_horario=slots,
    )

    limites = calcular_limites_teoricos(instancia)

    # formula ingenua daria max(0, 4-2)=2; correta: demanda(4) > n_slots(3) -> n_slots-compativeis = 3-2=1
    assert limites.detalhes_disponibilidade == {1: 1}


def test_instancia_sintetica_padrao_e_estruturalmente_viavel_em_slots():
    """O gerador (apos o fix) nao deve mais criar sala/professor/turma sobrecarregados por acidente.

    Carga/disponibilidade de professor continuam sorteio livre por design (ver docs/motor_horarios.md)
    -- essa seed especifica so comprova que existe uma instancia plenamente viavel nos parametros
    padrao, nao que toda seed sera assim.
    """
    instancia = gerar_instancia(seed=0)
    limites = calcular_limites_teoricos(instancia)
    assert limites.minimo_conflitos_sala == 0
    assert limites.minimo_conflitos_professor == 0
    assert limites.minimo_conflitos_turma == 0
    assert limites.minimo_violacoes_disponibilidade == 0
