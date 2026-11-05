# Motor de Horários

Motor de Algoritmo Genético para o problema de geração automática de quadro de horários escolar (School Timetabling Problem), desenvolvido como parte de um TCC. É standalone e genérico — não depende de nenhum sistema externo.

## Pré-requisitos

- Python 3.10+ (usa recursos como `list[int]` em type hints e `dataclass`)
- `pip`

## Instalação

Clone o repositório e instale as dependências (`deap`, `numpy`, `pandas`, `matplotlib`, `pytest`, `lxml`).

**Opção recomendada, com ambiente virtual:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Se `python3-venv` não estiver disponível no sistema** (ex: exigiria `sudo apt install python3-venv` e você não tem esse acesso), instale as dependências no escopo do usuário:
```bash
pip3 install --user --break-system-packages -r requirements.txt
```

## Rodando os testes

```bash
python3 -m pytest
```

## Rodando o exemplo pronto

Gera uma instância sintética, roda o AG, imprime o relatório de fitness comparado ao piso teórico de violações inevitáveis, e salva um quadro de horários renderizado (um sub-quadro por turma, PNG) em `resultados/quadro_exemplo.png`:

```bash
python3 -m scripts.gerar_quadro_exemplo
```

## Rodando o harness de experimentação

Roda o AG numa grade de escalas do problema (pequena/média/grande) x 30 seeds cada (0 a 29), com 300 gerações e população de 60, compara cada execução ao piso teórico, e salva os resultados em `resultados/`:

```bash
python3 -m scripts.rodar_experimentos
```

Saídas:
- `resultados/experimentos_resumo.csv` — uma linha por (escala, seed): fitness final, violações por dimensão vs. piso teórico, tempo de execução, se bateu o piso.
- `resultados/experimentos_convergencia.csv` — formato longo (uma linha por geração), para reanalisar/replotar a convergência.
- `resultados/experimentos_convergencia.png` — gráfico com uma curva por escala (média do melhor fitness por geração entre as seeds).

Para customizar as escalas/seeds/parâmetros do AG testados, edite as constantes no topo de `scripts/rodar_experimentos.py` (`ESCALAS`, `SEEDS`, `GERACOES`, `TAMANHO_POPULACAO`).

## Reproduzindo os resultados do artigo

Os números, tabelas e figuras do artigo saem dos scripts abaixo, nesta ordem. Os CSVs de `resultados/` já estão versionados, então os passos 4 e 5 podem ser rodados direto, sem repetir as execuções.

1. `python3 -m scripts.rodar_experimentos`: 90 execuções (3 escalas x 30 seeds, 300 gerações). Gera `resultados/experimentos_resumo.csv`, base das tabelas de violações e piso.
2. `python3 -m scripts.rodar_sensibilidade_geracoes`: repete as escalas média e grande com 1500 gerações, mesmas seeds. Gera `resultados/sensibilidade_geracoes_resumo.csv`.
3. `python3 -m scripts.rodar_convergencia_obrigatorias`: repete a base registrando, a cada geração, as violações obrigatórias do melhor indivíduo. Gera `resultados/convergencia_obrigatorias.csv`.
4. `python3 -m scripts.analisar_resultados`: estatísticas por escala (médias com IC de 95%, proporção de execuções no piso com IC exato de Clopper-Pearson e comparação pareada 300 x 1500 gerações).
5. `python3 -m scripts.gerar_figura_metodologia`, `gerar_figura_ciclo_ag`, `gerar_figura_quadro_exemplo` e `gerar_figura_convergencia`: Figuras 1 a 4 do artigo, salvas em `figuras/`.

Os passos 2 e 3 rodam em paralelo, então os tempos de execução registrados neles não são comparáveis com os do passo 1. Os tempos do artigo vêm do passo 1, numa única máquina.

## Rodando com parâmetros customizados

Sem editar nenhum arquivo, direto no terminal:

```bash
python3 -c "
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.motor_ga import evoluir

instancia = gerar_instancia(seed=7, n_turmas=5)
melhor, relatorio, historico = evoluir(instancia, geracoes=100, tamanho_populacao=40, seed=7)
print(relatorio)
"
```

