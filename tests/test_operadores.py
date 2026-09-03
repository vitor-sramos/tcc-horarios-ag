import random
from datetime import time

from motor_horarios.fitness import avaliar
from motor_horarios.individuo import Individuo
from motor_horarios.modelo import (
    ComponenteCurricular,
    DiaSemana,
    Disciplina,
    Disponibilidade,
    InstanciaProblema,
    Professor,
    Sala,
    SlotHorario,
    Turma,
)
from motor_horarios.operadores import mutar, reparar, reparar_disponibilidade, reparar_fragmentacao_disciplina


def _instancia_com_folga() -> InstanciaProblema:
    """3 turmas, 1 professor unico, slots suficientes para acomodar todo mundo sem conflito."""
    turmas = [Turma(i, f"Turma {i}", "MATUTINO") for i in range(1, 4)]
    professores = [Professor(1, "Prof", 100_000)]
    disciplinas = [Disciplina(1, "Disc")]
    salas = [Sala(i, f"Sala {i}") for i in range(1, 4)]
    componentes = [
        ComponenteCurricular(i, turma_id=i, professor_id=1, disciplina_id=1, sala_id=i, aulas_por_semana=1)
        for i in range(1, 4)
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 6)
    ]
    return InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )


def test_reparar_nao_piora_hard_constraints():
    instancia = _instancia_com_folga()
    rng = random.Random(0)
    # forca todo mundo no mesmo slot -> 2 conflitos de professor/sala/turma
    individuo = Individuo([1, 1, 1])
    antes = avaliar(individuo, instancia)
    reparado = reparar(individuo, instancia, rng, tentativas=10)
    depois = avaliar(reparado, instancia)
    assert depois.violacoes_professor <= antes.violacoes_professor
    assert depois.violacoes_sala <= antes.violacoes_sala
    assert depois.violacoes_turma <= antes.violacoes_turma


def test_reparar_zera_conflitos_quando_ha_folga_suficiente():
    instancia = _instancia_com_folga()
    rng = random.Random(0)
    individuo = Individuo([1, 1, 1])
    reparado = reparar(individuo, instancia, rng, tentativas=20)
    relatorio = avaliar(reparado, instancia)
    assert relatorio.violacoes_professor == 0
    assert relatorio.violacoes_sala == 0
    assert relatorio.violacoes_turma == 0


def test_reparar_disponibilidade_move_aula_para_janela_valida_sem_novo_conflito():
    instancia = _instancia_com_folga()
    # slots (ver _instancia_com_folga): 1=08:00 2=09:00 3=10:00 4=11:00 5=12:00
    # janela 09:00-12:00 cobre os slots 2, 3 e 4 -- espaco de sobra pra mover o slot 1 (fora da janela)
    instancia.disponibilidades.append(
        Disponibilidade(id=1, professor_id=1, dia_semana=DiaSemana.SEGUNDA, hora_inicio=time(9, 0), hora_fim=time(12, 0))
    )
    rng = random.Random(0)
    individuo = Individuo([1, 2, 3])  # componente 1 esta no slot 1, fora da janela
    antes = avaliar(individuo, instancia)
    assert antes.violacoes_disponibilidade == 1

    reparado = reparar_disponibilidade(individuo, instancia, rng, tentativas=10)
    depois = avaliar(reparado, instancia)
    assert depois.violacoes_disponibilidade == 0
    assert depois.violacoes_professor == 0
    assert depois.violacoes_sala == 0
    assert depois.violacoes_turma == 0


def _instancia_dominio_quase_lotado() -> InstanciaProblema:
    """10 componentes ocupam 10 dos 11 slots do dominio; so o slot 11 fica livre.

    Regressao do achado de 2026-09-02: com poucas tentativas (comportamento antigo, capado
    e com reposicao), o reparo tinha boa chance de nao experimentar o unico slot livre restante
    num dominio grande. Sem cap (tentativas=None, o padrao atual), o reparo percorre o dominio
    inteiro embaralhado e sempre acha o slot livre, se ele existir.
    """
    n = 10
    turmas = [Turma(1, "T1", "MATUTINO")]
    professores = [Professor(i, f"P{i}", 100_000) for i in range(1, n + 2)]
    disciplinas = [Disciplina(1, "D")]
    salas = [Sala(1, "S1")]
    componentes = [
        ComponenteCurricular(i, turma_id=1, professor_id=i, disciplina_id=1, sala_id=1, aulas_por_semana=1)
        for i in range(1, n + 1)
    ]
    # componente extra forcado no slot 1 (mesma sala/turma do componente 1) -> conflito de sala/turma
    componentes.append(
        ComponenteCurricular(n + 1, turma_id=1, professor_id=n + 1, disciplina_id=1, sala_id=1, aulas_por_semana=1)
    )
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, n + 2)
    ]
    return InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )


