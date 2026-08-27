# Motor de Horários — resumo dos módulos

Resumo objetivo de cada módulo em `motor_horarios/`, para referência durante a escrita do TCC.

## `modelo.py`

Define os **moldes de dados** (dataclasses) do domínio — não insere nenhum valor real, só a forma que os dados devem ter. Valores concretos vêm de fora (gerador sintético, parser de benchmark, ou testes).

- `Turma`, `Disciplina`, `Sala` — entidades simples. `Turma.turno` (MATUTINO/VESPERTINO/NOTURNO) não é decorativo: restringe a quais slots aquela turma pode ser alocada (ver `dominio_genes()` abaixo).
- `Professor` — além do básico, tem `disciplinas_habilitadas: tuple[int, ...]`, as disciplinas que ele pode lecionar. Vazio = sem restrição (mesma convenção de "ausência = sem restrição" já usada em `Disponibilidade`).
- `ComponenteCurricular` — o "molde" de uma aula: turma + professor + disciplina + sala + quantas vezes/semana. Tem um `__post_init__` (hook que roda logo após o `__init__` gerado pelo dataclass) que valida `aulas_por_semana > 0` — fail-fast, evita que um dado inválido gere silenciosamente 0 aulas pendentes e faça a disciplina "sumir" do problema sem erro nenhum.
- `Disponibilidade` — janela (dia + intervalo de horário) em que um professor está disponível. Soft constraint.
- `SlotHorario` — uma célula da grade semanal: dia da semana + número da aula + horário de relógio (início/fim) + `turno` (a que período do dia esse slot pertence).
- `AulaPendente` — uma ocorrência individual de um componente curricular ainda sem slot atribuído; é o que vira 1 gene do cromossomo.
- `InstanciaProblema` — o "pacote" com tudo que descreve uma instância do problema (todas as listas acima). No `__post_init__`, monta dicionários de índice por id (`_turmas_por_id`, etc. — busca O(1) em vez de percorrer listas), expande cada `ComponenteCurricular` em N `AulaPendente` (uma por `aulas_por_semana`) — essa lista final (`aulas_pendentes()`) define o tamanho do cromossomo — e pré-computa `dominio_genes()`: para cada aula pendente, a lista de `slot_id` cujo `turno` bate com o turno da turma daquele componente. É esse domínio (não mais a lista global de slots) que o cromossomo, a mutação e o reparo usam pra sortear/realocar genes. `validar()` é separado do `__post_init__` de propósito: checa referências cruzadas (ex. componente apontando pra turma inexistente, ou turma com um turno sem nenhum `SlotHorario` correspondente) e pode ser chamado a qualquer momento, inclusive depois de mutar as listas manualmente.

## `gerador_sintetico.py`

Instancia de verdade as classes de `modelo.py`, com **aleatoriedade controlada por seed** (`random.Random(seed)` próprio, não o `random` global — garante reprodutibilidade: mesma seed, mesma instância sempre).

- `gerar_slots()` — constrói os slots de um turno (dias × aulas por dia), estampando o `turno` recebido em cada um; `gerar_instancia()` chama essa função uma vez por turno em `turnos` (default `["MATUTINO"]`) e concatena o resultado, com `slot_id` corrido entre os blocos — cada turno tem seu próprio horário de início (`INICIO_PADRAO_POR_TURNO`). É pública (não `_gerar_slots`) porque `motor_horarios/persistencia.py` também reaproveita ela pra montar slots a partir de `configuracao_grade` num JSON externo.
- `_sortear_habilitacoes()` — decide quais disciplinas cada professor pode lecionar: primeiro garante que toda disciplina tem pelo menos 1 professor habilitado (evita gerar uma instância impossível), depois completa até `disciplinas_por_professor` por professor.
- `gerar_instancia()` — monta turmas (cada uma sorteando um turno de `turnos`), professores, disciplinas, salas, componentes curriculares e disponibilidades. Não é aleatoriedade solta: sala é sorteada respeitando `capacidade_restante_sala` (cada sala só comporta no máximo `n_slots` aulas/semana no total — uma sala pode ser usada em turnos diferentes sem conflito real, só o `slot_id`, já turno-específico, decide conflito de verdade — sem essa checagem, o gerador podia produzir instâncias estruturalmente impossíveis de resolver, causa raiz de um platô de convergência já investigado e corrigido); o professor de cada componente é sorteado só entre os habilitados pra aquela disciplina (`disciplinas_habilitadas`), mas sem checar carga horária — intencional: esse excesso é tratado depois pelo fitness/reparo, não pela geração; disponibilidade tem probabilidade configurável (`prob_disponibilidade_restrita`, 30% por padrão) de o professor ter 1 dia indisponível na semana — **ausência de registro de `Disponibilidade` significa "sem restrição"**, não "sempre indisponível".

## `individuo.py`

Define o **cromossomo** e a população inicial.

