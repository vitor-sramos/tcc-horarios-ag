import random

from motor_horarios.fitness import dentro_da_janela
from motor_horarios.individuo import Individuo
from motor_horarios.modelo import ComponenteCurricular, DiaSemana, InstanciaProblema


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


def reparar_fragmentacao_disciplina(
    individuo: Individuo, instancia: InstanciaProblema, rng: random.Random
) -> Individuo:
    """Depois dos outros reparos, tenta reagrupar (geminar) aulas da mesma disciplina que
    ficaram fragmentadas no mesmo dia de uma turma (ex: aula 1 e aula 4 de Física, com outra
    disciplina no meio) -- trocando de posição com quem ocupa o "buraco" no meio.

    A troca nunca sai da turma nem do dia (turma, turno e carga horária dos professores
    envolvidos não mudam), e só é aplicada se não criar um novo conflito de professor/sala
    nem piorar a disponibilidade de nenhum dos dois lados da troca. Não garante zerar toda
    fragmentação (às vezes não existe troca seguindo essas regras) -- o resto continua por
    conta da pressão seletiva do AG, igual já era antes desse reparo existir.
    """
    componentes = _componentes_dos_genes(instancia)
    genes = list(individuo.genes)
    slots_por_id = {s.id: s for s in instancia.slots_horario}
    slot_por_dia_periodo_turno = {
        (s.dia_semana, s.numero_aula, s.turno): s.id for s in instancia.slots_horario
    }

    disponibilidades_por_professor: dict[int, list] = {}
    for d in instancia.disponibilidades:
        disponibilidades_por_professor.setdefault(d.professor_id, []).append(d)

    def compativel(i: int, slot_id: int) -> bool:
        janelas = disponibilidades_por_professor.get(componentes[i].professor_id)
        return not janelas or any(dentro_da_janela(slots_por_id[slot_id], j) for j in janelas)

    ocupacao: set[tuple[str, int, int]] = set()
    for i, slot_id in enumerate(genes):
        c = componentes[i]
        ocupacao.add(("prof", slot_id, c.professor_id))
        ocupacao.add(("sala", slot_id, c.sala_id))

    def piora_disponibilidade(i: int, slot_antigo: int, slot_novo: int) -> bool:
        return compativel(i, slot_antigo) and not compativel(i, slot_novo)

    def livre_para(i: int, slot_id: int, ignorar: set[tuple[str, int, int]]) -> bool:
        c = componentes[i]
        chave_prof = ("prof", slot_id, c.professor_id)
        chave_sala = ("sala", slot_id, c.sala_id)
        return (chave_prof not in ocupacao or chave_prof in ignorar) and (
            chave_sala not in ocupacao or chave_sala in ignorar
        )

    def mover_seria_seguro(i: int, slot_novo: int) -> bool:
        slot_antigo = genes[i]
        c = componentes[i]
        ignorar = {("prof", slot_antigo, c.professor_id), ("sala", slot_antigo, c.sala_id)}
        return livre_para(i, slot_novo, ignorar) and not piora_disponibilidade(i, slot_antigo, slot_novo)

    def aplicar_movimento(i: int, slot_novo: int) -> None:
        slot_antigo = genes[i]
        c = componentes[i]
        ocupacao.discard(("prof", slot_antigo, c.professor_id))
        ocupacao.discard(("sala", slot_antigo, c.sala_id))
        genes[i] = slot_novo
        ocupacao.add(("prof", slot_novo, c.professor_id))
        ocupacao.add(("sala", slot_novo, c.sala_id))

    def troca_seria_segura(i: int, j: int, slot_i: int, slot_j: int) -> bool:
        ci, cj = componentes[i], componentes[j]
        antigas = {
            ("prof", slot_i, ci.professor_id), ("sala", slot_i, ci.sala_id),
            ("prof", slot_j, cj.professor_id), ("sala", slot_j, cj.sala_id),
        }
        if not livre_para(i, slot_j, antigas) or not livre_para(j, slot_i, antigas):
            return False
        if piora_disponibilidade(i, slot_i, slot_j) or piora_disponibilidade(j, slot_j, slot_i):
            return False
        return True

    def aplicar_troca(i: int, j: int) -> None:
        slot_i, slot_j = genes[i], genes[j]
        ci, cj = componentes[i], componentes[j]
        ocupacao.discard(("prof", slot_i, ci.professor_id))
        ocupacao.discard(("sala", slot_i, ci.sala_id))
        ocupacao.discard(("prof", slot_j, cj.professor_id))
        ocupacao.discard(("sala", slot_j, cj.sala_id))
        genes[i], genes[j] = genes[j], genes[i]
        ocupacao.add(("prof", slot_j, ci.professor_id))
        ocupacao.add(("sala", slot_j, ci.sala_id))
        ocupacao.add(("prof", slot_i, cj.professor_id))
        ocupacao.add(("sala", slot_i, cj.sala_id))

    grupos_turma_dia: dict[tuple[int, DiaSemana], list[int]] = {}
    for i, slot_id in enumerate(genes):
        chave = (componentes[i].turma_id, slots_por_id[slot_id].dia_semana)
        grupos_turma_dia.setdefault(chave, []).append(i)

    for indices_do_dia in grupos_turma_dia.values():
        posicao_por_indice = {i: slots_por_id[genes[i]].numero_aula for i in indices_do_dia}
        indice_por_posicao = {p: i for i, p in posicao_por_indice.items()}
        if len(indice_por_posicao) != len(indices_do_dia):
            # ainda ha conflito de turma nao resolvido nesse dia (2 genes na mesma posicao) --
            # estado transitorio esperado entre geracoes; reparar() cuida disso, nao aqui.
            continue
        turno_do_dia = slots_por_id[genes[indices_do_dia[0]]].turno
        dia_da_semana = slots_por_id[genes[indices_do_dia[0]]].dia_semana

        por_disciplina: dict[int, list[int]] = {}
        for i in indices_do_dia:
            por_disciplina.setdefault(componentes[i].disciplina_id, []).append(i)

        for indices_disciplina in por_disciplina.values():
            if len(indices_disciplina) < 2:
                continue
            posicoes = sorted(posicao_por_indice[i] for i in indices_disciplina)
            alvo = list(range(posicoes[0], posicoes[0] + len(posicoes)))
            origem = [p for p in posicoes if p not in alvo]
            destino = [p for p in alvo if p not in posicoes]
            rng.shuffle(destino)
            for p_origem, p_destino in zip(origem, destino):
                i = indice_por_posicao[p_origem]
                slot_destino = slot_por_dia_periodo_turno.get((dia_da_semana, p_destino, turno_do_dia))
                if slot_destino is None:
                    continue  # esse turno nao tem esse numero de aula (grade nao uniforme)

                if p_destino in indice_por_posicao:
                    j = indice_por_posicao[p_destino]
                    slot_i, slot_j = genes[i], genes[j]
                    if troca_seria_segura(i, j, slot_i, slot_j):
                        aplicar_troca(i, j)
                        indice_por_posicao[p_origem], indice_por_posicao[p_destino] = j, i
                        posicao_por_indice[i], posicao_por_indice[j] = p_destino, p_origem
                else:
                    # ninguem ocupa esse horario pra essa turma nesse dia -- so mover, sem troca
                    if mover_seria_seguro(i, slot_destino):
                        aplicar_movimento(i, slot_destino)
                        del indice_por_posicao[p_origem]
                        indice_por_posicao[p_destino] = i
                        posicao_por_indice[i] = p_destino

    return Individuo(genes)
