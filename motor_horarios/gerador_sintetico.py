import random
from datetime import time

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

DIAS_LETIVOS_PADRAO = [
    DiaSemana.SEGUNDA,
    DiaSemana.TERCA,
    DiaSemana.QUARTA,
    DiaSemana.QUINTA,
    DiaSemana.SEXTA,
]


def _minutos_para_time(minutos: int) -> time:
    return time(hour=minutos // 60, minute=minutos % 60)


def _gerar_slots(
    dias: list[DiaSemana], aulas_por_dia: int, duracao_minutos: int, inicio_minutos: int
) -> list[SlotHorario]:
    slots = []
    slot_id = 1
    for dia in dias:
        atual = inicio_minutos
        for numero in range(1, aulas_por_dia + 1):
            fim = atual + duracao_minutos
            slots.append(
                SlotHorario(
                    id=slot_id,
                    dia_semana=dia,
                    numero_aula=numero,
                    hora_inicio=_minutos_para_time(atual),
                    hora_fim=_minutos_para_time(fim),
                )
            )
            slot_id += 1
            atual = fim
    return slots


def gerar_instancia(
    seed: int,
    n_turmas: int = 10,
    n_professores: int = 15,
    n_disciplinas: int = 8,
    n_salas: int = 10,
    disciplinas_por_turma: int = 5,
    aulas_por_semana_min: int = 2,
    aulas_por_semana_max: int = 5,
    dias_letivos: list[DiaSemana] | None = None,
    aulas_por_dia: int = 6,
    duracao_aula_minutos: int = 50,
    inicio_turno_minutos: int = 7 * 60,
    carga_horaria_professor_minutos: int = 1200,
    prob_disponibilidade_restrita: float = 0.3,
) -> InstanciaProblema:
    """Gera uma instância sintética parametrizável do problema, reprodutível pela seed."""
    rng = random.Random(seed)
    dias = dias_letivos or DIAS_LETIVOS_PADRAO

    turmas = [Turma(id=i, nome=f"Turma {i}", turno="MATUTINO") for i in range(1, n_turmas + 1)]
    professores = [
        Professor(id=i, nome=f"Professor {i}", carga_horaria_maxima_minutos=carga_horaria_professor_minutos)
        for i in range(1, n_professores + 1)
    ]
    disciplinas = [Disciplina(id=i, nome=f"Disciplina {i}") for i in range(1, n_disciplinas + 1)]
    salas = [Sala(id=i, nome=f"Sala {i}") for i in range(1, n_salas + 1)]
    slots = _gerar_slots(dias, aulas_por_dia, duracao_aula_minutos, inicio_turno_minutos)

    componentes = []
    componente_id = 1
    for turma in turmas:
        disciplinas_da_turma = rng.sample(disciplinas, k=min(disciplinas_por_turma, len(disciplinas)))
        for disciplina in disciplinas_da_turma:
            componentes.append(
                ComponenteCurricular(
                    id=componente_id,
                    turma_id=turma.id,
                    professor_id=rng.choice(professores).id,
                    disciplina_id=disciplina.id,
                    sala_id=rng.choice(salas).id,
                    aulas_por_semana=rng.randint(aulas_por_semana_min, aulas_por_semana_max),
                )
            )
            componente_id += 1

    disponibilidades = []
    disp_id = 1
    for professor in professores:
        if rng.random() < prob_disponibilidade_restrita:
            dia_restrito = rng.choice(dias)
            janela_minutos = duracao_aula_minutos * (aulas_por_dia // 2)
            disponibilidades.append(
                Disponibilidade(
                    id=disp_id,
                    professor_id=professor.id,
                    dia_semana=dia_restrito,
                    hora_inicio=_minutos_para_time(inicio_turno_minutos),
                    hora_fim=_minutos_para_time(inicio_turno_minutos + janela_minutos),
                )
            )
            disp_id += 1

    instancia = InstanciaProblema(
        turmas=turmas,
        professores=professores,
        disciplinas=disciplinas,
        salas=salas,
        componentes=componentes,
        disponibilidades=disponibilidades,
        slots_horario=slots,
    )
    instancia.validar()
    return instancia
