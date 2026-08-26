import random

from motor_horarios.modelo import InstanciaProblema


class Individuo:
    """Um vetor de slot_id, um gene por aula pendente, na ordem de instancia.aulas_pendentes()."""

    __slots__ = ("genes",)

    def __init__(self, genes: list[int]):
        self.genes = genes

    def __len__(self) -> int:
        return len(self.genes)

    def __repr__(self) -> str:
        return f"Individuo({self.genes!r})"


def gerar_individuo_aleatorio(dominio_por_gene: list[list[int]], rng: random.Random) -> Individuo:
    return Individuo([rng.choice(dominio) for dominio in dominio_por_gene])


def gerar_populacao_inicial(instancia: InstanciaProblema, tamanho: int, seed: int) -> list[Individuo]:
    rng = random.Random(seed)
    dominio_por_gene = instancia.dominio_genes()
    return [gerar_individuo_aleatorio(dominio_por_gene, rng) for _ in range(tamanho)]


def decodificar(individuo: Individuo, instancia: InstanciaProblema) -> list[tuple[int, int]]:
    """(componente_id, slot_id) para cada gene — a grade completa que esse indivíduo representa."""
    pendentes = instancia.aulas_pendentes()
    return [(pendentes[i].componente_id, slot_id) for i, slot_id in enumerate(individuo.genes)]
