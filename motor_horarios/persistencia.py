import json
from datetime import time

from motor_horarios.gerador_sintetico import (
    DIAS_LETIVOS_PADRAO,
    INICIO_PADRAO_POR_TURNO,
    gerar_slots,
)
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


def _parse_hora(texto: str) -> time:
    hora, minuto = texto.split(":")
    return time(int(hora), int(minuto))


def _gerar_slots_da_configuracao(config: dict) -> list[SlotHorario]:
    dias = [DiaSemana[nome] for nome in config.get("dias_letivos", [d.name for d in DIAS_LETIVOS_PADRAO])]
    aulas_por_dia = config.get("aulas_por_dia", 6)
    duracao_aula_minutos = config.get("duracao_aula_minutos", 50)
    turnos = config.get("turnos", ["MATUTINO"])

    slots: list[SlotHorario] = []
    slot_id = 1
    for turno in turnos:
        slots_do_turno = gerar_slots(
            dias, aulas_por_dia, duracao_aula_minutos,
            INICIO_PADRAO_POR_TURNO.get(turno, 7 * 60), turno, slot_id_inicial=slot_id,
        )
        slots.extend(slots_do_turno)
        slot_id += len(slots_do_turno)
    return slots


def carregar_instancia_de_json(dados: dict) -> InstanciaProblema:
    """Monta uma InstanciaProblema a partir de um dict no formato de instância (turmas, professores,
    disciplinas, salas, componentes_curriculares, disponibilidades, configuracao_grade).

    professor_id em cada componente curricular vem sempre explícito (dados reais já sabem quem
    leciona o quê) -- ao contrário de gerar_instancia(), não há atribuição automática por habilitação.
    """
    slots = _gerar_slots_da_configuracao(dados.get("configuracao_grade", {}))

    turmas = [Turma(id=t["id"], nome=t["nome"], turno=t["turno"]) for t in dados["turmas"]]
    disciplinas = [Disciplina(id=d["id"], nome=d["nome"]) for d in dados["disciplinas"]]
    salas = [Sala(id=s["id"], nome=s["nome"]) for s in dados.get("salas", [])]
    professores = [
        Professor(
            id=p["id"],
            nome=p["nome"],
            carga_horaria_maxima_minutos=p["carga_horaria_maxima_minutos"],
            disciplinas_habilitadas=tuple(p.get("disciplinas_habilitadas", ())),
        )
        for p in dados["professores"]
    ]
    componentes = [
        ComponenteCurricular(
            id=c["id"],
            turma_id=c["turma_id"],
            professor_id=c["professor_id"],
            disciplina_id=c["disciplina_id"],
            sala_id=c["sala_id"],
            aulas_por_semana=c["aulas_por_semana"],
        )
        for c in dados["componentes_curriculares"]
    ]
    disponibilidades = [
        Disponibilidade(
            id=d["id"],
            professor_id=d["professor_id"],
            dia_semana=DiaSemana[d["dia_semana"]],
            hora_inicio=_parse_hora(d["hora_inicio"]),
            hora_fim=_parse_hora(d["hora_fim"]),
        )
        for d in dados.get("disponibilidades", [])
    ]

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


def carregar_instancia_de_arquivo(caminho: str) -> InstanciaProblema:
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)
    return carregar_instancia_de_json(dados)
