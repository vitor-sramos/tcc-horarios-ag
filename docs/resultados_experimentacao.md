# Resultados de experimentação

Registro dos resultados empíricos coletados até agora, pra servir de referência na escrita do capítulo de resultados do TCC — não repetir essas rodadas do zero, só atualizar aqui quando algo mudar de verdade no motor.

## Harness re-rodado após novas dimensões de fitness (2026-09-16)

`fitness.py` ganhou 2 dimensões soft novas (`janelas_professor` e `distribuicao_semanal_disciplina`,
ver `docs/motor_horarios.md`), pra fechar 2 critérios da proposta do TCC que não eram medidos antes
("redução de períodos vagos na jornada docente" e "distribuição equilibrada das aulas ao longo da
semana"). O harness completo foi re-rodado com o motor atual (mesmo dia) — a tabela abaixo já reflete
a versão nova do fitness.

**O que mudou nos números:** as 5 dimensões com piso teórico (professor/sala/turma/carga
horária/disponibilidade) continuam batendo o piso exatamente sempre que batiam antes — a invariante
central do projeto não foi afetada por adicionar dimensões novas. O que mudou foi a taxa de "bateu o
piso completo" em escala média (2/5 → 3/5) e o tempo médio de execução (subiu ~35-43% em todas as
escalas, esperado: mais 2 dimensões calculadas por indivíduo por geração). Ambas as variações são
ruído/custo esperado de mudar a função de fitness (a trajetória do AG muda porque a pressão seletiva
agora também empurra pras 2 dimensões novas), não regressão.

**Achado sobre as 2 dimensões novas:** em escala pequena, `janelas_professor` zera só com pressão
seletiva (sem reparo dedicado), igual `janelas_turma` já zerava. Já `distribuicao_semanal_disciplina`
não zera sozinha (residual de ~4 por execução mesmo em escala pequena, 300 gerações) — é por isso
que a escala pequena deixou de ter fitness final = 0 (antes o motor resolvia essa escala
"perfeitamente", agora resta esse resíduo). Mesmo padrão que `fragmentacao_disciplina` teve antes de
ganhar um reparo dedicado (ver seção "Reparo dedicado pra fragmentação de disciplina" abaixo). Não
implementado reparo equivalente pra distribuição semanal — decisão em aberto.

**Atualização (2026-09-23):** a limitação registrada aqui (harness sem as dimensões soft) foi resolvida: `ResultadoExecucao` e `experimentos_resumo.csv` agora trazem `janelas_turma`, `janelas_professor`, `fragmentacao_disciplina` e `distribuicao_semanal_disciplina` nas 15 execuções.

## Harness principal (`scripts/rodar_experimentos.py`)

3 escalas × 5 seeds, 300 gerações, população 60. `disciplinas_por_professor` é parametrizado por escala pra manter ~75% de cobertura de qualificação em todas (ver `docs/motor_horarios.md`, seção `experimentacao.py`).

| Escala | Turmas/Professores/Disciplinas/Salas | Cromossomo (média) | Bateu o piso (todas as dimensões) | Excesso médio de disponibilidade sobre o piso | Tempo médio (± desvio) |
|---|---|---|---|---|---|
| Pequena | 3/5/4/4 | 44,2 (39-49) | 5/5 | 0,0 | 6,4 s (± 1,1) |
| Média | 10/15/8/10 | 175,0 (168-183) | 3/5 | 1,2 (máx. 4) | 33,9 s (± 4,7) |
| Grande | 25/35/12/20 | 435,8 (426-444) | 0/5 | 7,0 (máx. 12) | 81,5 s (± 6,4) |

Hardware: Intel Core i5-8265U (1,6 GHz, 8 threads), 31 GB de RAM, Python 3.12.3. Execução em série. Valores conferidos em 2026-10-13 (CSV reproduz exatamente por seed; só o tempo varia).

Dados brutos em `resultados/experimentos_resumo.csv` (uma linha por execução) e `resultados/experimentos_convergencia.csv` (uma linha por geração); gráfico em `resultados/experimentos_convergencia.png`.

**Leitura:** em escala pequena, **as 5 dimensões com piso teórico** batem o mínimo exatamente nas 5 execuções — o resíduo de fitness que sobra vem só das 2 dimensões soft novas sem piso (ver achado acima), não de conflito real. Em média e grande, **as dimensões hard (professor/sala/turma/carga horária) batem o piso exatamente em 100% das 15 execuções** — o único motivo de uma execução não bater o piso completo é a dimensão soft de disponibilidade ficar acima do mínimo teórico, nunca um conflito real de agenda. Ver diagnóstico de convergência abaixo antes de interpretar essa distância residual como limitação do motor.

## Bug encontrado e corrigido: piso teórico de disponibilidade superestimado