- `Individuo` — encapsula `genes: list[int]` (um `slot_id` por aula pendente, na ordem de `instancia.aulas_pendentes()`). Usa `__slots__` por otimização de memória (o AG cria muitos indivíduos ao longo das gerações).
- `gerar_individuo_aleatorio` / `gerar_populacao_inicial` — criam a população inicial 100% aleatória (nenhuma checagem de conflito ainda), sorteando cada gene dentro do seu próprio domínio (`instancia.dominio_genes()` — restrito ao turno da turma daquele componente), não de uma lista única de slots pra todo mundo.
- `decodificar` — traduz o vetor cru de genes em pares `(componente_id, slot_id)` legíveis, usando a posição no vetor para descobrir a qual aula pendente cada gene pertence.

**Hierarquia da representação** (população → indivíduo → genes → gene):

```
População = [Individuo_1, Individuo_2, Individuo_3, ...]
                ↓
Individuo = UM "quadro de horários" completo = o vetor genes inteiro
                ↓
genes = [gene_0, gene_1, gene_2, ..., gene_n]
                ↓
1 gene = 1 posição do vetor = o slot escolhido pra 1 aula pendente específica
```

Um gene isolado não é "bom" ou "ruim" nem tem conflito próprio — conflito só existe comparando genes entre si, e a avaliação de qualidade (fitness) é sempre propriedade do indivíduo inteiro.

## `fitness.py`

Avalia um indivíduo, transformando violações de restrição em um único número (`valor`, a minimizar).

- `PESO_HARD = 1000` vs `PESO_SOFT = 1` — combina hard e soft constraints numa única nota, garantindo que o AG sempre priorize eliminar violações hard antes de otimizar as soft.
- `RelatorioFitness` — guarda não só o `valor` final, mas o breakdown discriminado (violações de professor, sala, turma, minutos excedentes de carga horária, violações de disponibilidade) — permite comparar campo a campo com o piso teórico de violações inevitáveis (`analise.py`).
- `_contar_conflitos` — função genérica (reaproveitada para professor/sala/turma): agrupa pares `(slot_id, recurso_id)` e conta o excedente de cada grupo repetido (`c - 1`, não `c`).
- `avaliar()` — decodifica o indivíduo (reaproveitando `individuo.decodificar`), acumula os pares de conflito, soma minutos por professor, e checa disponibilidade — só penaliza quando o professor **tem** janela declarada e o slot cai fora dela (ausência de janela nunca penaliza).

## `operadores.py`

Como uma geração vira a próxima. Duas categorias:

**Operadores clássicos de AG:**
- `selecionar_torneio` — sorteia 3 indivíduos, retorna o de menor fitness.
- `cruzar` — crossover uniforme: cada gene do filho vem de um dos dois pais, 50/50.
- `mutar` — 2% de chance por gene de virar um slot aleatório novo, sorteado dentro do domínio daquele gene (mesma restrição de turno de `dominio_genes()`).

**Reparo específico do domínio** (heurística própria do problema, não operador clássico de livro-texto):
- `reparar` — detecta genes com conflito hard (professor/sala/turma) e tenta realocar só esses num slot livre dentro do domínio do gene (guloso, até 5 tentativas cada; não garante zerar tudo — o que sobra fica pra pressão seletiva resolver ao longo das gerações).
- `reparar_disponibilidade` — roda depois (assume hard já limpo); tenta mover aulas fora da janela de disponibilidade do professor para um slot compatível (interseção entre a janela e o domínio do gene), sem criar conflito novo.

Essa correção ativa depois de cada crossover/mutação foi o que permitiu ao AG bater o piso teórico de violações, em vez de depender só da seleção natural ao longo de muitas gerações.

## `motor_ga.py`

O loop principal (`evoluir()`), que orquestra todos os módulos acima.

- Parâmetros (`geracoes`, `tamanho_populacao`, `seed`, `taxa_mutacao`, `tamanho_torneio`, `elite`) são os "botões" a variar na fase de experimentação.
- Retorna: melhor indivíduo encontrado em qualquer geração (não só a última), seu relatório de fitness, e o histórico do melhor fitness por geração (para o gráfico de convergência).
- A cada geração: avalia toda a população (`fitness.avaliar`), ordena por fitness, atualiza o melhor de todos os tempos, e monta a próxima geração — copiando os `elite` melhores sem alteração (elitismo, evita perder progresso por azar) e preenchendo o resto via seleção por torneio → crossover → mutação → reparo hard → reparo de disponibilidade, um filho de cada vez.

## `analise.py`

Calcula o **piso teórico de violações inevitáveis** de uma instância — o número mínimo de conflitos que nenhum algoritmo, por melhor que seja, consegue evitar, porque a própria instância sobrecarrega um recurso (mais demanda do que capacidade existe). É a métrica objetiva usada para julgar se um resultado do AG é bom: nunca comparar contra zero, sempre contra esse piso.

