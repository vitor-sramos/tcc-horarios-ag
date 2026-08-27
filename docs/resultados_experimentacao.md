# Resultados de experimentação

Registro dos resultados empíricos coletados até agora, pra servir de referência na escrita do capítulo de resultados do TCC — não repetir essas rodadas do zero, só atualizar aqui quando algo mudar de verdade no motor.

## Harness principal (`scripts/rodar_experimentos.py`)

3 escalas × 5 seeds, 300 gerações, população 60. `disciplinas_por_professor` é parametrizado por escala pra manter ~75% de cobertura de qualificação em todas (ver `docs/motor_horarios.md`, seção `experimentacao.py`).

| Escala | Turmas/Professores/Disciplinas/Salas | Cromossomo | Bateu o piso | Tempo médio |
|---|---|---|---|---|
| Pequena | 3/5/4/4 | ~40-50 genes | 5/5 | ~7,4s |
| Média | 10/15/8/10 | ~166-180 genes | 4/5 | ~20,8s |
| Grande | 25/35/12/20 | ~430-455 genes | 0/5 | ~53,6s |

Dados brutos em `resultados/experimentos_resumo.csv` (uma linha por execução) e `resultados/experimentos_convergencia.csv` (uma linha por geração); gráfico em `resultados/experimentos_convergencia.png`.

**Leitura:** o motor resolve **perfeitamente** (bate o mínimo teórico de violações) em escala pequena e quase sempre em escala média. Em escala grande, não bate com esses hiperparâmetros — ver diagnóstico abaixo antes de interpretar isso como limitação do motor.

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
