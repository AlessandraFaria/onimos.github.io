from __future__ import annotations
from typing import Protocol


class AuditSink(Protocol):
    def write(self, entry: dict) -> None: ...


class InMemoryAuditSink:
    """Pra dev/teste. Em produção troca por um producer de fila (Kafka,
    Kinesis) ou logger estruturado -- a interface é só write(entry), o
    agente não precisa saber qual é o destino real."""

    def __init__(self):
        self.entries: list[dict] = []

    def write(self, entry: dict) -> None:
        self.entries.append(entry)
