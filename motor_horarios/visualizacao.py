import os
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from motor_horarios.individuo import Individuo, decodificar
from motor_horarios.modelo import DiaSemana, InstanciaProblema, Turma

_ABREVIACAO_DIA = {
    DiaSemana.SEGUNDA: "SEG",
    DiaSemana.TERCA: "TER",
    DiaSemana.QUARTA: "QUA",
    DiaSemana.QUINTA: "QUI",
    DiaSemana.SEXTA: "SEX",
    DiaSemana.SABADO: "SAB",
}


def montar_grade(instancia: InstanciaProblema, individuo: Individuo) -> dict[int, dict[int, dict[str, str]]]:
    """grade[turma_id][slot_id] = {"disciplina", "professor", "sala"} para cada aula alocada."""
    grade: dict[int, dict[int, dict[str, str]]] = {t.id: {} for t in instancia.turmas}
    for componente_id, slot_id in decodificar(individuo, instancia):
        componente = instancia.componente(componente_id)
        grade[componente.turma_id][slot_id] = {
            "disciplina": instancia.disciplina(componente.disciplina_id).nome,
            "professor": instancia.professor(componente.professor_id).nome,
            "sala": instancia.sala(componente.sala_id).nome,
        }
    return grade


def _eixos_da_grade(slots: list) -> tuple[list[DiaSemana], list[int]]:
    ordem_dias = list(DiaSemana)
    dias_presentes = sorted({s.dia_semana for s in slots}, key=ordem_dias.index)
    numeros_presentes = sorted({s.numero_aula for s in slots})
    return dias_presentes, numeros_presentes


def _slot_id_por_dia_e_numero(slots: list) -> dict[tuple[DiaSemana, int], int]:
    return {(s.dia_semana, s.numero_aula): s.id for s in slots}


def _renderizar_quadro_turma(ax, instancia: InstanciaProblema, grade_turma: dict[int, dict], turma: Turma) -> None:
    # slots de outros turnos podem repetir (dia, numero_aula) -- restringe ao turno da turma
    # antes de montar eixos/lookup, senao as celulas colidem.
    slots_do_turno = [s for s in instancia.slots_horario if s.turno == turma.turno]
    dias, numeros = _eixos_da_grade(slots_do_turno)
    slot_por_posicao = _slot_id_por_dia_e_numero(slots_do_turno)
    mapa_cores = plt.get_cmap("Pastel1")
    disciplinas_vistas: dict[str, int] = {}

    celulas: list[list[str]] = []
    cores: list[list] = []
    for numero in numeros:
        linha_texto = []
        linha_cor = []
        for dia in dias:
            slot_id = slot_por_posicao.get((dia, numero))
            info = grade_turma.get(slot_id) if slot_id is not None else None
            if info is None:
                linha_texto.append("")
                linha_cor.append("#f2f2f2")
            else:
                linha_texto.append(f"{info['disciplina']}\n{info['professor']}\n{info['sala']}")
                indice = disciplinas_vistas.setdefault(info["disciplina"], len(disciplinas_vistas))
                linha_cor.append(mapa_cores(indice % mapa_cores.N))
        celulas.append(linha_texto)
        cores.append(linha_cor)

    ax.axis("off")
    ax.set_title(turma.nome, fontsize=10, fontweight="bold")
    tabela = ax.table(
        cellText=celulas,
        cellColours=cores,
        rowLabels=[f"Aula {n}" for n in numeros],
        colLabels=[_ABREVIACAO_DIA[d] for d in dias],
        loc="center",
        cellLoc="center",
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(6)
    tabela.scale(1, 2.2)


def salvar_quadro_horarios(
    instancia: InstanciaProblema,
    individuo: Individuo,
    caminho_saida: str,
    turma_ids: list[int] | None = None,
    colunas: int = 2,
) -> None:
    """Renderiza o quadro turma x dia x aula do indivíduo (um sub-quadro por turma) e salva como PNG."""
    grade = montar_grade(instancia, individuo)
    ids_selecionados = turma_ids or [t.id for t in instancia.turmas]

    linhas = -(-len(ids_selecionados) // colunas)
    fig, eixos = plt.subplots(linhas, colunas, figsize=(colunas * 5, linhas * 4), squeeze=False)
    eixos_flat = eixos.flatten()

    for eixo, turma_id in zip(eixos_flat, ids_selecionados):
        turma = instancia.turma(turma_id)
        _renderizar_quadro_turma(eixo, instancia, grade[turma_id], turma)
    for eixo_sobra in eixos_flat[len(ids_selecionados):]:
        eixo_sobra.axis("off")

    diretorio = os.path.dirname(caminho_saida)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)


def plotar_convergencia(execucoes: list, caminho_saida: str, escala_log: bool = True) -> None:
    """Uma curva por escala: média do melhor fitness por geração entre as seeds daquela escala."""
    por_escala: dict[str, list[list[float]]] = {}
    for execucao in execucoes:
        por_escala.setdefault(execucao.resultado.escala, []).append(execucao.historico_melhor_fitness)

    fig, ax = plt.subplots(figsize=(8, 5))
    for nome_escala, historicos in por_escala.items():
        n_geracoes = min(len(h) for h in historicos)
        media = [statistics.mean(h[g] for h in historicos) for g in range(n_geracoes)]
        ax.plot(range(n_geracoes), media, label=nome_escala)

    ax.set_xlabel("Geração")
    ax.set_ylabel("Melhor fitness (média entre seeds)")
    if escala_log:
        ax.set_yscale("log")
    ax.set_title("Convergência do AG por escala do problema")
    ax.legend()
    ax.grid(True, alpha=0.3)

    diretorio = os.path.dirname(caminho_saida)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)
    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150)
    plt.close(fig)
