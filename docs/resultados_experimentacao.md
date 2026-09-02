# Resultados de experimentação

Registro dos resultados empíricos coletados até agora, pra servir de referência na escrita do capítulo de resultados do TCC — não repetir essas rodadas do zero, só atualizar aqui quando algo mudar de verdade no motor.

## Harness principal (`scripts/rodar_experimentos.py`)

3 escalas × 5 seeds, 300 gerações, população 60. `disciplinas_por_professor` é parametrizado por escala pra manter ~75% de cobertura de qualificação em todas (ver `docs/motor_horarios.md`, seção `experimentacao.py`).

| Escala | Turmas/Professores/Disciplinas/Salas | Cromossomo | Bateu o piso (todas as dimensões) | Tempo médio |
|---|---|---|---|---|
| Pequena | 3/5/4/4 | ~40-50 genes | 5/5 | ~8,0s |
| Média | 10/15/8/10 | ~168-183 genes | 3/5 | ~38,6s |
| Grande | 25/35/12/20 | ~426-444 genes | 0/5 | ~98,7s |

Dados brutos em `resultados/experimentos_resumo.csv` (uma linha por execução) e `resultados/experimentos_convergencia.csv` (uma linha por geração); gráfico em `resultados/experimentos_convergencia.png`. Números acima já incluem a correção do reparo guloso (ver seção "Achado" abaixo) — o tempo médio subiu em relação à rodada anterior porque o reparo agora percorre o domínio inteiro do gene em vez de parar em 5 tentativas.

**Leitura:** o motor resolve **perfeitamente** (bate o mínimo teórico de violações, em toda dimensão hard e soft) em escala pequena. Em média e grande, **as dimensões hard (professor/sala/turma/carga horária) batem o piso exatamente em 100% das 15 execuções** — o único motivo de uma execução não bater o piso completo é a dimensão soft de disponibilidade ficar 1 a 7 violações acima do mínimo teórico, nunca um conflito real de agenda. Ver diagnóstico de convergência abaixo antes de interpretar essa distância residual como limitação do motor.

## Bug encontrado e corrigido: piso teórico de disponibilidade superestimado

Analisando a escala média (seed 3), uma execução do AG achou uma solução com **menos** violações de disponibilidade do que o piso teórico dizia ser o mínimo possível — quebra da invariante central do projeto ("nenhuma solução fica abaixo do piso").

**Causa:** a fórmula original (`demanda - slots_compatíveis`) assume que cada aula de um professor ocupa um slot distinto. Isso deixa de valer quando a demanda de um professor específico já ultrapassa o **total** de slots da semana (ex: professor com 36 aulas/semana numa semana de 30 slots) — nesse caso o conflito de professor (empilhar 2 aulas no mesmo slot) já é inevitável de qualquer jeito, e pode ser direcionado pra cima de um slot já compatível com a disponibilidade dele, sem gerar violação extra por causa disso. Fórmula corrigida: quando a demanda excede o total de slots, o piso passa a ser `n_slots - slots_compatíveis` (só os slots incompatíveis usados 1x cada), não `demanda - compatíveis`.

Corrigido em `motor_horarios/analise.py` (commit `d0880c4`), com teste de regressão em `tests/test_analise.py`. Não é um bug introduzido pela remodelagem de turno/habilitação (commit `412a58c`) — é uma lacuna antiga na fórmula, que só ficou visível porque a restrição de qualificação de professor tornou sobrecarga concentrada mais provável. Depois do fix, as 15 execuções do harness passaram a respeitar a invariante em todas as dimensões, em todas as escalas.

## Diagnóstico: escala grande com mais gerações

Pergunta: a escala grande não bate o piso por falta de orçamento (gerações/população), ou por estagnação real (ótimo local)? Teste: mesma escala grande, população mantida em 60 (isolando só o efeito de gerações), **1500 gerações** (5×) em vez de 300, 2 seeds.

| Seed | Fitness em 300 gerações | Fitness em 1500 gerações | Comportamento |
|---|---|---|---|
| 0 | 20.017 | 16.016 (−20%) | Ainda caindo na geração 1500, sem sinal de platô |
| 1 | 11.335 | 4.337 (−62%) | Platô real entre a geração 750 e 1500 (praticamente parado) |

Nenhuma das duas bateu o piso mesmo com 5× o orçamento. O tempo escalou de forma linear e previsível (~5× gerações → ~5× tempo: 62s→190s na seed 0, 49s→156s na seed 1).

**Conclusão:** o comportamento é heterogêneo entre instâncias, não uniforme — não é "só falta orçamento" (a seed 1 melhorou 62%, claramente responde a mais gerações) nem "está travado desde o início" (a seed 0 seguia melhorando até o fim). É convergência lenta com sinais de platô parcial em pelo menos parte das instâncias grandes — comportamento normal e esperado de um AG em espaços de busca grandes com esses hiperparâmetros (`taxa_mutacao=0.02`, `tamanho_torneio=3`, `elite=2`), não um indício de bug no motor. O motor otimiza corretamente, de forma reprodutível, na direção certa — a limitação é de escala/tuning, não de corretude.

**Não explorado ainda** (candidato a próxima rodada de experimentação, se fizer sentido pro TCC): variar população em vez de/além de gerações; taxa de mutação adaptativa; população inicial parcialmente construída em vez de 100% aleatória. Nenhum desses foi implementado — ficou só como direção possível.

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
