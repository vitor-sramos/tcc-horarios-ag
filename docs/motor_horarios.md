# Motor de Horários — resumo dos módulos

Resumo objetivo de cada módulo em `motor_horarios/`, para referência durante a escrita do TCC.

## `modelo.py`

Define os **moldes de dados** (dataclasses) do domínio — não insere nenhum valor real, só a forma que os dados devem ter. Valores concretos vêm de fora (gerador sintético, parser de benchmark, ou testes).

- `Turma`, `Professor`, `Disciplina`, `Sala` — entidades simples.
- `ComponenteCurricular` — o "molde" de uma aula: turma + professor + disciplina + sala + quantas vezes/semana. Tem um `__post_init__` (hook que roda logo após o `__init__` gerado pelo dataclass) que valida `aulas_por_semana > 0` — fail-fast, evita que um dado inválido gere silenciosamente 0 aulas pendentes e faça a disciplina "sumir" do problema sem erro nenhum.
- `Disponibilidade` — janela (dia + intervalo de horário) em que um professor está disponível. Soft constraint.
- `SlotHorario` — uma célula da grade semanal: dia da semana + número da aula + horário de relógio (início/fim).
- `AulaPendente` — uma ocorrência individual de um componente curricular ainda sem slot atribuído; é o que vira 1 gene do cromossomo.
- `InstanciaProblema` — o "pacote" com tudo que descreve uma instância do problema (todas as listas acima). No `__post_init__`, monta dicionários de índice por id (`_turmas_por_id`, etc. — busca O(1) em vez de percorrer listas) e expande cada `ComponenteCurricular` em N `AulaPendente` (uma por `aulas_por_semana`) — essa lista final (`aulas_pendentes()`) define o tamanho do cromossomo. `validar()` é separado do `__post_init__` de propósito: checa referências cruzadas (ex. componente apontando pra turma inexistente) e pode ser chamado a qualquer momento, inclusive depois de mutar as listas manualmente.

## `gerador_sintetico.py`

Instancia de verdade as classes de `modelo.py`, com **aleatoriedade controlada por seed** (`random.Random(seed)` próprio, não o `random` global — garante reprodutibilidade: mesma seed, mesma instância sempre).

- `_gerar_slots()` — constrói todos os slots da semana (dias × aulas por dia).
- `gerar_instancia()` — monta turmas, professores, disciplinas, salas, componentes curriculares e disponibilidades. Não é aleatoriedade solta: sala é sorteada respeitando `capacidade_restante_sala` (cada sala só comporta no máximo `n_slots` aulas/semana — sem essa checagem, o gerador podia produzir instâncias estruturalmente impossíveis de resolver, causa raiz de um platô de convergência já investigado e corrigido); disponibilidade tem probabilidade configurável (`prob_disponibilidade_restrita`, 30% por padrão) de o professor ter 1 dia indisponível na semana — **ausência de registro de `Disponibilidade` significa "sem restrição"**, não "sempre indisponível". Já a escolha do professor de cada componente é sorteio livre, sem checar carga horária — intencional: esse excesso é tratado depois pelo fitness/reparo, não pela geração.

## `individuo.py`

Define o **cromossomo** e a população inicial.

- `Individuo` — encapsula `genes: list[int]` (um `slot_id` por aula pendente, na ordem de `instancia.aulas_pendentes()`). Usa `__slots__` por otimização de memória (o AG cria muitos indivíduos ao longo das gerações).
- `gerar_individuo_aleatorio` / `gerar_populacao_inicial` — criam a população inicial 100% aleatória (nenhuma checagem de conflito ainda).
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
- `mutar` — 2% de chance por gene de virar um slot aleatório novo.