def test_reparar_sem_cap_de_tentativas_acha_unico_slot_livre_em_dominio_grande():
    instancia = _instancia_dominio_quase_lotado()
    genes = list(range(1, 11)) + [1]  # componente 11 forcado no slot 1, ja ocupado
    individuo = Individuo(genes)

    capado = reparar(individuo, instancia, random.Random(0), tentativas=1)
    assert avaliar(capado, instancia).violacoes_sala > 0  # 1 tentativa nao acha o unico slot livre

    sem_cap = reparar(individuo, instancia, random.Random(0), tentativas=None)
    relatorio = avaliar(sem_cap, instancia)
    assert relatorio.violacoes_sala == 0
    assert relatorio.violacoes_turma == 0


def test_mutar_reproducivel_com_mesma_seed():
    dominio_por_gene = [[1, 2, 3, 4, 5]] * 5
    individuo = Individuo([1, 1, 1, 1, 1])
    a = mutar(individuo, dominio_por_gene, random.Random(7), taxa=0.5)
    b = mutar(individuo, dominio_por_gene, random.Random(7), taxa=0.5)
    assert a.genes == b.genes


def test_reparar_fragmentacao_geminam_aulas_da_mesma_disciplina():
    """Turma 1, segunda-feira, 4 aulas: A(disc.10) na 1 e na 4, B(disc.20) na 2, C(disc.30) na 3.
    A troca segura (ninguem mais usa os professores/salas envolvidos) deve mover A pra 1-2."""
    turmas = [Turma(1, "T1", "MATUTINO")]
    professores = [Professor(1, "Prof A", 100_000), Professor(2, "Prof B", 100_000), Professor(3, "Prof C", 100_000)]
    disciplinas = [Disciplina(10, "A"), Disciplina(20, "B"), Disciplina(30, "C")]
    salas = [Sala(1, "Sala A"), Sala(2, "Sala B"), Sala(3, "Sala C")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=10, sala_id=1, aulas_por_semana=2),
        ComponenteCurricular(2, turma_id=1, professor_id=2, disciplina_id=20, sala_id=2, aulas_por_semana=1),
        ComponenteCurricular(3, turma_id=1, professor_id=3, disciplina_id=30, sala_id=3, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 5)
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    # aulas_pendentes(): [A-occ0, A-occ1, B-occ0, C-occ0] -> genes: A na 1 e na 4, B na 2, C na 3
    individuo = Individuo([1, 4, 2, 3])
    antes = avaliar(individuo, instancia)
    assert antes.fragmentacao_disciplina == 2  # buraco de tamanho 2 (posicoes 2 e 3) pra disciplina A

    reparado = reparar_fragmentacao_disciplina(individuo, instancia, random.Random(0))
    depois = avaliar(reparado, instancia)
    assert depois.fragmentacao_disciplina == 0
    assert depois.violacoes_professor == 0
    assert depois.violacoes_sala == 0
    assert depois.violacoes_turma == 0
    assert sorted(reparado.genes[:2]) == [1, 2]  # A concentrada nas aulas 1 e 2


