from dataclasses import dataclass

from motor_horarios.individuo import Individuo, decodificar
from motor_horarios.modelo import DiaSemana, Disponibilidade, InstanciaProblema, SlotHorario

PESO_HARD = 1000.0
PESO_SOFT = 1.0


@dataclass
class RelatorioFitness:
    valor: float
    violacoes_professor: int
    violacoes_sala: int
    violacoes_turma: int
    minutos_excedentes_carga_horaria: int
    violacoes_disponibilidade: int
    janelas_turma: int
    fragmentacao_disciplina: int
    janelas_professor: int
    distribuicao_semanal_disciplina: int


def duracao_minutos(slot: SlotHorario) -> int:
    inicio = slot.hora_inicio.hour * 60 + slot.hora_inicio.minute
    fim = slot.hora_fim.hour * 60 + slot.hora_fim.minute
    return fim - inicio


def _contar_conflitos(pares: list[tuple[int, int]]) -> int:
    """pares = (slot_id, recurso_id); conta quantas aulas 'sobram' além da 1a em cada grupo."""
    contagem: dict[tuple[int, int], int] = {}
    for par in pares:
        contagem[par] = contagem.get(par, 0) + 1
    return sum(c - 1 for c in contagem.values() if c > 1)


def _contar_buracos(ocupacoes: dict) -> int:
    """ocupacoes = {chave: set(numero_aula)}; soma os buracos entre a 1a e a ultima aula de
    cada grupo com 2+ aulas (nao conta inicio/fim do dia livre, so vazio entre duas aulas)."""
    total = 0
    for numeros in ocupacoes.values():
        if len(numeros) >= 2:
            total += (max(numeros) - min(numeros) + 1) - len(numeros)
    return total


def dentro_da_janela(slot: SlotHorario, disponibilidade: Disponibilidade) -> bool:
    return (
        slot.dia_semana == disponibilidade.dia_semana
        and slot.hora_inicio >= disponibilidade.hora_inicio
        and slot.hora_fim <= disponibilidade.hora_fim
    )


def _dias_disponiveis_por_turno(instancia: InstanciaProblema) -> dict[str, int]:
    dias_por_turno: dict[str, set[DiaSemana]] = {}
    for s in instancia.slots_horario:
        dias_por_turno.setdefault(s.turno, set()).add(s.dia_semana)
    return {turno: len(dias) for turno, dias in dias_por_turno.items()}


def _contar_concentracao_semanal(
    dias_por_componente: dict[int, set[DiaSemana]], instancia: InstanciaProblema
) -> int:
    """Para cada componente curricular, o ideal é 1 aula por dia distinto, até o limite de dias
    letivos existentes no turno da turma (ex: 3 aulas/semana com 5 dias disponíveis -> ideal = 3
    dias diferentes). Penaliza o déficit quando as aulas da semana ficam concentradas em menos
    dias do que isso -- mesmo sem gerar conflito de turma nem buraco na grade."""
    dias_por_turno = _dias_disponiveis_por_turno(instancia)
    total = 0
    for componente in instancia.componentes:
        turno = instancia.turma(componente.turma_id).turno
        ideal = min(componente.aulas_por_semana, dias_por_turno.get(turno, 0))
        usados = len(dias_por_componente.get(componente.id, set()))
        total += max(0, ideal - usados)
    return total


def avaliar(individuo: Individuo, instancia: InstanciaProblema) -> RelatorioFitness:
    grade = decodificar(individuo, instancia)

    pares_professor: list[tuple[int, int]] = []
    pares_sala: list[tuple[int, int]] = []
    pares_turma: list[tuple[int, int]] = []
    minutos_por_professor: dict[int, int] = {}
    violacoes_disponibilidade = 0
    ocupacao_turma_dia: dict[tuple[int, DiaSemana], set[int]] = {}
    ocupacao_disciplina_dia: dict[tuple[int, DiaSemana, int], set[int]] = {}
    ocupacao_professor_dia: dict[tuple[int, DiaSemana], set[int]] = {}
    dias_por_componente: dict[int, set[DiaSemana]] = {}

    disponibilidades_por_professor: dict[int, list[Disponibilidade]] = {}
    for d in instancia.disponibilidades:
        disponibilidades_por_professor.setdefault(d.professor_id, []).append(d)

    for componente_id, slot_id in grade:
        componente = instancia.componente(componente_id)
        slot = instancia.slot(slot_id)

        pares_professor.append((slot_id, componente.professor_id))
        pares_sala.append((slot_id, componente.sala_id))
        pares_turma.append((slot_id, componente.turma_id))

        duracao = duracao_minutos(slot)
        minutos_por_professor[componente.professor_id] = (
            minutos_por_professor.get(componente.professor_id, 0) + duracao
        )

        janelas = disponibilidades_por_professor.get(componente.professor_id)
        if janelas and not any(dentro_da_janela(slot, j) for j in janelas):
            violacoes_disponibilidade += 1

        ocupacao_turma_dia.setdefault((componente.turma_id, slot.dia_semana), set()).add(slot.numero_aula)
        ocupacao_disciplina_dia.setdefault(
            (componente.turma_id, slot.dia_semana, componente.disciplina_id), set()
        ).add(slot.numero_aula)
        ocupacao_professor_dia.setdefault((componente.professor_id, slot.dia_semana), set()).add(slot.numero_aula)
        dias_por_componente.setdefault(componente_id, set()).add(slot.dia_semana)

    violacoes_professor = _contar_conflitos(pares_professor)
    violacoes_sala = _contar_conflitos(pares_sala)
    violacoes_turma = _contar_conflitos(pares_turma)
    janelas_turma = _contar_buracos(ocupacao_turma_dia)
    fragmentacao_disciplina = _contar_buracos(ocupacao_disciplina_dia)
    janelas_professor = _contar_buracos(ocupacao_professor_dia)
    distribuicao_semanal_disciplina = _contar_concentracao_semanal(dias_por_componente, instancia)

    minutos_excedentes = 0
    for professor_id, minutos in minutos_por_professor.items():
        maximo = instancia.professor(professor_id).carga_horaria_maxima_minutos
        minutos_excedentes += max(0, minutos - maximo)

    total_hard = violacoes_professor + violacoes_sala + violacoes_turma + (minutos_excedentes / 60)
    total_soft = (
        violacoes_disponibilidade
        + janelas_turma
        + fragmentacao_disciplina
        + janelas_professor
        + distribuicao_semanal_disciplina
    )
    valor = PESO_HARD * total_hard + PESO_SOFT * total_soft

    return RelatorioFitness(
        valor=valor,
        violacoes_professor=violacoes_professor,
        violacoes_sala=violacoes_sala,
        violacoes_turma=violacoes_turma,
        minutos_excedentes_carga_horaria=minutos_excedentes,
        violacoes_disponibilidade=violacoes_disponibilidade,
        janelas_turma=janelas_turma,
        fragmentacao_disciplina=fragmentacao_disciplina,
        janelas_professor=janelas_professor,
        distribuicao_semanal_disciplina=distribuicao_semanal_disciplina,
    )
