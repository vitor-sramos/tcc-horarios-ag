from datetime import time

from motor_horarios.motor_ga import evoluir
from motor_horarios.persistencia import carregar_instancia_de_arquivo, carregar_instancia_de_json

CAMINHO_EXEMPLO = "exemplos/instancia_exemplo.json"


def _dados_minimos() -> dict:
    return {
        "turmas": [{"id": 1, "nome": "Turma 1", "turno": "MATUTINO"}],
        "disciplinas": [{"id": 1, "nome": "Disciplina 1"}],
        "professores": [{"id": 1, "nome": "Prof", "carga_horaria_maxima_minutos": 1200}],
        "componentes_curriculares": [
            {"id": 1, "turma_id": 1, "disciplina_id": 1, "professor_id": 1, "sala_id": 1, "aulas_por_semana": 2}
        ],
        "salas": [{"id": 1, "nome": "Sala 1"}],
    }


def test_carrega_instancia_do_exemplo_com_contagens_corretas():
    instancia = carregar_instancia_de_arquivo(CAMINHO_EXEMPLO)

    assert len(instancia.turmas) == 2
    assert len(instancia.professores) == 3
    assert len(instancia.disciplinas) == 3
    assert len(instancia.salas) == 2
    assert len(instancia.componentes) == 6
    assert len(instancia.disponibilidades) == 1


def test_instancia_do_exemplo_roda_o_ag_sem_erro():
    instancia = carregar_instancia_de_arquivo(CAMINHO_EXEMPLO)

    _, relatorio, historico = evoluir(instancia, geracoes=100, tamanho_populacao=30, seed=1)

    assert relatorio.valor >= 0
    assert len(historico) == 100


def test_configuracao_grade_omitida_usa_defaults():
    instancia = carregar_instancia_de_json(_dados_minimos())

    assert len(instancia.slots_horario) == 5 * 6  # 5 dias letivos padrão x 6 aulas/dia padrão
    assert {s.turno for s in instancia.slots_horario} == {"MATUTINO"}


def test_disponibilidade_converte_string_de_hora_para_time():
    dados = _dados_minimos()
    dados["disponibilidades"] = [
        {"id": 1, "professor_id": 1, "dia_semana": "SEGUNDA", "hora_inicio": "07:00", "hora_fim": "12:00"}
    ]

    instancia = carregar_instancia_de_json(dados)

    disponibilidade = instancia.disponibilidades[0]
    assert disponibilidade.hora_inicio == time(7, 0)
    assert disponibilidade.hora_fim == time(12, 0)


def test_professor_sem_disciplinas_habilitadas_fica_sem_restricao():
    instancia = carregar_instancia_de_json(_dados_minimos())

    assert instancia.professores[0].disciplinas_habilitadas == ()