def test_reparar_fragmentacao_nao_troca_se_criar_conflito_de_professor():
    """Mesmo cenario do teste anterior, mas o professor de A tambem da aula (em outra turma)
    exatamente no horario que seria o destino da troca -- a troca deve ser recusada."""
    turmas = [Turma(1, "T1", "MATUTINO"), Turma(2, "T2", "MATUTINO")]
    professores = [Professor(1, "Prof A", 100_000), Professor(2, "Prof B", 100_000), Professor(3, "Prof C", 100_000)]
    disciplinas = [Disciplina(10, "A"), Disciplina(20, "B"), Disciplina(30, "C"), Disciplina(40, "D")]
    salas = [Sala(1, "Sala A"), Sala(2, "Sala B"), Sala(3, "Sala C"), Sala(4, "Sala D")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=10, sala_id=1, aulas_por_semana=2),
        ComponenteCurricular(2, turma_id=1, professor_id=2, disciplina_id=20, sala_id=2, aulas_por_semana=1),
        ComponenteCurricular(3, turma_id=1, professor_id=3, disciplina_id=30, sala_id=3, aulas_por_semana=1),
        # mesmo professor de A (id=1), turma diferente, ocupando o horario 2 -- bloqueia a troca
        ComponenteCurricular(4, turma_id=2, professor_id=1, disciplina_id=40, sala_id=4, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 5)
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    # aulas_pendentes(): [A-occ0, A-occ1, B-occ0, C-occ0, D-occ0]
    individuo = Individuo([1, 4, 2, 3, 2])
    antes = avaliar(individuo, instancia)
    assert antes.violacoes_professor == 0

    reparado = reparar_fragmentacao_disciplina(individuo, instancia, random.Random(0))
    depois = avaliar(reparado, instancia)
    assert depois.violacoes_professor == 0  # nao pode ter piorado
    assert reparado.genes == individuo.genes  # troca recusada, nada mudou


def test_reparar_fragmentacao_nao_troca_se_piorar_disponibilidade():
    """Slots: 1=08:00 2=09:00 3=10:00 4=11:00. Professor de A so pode dar aula 10:30-12:00
    (cobre so o slot 4). A ocupa as posicoes 1 e 4 (fragmentado); a geminacao tentaria mover
    a ocorrencia da posicao 4 (dentro da janela) pra posicao 2 (fora da janela) -- deve recusar."""
    turmas = [Turma(1, "T1", "MATUTINO")]
    professores = [Professor(1, "Prof A", 100_000), Professor(2, "Prof B", 100_000), Professor(3, "Prof C", 100_000)]
    disciplinas = [Disciplina(10, "A"), Disciplina(20, "B"), Disciplina(30, "C")]
    salas = [Sala(1, "Sala A"), Sala(2, "Sala B"), Sala(3, "Sala C")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=10, sala_id=1, aulas_por_semana=2),
        ComponenteCurricular(2, turma_id=1, professor_id=2, disciplina_id=20, sala_id=2, aulas_por_semana=1),
        ComponenteCurricular(3, turma_id=1, professor_id=3, disciplina_id=30, sala_id=3, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 5)
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
        disponibilidades=[
            Disponibilidade(id=1, professor_id=1, dia_semana=DiaSemana.SEGUNDA, hora_inicio=time(10, 30), hora_fim=time(12, 0))
        ],
    )
    # aulas_pendentes(): [A-occ0, A-occ1, B-occ0, C-occ0] -- A na 1 e na 4, B na 2, C na 3.
    individuo = Individuo([1, 4, 2, 3])
    antes = avaliar(individuo, instancia)
    assert antes.fragmentacao_disciplina == 2
    # posicao 1 (08:00) ja viola a janela (fora do escopo desse reparo); posicao 4 (11:00) nao viola.

    reparado = reparar_fragmentacao_disciplina(individuo, instancia, random.Random(0))
    depois = avaliar(reparado, instancia)
    assert depois.violacoes_disponibilidade == antes.violacoes_disponibilidade  # nao pode ter piorado
    assert reparado.genes == individuo.genes  # unica troca possivel tiraria A da janela -> recusada


def test_reparar_fragmentacao_move_para_horario_vago_sem_swap():
    """Turma sem grade cheia: aulas 2 e 4 vagas nesse dia (so A na 1 e na 5, B na 3). O alvo da
    geminacao de A e' 1-2; como a posicao 2 nao tem ninguem, deve so MOVER (nao precisa de swap)."""
    turmas = [Turma(1, "T1", "MATUTINO")]
    professores = [Professor(1, "Prof A", 100_000), Professor(2, "Prof B", 100_000)]
    disciplinas = [Disciplina(10, "A"), Disciplina(20, "B")]
    salas = [Sala(1, "Sala A"), Sala(2, "Sala B")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=10, sala_id=1, aulas_por_semana=2),
        ComponenteCurricular(2, turma_id=1, professor_id=2, disciplina_id=20, sala_id=2, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 6)
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    # aulas_pendentes(): [A-occ0, A-occ1, B-occ0] -- A na 1 e na 5, B na 3; aulas 2 e 4 vagas.
    individuo = Individuo([1, 5, 3])
    antes = avaliar(individuo, instancia)
    assert antes.fragmentacao_disciplina == 3  # buracos nas aulas 2, 3 e 4

    reparado = reparar_fragmentacao_disciplina(individuo, instancia, random.Random(0))
    depois = avaliar(reparado, instancia)
    # fragmentacao e' por disciplina: A concentrada em 1-2 zera o buraco dela; B sozinha na 3
    # nunca conta (a metrica so penaliza os buracos dentro das ocorrencias da MESMA disciplina).
    assert depois.fragmentacao_disciplina == 0
    assert depois.violacoes_professor == 0
    assert depois.violacoes_sala == 0
    assert sorted(reparado.genes[:2]) == [1, 2]  # a ocorrencia da aula 5 moveu pra aula 2 (vaga)


