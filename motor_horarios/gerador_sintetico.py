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

INICIO_PADRAO_POR_TURNO = {
    "MATUTINO": 7 * 60,
    "VESPERTINO": 13 * 60,
    "NOTURNO": 19 * 60,
}


def _minutos_para_time(minutos: int) -> time:
    return time(hour=minutos // 60, minute=minutos % 60)


def _gerar_slots(
    dias: list[DiaSemana],
    aulas_por_dia: int,
    duracao_minutos: int,
    inicio_minutos: int,
    turno: str,
    slot_id_inicial: int = 1,
) -> list[SlotHorario]:
    slots = []
    slot_id = slot_id_inicial
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
                    turno=turno,
                )
            )
            slot_id += 1
            atual = fim
    return slots


def _sortear_habilitacoes(
    n_professores: int, disciplinas: list[Disciplina], disciplinas_por_professor: int, rng: random.Random
) -> dict[int, tuple[int, ...]]:
    """Garante que toda disciplina tem pelo menos 1 professor habilitado, depois completa
    até disciplinas_por_professor por professor."""
    habilitacoes: dict[int, set[int]] = {i: set() for i in range(1, n_professores + 1)}
    for disciplina in disciplinas:
        professor_id = rng.randint(1, n_professores)
        habilitacoes[professor_id].add(disciplina.id)

    for professor_id, disciplinas_do_professor in habilitacoes.items():
        faltam = disciplinas_por_professor - len(disciplinas_do_professor)
        if faltam > 0:
            candidatas = [d.id for d in disciplinas if d.id not in disciplinas_do_professor]
            disciplinas_do_professor.update(rng.sample(candidatas, k=min(faltam, len(candidatas))))

    return {professor_id: tuple(sorted(ids)) for professor_id, ids in habilitacoes.items()}


def gerar_instancia(
    seed: int,
    n_turmas: int = 10,
    n_professores: int = 15,
    n_disciplinas: int = 8,
    n_salas: int = 10,
    disciplinas_por_turma: int = 5,
    disciplinas_por_professor: int = 3,
    aulas_por_semana_min: int = 2,
    aulas_por_semana_max: int = 5,
    dias_letivos: list[DiaSemana] | None = None,
    aulas_por_dia: int = 6,
    duracao_aula_minutos: int = 50,
    turnos: list[str] | None = None,
    carga_horaria_professor_minutos: int = 1200,
    prob_disponibilidade_restrita: float = 0.3,
) -> InstanciaProblema:
    """Gera uma instância sintética parametrizável do problema, reprodutível pela seed."""
    rng = random.Random(seed)
    dias = dias_letivos or DIAS_LETIVOS_PADRAO
    turnos = turnos or ["MATUTINO"]
    disciplinas_por_professor = min(disciplinas_por_professor, n_disciplinas)

    turmas = [Turma(id=i, nome=f"Turma {i}", turno=rng.choice(turnos)) for i in range(1, n_turmas + 1)]
    disciplinas = [Disciplina(id=i, nome=f"Disciplina {i}") for i in range(1, n_disciplinas + 1)]
    salas = [Sala(id=i, nome=f"Sala {i}") for i in range(1, n_salas + 1)]

    slots = []
    slot_id = 1
    for turno in turnos:
        slots_do_turno = _gerar_slots(
            dias, aulas_por_dia, duracao_aula_minutos,
            INICIO_PADRAO_POR_TURNO.get(turno, 7 * 60), turno, slot_id_inicial=slot_id,
        )
        slots.extend(slots_do_turno)
        slot_id += len(slots_do_turno)

    n_slots = len(slots)
    capacidade_restante_sala = {s.id: n_slots for s in salas}

    habilitacoes = _sortear_habilitacoes(n_professores, disciplinas, disciplinas_por_professor, rng)
    professores = [
        Professor(
            id=i, nome=f"Professor {i}", carga_horaria_maxima_minutos=carga_horaria_professor_minutos,
            disciplinas_habilitadas=habilitacoes[i],
        )
        for i in range(1, n_professores + 1)
    ]

    componentes = []
    componente_id = 1
    for turma in turmas:
        disciplinas_da_turma = rng.sample(disciplinas, k=min(disciplinas_por_turma, len(disciplinas)))
        for disciplina in disciplinas_da_turma:
            aulas_semana = rng.randint(aulas_por_semana_min, aulas_por_semana_max)

            salas_viaveis = [s for s in salas if capacidade_restante_sala[s.id] >= aulas_semana]
            sala_escolhida = (
                rng.choice(salas_viaveis)
                if salas_viaveis
                else max(salas, key=lambda s: capacidade_restante_sala[s.id])
            )
            capacidade_restante_sala[sala_escolhida.id] -= aulas_semana

            professores_da_disciplina = [p for p in professores if disciplina.id in p.disciplinas_habilitadas]

            componentes.append(
                ComponenteCurricular(
                    id=componente_id,
                    turma_id=turma.id,
                    professor_id=rng.choice(professores_da_disciplina).id,
                    disciplina_id=disciplina.id,
                    sala_id=sala_escolhida.id,
                    aulas_por_semana=aulas_semana,
                )
            )
            componente_id += 1

    inicio_dia = min(INICIO_PADRAO_POR_TURNO.get(t, 7 * 60) for t in turnos)
    fim_dia = max(INICIO_PADRAO_POR_TURNO.get(t, 7 * 60) for t in turnos) + duracao_aula_minutos * aulas_por_dia

    disponibilidades = []
    disp_id = 1
    for professor in professores:
        if rng.random() < prob_disponibilidade_restrita:
            # professor indisponivel em 1 dia da semana, disponivel o dia inteiro (todos os turnos) nos demais
            dia_indisponivel = rng.choice(dias)
            for dia in dias:
                if dia == dia_indisponivel:
                    continue
                disponibilidades.append(
                    Disponibilidade(
                        id=disp_id,
                        professor_id=professor.id,
                        dia_semana=dia,
                        hora_inicio=_minutos_para_time(inicio_dia),
                        hora_fim=_minutos_para_time(fim_dia),
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
