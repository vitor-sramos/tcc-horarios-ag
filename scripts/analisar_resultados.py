"""Estatísticas descritivas dos experimentos, para o artigo e para validação com a estatística.

Para cada escala: média, desvio-padrão, IC de 95% (t de Student), mediana e quartis das medidas principais; proporção de
execuções que atingiram o piso, com IC exato de Clopper-Pearson; e, se existir o teste de 1500 gerações, a comparação
pareada (mesma seed) entre 300 e 1500 gerações.

Sem scipy: o valor crítico de t vem de tabela (gl = n - 1) e o IC exato da proporção é calculado por bisseção.

Uso: python3 -m scripts.analisar_resultados
"""

import math
import os

import pandas as pd

RESUMO = "resultados/experimentos_resumo.csv"
SENSIBILIDADE = "resultados/sensibilidade_geracoes_resumo.csv"

# t de Student bicaudal, 95%, por graus de liberdade (suficiente para n = 5, 10, 30)
T_CRITICO = {4: 2.776, 9: 2.262, 29: 2.045}


def _t(n: int) -> float:
    gl = n - 1
    if gl not in T_CRITICO:
        raise ValueError(f"adicionar t crítico para gl={gl}")
    return T_CRITICO[gl]


def ic_media(x: pd.Series) -> tuple[float, float, float]:
    n = len(x)
    media, dp = x.mean(), x.std(ddof=1)
    h = _t(n) * dp / math.sqrt(n)
    return media, media - h, media + h


def _cdf_binomial(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def ic_exato_proporcao(k: int, n: int, alfa: float = 0.05) -> tuple[float, float]:
    """IC exato de Clopper-Pearson (bicaudal), por bisseção na distribuição binomial."""

    def bissecao(f, crescente: bool) -> float:
        """Raiz de f no intervalo [0, 1]; `crescente` diz se f aumenta com p."""
        baixo, alto = 0.0, 1.0
        for _ in range(100):
            meio = (baixo + alto) / 2
            if (f(meio) < 0) == crescente:
                baixo = meio
            else:
                alto = meio
        return (baixo + alto) / 2

    # limite inferior: P(X >= k | p) = alfa/2 (cresce com p); limite superior: P(X <= k | p) = alfa/2 (decresce com p)
    inferior = 0.0 if k == 0 else bissecao(lambda p: (1 - _cdf_binomial(k - 1, n, p)) - alfa / 2, crescente=True)
    superior = 1.0 if k == n else bissecao(lambda p: _cdf_binomial(k, n, p) - alfa / 2, crescente=False)
    return inferior, superior


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["piso_hard"] = df.piso_professor + df.piso_sala + df.piso_turma + df.piso_carga_horaria / 60
    df["hard_obtido"] = df.violacoes_professor + df.violacoes_sala + df.violacoes_turma + df.minutos_excedentes_carga_horaria / 60
    df["excesso_hard"] = df.hard_obtido - df.piso_hard
    df["excesso_disponibilidade"] = df.violacoes_disponibilidade - df.piso_disponibilidade
    df["fitness_acima_piso_hard"] = df.fitness_final - 1000 * df.piso_hard
    return df


MEDIDAS = [
    ("excesso_hard", "excesso hard sobre o piso (unidades)"),
    ("excesso_disponibilidade", "excesso de disponibilidade sobre o piso"),
    ("janelas_turma", "períodos vagos na grade da turma"),
    ("janelas_professor", "períodos vagos na agenda do professor"),
    ("fragmentacao_disciplina", "fragmentação de disciplina"),
    ("distribuicao_semanal_disciplina", "concentração semanal das aulas"),
    ("fitness_acima_piso_hard", "fitness acima do piso hard"),
    ("tempo_execucao_segundos", "tempo de execução (s)"),
]


def descrever(df: pd.DataFrame) -> None:
    for escala in ["pequena", "media", "grande"]:
        g = df[df.escala == escala]
        n = len(g)
        no_piso = int(g.bateu_piso.sum())
        inf, sup = ic_exato_proporcao(no_piso, n)
        print(f"\n== {escala} (n = {n}) ==")
        print(f"atingiram o piso: {no_piso}/{n} = {no_piso / n:.1%}, IC95% exato [{inf:.1%}; {sup:.1%}]")
        hard_no_piso = int((g.excesso_hard.abs() < 1e-9).sum())
        inf, sup = ic_exato_proporcao(hard_no_piso, n)
        print(f"restrições hard no piso: {hard_no_piso}/{n}, IC95% exato [{inf:.1%}; {sup:.1%}]")
        print(f"abaixo do piso (deveria ser 0): hard {int((g.excesso_hard < -1e-9).sum())}, disponibilidade {int((g.excesso_disponibilidade < 0).sum())}")
        for coluna, nome in MEDIDAS:
            x = g[coluna]
            media, lo, hi = ic_media(x)
            q1, q2, q3 = x.quantile([0.25, 0.5, 0.75])
            print(f"  {nome}: média {media:.2f} (IC95% {lo:.2f} a {hi:.2f}), dp {x.std(ddof=1):.2f}, mediana {q2:.2f} [Q1 {q1:.2f}; Q3 {q3:.2f}], min {x.min():.2f}, max {x.max():.2f}")


def comparar_geracoes(base: pd.DataFrame, estendido: pd.DataFrame) -> None:
    print("\n\n== Comparação pareada: 300 contra 1500 gerações (mesma seed) ==")
    for escala in ["media", "grande"]:
        a = base[base.escala == escala].set_index("seed")
        b = estendido[estendido.escala == escala].set_index("seed")
        seeds = sorted(set(a.index) & set(b.index))
        n = len(seeds)
        if n < 2:
            continue
        for coluna, nome in [("fitness_acima_piso_hard", "fitness acima do piso hard"), ("excesso_disponibilidade", "excesso de disponibilidade"), ("janelas_turma", "períodos vagos na turma")]:
            d = (a.loc[seeds, coluna] - b.loc[seeds, coluna])  # positivo = melhorou com 1500
            media, lo, hi = ic_media(d)
            melhoraram = int((d > 0).sum())
            iguais = int((d == 0).sum())
            reducao = 100 * d.mean() / a.loc[seeds, coluna].mean()
            print(f"{escala} / {nome}: redução média {media:.2f} (IC95% {lo:.2f} a {hi:.2f}), {reducao:.1f}% da média de 300 gerações; melhoraram {melhoraram}/{n}, iguais {iguais}")
        no_piso_300 = int(a.loc[seeds, "bateu_piso"].sum())
        no_piso_1500 = int(b.loc[seeds, "bateu_piso"].sum())
        print(f"{escala}: atingiram o piso em 300 gerações {no_piso_300}/{n}; em 1500 gerações {no_piso_1500}/{n}")


def main() -> None:
    base = preparar(pd.read_csv(RESUMO))
    descrever(base)
    if os.path.exists(SENSIBILIDADE):
        comparar_geracoes(base, preparar(pd.read_csv(SENSIBILIDADE)))


if __name__ == "__main__":
    main()
