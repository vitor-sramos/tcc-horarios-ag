"""Gera 3 instâncias de exemplo (pequena/média/grande) prontas pra apresentação, com soft
constraints (disponibilidade) incluídas, e um relatório em Markdown de cada uma pra consulta
rápida na hora de apresentar (contagens + piso teórico).

Reaproveita as mesmas escalas documentadas em resultados_experimentacao.md (mesmos parâmetros
do harness em scripts/rodar_experimentos.py) e a mesma seed=0 -- os números de piso teórico
aqui já foram observados nas execuções reais registradas naquele documento.

Uso: python3 -m scripts.gerar_exemplos_apresentacao
"""

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.modelo import InstanciaProblema
from motor_horarios.persistencia import salvar_instancia_em_arquivo

SEED = 0

ESCALAS = [
    {
        "nome": "pequena",
        "titulo": "Escola Pequena",
        "n_turmas": 3, "n_professores": 5, "n_disciplinas": 4, "n_salas": 4,
        "disciplinas_por_professor": 3,
    },
    {
        "nome": "media",
        "titulo": "Escola Média",
        "n_turmas": 10, "n_professores": 15, "n_disciplinas": 8, "n_salas": 10,
        "disciplinas_por_professor": 6,
    },
    {
        "nome": "grande",
        "titulo": "Escola Grande",
        "n_turmas": 25, "n_professores": 35, "n_disciplinas": 12, "n_salas": 20,
        "disciplinas_por_professor": 9,
    },
]


def _contagem_por_turno(instancia: InstanciaProblema) -> dict[str, int]:
    contagem: dict[str, int] = {}
    for turma in instancia.turmas:
        contagem[turma.turno] = contagem.get(turma.turno, 0) + 1
    return contagem


def _professores_com_disponibilidade_restrita(instancia: InstanciaProblema) -> int:
    return len({d.professor_id for d in instancia.disponibilidades})


def _secao_markdown(escala: dict, instancia: InstanciaProblema) -> str:
    piso = calcular_limites_teoricos(instancia)
    turnos = _contagem_por_turno(instancia)
    turnos_str = ", ".join(f"{turno.capitalize()}: {qtd}" for turno, qtd in turnos.items())
    n_profs_restritos = _professores_com_disponibilidade_restrita(instancia)

    return f"""## {escala["titulo"]}

Arquivo: `exemplos/escola_{escala["nome"]}.json` (seed={SEED}, mesma escala e seed documentadas
em `docs/resultados_experimentacao.md`, linha `{escala["nome"]}` / seed `{SEED}`).

| Métrica | Valor |
|---|---|
| Turmas | {len(instancia.turmas)} ({turnos_str}) |
| Professores | {len(instancia.professores)} |
| Disciplinas | {len(instancia.disciplinas)} |
| Salas | {len(instancia.salas)} |
| Componentes curriculares (turma × disciplina) | {len(instancia.componentes)} |
| Aulas pendentes (tamanho do cromossomo) | {len(instancia.aulas_pendentes())} |
| Professores com disponibilidade restrita | {n_profs_restritos} de {len(instancia.professores)} |

**Piso teórico** (mínimo de violações inevitável, calculado por `calcular_limites_teoricos`):

| Dimensão | Piso |
|---|---|
| Conflitos de professor | {piso.minimo_conflitos_professor} |
| Conflitos de sala | {piso.minimo_conflitos_sala} |
| Conflitos de turma | {piso.minimo_conflitos_turma} |
| Minutos excedentes de carga horária | {piso.minimo_minutos_excedentes_carga_horaria} |
| Violações de disponibilidade | {piso.minimo_violacoes_disponibilidade} |
"""


def main() -> None:
    secoes = []
    for escala in ESCALAS:
        instancia = gerar_instancia(
            seed=SEED,
            n_turmas=escala["n_turmas"],
            n_professores=escala["n_professores"],
            n_disciplinas=escala["n_disciplinas"],
            n_salas=escala["n_salas"],
            disciplinas_por_professor=escala["disciplinas_por_professor"],
        )
        caminho_json = f"exemplos/escola_{escala['nome']}.json"
        salvar_instancia_em_arquivo(instancia, caminho_json)
        secoes.append(_secao_markdown(escala, instancia))
        print(f"{escala['titulo']}: {caminho_json} salvo "
              f"({len(instancia.turmas)} turmas, {len(instancia.aulas_pendentes())} aulas pendentes)")

    corpo = "\n".join(secoes)
    conteudo = f"""# Exemplos para apresentação: escola pequena, média e grande

Três instâncias prontas pra rodar ao vivo (`webapp/`, modo "Colar JSON") ou por script, cada
uma numa escala diferente, todas com disponibilidade de professor (soft constraint) incluída.
Gerado por `scripts/gerar_exemplos_apresentacao.py` -- não editar os JSONs à mão, rodar o script
de novo se precisar mudar algo (reprodutível pela seed).

{corpo}
"""
    with open("docs/exemplos_apresentacao.md", "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    print("\nRelatório salvo em docs/exemplos_apresentacao.md")


if __name__ == "__main__":
    main()
