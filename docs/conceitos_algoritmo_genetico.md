# Conceitos de Algoritmo Genético utilizados

Fundamentação teórica dos conceitos de AG usados no motor, amarrada aos trechos de código onde cada um aparece (ver resumo dos módulos em [`motor_horarios.md`](./motor_horarios.md)).

Um AG resolve otimização imitando seleção natural: mantém uma **população** de soluções candidatas e, a cada **geração**, as melhores têm mais chance de "reproduzir", enquanto mutações aleatórias introduzem variação. É uma **metaheurística** — não garante o ótimo global, mas é viável onde testar todas as combinações não é (espaço de busca aqui é astronomicamente grande: centenas de aulas pendentes × dezenas de slots).

## Instância vs. indivíduo: o que é fixo, o que varia

Ponto que costuma confundir: o AG **não gera várias instâncias do problema** — existe uma só (`InstanciaProblema`, vinda de `gerar_instancia()` ou de `carregar_instancia_de_json()`, tanto faz) e ela nunca muda durante a execução. O que existe em várias cópias são **indivíduos**, ou seja, tentativas de *solução* pra essa mesma instância fixa.

- **`InstanciaProblema.aulas_pendentes()`** — cada `ComponenteCurricular` (turma+disciplina+professor+sala já decididos, vindos do seu cadastro ou do JSON) é expandido em `aulas_por_semana` "aulas pendentes" (`modelo.py`). Essa lista é fixa e define o **tamanho do cromossomo**: se você tem componentes com 4+3+2 aulas/semana, são 9 aulas pendentes, logo todo indivíduo tem 9 genes — sempre as mesmas 9 aulas, na mesma ordem.
- **`Individuo`** (`individuo.py`) é só uma lista de `slot_id`, um por aula pendente — isto é, "essa aula acontece nesse horário". Não é uma instância nova, é uma resposta candidata pra instância que já existe.
- **`gerar_populacao_inicial(instancia, tamanho, seed)`** consulta a instância fixa uma vez (quantas aulas pendentes existem, qual o domínio de slots permitido pra cada uma — já filtrado pelo turno) e, a partir daí, sorteia `tamanho` (ex: 60) indivíduos independentes: pra cada aula pendente, cada indivíduo recebe um slot aleatório dentro do domínio dela. Como o sorteio é independente por indivíduo, as 60 combinações resultantes são diferentes entre si e quase certamente cheias de conflito — isso é esperado, é o ponto de partida que a seleção + crossover + mutação + reparo vão melhorar geração após geração.
- **Analogia:** um quebra-cabeça fixo (as mesmas peças sempre) com 60 tentativas diferentes e aleatórias de montagem. O quebra-cabeça não muda — só as tentativas.
- Esse mecanismo é **idêntico** independente de a instância ter vindo de `gerar_instancia()` (dados sintéticos) ou de `carregar_instancia_de_json()` (dados reais colados na tela) — a única diferença entre os dois modos é *como a instância nasceu*, nunca como a população nasce a partir dela.

**Ciclo de uma geração** (`motor_ga.py:evoluir()`): avaliação → seleção dos pais → recombinação (crossover) → mutação → nova população substitui a antiga.

- **Seleção (`operadores.py:selecionar_torneio`)** — quanto melhor o fitness, maior a chance de virar pai, mas não pode ser só o melhor sempre (perde diversidade, prende em ótimo local). Torneio (sorteia 3, pega o melhor) calibra isso; `tamanho_torneio` controla a **pressão seletiva** — maior = converge mais rápido mas arrisca ótimo local, menor = mais exploração.
- **Crossover (`operadores.py:cruzar`)** — combina pedaços de solução boa de dois pais na esperança de um filho ainda melhor. Uniforme (cada gene vem de um pai ou outro, 50/50) faz sentido aqui porque cada gene é uma decisão praticamente independente (slot de uma aula específica).
- **Mutação (`operadores.py:mutar`, 2%/gene)** — contrapeso ao crossover: sem ela a população só recombina genes que já existiam desde a população inicial, arriscando convergência prematura pra uma solução medíocre. Taxa baixa de propósito — mutação alta demais vira busca aleatória.
- **Elitismo (`motor_ga.py`, parâmetro `elite`)** — não é AG "canônico" de livro-texto, mas é padrão na prática: copia os N melhores direto pra próxima geração, garantindo que o melhor fitness histórico nunca piora geração a geração.
- **Reparo (`operadores.py:reparar`, `reparar_disponibilidade`)** — não é conceito clássico de AG genérico; é uma heurística de domínio (hibridização com busca local), comum especificamente em *timetabling* porque conflitos hard são fáceis de detectar e corrigir localmente. Foi o que resolveu o platô de convergência do projeto.
- **Convergência** — `historico_melhor_fitness` (retornado por `evoluir()`) é a série usada para plotar fitness do melhor indivíduo × geração na fase de experimentação.

**Trade-off central dos parâmetros** (`tamanho_populacao`, `geracoes`, `taxa_mutacao`, `tamanho_torneio`, `elite`): cada um equilibra **exploração** (evitar ótimo local) vs **explotação** (refinar o que já é bom). Não há valor "certo" universal — medir esse efeito na prática, comparado ao piso teórico (`analise.py`), é parte do valor experimental do TCC.
