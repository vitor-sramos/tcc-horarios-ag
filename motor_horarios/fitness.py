from dataclasses import dataclass

from motor_horarios.individuo import Individuo, decodificar
from motor_horarios.modelo import InstanciaProblema, SlotHorario, Disponibilidade

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


def _duracao_minutos(slot: SlotHorario) -> int:
    inicio = slot.hora_inicio.hour * 60 + slot.hora_inicio.minute
    fim = slot.hora_fim.hour * 60 + slot.hora_fim.minute
    return fim - inicio


def _contar_conflitos(pares: list[tuple[int, int]]) -> int:
    """pares = (slot_id, recurso_id); conta quantas aulas 'sobram' além da 1a em cada grupo."""
    contagem: dict[tuple[int, int], int] = {}
    for par in pares:
        contagem[par] = contagem.get(par, 0) + 1
    return sum(c - 1 for c in contagem.values() if c > 1)


def _dentro_da_janela(slot: SlotHorario, disponibilidade: Disponibilidade) -> bool:
    return (
        slot.dia_semana == disponibilidade.dia_semana
        and slot.hora_inicio >= disponibilidade.hora_inicio
        and slot.hora_fim <= disponibilidade.hora_fim
    )


def avaliar(individuo: Individuo, instancia: InstanciaProblema) -> RelatorioFitness:
    grade = decodificar(individuo, instancia)

    pares_professor: list[tuple[int, int]] = []
    pares_sala: list[tuple[int, int]] = []
    pares_turma: list[tuple[int, int]] = []
    minutos_por_professor: dict[int, int] = {}
    violacoes_disponibilidade = 0

    disponibilidades_por_professor: dict[int, list[Disponibilidade]] = {}
    for d in instancia.disponibilidades:
        disponibilidades_por_professor.setdefault(d.professor_id, []).append(d)

    for componente_id, slot_id in grade:
        componente = instancia.componente(componente_id)
        slot = instancia.slot(slot_id)

        pares_professor.append((slot_id, componente.professor_id))
        pares_sala.append((slot_id, componente.sala_id))
        pares_turma.append((slot_id, componente.turma_id))

        duracao = _duracao_minutos(slot)
        minutos_por_professor[componente.professor_id] = (
            minutos_por_professor.get(componente.professor_id, 0) + duracao
        )

        janelas = disponibilidades_por_professor.get(componente.professor_id)
        if janelas and not any(_dentro_da_janela(slot, j) for j in janelas):
            violacoes_disponibilidade += 1

    violacoes_professor = _contar_conflitos(pares_professor)
    violacoes_sala = _contar_conflitos(pares_sala)
    violacoes_turma = _contar_conflitos(pares_turma)

    minutos_excedentes = 0
    for professor_id, minutos in minutos_por_professor.items():
        maximo = instancia.professor(professor_id).carga_horaria_maxima_minutos
        minutos_excedentes += max(0, minutos - maximo)

    total_hard = violacoes_professor + violacoes_sala + violacoes_turma + (minutos_excedentes / 60)
    valor = PESO_HARD * total_hard + PESO_SOFT * violacoes_disponibilidade

    return RelatorioFitness(
        valor=valor,
        violacoes_professor=violacoes_professor,
        violacoes_sala=violacoes_sala,
        violacoes_turma=violacoes_turma,
        minutos_excedentes_carga_horaria=minutos_excedentes,
        violacoes_disponibilidade=violacoes_disponibilidade,
    )
