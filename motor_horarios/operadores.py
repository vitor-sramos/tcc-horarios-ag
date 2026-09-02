import random

from motor_horarios.fitness import dentro_da_janela
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


def mutar(individuo: Individuo, dominio_por_gene: list[list[int]], rng: random.Random, taxa: float = 0.02) -> Individuo:
    genes = [
        rng.choice(dominio_por_gene[i]) if rng.random() < taxa else gene
        for i, gene in enumerate(individuo.genes)
    ]
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


def reparar(
    individuo: Individuo, instancia: InstanciaProblema, rng: random.Random, tentativas: int | None = None
) -> Individuo:
    """Após crossover/mutação, tenta realocar genes em conflito de hard constraint (professor/sala/turma).

    Por padrão (`tentativas=None`) percorre o domínio inteiro do gene (embaralhado), sem repetir
    candidato — só desiste quando nenhum slot do domínio está livre. `tentativas` limita a busca a
    um número menor de candidatos, caso o custo de percorrer o domínio inteiro seja indesejado.

    Ainda assim não garante zerar todos os conflitos quando não há slot livre no domínio (conflito
    estrutural de recurso) — o que sobrar continua penalizado pela função de fitness e a pressão
    seletiva do AG cuida do resto ao longo das gerações.
    """
    componentes = _componentes_dos_genes(instancia)
    genes = list(individuo.genes)

    indices_conflito = _indices_conflituosos(genes, componentes)
    if not indices_conflito:
        return individuo

    dominio_por_gene = instancia.dominio_genes()
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
        candidatos = list(dominio_por_gene[i])
        rng.shuffle(candidatos)
        for candidato in candidatos[:tentativas]:
            if livre(i, candidato):
                escolhido = candidato
                break
        genes[i] = escolhido
        ocupar(i, escolhido)

    return Individuo(genes)


def reparar_disponibilidade(
    individuo: Individuo, instancia: InstanciaProblema, rng: random.Random, tentativas: int | None = None
) -> Individuo:
    """Depois do reparo de hard constraints, tenta mover aulas que violam a disponibilidade
    do professor para um slot dentro da janela declarada — sem criar um novo conflito.

    Por padrão (`tentativas=None`) percorre todos os candidatos compatíveis com a janela
    (embaralhados), sem repetir; `tentativas` limita a busca a um número menor, se necessário.

    Roda por último no pipeline: só mexe em slots que já não têm conflito de professor/sala/turma.
    """
    disponibilidades_por_professor: dict[int, list] = {}
    for d in instancia.disponibilidades:
        disponibilidades_por_professor.setdefault(d.professor_id, []).append(d)

    if not disponibilidades_por_professor:
        return individuo

    componentes = _componentes_dos_genes(instancia)
    genes = list(individuo.genes)
    slots_por_id = {s.id: s for s in instancia.slots_horario}
    dominio_por_gene = instancia.dominio_genes()

    ocupacao: set[tuple[str, int, int]] = set()
    for i, slot_id in enumerate(genes):
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

    def trocar(i: int, slot_antigo: int, slot_novo: int) -> None:
        c = componentes[i]
        ocupacao.discard(("prof", slot_antigo, c.professor_id))
        ocupacao.discard(("sala", slot_antigo, c.sala_id))
        ocupacao.discard(("turma", slot_antigo, c.turma_id))
        ocupacao.add(("prof", slot_novo, c.professor_id))
        ocupacao.add(("sala", slot_novo, c.sala_id))
        ocupacao.add(("turma", slot_novo, c.turma_id))
        genes[i] = slot_novo

    for i, slot_id in enumerate(genes):
        c = componentes[i]
        janelas = disponibilidades_por_professor.get(c.professor_id)
        if not janelas:
            continue
        if any(dentro_da_janela(slots_por_id[slot_id], j) for j in janelas):
            continue

        candidatos_compativeis = [
            slot_id
            for slot_id in dominio_por_gene[i]
            if any(dentro_da_janela(slots_por_id[slot_id], j) for j in janelas)
        ]
        rng.shuffle(candidatos_compativeis)
        for candidato in candidatos_compativeis[:tentativas]:
            if livre(i, candidato):
                trocar(i, slot_id, candidato)
                break

    return Individuo(genes)