- `gerar_instancia(seed=..., n_turmas=..., n_professores=..., n_disciplinas=..., n_salas=..., ...)` — a `seed` fixa a aleatoriedade (mesma seed = mesma instância sempre, em qualquer máquina); os demais parâmetros controlam a escala do problema.
- `evoluir(instancia, geracoes=..., tamanho_populacao=..., seed=..., taxa_mutacao=..., tamanho_torneio=..., elite=...)` — parâmetros do AG. Retorna o melhor indivíduo encontrado, seu relatório de fitness (`RelatorioFitness`) e o histórico do melhor fitness por geração (para gráfico de convergência).

Para renderizar o resultado de uma execução customizada como quadro de horários:

```python
from motor_horarios.visualizacao import salvar_quadro_horarios
salvar_quadro_horarios(instancia, melhor, "resultados/meu_teste.png")
```

## Rodando a interface web (demo)

Uma interface web mínima sobre o motor, pensada só como demo visual (o foco do TCC é o motor em `motor_horarios/`, com o AG e o piso teórico, não esta camada). Ela não faz cadastro de turma/professor/disciplina/sala um a um — o formulário ajusta os mesmos parâmetros de escala de `gerar_instancia()`, e o botão roda o AG e mostra o relatório de fitness (comparado ao piso teórico) e o quadro de horários por turma, em HTML em vez do PNG estático.

```bash
pip3 install --user --break-system-packages -r webapp/requirements.txt   # só adiciona flask
python3 -m webapp.app
```

Abra `http://127.0.0.1:5000/` no navegador. Os campos já vêm preenchidos com os defaults do motor (via `/api/parametros-padrao`); é só clicar em "Gerar e executar".

Detalhes:
- `webapp/app.py` — rotas Flask; só orquestra chamadas a `gerar_instancia`, `evoluir`, `montar_grade` e `calcular_limites_teoricos` (nenhuma lógica de domínio nova).
- `webapp/serializacao.py` — conversão de `SlotHorario` (Enum `DiaSemana` + `datetime.time`) para JSON.
- `webapp/static/` — página única (HTML/CSS/JS puro, sem build step/framework).
- Fora de escopo, deliberadamente: banco de dados, autenticação, CRUD de entidades individuais, edição manual de instância, deploy, execução assíncrona do AG (a chamada é síncrona — aceitável nas escalas do TCC).

## Estrutura do projeto

```
motor_horarios/     # módulos do motor (modelo, gerador sintético, cromossomo, fitness, operadores, AG, análise, visualização)
webapp/              # interface web mínima (Flask) sobre o motor — só demo, motor_horarios/ não depende dela
tests/               # suite de testes pytest
scripts/             # scripts de exemplo, experimentos, análise estatística e figuras do artigo
docs/                # documentação de referência (resumo dos módulos, fundamentação teórica de AG)
resultados/          # CSVs dos experimentos usados no artigo (reproduzíveis via seed)
figuras/             # figuras do artigo, geradas pelos scripts gerar_figura_*
```

Documentação de referência:
- [`docs/motor_horarios.md`](docs/motor_horarios.md) — resumo de cada módulo do motor.
- [`docs/conceitos_algoritmo_genetico.md`](docs/conceitos_algoritmo_genetico.md) — fundamentação teórica dos conceitos de AG usados.
- [`docs/parametros_de_entrada.md`](docs/parametros_de_entrada.md) — glossário de cada campo do formulário da interface web (o que significa, e o parâmetro correspondente no código).
- [`docs/resultados_experimentacao.md`](docs/resultados_experimentacao.md) — resultados do harness por escala, bugs encontrados/corrigidos no processo, e diagnósticos de convergência.
- [`docs/exemplos_apresentacao.md`](docs/exemplos_apresentacao.md) — 3 instâncias prontas (escola pequena/média/grande, com disponibilidade) pra rodar ao vivo, com relatório de contagens e piso teórico de cada uma.

## Regras do projeto

- O motor é intencionalmente desacoplado de qualquer sistema real — toda modelagem é genérica, fundamentada em literatura de Timetabling, não em código/schema de terceiros.
- Sem banco de dados no loop de fitness — tudo em memória; persistência é só para instâncias de entrada (JSON) e resultados de experimentos (CSV/SQLite).