**Reparo específico do domínio** (heurística própria do problema, não operador clássico de livro-texto):
- `reparar` — detecta genes com conflito hard (professor/sala/turma) e tenta realocar só esses num slot livre (guloso, até 5 tentativas cada; não garante zerar tudo — o que sobra fica pra pressão seletiva resolver ao longo das gerações).
- `reparar_disponibilidade` — roda depois (assume hard já limpo); tenta mover aulas fora da janela de disponibilidade do professor para um slot compatível, sem criar conflito novo.

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
- Sala/professor/turma — compara a demanda de cada recurso com `n_slots` (total de slots na semana). Se demanda > slots, o excesso é conflito garantido.
- Disponibilidade — mais elaborado, pois a restrição é por professor: agrupa as janelas de cada professor, conta quantos slots da semana caem dentro da **união** de todas as suas janelas (reaproveitando `dentro_da_janela` do `fitness.py`), e compara com a demanda dele. Professor sem janela declarada nem entra no cálculo (mesma regra do gerador: ausência de restrição nunca penaliza).
- Carga horária — assume o melhor caso possível (todas as aulas do professor caindo no slot de menor duração que existe na instância) e checa se mesmo assim ele estouraria `carga_horaria_maxima_minutos`.

Esse módulo foi o que resolveu o platô de convergência investigado anteriormente: a causa raiz não era o AG estagnando, era a instância sintética gerando recursos estruturalmente sobrecarregados. Depois de corrigir o gerador e comparar contra esse piso, o AG passou a bater o piso teórico exatamente em todas as dimensões.

## Conceitos de Algoritmo Genético utilizados

Um AG resolve otimização imitando seleção natural: mantém uma **população** de soluções candidatas e, a cada **geração**, as melhores têm mais chance de "reproduzir", enquanto mutações aleatórias introduzem variação. É uma **metaheurística** — não garante o ótimo global, mas é viável onde testar todas as combinações não é (espaço de busca aqui é astronomicamente grande: centenas de aulas pendentes × dezenas de slots).

**Ciclo de uma geração** (`motor_ga.py:evoluir()`): avaliação → seleção dos pais → recombinação (crossover) → mutação → nova população substitui a antiga.

- **Seleção (`operadores.py:selecionar_torneio`)** — quanto melhor o fitness, maior a chance de virar pai, mas não pode ser só o melhor sempre (perde diversidade, prende em ótimo local). Torneio (sorteia 3, pega o melhor) calibra isso; `tamanho_torneio` controla a **pressão seletiva** — maior = converge mais rápido mas arrisca ótimo local, menor = mais exploração.
- **Crossover (`operadores.py:cruzar`)** — combina pedaços de solução boa de dois pais na esperança de um filho ainda melhor. Uniforme (cada gene vem de um pai ou outro, 50/50) faz sentido aqui porque cada gene é uma decisão praticamente independente (slot de uma aula específica).
- **Mutação (`operadores.py:mutar`, 2%/gene)** — contrapeso ao crossover: sem ela a população só recombina genes que já existiam desde a população inicial, arriscando convergência prematura pra uma solução medíocre. Taxa baixa de propósito — mutação alta demais vira busca aleatória.
- **Elitismo (`motor_ga.py`, parâmetro `elite`)** — não é AG "canônico" de livro-texto, mas é padrão na prática: copia os N melhores direto pra próxima geração, garantindo que o melhor fitness histórico nunca piora geração a geração.
- **Reparo (`operadores.py:reparar`, `reparar_disponibilidade`)** — não é conceito clássico de AG genérico; é uma heurística de domínio (hibridização com busca local), comum especificamente em *timetabling* porque conflitos hard são fáceis de detectar e corrigir localmente. Foi o que resolveu o platô de convergência do projeto.
- **Convergência** — `historico_melhor_fitness` (retornado por `evoluir()`) é a série usada para plotar fitness do melhor indivíduo × geração na fase de experimentação.

**Trade-off central dos parâmetros** (`tamanho_populacao`, `geracoes`, `taxa_mutacao`, `tamanho_torneio`, `elite`): cada um equilibra **exploração** (evitar ótimo local) vs **explotação** (refinar o que já é bom). Não há valor "certo" universal — medir esse efeito na prática, comparado ao piso teórico (`analise.py`), é parte do valor experimental do TCC.
