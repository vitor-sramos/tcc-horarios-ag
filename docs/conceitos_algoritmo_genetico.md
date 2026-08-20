# Conceitos de Algoritmo Genético utilizados

Fundamentação teórica dos conceitos de AG usados no motor, amarrada aos trechos de código onde cada um aparece (ver resumo dos módulos em [`motor_horarios.md`](./motor_horarios.md)).

Um AG resolve otimização imitando seleção natural: mantém uma **população** de soluções candidatas e, a cada **geração**, as melhores têm mais chance de "reproduzir", enquanto mutações aleatórias introduzem variação. É uma **metaheurística** — não garante o ótimo global, mas é viável onde testar todas as combinações não é (espaço de busca aqui é astronomicamente grande: centenas de aulas pendentes × dezenas de slots).

**Ciclo de uma geração** (`motor_ga.py:evoluir()`): avaliação → seleção dos pais → recombinação (crossover) → mutação → nova população substitui a antiga.

- **Seleção (`operadores.py:selecionar_torneio`)** — quanto melhor o fitness, maior a chance de virar pai, mas não pode ser só o melhor sempre (perde diversidade, prende em ótimo local). Torneio (sorteia 3, pega o melhor) calibra isso; `tamanho_torneio` controla a **pressão seletiva** — maior = converge mais rápido mas arrisca ótimo local, menor = mais exploração.
- **Crossover (`operadores.py:cruzar`)** — combina pedaços de solução boa de dois pais na esperança de um filho ainda melhor. Uniforme (cada gene vem de um pai ou outro, 50/50) faz sentido aqui porque cada gene é uma decisão praticamente independente (slot de uma aula específica).
- **Mutação (`operadores.py:mutar`, 2%/gene)** — contrapeso ao crossover: sem ela a população só recombina genes que já existiam desde a população inicial, arriscando convergência prematura pra uma solução medíocre. Taxa baixa de propósito — mutação alta demais vira busca aleatória.
- **Elitismo (`motor_ga.py`, parâmetro `elite`)** — não é AG "canônico" de livro-texto, mas é padrão na prática: copia os N melhores direto pra próxima geração, garantindo que o melhor fitness histórico nunca piora geração a geração.
- **Reparo (`operadores.py:reparar`, `reparar_disponibilidade`)** — não é conceito clássico de AG genérico; é uma heurística de domínio (hibridização com busca local), comum especificamente em *timetabling* porque conflitos hard são fáceis de detectar e corrigir localmente. Foi o que resolveu o platô de convergência do projeto.
- **Convergência** — `historico_melhor_fitness` (retornado por `evoluir()`) é a série usada para plotar fitness do melhor indivíduo × geração na fase de experimentação.

**Trade-off central dos parâmetros** (`tamanho_populacao`, `geracoes`, `taxa_mutacao`, `tamanho_torneio`, `elite`): cada um equilibra **exploração** (evitar ótimo local) vs **explotação** (refinar o que já é bom). Não há valor "certo" universal — medir esse efeito na prática, comparado ao piso teórico (`analise.py`), é parte do valor experimental do TCC.