- `LimitesTeoricos` — dataclass de resultado, com um `minimo_*` (total) e um `detalhes_*` (dicionário `{id_do_recurso: excesso}`) para cada uma das 5 dimensões que o `fitness.py` penaliza: sala, professor, turma, disponibilidade, carga horária.
- `_demanda_por` — função auxiliar genérica: soma `aulas_por_semana` de todos os `ComponenteCurricular`, agrupado por um atributo (`sala_id`, `professor_id` ou `turma_id`). Resultado: quantas aulas/semana cada recurso precisa atender, antes de qualquer alocação existir.
- Sala/professor — comparam a demanda de cada recurso com `n_slots` (total de slots na semana, somando todos os turnos): podem, em tese, ser usados em qualquer turno. Turma — compara com o total de slots **só do turno daquela turma** (`n_slots_por_turno`), já que uma turma está presa ao seu próprio turno; usar o total global aqui subestimaria o piso assim que a instância tem mais de um turno. Em qualquer um dos três, se demanda > capacidade, o excesso é conflito garantido.
- Disponibilidade — mais elaborado, pois a restrição é por professor: agrupa as janelas de cada professor, conta quantos slots da semana caem dentro da **união** de todas as suas janelas (reaproveitando `dentro_da_janela` do `fitness.py`), e compara com a demanda dele. Professor sem janela declarada nem entra no cálculo (mesma regra do gerador: ausência de restrição nunca penaliza). **Caso especial** (achado analisando resultados do harness, não óbvio de início): se a demanda do professor já ultrapassa o **total** de slots da semana, o conflito de professor (empilhamento) é inevitável de qualquer jeito — e esse empilhamento pode ser direcionado pra cima de slots já compatíveis, sem gerar violação de disponibilidade extra por causa disso. Nesse caso o piso é só `n_slots - slots_compatíveis` (quantos slots incompatíveis sobram, usados 1x cada), não `demanda - compatíveis` — a fórmula ingênua superestima o piso e chega a quebrar a invariante "nenhuma solução do AG fica abaixo do piso".
- Carga horária — assume o melhor caso possível (todas as aulas do professor caindo no slot de menor duração que existe na instância) e checa se mesmo assim ele estouraria `carga_horaria_maxima_minutos`.

Esse módulo foi o que resolveu o platô de convergência investigado anteriormente: a causa raiz não era o AG estagnando, era a instância sintética gerando recursos estruturalmente sobrecarregados. Depois de corrigir o gerador e comparar contra esse piso, o AG passou a bater o piso teórico exatamente em todas as dimensões.

## `experimentacao.py`

Harness de experimentação: roda o AG numa **grade** (produto cartesiano) de escalas do problema × seeds, e empacota os resultados no formato certo para análise/gráfico — não faz I/O (CSV/PNG) sozinho, isso fica nos scripts que o chamam.

- `ConfiguracaoEscala` — um ponto de escala a testar (quantas turmas/professores/disciplinas/salas, `disciplinas_por_turma`, `disciplinas_por_professor`), sem os detalhes de disponibilidade/carga horária (esses continuam vindo dos defaults de `gerar_instancia`). `disciplinas_por_professor` é parametrizado por escala de propósito: se ficasse fixo enquanto `n_disciplinas` cresce entre escalas, a cobertura relativa de qualificação por professor encolheria escondida junto com o tamanho do cromossomo, confundindo dois efeitos diferentes no experimento — `scripts/rodar_experimentos.py` mantém a mesma cobertura proporcional (~75%) em todas as escalas por isso.
- `rodar_execucao()` — gera a instância da escala+seed, roda `evoluir()`, cronometra (`time.perf_counter`, só para medir performance — não afeta reprodutibilidade, que continua 100% controlada pela seed), e já compara o relatório final ao piso teórico (`analise.calcular_limites_teoricos`) campo a campo, incluindo um booleano agregado `bateu_piso`.
- `rodar_grade()` — roda `rodar_execucao` para cada combinação (escala, seed); é o produto cartesiano das duas listas, não um zip.
- `resultados_para_linhas()` / `convergencia_para_linhas()` — dois formatos de saída, propositalmente separados: um linha-por-execução (métricas finais, pronto pra `pandas.DataFrame`/CSV "resumo") e outro linha-por-geração ("formato longo", a granularidade certa para plotar convergência com uma linha por escala, agregando entre seeds).

Ver `plotar_convergencia()` em `visualizacao.py` (uma curva por escala, média do melhor fitness por geração entre as seeds daquela escala, escala log no eixo Y) e `scripts/rodar_experimentos.py` (grade concreta de escalas/seeds usada, e onde os CSVs/PNG são salvos em `resultados/`).

## Fundamentação teórica

A teoria de Algoritmo Genético por trás desses módulos (população/geração, seleção, crossover, mutação, elitismo, convergência) está documentada separadamente em [`conceitos_algoritmo_genetico.md`](./conceitos_algoritmo_genetico.md).
