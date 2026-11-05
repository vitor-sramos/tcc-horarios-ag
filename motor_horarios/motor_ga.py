import random

from motor_horarios.fitness import RelatorioFitness, avaliar
from motor_horarios.individuo import Individuo, gerar_populacao_inicial
from motor_horarios.modelo import InstanciaProblema
from motor_horarios.operadores import (
    cruzar,
    mutar,
    reparar,
    reparar_disponibilidade,
    reparar_fragmentacao_disciplina,
    selecionar_torneio,
)


def evoluir(
    instancia: InstanciaProblema,
    geracoes: int = 200,
    tamanho_populacao: int = 60,
    seed: int = 0,
    taxa_mutacao: float = 0.02,
    tamanho_torneio: int = 3,
    elite: int = 2,
    registro_obrigatorias: list[float] | None = None,
) -> tuple[Individuo, RelatorioFitness, list[float]]:
    """Loop principal do AG. Retorna o melhor indivíduo, seu relatório de fitness,
    e o histórico do melhor fitness por geração (para o gráfico de convergência).

    `registro_obrigatorias`, se fornecida, recebe a cada geração o total de violações obrigatórias do melhor indivíduo
    até então (conflitos de professor, sala e turma + excesso de carga horária em horas). É só registro: não altera a busca."""
    rng = random.Random(seed)
    dominio_por_gene = instancia.dominio_genes()

    populacao = gerar_populacao_inicial(instancia, tamanho_populacao, seed)
    historico_melhor_fitness: list[float] = []
    melhor_individuo: Individuo | None = None
    melhor_relatorio: RelatorioFitness | None = None

    for _ in range(geracoes):
        relatorios = [avaliar(ind, instancia) for ind in populacao]
        fitnesses = [r.valor for r in relatorios]
        ordenados = sorted(range(len(populacao)), key=lambda i: fitnesses[i])

        if melhor_relatorio is None or relatorios[ordenados[0]].valor < melhor_relatorio.valor:
            melhor_individuo = populacao[ordenados[0]]
            melhor_relatorio = relatorios[ordenados[0]]
        historico_melhor_fitness.append(melhor_relatorio.valor)
        if registro_obrigatorias is not None:
            registro_obrigatorias.append(
                melhor_relatorio.violacoes_professor
                + melhor_relatorio.violacoes_sala
                + melhor_relatorio.violacoes_turma
                + melhor_relatorio.minutos_excedentes_carga_horaria / 60
            )

        nova_populacao = [populacao[i] for i in ordenados[:elite]]
        while len(nova_populacao) < tamanho_populacao:
            pai1 = selecionar_torneio(populacao, fitnesses, rng, tamanho_torneio)
            pai2 = selecionar_torneio(populacao, fitnesses, rng, tamanho_torneio)
            filho = cruzar(pai1, pai2, rng)
            filho = mutar(filho, dominio_por_gene, rng, taxa_mutacao)
            filho = reparar(filho, instancia, rng)
            filho = reparar_disponibilidade(filho, instancia, rng)
            filho = reparar_fragmentacao_disciplina(filho, instancia, rng)
            nova_populacao.append(filho)

        populacao = nova_populacao

    assert melhor_individuo is not None and melhor_relatorio is not None
    return melhor_individuo, melhor_relatorio, historico_melhor_fitness
