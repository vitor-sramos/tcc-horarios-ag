import inspect
from dataclasses import asdict

from flask import Flask, jsonify, request, send_from_directory

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.motor_ga import evoluir
from motor_horarios.visualizacao import montar_grade
from webapp.serializacao import eixos_ordenados, serializar_slots

app = Flask(__name__, static_folder="static", static_url_path="")


def _defaults(func, excluir: set[str] = frozenset()) -> dict:
    return {
        nome: parametro.default
        for nome, parametro in inspect.signature(func).parameters.items()
        if parametro.default is not inspect.Parameter.empty and nome not in excluir
    }


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/parametros-padrao")
def parametros_padrao():
    return jsonify(
        {
            "instancia": _defaults(gerar_instancia, excluir={"dias_letivos"}),
            "ag": _defaults(evoluir, excluir={"instancia"}),
        }
    )


@app.post("/api/executar")
def executar():
    body = request.get_json(force=True) or {}
    try:
        instancia = gerar_instancia(**body.get("instancia", {}))
        melhor, relatorio, historico = evoluir(instancia, **body.get("ag", {}))
    except (TypeError, ValueError) as erro:
        return jsonify({"erro": str(erro)}), 400

    piso = calcular_limites_teoricos(instancia)
    grade = montar_grade(instancia, melhor)
    dias, numeros_aula = eixos_ordenados(instancia.slots_horario)

    return jsonify(
        {
            "relatorio": asdict(relatorio),
            "piso_teorico": asdict(piso),
            "turmas": [asdict(t) for t in instancia.turmas],
            "slots": serializar_slots(instancia.slots_horario),
            "dias": dias,
            "numeros_aula": numeros_aula,
            "grade_por_turma": grade,
            "historico_fitness": historico,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