Analisando a escala média (seed 3), uma execução do AG achou uma solução com **menos** violações de disponibilidade do que o piso teórico dizia ser o mínimo possível — quebra da invariante central do projeto ("nenhuma solução fica abaixo do piso").

**Causa:** a fórmula original (`demanda - slots_compatíveis`) assume que cada aula de um professor ocupa um slot distinto. Isso deixa de valer quando a demanda de um professor específico já ultrapassa o **total** de slots da semana (ex: professor com 36 aulas/semana numa semana de 30 slots) — nesse caso o conflito de professor (empilhar 2 aulas no mesmo slot) já é inevitável de qualquer jeito, e pode ser direcionado pra cima de um slot já compatível com a disponibilidade dele, sem gerar violação extra por causa disso. Fórmula corrigida: quando a demanda excede o total de slots, o piso passa a ser `n_slots - slots_compatíveis` (só os slots incompatíveis usados 1x cada), não `demanda - compatíveis`.

Corrigido em `motor_horarios/analise.py` (commit `d0880c4`), com teste de regressão em `tests/test_analise.py`. Não é um bug introduzido pela remodelagem de turno/habilitação (commit `412a58c`) — é uma lacuna antiga na fórmula, que só ficou visível porque a restrição de qualificação de professor tornou sobrecarga concentrada mais provável. Depois do fix, as 15 execuções do harness passaram a respeitar a invariante em todas as dimensões, em todas as escalas.

## Sensibilidade ao número de gerações (re-rodado em 2026-10-13, motor atual)

Substitui o diagnóstico anterior (2 seeds, escala grande), que era anterior à correção do reparo e à adição das dimensões soft novas. Script: `scripts/rodar_sensibilidade_geracoes.py`. Mesmas instâncias e mesmos parâmetros do harness principal, só com **1500 gerações** (5x), escalas média e grande, 5 seeds. Dados em `resultados/sensibilidade_geracoes_resumo.csv` e `resultados/sensibilidade_geracoes_convergencia.csv`. Execuções em paralelo (4 processos): o tempo desse teste NÃO é comparável com o do harness principal (média ~294 s, grande ~771 s por execução).

| Escala | Bateu o piso em 300 ger. | Bateu o piso em 1500 ger. | Fitness médio 300 -> 1500 (só seeds sem piso alto) |
|---|---|---|---|
| Média | 3/5 | 3/5 (as mesmas seeds) | seeds 0, 1, 4: 85, 82, 90 -> 62, 67, 70 |
| Grande | 0/5 | 0/5 | 11418 -> 11359; 3694 -> 3646; 3741 -> 3638; 2830 -> 2783; 4571 -> 4481 |

- As dimensões professor/sala/turma/carga horária continuam no piso em 10/10 execuções (nenhum conflito real surge ou some com mais gerações).
- Disponibilidade: seeds da média 0 e 2 melhoraram (4 -> 3 e 2 -> 1), mas nenhuma chegou ao piso. Na grande, 4 das 5 seeds melhoraram 1 a 3 violações; a seed 0 ficou em 20 (piso 8). Nenhuma bateu o piso.
- Soft (médias 300 -> 1500): média: janelas turma 31,8 -> 18,2; janelas professor 26,2 -> 18,8; fragmentação 6,0 -> 3,2; distribuição semanal 29,2 -> 30,2. Grande: 116,8 -> 98,0; 104,2 -> 85,4; 63,0 -> 45,6; 90,8 -> 77,8.
- Convergência: na grande, o ganho de 300 para 1500 gerações é pequeno em termos absolutos (1% a 3% do fitness, que é dominado pelo piso de carga horária e professor), com a curva quase plana depois da geração ~500. Na média, as seeds sem piso alto seguem caindo devagar até 1500 (-20% a -27%).

**Conclusão:** mais gerações melhoram as dimensões desejáveis, mas não fecham a distância da disponibilidade até o piso nas instâncias que não o batiam. O platô é parcial e consistente com a observação anterior (convergência lenta de AG em espaço de busca grande), agora com 5 seeds e o motor atual.

## Achado e corrigido: reparo guloso deixava violações hard reais em escala grande

Reanalisando `resultados/experimentos_resumo.csv` (rodada de 300 gerações, população 60, antes da correção abaixo), a leitura de "escala grande não bate o piso" escondia um detalhe importante: nas 5 sementes, o melhor indivíduo final tinha **violações reais de hard constraint acima do piso**, não só folga nas dimensões soft. Exemplos (dados da rodada antiga, já superados):

| Seed | violações sala | piso sala | violações professor | piso professor |
|---|---|---|---|---|
| 0 | 6 | 0 | 3 | 1 |
| 1 | 5 | 1 | 2 | 0 |
| 2 | 6 | 0 | 3 | 0 |
| 4 | 9 | 0 | 3 | 0 |

Ou seja, em escala grande, o quadro gerado tinha **conflito de sala/professor de verdade** — não era só "não é ótimo nas restrições soft".

