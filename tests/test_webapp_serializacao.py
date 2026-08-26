from datetime import time

from motor_horarios.modelo import DiaSemana, SlotHorario
from webapp.app import app
from webapp.serializacao import eixos_ordenados, serializar_slots


def _slot(id_, dia, numero, hora_inicio, hora_fim, turno="MATUTINO"):
    return SlotHorario(
        id=id_, dia_semana=dia, numero_aula=numero, hora_inicio=hora_inicio, hora_fim=hora_fim, turno=turno,
    )


def test_serializar_slots_converte_enum_e_time_para_string():
    slots = [
        _slot(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50)),
        _slot(2, DiaSemana.TERCA, 2, time(7, 50), time(8, 40), turno="VESPERTINO"),
    ]

    serializados = serializar_slots(slots)

    assert serializados == [
        {"id": 1, "dia_semana": "SEGUNDA", "numero_aula": 1, "hora_inicio": "07:00", "hora_fim": "07:50", "turno": "MATUTINO"},
        {"id": 2, "dia_semana": "TERCA", "numero_aula": 2, "hora_inicio": "07:50", "hora_fim": "08:40", "turno": "VESPERTINO"},
    ]


def test_eixos_ordenados_respeita_ordem_do_enum_e_deduplica():
    slots = [
        _slot(1, DiaSemana.QUARTA, 2, time(7, 0), time(7, 50)),
        _slot(2, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50)),
        _slot(3, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40)),
        _slot(4, DiaSemana.QUARTA, 1, time(7, 0), time(7, 50)),
    ]

    dias, numeros_aula = eixos_ordenados(slots)

    assert dias == ["SEGUNDA", "QUARTA"]
    assert numeros_aula == [1, 2]


def test_post_executar_end_to_end():
    cliente = app.test_client()
    corpo = {
        "instancia": {
            "seed": 1, "n_turmas": 1, "n_professores": 2, "n_disciplinas": 2,
            "n_salas": 2, "disciplinas_por_turma": 2,
        },
        "ag": {"geracoes": 1, "tamanho_populacao": 4, "seed": 1},
    }

    resposta = cliente.post("/api/executar", json=corpo)

    assert resposta.status_code == 200
    dados = resposta.get_json()
    assert set(dados) == {
        "relatorio", "piso_teorico", "turmas", "slots",
        "dias", "numeros_aula", "grade_por_turma", "historico_fitness",
    }
    assert len(dados["turmas"]) == 1


def test_post_executar_com_multiplos_turnos():
    cliente = app.test_client()
    corpo = {
        "instancia": {
            "seed": 1, "n_turmas": 4, "n_professores": 3, "n_disciplinas": 2,
            "n_salas": 2, "disciplinas_por_turma": 2, "turnos": ["MATUTINO", "VESPERTINO"],
        },
        "ag": {"geracoes": 1, "tamanho_populacao": 4, "seed": 1},
    }

    resposta = cliente.post("/api/executar", json=corpo)

    assert resposta.status_code == 200
    dados = resposta.get_json()
    assert {t["turno"] for t in dados["turmas"]} <= {"MATUTINO", "VESPERTINO"}
    assert all("turno" in s for s in dados["slots"])


def test_post_executar_com_parametro_invalido_retorna_400():
    cliente = app.test_client()

    resposta = cliente.post("/api/executar", json={"instancia": {"seed": 1, "n_turmas_invalido": 1}})

    assert resposta.status_code == 400
    assert "erro" in resposta.get_json()
