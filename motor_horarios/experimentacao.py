import time as _cronometro
from dataclasses import asdict, dataclass, field

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.motor_ga import evoluir


@dataclass(frozen=True)
class ConfiguracaoEscala:
    """Um ponto de escala do problema a testar — os parâmetros de `gerar_instancia` que controlam o tamanho."""

    nome: str
    n_turmas: int
    n_professores: int
    n_disciplinas: int
    n_salas: int
    disciplinas_por_turma: int = 5
    disciplinas_por_professor: int = 3


@dataclass(frozen=True)
class ResultadoExecucao:
    """Uma linha do experimento: uma (escala, seed) — métricas finais comparadas ao piso teórico."""

    escala: str
    seed: int
    tamanho_cromossomo: int
    geracoes: int
    tamanho_populacao: int
    tempo_execucao_segundos: float
    fitness_final: float
    violacoes_professor: int
    piso_professor: int
    violacoes_sala: int
    piso_sala: int
    violacoes_turma: int
    piso_turma: int
    minutos_excedentes_carga_horaria: int
    piso_carga_horaria: int
    violacoes_disponibilidade: int
    piso_disponibilidade: int
    bateu_piso: bool


@dataclass(frozen=True)
class ExecucaoCompleta:
    """Resultado de uma execução + o histórico de convergência (gráfico), separados por não terem o mesmo formato."""

    resultado: ResultadoExecucao
    historico_melhor_fitness: list[float] = field(repr=False)


def rodar_execucao(
    escala: ConfiguracaoEscala,
    seed: int,
    geracoes: int,
    tamanho_populacao: int,
    **parametros_ga,
) -> ExecucaoCompleta:
    """Gera a instância da escala dada, roda o AG uma vez e compara o resultado ao piso teórico."""
    instancia = gerar_instancia(
        seed=seed,
        n_turmas=escala.n_turmas,
        n_professores=escala.n_professores,
        n_disciplinas=escala.n_disciplinas,
        n_salas=escala.n_salas,
        disciplinas_por_turma=escala.disciplinas_por_turma,
        disciplinas_por_professor=escala.disciplinas_por_professor,
    )
    piso = calcular_limites_teoricos(instancia)

    inicio = _cronometro.perf_counter()
    _, relatorio, historico = evoluir(
        instancia, geracoes=geracoes, tamanho_populacao=tamanho_populacao, seed=seed, **parametros_ga
    )
    tempo_execucao = _cronometro.perf_counter() - inicio

    bateu_piso = (
        relatorio.violacoes_professor == piso.minimo_conflitos_professor
        and relatorio.violacoes_sala == piso.minimo_conflitos_sala
        and relatorio.violacoes_turma == piso.minimo_conflitos_turma
        and relatorio.minutos_excedentes_carga_horaria == piso.minimo_minutos_excedentes_carga_horaria
        and relatorio.violacoes_disponibilidade == piso.minimo_violacoes_disponibilidade
    )

    resultado = ResultadoExecucao(
        escala=escala.nome,
        seed=seed,
        tamanho_cromossomo=len(instancia.aulas_pendentes()),
        geracoes=geracoes,
        tamanho_populacao=tamanho_populacao,
        tempo_execucao_segundos=tempo_execucao,
        fitness_final=relatorio.valor,
        violacoes_professor=relatorio.violacoes_professor,
        piso_professor=piso.minimo_conflitos_professor,
        violacoes_sala=relatorio.violacoes_sala,
        piso_sala=piso.minimo_conflitos_sala,
        violacoes_turma=relatorio.violacoes_turma,
        piso_turma=piso.minimo_conflitos_turma,
        minutos_excedentes_carga_horaria=relatorio.minutos_excedentes_carga_horaria,
        piso_carga_horaria=piso.minimo_minutos_excedentes_carga_horaria,
        violacoes_disponibilidade=relatorio.violacoes_disponibilidade,
        piso_disponibilidade=piso.minimo_violacoes_disponibilidade,
        bateu_piso=bateu_piso,
    )
    return ExecucaoCompleta(resultado=resultado, historico_melhor_fitness=historico)


def rodar_grade(
    escalas: list[ConfiguracaoEscala],
    seeds: list[int],
    geracoes: int,
    tamanho_populacao: int,
    **parametros_ga,
) -> list[ExecucaoCompleta]:
    """Roda uma execução para cada combinação (escala, seed) — o produto cartesiano das duas listas."""
    return [
        rodar_execucao(escala, seed, geracoes, tamanho_populacao, **parametros_ga)
        for escala in escalas
        for seed in seeds
    ]


def resultados_para_linhas(execucoes: list[ExecucaoCompleta]) -> list[dict]:
    """Uma linha (dict) por execução, no formato pronto para `pandas.DataFrame`/CSV."""
    return [asdict(e.resultado) for e in execucoes]


def convergencia_para_linhas(execucoes: list[ExecucaoCompleta]) -> list[dict]:
    """Formato longo (uma linha por geração) — a granularidade certa para plotar convergência."""
    linhas = []
    for execucao in execucoes:
        for geracao, fitness in enumerate(execucao.historico_melhor_fitness):
            linhas.append(
                {
                    "escala": execucao.resultado.escala,
                    "seed": execucao.resultado.seed,
                    "geracao": geracao,
                    "melhor_fitness": fitness,
                }
            )
    return linhas
