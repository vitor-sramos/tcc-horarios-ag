# Parâmetros de entrada (interface web)

Glossário de cada campo do formulário em `webapp/static/index.html`. Complementa [`conceitos_algoritmo_genetico.md`](./conceitos_algoritmo_genetico.md) (que explica *por que* cada conceito de AG existe) com o que cada campo *significa na prática*, e amarra o rótulo em português da tela ao parâmetro real no código — `gerar_instancia()` (`motor_horarios/gerador_sintetico.py`) pros campos de Instância, `evoluir()` (`motor_horarios/motor_ga.py`) pros campos de Algoritmo genético.

## O que é "gerar uma instância"

O motor não usa dados reais de uma escola — não há esse cadastro disponível fora do sistema da empresa (ver [`motor_horarios.md`](./motor_horarios.md), o motor é intencionalmente desacoplado de qualquer sistema real). Em vez disso, `gerar_instancia()` **inventa** um cenário de escola plausível (turmas, professores, disciplinas, salas, quem leciona o quê, quantas aulas cada turma tem de cada disciplina) a partir dos parâmetros de escala do formulário. "Gerar uma instância" = "criar um problema de teste completo" — é a entrada que o algoritmo genético (`evoluir()`) recebe pra tentar resolver.

## Por que existem dois campos de "Seed"

`seed` fixa a aleatoriedade: mesma seed → exatamente os mesmos números "aleatórios" toda vez, em qualquer máquina (`random.Random(seed)` próprio, não o `random` global do Python). Isso é o que garante **reprodutibilidade** — pré-requisito de rigor experimental no TCC, já que qualquer resultado citado precisa poder ser reproduzido por outra pessoa.

Existem dois porque são duas aleatoriedades independentes:
- **Seed da Instância** — controla a criação do cenário (que professor existe, quantas aulas cada disciplina de cada turma tem, etc.).
- **Seed do Algoritmo genético** — controla como o AG resolve aquele cenário (população inicial e sorteios ao longo da evolução).

Trocar só uma delas isola o que está sendo variado: mesma instância + seeds de AG diferentes mostra a variância do algoritmo sobre o mesmo problema; mesma seed de AG + instâncias diferentes mostra como o algoritmo se comporta em cenários distintos.

## Parâmetros da Instância

| Campo na tela | Parâmetro (`gerar_instancia`) | O que significa |
|---|---|---|
| Seed | `seed` | Trava a aleatoriedade da geração do cenário — ver seção acima |
| Turmas | `n_turmas` | Quantas turmas o gerador cria |
| Professores | `n_professores` | Quantos professores o gerador cria |
| Disciplinas | `n_disciplinas` | Quantas disciplinas o gerador cria |
| Salas | `n_salas` | Quantas salas físicas o gerador cria (extensão opcional do motor, fora do núcleo pedido pelo orientador — ver `docs/motor_horarios.md`) |
| Disciplinas por turma | `disciplinas_por_turma` | Cada turma "cursa" esse tanto de disciplinas, sorteadas entre as que existem — isso monta a matriz curricular (`ComponenteCurricular`) |
| Disciplinas por professor | `disciplinas_por_professor` | Cada professor é habilitado a lecionar esse tanto de disciplinas (`Professor.disciplinas_habilitadas`) — o gerador só atribui a um componente curricular um professor habilitado pra aquela disciplina |
| Aulas/semana (mín.) / (máx.) | `aulas_por_semana_min` / `_max` | Quantas vezes por semana cada disciplina de cada turma acontece — sorteado entre esses dois valores |
| Aulas por dia | `aulas_por_dia` | Quantos períodos existem no dia (ex: 6 = "Aula 1" a "Aula 6" na grade) |
| Duração da aula (min) | `duracao_aula_minutos` | Duração de cada período, em minutos |
| Turnos | `turnos` | Quais turnos existem (MATUTINO/VESPERTINO/NOTURNO) — cada turma sorteia um deles e só pode ser alocada em slots do seu próprio turno (`InstanciaProblema.dominio_genes()`) |
| Carga horária máx. professor (min) | `carga_horaria_professor_minutos` | Limite semanal de minutos que um professor pode dar aula — constraint que o AG tenta respeitar (extensão opcional, fora do núcleo pedido pelo orientador) |
| Prob. disponibilidade restrita | `prob_disponibilidade_restrita` | Chance (0 a 1) de um professor ter 1 dia da semana em que não pode dar aula — ausência dessa restrição significa "sem restrição", não "sempre indisponível" (extensão opcional) |

## Parâmetros do Algoritmo Genético

| Campo na tela | Parâmetro (`evoluir`) | O que significa |
|---|---|---|
| Seed | `seed` | Trava a aleatoriedade da busca do AG (população inicial, mutação, seleção) — ver seção acima |
| Gerações | `geracoes` | Quantas rodadas de evolução rodam. Mais gerações = mais chance de melhorar, mais tempo de execução |
| Tamanho da população | `tamanho_populacao` | Quantos quadros de horário candidatos existem, competindo entre si, em cada geração — ver [`conceitos_algoritmo_genetico.md`](./conceitos_algoritmo_genetico.md#instância-vs-indivíduo-o-que-é-fixo-o-que-varia) pra como esses candidatos nascem a partir da instância (única, fixa) |
| Taxa de mutação | `taxa_mutacao` | Chance (por gene, ou seja, por aula) de virar um slot aleatório novo — é o que evita a busca convergir cedo demais numa solução medíocre |
| Tamanho do torneio | `tamanho_torneio` | Quantos candidatos competem pra virar "pai" de um novo candidato — sorteia esse tanto e o melhor deles vence, calibrando pressão seletiva vs. diversidade |
| Elite | `elite` | Quantos dos melhores candidatos da geração atual passam direto pra próxima, sem alteração — garante que o melhor fitness já alcançado nunca piora |

Fundamentação teórica de cada um desses conceitos (seleção, crossover, mutação, elitismo) em [`conceitos_algoritmo_genetico.md`](./conceitos_algoritmo_genetico.md).
