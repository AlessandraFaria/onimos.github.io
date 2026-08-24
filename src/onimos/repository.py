from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
import json
import threading


@dataclass
class OnimoEntry:
    id: str
    term: str
    definition: str
    scope: dict[str, str]
    excludes: list[str]
    version: int
    valid_from: datetime
    valid_to: datetime | None = None

    def is_current_at(self, as_of: datetime) -> bool:
        return self.valid_from <= as_of and (self.valid_to is None or as_of < self.valid_to)


class OnimoRepository:
    """
    Fonte de verdade das definições -- em produção isso é uma tabela versionada
    (Postgres, BigQuery), não um dict em memória. Escrita nunca sobrescreve:
    fecha a versão anterior (valid_to) e abre uma nova. É isso que garante
    correção ponto-no-tempo -- um log de auditoria de seis meses atrás aponta
    pro ID da versão vigente naquela data, não pro estado atual da definição.

    Implementação aqui é em memória, pra dev e teste. Trocar por Postgres é
    reimplementar get_candidates/add_version com queries reais; o resto do
    pipeline (matcher, cache, agente) não muda porque só depende dessa
    interface.
    """

    def __init__(self):
        self._by_term: dict[str, list[OnimoEntry]] = {}
        self._lock = threading.RLock()
        self._watermark = 0  # incrementa a cada escrita, sinaliza pro agente que o automaton está desatualizado

    def all_terms(self) -> list[str]:
        with self._lock:
            return list(self._by_term.keys())

    @property
    def watermark(self) -> int:
        return self._watermark

    def get_candidates(self, term: str, as_of: datetime | None = None) -> list[OnimoEntry]:
        as_of = as_of or datetime.now(timezone.utc)
        with self._lock:
            entries = self._by_term.get(term.lower(), [])
            return [e for e in entries if e.is_current_at(as_of)]

    def add_version(
        self, term: str, definition: str, scope: dict, excludes: list[str] | None = None,
        as_of: datetime | None = None,
    ) -> OnimoEntry:
        as_of = as_of or datetime.now(timezone.utc)
        term = term.lower()
        excludes = excludes or []
        with self._lock:
            existing = self._by_term.setdefault(term, [])
            same_scope = [e for e in existing if e.scope == scope and e.valid_to is None]
            next_version = 1
            for e in same_scope:
                e.valid_to = as_of
                next_version = e.version + 1
            entry = OnimoEntry(
                id=uuid4().hex[:12], term=term, definition=definition, scope=scope,
                excludes=excludes, version=next_version, valid_from=as_of, valid_to=None,
            )
            existing.append(entry)
            self._watermark += 1
            return entry

    @classmethod
    def from_json_file(cls, path: str) -> "OnimoRepository":
        repo = cls()
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        baseline = datetime.now(timezone.utc)
        for term, candidates in raw.items():
            for c in candidates:
                repo.add_version(
                    term=term, definition=c["definicao"], scope=c.get("escopo", {}),
                    excludes=c.get("exclui", []), as_of=baseline,
                )
        return repo
