from dataclasses import dataclass

from motor_horarios.fitness import dentro_da_janela, duracao_minutos
from motor_horarios.modelo import InstanciaProblema


@dataclass
class LimitesTeoricos:
    minimo_conflitos_sala: int
    minimo_conflitos_professor: int
    minimo_conflitos_turma: int
    minimo_violacoes_disponibilidade: int
    minimo_minutos_excedentes_carga_horaria: int
    detalhes_sala: dict[int, int]
    detalhes_professor: dict[int, int]
    detalhes_turma: dict[int, int]
    detalhes_disponibilidade: dict[int, int]
    detalhes_carga_horaria: dict[int, int]


def _demanda_por(instancia: InstanciaProblema, atributo: str) -> dict[int, int]:
    demanda: dict[int, int] = {}
    for c in instancia.componentes:
        chave = getattr(c, atributo)
        demanda[chave] = demanda.get(chave, 0) + c.aulas_por_semana
    return demanda


def calcular_limites_teoricos(instancia: InstanciaProblema) -> LimitesTeoricos:
    """Piso de violações inevitáveis nesta instância, por sobrecarga de recurso.

    Nunca julgue a qualidade de uma solução do AG sem comparar com esse piso —
    um recurso sobrecarregado (mais aulas/semana do que slots existentes) força
    conflitos que nenhum algoritmo consegue evitar.
    """
    n_slots = len(instancia.slots_horario)
    n_slots_por_turno: dict[str, int] = {}
    for s in instancia.slots_horario:
        n_slots_por_turno[s.turno] = n_slots_por_turno.get(s.turno, 0) + 1

    demanda_sala = _demanda_por(instancia, "sala_id")
    demanda_professor = _demanda_por(instancia, "professor_id")
    demanda_turma = _demanda_por(instancia, "turma_id")

    # sala/professor podem ser usados em qualquer turno -> capacidade e o total global de slots.
    # turma esta presa ao seu proprio turno -> capacidade e so os slots daquele turno.
    detalhes_sala = {k: max(0, v - n_slots) for k, v in demanda_sala.items() if v > n_slots}
    detalhes_professor = {k: max(0, v - n_slots) for k, v in demanda_professor.items() if v > n_slots}
    detalhes_turma = {}
    for turma_id, v in demanda_turma.items():
        capacidade = n_slots_por_turno.get(instancia.turma(turma_id).turno, 0)
        if v > capacidade:
            detalhes_turma[turma_id] = v - capacidade

    disponibilidades_por_professor: dict[int, list] = {}
    for d in instancia.disponibilidades:
        disponibilidades_por_professor.setdefault(d.professor_id, []).append(d)

    detalhes_disponibilidade: dict[int, int] = {}
    for professor_id, janelas in disponibilidades_por_professor.items():
        # uniao de todas as janelas do professor, nao uma por vez -- um professor pode
        # ter varias janelas (uma por dia disponivel) que juntas cobrem bem mais slots
        slots_compativeis = sum(
            1 for s in instancia.slots_horario if any(dentro_da_janela(s, j) for j in janelas)
        )
        precisa = demanda_professor.get(professor_id, 0)
        minimo = max(0, precisa - slots_compativeis)
        if minimo > 0:
            detalhes_disponibilidade[professor_id] = minimo

    # melhor caso possivel: todas as aulas do professor caindo nos slots mais curtos que existem
    menor_duracao = min((duracao_minutos(s) for s in instancia.slots_horario), default=0)
    detalhes_carga_horaria: dict[int, int] = {}
    for professor in instancia.professores:
        minutos_no_melhor_caso = demanda_professor.get(professor.id, 0) * menor_duracao
        excesso = max(0, minutos_no_melhor_caso - professor.carga_horaria_maxima_minutos)
        if excesso > 0:
            detalhes_carga_horaria[professor.id] = excesso

    return LimitesTeoricos(
        minimo_conflitos_sala=sum(detalhes_sala.values()),
        minimo_conflitos_professor=sum(detalhes_professor.values()),
        minimo_conflitos_turma=sum(detalhes_turma.values()),
        minimo_violacoes_disponibilidade=sum(detalhes_disponibilidade.values()),
        minimo_minutos_excedentes_carga_horaria=sum(detalhes_carga_horaria.values()),
        detalhes_sala=detalhes_sala,
        detalhes_professor=detalhes_professor,
        detalhes_turma=detalhes_turma,
        detalhes_disponibilidade=detalhes_disponibilidade,
        detalhes_carga_horaria=detalhes_carga_horaria,
    )