**Causa:** `reparar()` em `motor_horarios/operadores.py` usava só `tentativas=5` sorteios **com reposição** de slot por gene em conflito (`rng.choice` dentro de um loop, podia repetir o mesmo slot já ocupado várias vezes). Em escala grande, o domínio de slots por gene é mais restrito (turno já filtra boa parte), então a chance de nenhuma das 5 tentativas cair num slot livre — mesmo havendo um — era alta.

**Correção (commit a seguir, 2026-09-02):** `reparar()` e `reparar_disponibilidade()` agora embaralham o domínio inteiro do gene e percorrem **sem repetir candidato**; por padrão (`tentativas=None`) não há mais cap artificial — só desiste quando todo o domínio foi checado e nenhum slot está livre. `tentativas` continua aceito como parâmetro opcional pra limitar o custo, se algum dia fizer sentido. Teste de regressão em `tests/test_operadores.py` (`test_reparar_sem_cap_de_tentativas_acha_unico_slot_livre_em_dominio_grande`).

**Resultado depois da correção** (harness completo re-rodado, mesmos parâmetros): nas 15 execuções (3 escalas × 5 seeds), **professor/sala/turma/carga horária batem o piso teórico exatamente em 100% dos casos** — zero conflito real de agenda sobrando, inclusive em escala grande. O único resíduo que impede "bater o piso" por completo em média/grande é a dimensão soft de disponibilidade (1 a 7 violações acima do piso, a mesma família do platô de convergência diagnosticado acima) — nunca mais hard constraint. Ver tabela do harness principal no topo do documento pros números atualizados.

**Custo:** o tempo médio de execução praticamente dobrou (grande: ~53,6s → ~98,7s; média: ~20,8s → ~38,6s; pequena: praticamente igual, ~7,4s → ~8,0s) — esperado, já que o reparo agora pode percorrer o domínio inteiro em vez de parar em 5 tentativas. Nenhum problema de escala prático (menos de 2 minutos por execução mesmo na escala grande).

**Como isso deve entrar no TCC:** bom material pra metodologia — mostra um ciclo real de "achado empírico → causa raiz → correção → validação experimental", não só um resultado final. A limitação de convergência das dimensões soft em escala grande continua existindo e é discutida na seção de diagnóstico acima; agora fica mais nítido que ela é **puramente de tuning/convergência do AG**, isolada de qualquer questão de corretude do reparo.

## Reparo dedicado pra fragmentação de disciplina

Até aqui, `janelas_turma` e `fragmentacao_disciplina` (as duas dimensões soft sem piso teórico, ver `docs/motor_horarios.md`) só contavam com a pressão de seleção do AG pra melhorar — sem reparo dedicado, igual disponibilidade estava antes do `reparar_disponibilidade` existir. Implementado `reparar_fragmentacao_disciplina` (`motor_horarios/operadores.py`, 2026-09-02): depois dos outros reparos, agrupa as aulas de cada turma por dia, identifica disciplinas fragmentadas (ex: aula 1 e aula 4 da mesma matéria, com outra no meio) e tenta reagrupá-las — trocando de lugar com quem ocupa o "buraco" (ou só movendo, se o horário estiver vago), sempre sem piorar hard constraints nem disponibilidade de nenhum dos dois lados da troca.

**Resultado real** (instância "escola fundamental" de `exemplos/instancia_exemplo_escola_fundamental.json`, 350 aulas pendentes, 200 gerações/pop. 60/seed 0): fragmentação caiu de **54 para 31** (~43%) com esse reparo, sem alterar nenhuma das dimensões que já estavam em 0 (professor/sala/turma/carga horária/disponibilidade continuam no piso). Não zera sozinho — o resto ainda depende da pressão de seleção ao longo das gerações, mesmo padrão dos outros reparos.

**Bug encontrado e corrigido durante a implementação:** a primeira versão quebrava com `KeyError` sempre que um dia de uma turma ainda tinha um conflito de turma não resolvido (2 aulas da mesma turma no mesmo horário) — estado transitório normal entre gerações, já que `reparar()` é heurística e não garante zerar tudo de uma vez. A causa era o mapeamento posição→gene ficar ambíguo (duas posições iguais colidindo num dict) nesse cenário. Corrigido pulando o dia inteiro quando isso acontece (não é papel desse reparo consertar conflito de turma) — teste de regressão em `tests/test_operadores.py` (`test_reparar_fragmentacao_nao_quebra_com_conflito_de_turma_nao_resolvido`), reproduzido originalmente numa execução real do harness (escala média, seed 2, geração 45).

**Atualização (2026-09-23):** `janelas_turma` e `fragmentacao_disciplina` já são registradas nas 15 execuções da grade (ver tabela principal e `resultados/experimentos_resumo.csv`). O número acima (54 -> 31) vem de execução avulsa anterior, na instância da escola fundamental.
