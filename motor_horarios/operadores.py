import random

from motor_horarios.individuo import Individuo
from motor_horarios.modelo import ComponenteCurricular, InstanciaProblema


def selecionar_torneio(
    populacao: list[Individuo], fitnesses: list[float], rng: random.Random, tamanho_torneio: int = 3
) -> Individuo:
    """Sorteia N indivíduos e devolve o de menor fitness (estamos minimizando)."""
    candidatos = rng.sample(range(len(populacao)), k=tamanho_torneio)
    vencedor = min(candidatos, key=lambda i: fitnesses[i])
    return populacao[vencedor]


def cruzar(pai1: Individuo, pai2: Individuo, rng: random.Random) -> Individuo:
    """Crossover uniforme: cada gene do filho vem de um dos dois pais, 50/50."""
    genes = [g1 if rng.random() < 0.5 else g2 for g1, g2 in zip(pai1.genes, pai2.genes)]
    return Individuo(genes)


def mutar(individuo: Individuo, slot_ids: list[int], rng: random.Random, taxa: float = 0.02) -> Individuo:
    genes = [rng.choice(slot_ids) if rng.random() < taxa else gene for gene in individuo.genes]
    return Individuo(genes)


def _componentes_dos_genes(instancia: InstanciaProblema) -> list[ComponenteCurricular]:
    return [instancia.componente(p.componente_id) for p in instancia.aulas_pendentes()]


def _indices_conflituosos(genes: list[int], componentes: list[ComponenteCurricular]) -> set[int]:
    conflituosos: set[int] = set()
    for atributo in ("professor_id", "sala_id", "turma_id"):
        grupos: dict[tuple[int, int], list[int]] = {}
        for i, slot_id in enumerate(genes):
            chave = (slot_id, getattr(componentes[i], atributo))
            grupos.setdefault(chave, []).append(i)
        for indices in grupos.values():
            if len(indices) > 1:
                conflituosos.update(indices)
    return conflituosos


def reparar(individuo: Individuo, instancia: InstanciaProblema, rng: random.Random, tentativas: int = 5) -> Individuo:
    """Após crossover/mutação, tenta realocar genes em conflito de hard constraint (professor/sala/turma).

    Não garante zerar todos os conflitos — é uma heurística gulosa. O que sobrar continua
    penalizado pela função de fitness e a pressão seletiva do AG cuida do resto ao longo das gerações.
    """
    componentes = _componentes_dos_genes(instancia)
    genes = list(individuo.genes)

    indices_conflito = _indices_conflituosos(genes, componentes)
    if not indices_conflito:
        return individuo

    slot_ids = [s.id for s in instancia.slots_horario]
    ocupacao: set[tuple[str, int, int]] = set()
    for i, slot_id in enumerate(genes):
        if i in indices_conflito:
            continue
        c = componentes[i]
        ocupacao.add(("prof", slot_id, c.professor_id))
        ocupacao.add(("sala", slot_id, c.sala_id))
        ocupacao.add(("turma", slot_id, c.turma_id))

    def livre(i: int, slot_id: int) -> bool:
        c = componentes[i]
        return (
            ("prof", slot_id, c.professor_id) not in ocupacao
            and ("sala", slot_id, c.sala_id) not in ocupacao
            and ("turma", slot_id, c.turma_id) not in ocupacao
        )

    def ocupar(i: int, slot_id: int) -> None:
        c = componentes[i]
        ocupacao.add(("prof", slot_id, c.professor_id))
        ocupacao.add(("sala", slot_id, c.sala_id))
        ocupacao.add(("turma", slot_id, c.turma_id))

    for i in indices_conflito:
        escolhido = genes[i]
        for _ in range(tentativas):
            candidato = rng.choice(slot_ids)
            if livre(i, candidato):
                escolhido = candidato
                break
        genes[i] = escolhido
        ocupar(i, escolhido)

    return Individuo(genes)
