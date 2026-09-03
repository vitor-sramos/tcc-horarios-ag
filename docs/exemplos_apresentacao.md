# Exemplos para apresentação: escola pequena, média e grande

Três instâncias prontas pra rodar ao vivo (`webapp/`, modo "Colar JSON") ou por script, cada
uma numa escala diferente, todas com disponibilidade de professor (soft constraint) incluída.
Gerado por `scripts/gerar_exemplos_apresentacao.py` -- não editar os JSONs à mão, rodar o script
de novo se precisar mudar algo (reprodutível pela seed).

## Escola Pequena

Arquivo: `exemplos/escola_pequena.json` (seed=0, mesma escala e seed documentadas
em `docs/resultados_experimentacao.md`, linha `pequena` / seed `0`).

| Métrica | Valor |
|---|---|
| Turmas | 3 (Matutino: 3) |
| Professores | 5 |
| Disciplinas | 4 |
| Salas | 4 |
| Componentes curriculares (turma × disciplina) | 12 |
| Aulas pendentes (tamanho do cromossomo) | 49 |
| Professores com disponibilidade restrita | 4 de 5 |

**Piso teórico** (mínimo de violações inevitável, calculado por `calcular_limites_teoricos`):

| Dimensão | Piso |
|---|---|
| Conflitos de professor | 0 |
| Conflitos de sala | 0 |
| Conflitos de turma | 0 |
| Minutos excedentes de carga horária | 0 |
| Violações de disponibilidade | 0 |

## Escola Média

Arquivo: `exemplos/escola_media.json` (seed=0, mesma escala e seed documentadas
em `docs/resultados_experimentacao.md`, linha `media` / seed `0`).

| Métrica | Valor |
|---|---|
| Turmas | 10 (Matutino: 10) |
| Professores | 15 |
| Disciplinas | 8 |
| Salas | 10 |
| Componentes curriculares (turma × disciplina) | 50 |
| Aulas pendentes (tamanho do cromossomo) | 168 |
| Professores com disponibilidade restrita | 4 de 15 |

**Piso teórico** (mínimo de violações inevitável, calculado por `calcular_limites_teoricos`):

| Dimensão | Piso |
|---|---|
| Conflitos de professor | 0 |
| Conflitos de sala | 0 |
| Conflitos de turma | 0 |
| Minutos excedentes de carga horária | 0 |
| Violações de disponibilidade | 0 |

## Escola Grande

Arquivo: `exemplos/escola_grande.json` (seed=0, mesma escala e seed documentadas
em `docs/resultados_experimentacao.md`, linha `grande` / seed `0`).

| Métrica | Valor |
|---|---|
| Turmas | 25 (Matutino: 25) |
| Professores | 35 |
| Disciplinas | 12 |
| Salas | 20 |
| Componentes curriculares (turma × disciplina) | 125 |
| Aulas pendentes (tamanho do cromossomo) | 444 |
| Professores com disponibilidade restrita | 13 de 35 |

**Piso teórico** (mínimo de violações inevitável, calculado por `calcular_limites_teoricos`):

| Dimensão | Piso |
|---|---|
| Conflitos de professor | 1 |
| Conflitos de sala | 0 |
| Conflitos de turma | 0 |
| Minutos excedentes de carga horária | 600 |
| Violações de disponibilidade | 8 |