def test_reparar_fragmentacao_nao_quebra_com_conflito_de_turma_nao_resolvido():
    """Regressao: reparar() e' heuristica e pode deixar um conflito de turma sem resolver (2
    genes da mesma turma na mesma posicao) -- estado transitorio normal entre geracoes.
    reparar_fragmentacao_disciplina precisa so pular esse dia, nunca quebrar com KeyError."""
    turmas = [Turma(1, "T1", "MATUTINO")]
    professores = [Professor(1, "Prof A", 100_000), Professor(2, "Prof B", 100_000)]
    disciplinas = [Disciplina(10, "A"), Disciplina(20, "B")]
    salas = [Sala(1, "Sala A"), Sala(2, "Sala B")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=10, sala_id=1, aulas_por_semana=1),
        ComponenteCurricular(2, turma_id=1, professor_id=2, disciplina_id=20, sala_id=2, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(i, DiaSemana.SEGUNDA, i, time(7 + i, 0), time(7 + i, 50), "MATUTINO") for i in range(1, 3)
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    # Os dois genes (turma 1, mesmo dia) forcados na MESMA posicao -- conflito de turma de proposito.
    individuo = Individuo([1, 1])

    reparado = reparar_fragmentacao_disciplina(individuo, instancia, random.Random(0))
    assert reparado.genes == individuo.genes  # dia com conflito de turma e' pulado, nada muda


def test_mutar_e_reparar_nunca_saem_do_turno_da_turma():
    """Instancia multi-turno: cada componente esta preso ao turno da sua turma (ver InstanciaProblema.dominio_genes)."""
    turmas = [Turma(1, "Matutina", "MATUTINO"), Turma(2, "Vespertina", "VESPERTINO")]
    professores = [Professor(1, "Prof", 100_000)]
    disciplinas = [Disciplina(1, "Disc")]
    salas = [Sala(1, "Sala 1")]
    componentes = [
        ComponenteCurricular(1, turma_id=1, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1),
        ComponenteCurricular(2, turma_id=2, professor_id=1, disciplina_id=1, sala_id=1, aulas_por_semana=1),
    ]
    slots = [
        SlotHorario(1, DiaSemana.SEGUNDA, 1, time(7, 0), time(7, 50), "MATUTINO"),
        SlotHorario(2, DiaSemana.SEGUNDA, 2, time(7, 50), time(8, 40), "MATUTINO"),
        SlotHorario(3, DiaSemana.SEGUNDA, 1, time(13, 0), time(13, 50), "VESPERTINO"),
        SlotHorario(4, DiaSemana.SEGUNDA, 2, time(13, 50), time(14, 40), "VESPERTINO"),
    ]
    instancia = InstanciaProblema(
        turmas=turmas, professores=professores, disciplinas=disciplinas, salas=salas,
        componentes=componentes, slots_horario=slots,
    )
    dominio_por_gene = instancia.dominio_genes()
    rng = random.Random(0)

    for _ in range(50):
        individuo = Individuo([rng.choice([1, 2, 3, 4]) for _ in range(2)])
        mutado = mutar(individuo, dominio_por_gene, rng, taxa=1.0)
        reparado = reparar(mutado, instancia, rng, tentativas=10)
        assert reparado.genes[0] in {1, 2}  # componente 1 (matutina) so pode usar slots 1/2
        assert reparado.genes[1] in {3, 4}  # componente 2 (vespertina) so pode usar slots 3/4
