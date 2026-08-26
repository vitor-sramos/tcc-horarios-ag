from motor_horarios.modelo import DiaSemana, SlotHorario


def serializar_slots(slots: list[SlotHorario]) -> list[dict]:
    """Um slot por dict, com dia_semana e horários convertidos pra string (JSON-safe)."""
    return [
        {
            "id": slot.id,
            "dia_semana": slot.dia_semana.value,
            "numero_aula": slot.numero_aula,
            "hora_inicio": slot.hora_inicio.strftime("%H:%M"),
            "hora_fim": slot.hora_fim.strftime("%H:%M"),
            "turno": slot.turno,
        }
        for slot in slots
    ]


def eixos_ordenados(slots: list[SlotHorario]) -> tuple[list[str], list[int]]:
    """(dias presentes na ordem canônica de DiaSemana, números de aula únicos e ordenados)."""
    ordem_dias = list(DiaSemana)
    dias_presentes = sorted({s.dia_semana for s in slots}, key=ordem_dias.index)
    numeros_presentes = sorted({s.numero_aula for s in slots})
    return [d.value for d in dias_presentes], numeros_presentes
