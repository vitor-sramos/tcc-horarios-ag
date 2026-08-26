from dataclasses import dataclass, field
from datetime import time
from enum import Enum


class DiaSemana(Enum):
    SEGUNDA = "SEGUNDA"
    TERCA = "TERCA"
    QUARTA = "QUARTA"
    QUINTA = "QUINTA"
    SEXTA = "SEXTA"
    SABADO = "SABADO"


@dataclass(frozen=True)
class Turma:
    id: int
    nome: str
    turno: str


@dataclass(frozen=True)
class Professor:
    id: int
    nome: str
    carga_horaria_maxima_minutos: int
    disciplinas_habilitadas: tuple[int, ...] = ()


@dataclass(frozen=True)
class Disciplina:
    id: int
    nome: str


@dataclass(frozen=True)
class Sala:
    id: int
    nome: str


@dataclass(frozen=True)
class ComponenteCurricular:
    """O molde de uma aula: turma + professor + disciplina + sala + quantas vezes/semana."""

    id: int
    turma_id: int
    professor_id: int
    disciplina_id: int
    sala_id: int
    aulas_por_semana: int

    def __post_init__(self) -> None:
        if self.aulas_por_semana <= 0:
            raise ValueError(
                f"aulas_por_semana deve ser positivo (componente {self.id})"
            )


@dataclass(frozen=True)
class Disponibilidade:
    id: int
    professor_id: int
    dia_semana: DiaSemana
    hora_inicio: time
    hora_fim: time


@dataclass(frozen=True)
class SlotHorario:
    """Um horário possível na grade: um dia da semana + um número de aula."""

    id: int
    dia_semana: DiaSemana
    numero_aula: int
    hora_inicio: time
    hora_fim: time
    turno: str


@dataclass(frozen=True)
class AulaPendente:
    """Uma ocorrência individual de um componente curricular, ainda sem slot — 1 gene do cromossomo."""

    componente_id: int
    indice: int


@dataclass
class InstanciaProblema:
    turmas: list[Turma]
    professores: list[Professor]
    disciplinas: list[Disciplina]
    salas: list[Sala]
    componentes: list[ComponenteCurricular]
    disponibilidades: list[Disponibilidade] = field(default_factory=list)
    slots_horario: list[SlotHorario] = field(default_factory=list)

    _turmas_por_id: dict[int, Turma] = field(init=False, repr=False, default_factory=dict)
    _professores_por_id: dict[int, Professor] = field(init=False, repr=False, default_factory=dict)
    _disciplinas_por_id: dict[int, Disciplina] = field(init=False, repr=False, default_factory=dict)
    _salas_por_id: dict[int, Sala] = field(init=False, repr=False, default_factory=dict)
    _componentes_por_id: dict[int, ComponenteCurricular] = field(init=False, repr=False, default_factory=dict)
    _slots_por_id: dict[int, SlotHorario] = field(init=False, repr=False, default_factory=dict)
    _aulas_pendentes: list[AulaPendente] = field(init=False, repr=False, default_factory=list)
    _dominio_por_gene: list[list[int]] = field(init=False, repr=False, default_factory=list)

    def __post_init__(self) -> None:
        self._turmas_por_id = {t.id: t for t in self.turmas}
        self._professores_por_id = {p.id: p for p in self.professores}
        self._disciplinas_por_id = {d.id: d for d in self.disciplinas}
        self._salas_por_id = {s.id: s for s in self.salas}
        self._componentes_por_id = {c.id: c for c in self.componentes}
        self._slots_por_id = {s.id: s for s in self.slots_horario}
        self._aulas_pendentes = [
            AulaPendente(componente_id=c.id, indice=i)
            for c in self.componentes
            for i in range(c.aulas_por_semana)
        ]

        slot_ids_por_turno: dict[str, list[int]] = {}
        for s in self.slots_horario:
            slot_ids_por_turno.setdefault(s.turno, []).append(s.id)
        self._dominio_por_gene = [
            slot_ids_por_turno.get(self.turma(self.componente(p.componente_id).turma_id).turno, [])
            for p in self._aulas_pendentes
        ]

    def turma(self, turma_id: int) -> Turma:
        return self._turmas_por_id[turma_id]

    def professor(self, professor_id: int) -> Professor:
        return self._professores_por_id[professor_id]

    def disciplina(self, disciplina_id: int) -> Disciplina:
        return self._disciplinas_por_id[disciplina_id]

    def sala(self, sala_id: int) -> Sala:
        return self._salas_por_id[sala_id]

    def componente(self, componente_id: int) -> ComponenteCurricular:
        return self._componentes_por_id[componente_id]

    def slot(self, slot_id: int) -> SlotHorario:
        return self._slots_por_id[slot_id]

    def aulas_pendentes(self) -> list[AulaPendente]:
        """Cada componente curricular expandido em N ocorrências — o tamanho do cromossomo."""
        return self._aulas_pendentes

    def dominio_genes(self) -> list[list[int]]:
        """Para cada aula pendente (mesma ordem de aulas_pendentes()), os slot_id válidos —
        restritos ao turno da turma daquele componente."""
        return self._dominio_por_gene

    def validar(self) -> None:
        for c in self.componentes:
            if c.turma_id not in self._turmas_por_id:
                raise ValueError(f"componente {c.id}: turma_id {c.turma_id} inexistente")
            if c.professor_id not in self._professores_por_id:
                raise ValueError(f"componente {c.id}: professor_id {c.professor_id} inexistente")
            if c.disciplina_id not in self._disciplinas_por_id:
                raise ValueError(f"componente {c.id}: disciplina_id {c.disciplina_id} inexistente")
            if c.sala_id not in self._salas_por_id:
                raise ValueError(f"componente {c.id}: sala_id {c.sala_id} inexistente")
        for d in self.disponibilidades:
            if d.professor_id not in self._professores_por_id:
                raise ValueError(f"disponibilidade {d.id}: professor_id {d.professor_id} inexistente")

        turnos_com_slots = {s.turno for s in self.slots_horario}
        for t in self.turmas:
            if t.turno not in turnos_com_slots:
                raise ValueError(f"turma {t.id}: turno {t.turno!r} nao tem nenhum slot_horario correspondente")
