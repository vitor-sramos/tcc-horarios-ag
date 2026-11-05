"""Figura de exemplo para o artigo: quadro de horários de UMA turma gerado pelo AG na instância da escola fictícia.

Instância: exemplos/instancia_exemplo_escola_fundamental.json (14 turmas, 3 turnos). AG: 300 gerações, população 60, seed 0.
A cor de cada disciplina é fixa (ordem alfabética), ao contrário de `visualizacao.py`, que colore por ordem de aparição
dentro da turma. Sem título interno: a legenda fica no LaTeX.

Uso: python3 -m scripts.gerar_figura_quadro_exemplo
Saída: figuras/figura_quadro_exemplo.png e .pdf
"""

import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.motor_ga import evoluir
from motor_horarios.persistencia import carregar_instancia_de_arquivo
from motor_horarios.visualizacao import _ABREVIACAO_DIA, _eixos_da_grade, _slot_id_por_dia_e_numero, montar_grade

CAMINHO_INSTANCIA = "exemplos/instancia_exemplo_escola_fundamental.json"
SAIDA = "figuras/figura_quadro_exemplo"
NOME_TURMA = "6º Ano A"
SEED = 0


def main() -> None:
    instancia = carregar_instancia_de_arquivo(CAMINHO_INSTANCIA)
    melhor, relatorio, _historico = evoluir(instancia, geracoes=300, tamanho_populacao=60, seed=SEED)
    piso = calcular_limites_teoricos(instancia)
    print(
        f"hard: prof {relatorio.violacoes_professor}/{piso.minimo_conflitos_professor}, "
        f"sala {relatorio.violacoes_sala}/{piso.minimo_conflitos_sala}, "
        f"turma {relatorio.violacoes_turma}/{piso.minimo_conflitos_turma}, "
        f"carga {relatorio.minutos_excedentes_carga_horaria}/{piso.minimo_minutos_excedentes_carga_horaria}, "
        f"disp {relatorio.violacoes_disponibilidade}/{piso.minimo_violacoes_disponibilidade}"
    )

    turma = next(t for t in instancia.turmas if t.nome.startswith(NOME_TURMA))
    grade_turma = montar_grade(instancia, melhor)[turma.id]

    slots_do_turno = [s for s in instancia.slots_horario if s.turno == turma.turno]
    dias, numeros = _eixos_da_grade(slots_do_turno)
    slot_por_posicao = _slot_id_por_dia_e_numero(slots_do_turno)

    nomes_disciplinas = sorted({info["disciplina"] for info in grade_turma.values()})
    paleta = plt.get_cmap("Pastel1")
    cor_da_disciplina = {nome: paleta(i % paleta.N) for i, nome in enumerate(nomes_disciplinas)}

    textos, cores = [], []
    for numero in numeros:
        linha_texto, linha_cor = [], []
        for dia in dias:
            info = grade_turma.get(slot_por_posicao.get((dia, numero)))
            if info is None:
                linha_texto.append("")
                linha_cor.append("#f2f2f2")
            else:
                professor = textwrap.fill(info["professor"].removeprefix("Prof. "), 16)
                linha_texto.append(f"{info['disciplina']}\nProf. {professor}")
                linha_cor.append(cor_da_disciplina[info["disciplina"]])
        textos.append(linha_texto)
        cores.append(linha_cor)

    fig, ax = plt.subplots(figsize=(6.3, 3.05), dpi=250)
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])
    tabela = ax.table(
        cellText=textos,
        cellColours=cores,
        rowLabels=[f"Aula {n}" for n in numeros],
        colLabels=[_ABREVIACAO_DIA[d] for d in dias],
        loc="center",
        cellLoc="center",
    )
    tabela.auto_set_font_size(False)
    tabela.set_fontsize(6.2)
    tabela.scale(1, 2.7)
    fig.savefig(f"{SAIDA}.png", bbox_inches="tight", pad_inches=0.02)
    fig.savefig(f"{SAIDA}.pdf", bbox_inches="tight", pad_inches=0.02)
    print(f"Turma: {turma.nome} ({turma.turno}). Figura salva em {SAIDA}.png/.pdf")


if __name__ == "__main__":
    main()
