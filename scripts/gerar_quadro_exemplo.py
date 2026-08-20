"""Roda o AG numa instância sintética e salva um quadro de horários renderizado (PNG)."""

from motor_horarios.analise import calcular_limites_teoricos
from motor_horarios.gerador_sintetico import gerar_instancia
from motor_horarios.motor_ga import evoluir
from motor_horarios.visualizacao import salvar_quadro_horarios

CAMINHO_SAIDA = "resultados/quadro_exemplo.png"


def main() -> None:
    instancia = gerar_instancia(seed=42)
    melhor, relatorio, _historico = evoluir(instancia, geracoes=300, tamanho_populacao=60, seed=42)
    piso = calcular_limites_teoricos(instancia)

    print(f"Fitness final: {relatorio.valor}")
    print(f"Conflitos de professor: {relatorio.violacoes_professor} (piso teórico: {piso.minimo_conflitos_professor})")
    print(f"Conflitos de sala: {relatorio.violacoes_sala} (piso teórico: {piso.minimo_conflitos_sala})")
    print(f"Conflitos de turma: {relatorio.violacoes_turma} (piso teórico: {piso.minimo_conflitos_turma})")
    print(
        f"Minutos excedentes de carga horária: {relatorio.minutos_excedentes_carga_horaria} "
        f"(piso teórico: {piso.minimo_minutos_excedentes_carga_horaria})"
    )
    print(
        f"Violações de disponibilidade: {relatorio.violacoes_disponibilidade} "
        f"(piso teórico: {piso.minimo_violacoes_disponibilidade})"
    )

    salvar_quadro_horarios(instancia, melhor, CAMINHO_SAIDA)
    print(f"Quadro de horários salvo em {CAMINHO_SAIDA}")


if __name__ == "__main__":
    main()
