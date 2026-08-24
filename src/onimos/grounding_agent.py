from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .repository import OnimoRepository, OnimoEntry
from .term_matcher import TermMatcher
from .cache import TTLCache
from .audit import AuditSink, InMemoryAuditSink


@dataclass
class TermResolution:
    term: str
    status: str  # resolved | ambiguous | not_in_glossary
    chosen: OnimoEntry | None = None
    candidates: list[OnimoEntry] = field(default_factory=list)
    reason: str = ""


@dataclass
class GroundingResult:
    query: str
    context_signals: dict[str, str]
    resolutions: list[TermResolution]
    grounded_context: str
    needs_clarification: bool
    clarification_questions: list[str]


class ContextGroundingAgent:
    def __init__(
        self, repository: OnimoRepository, cache: TTLCache | None = None,
        audit_sink: AuditSink | None = None,
    ):
        self.repository = repository
        self.cache = cache or TTLCache()
        self.audit_sink = audit_sink or InMemoryAuditSink()
        self._matcher: TermMatcher | None = None
        self._known_terms: set[str] = set()
        self._matcher_watermark = -1
        self._ensure_matcher()

    def _ensure_matcher(self) -> None:
        if self._matcher is None:
            self._matcher = TermMatcher(self.repository.all_terms())
            self._known_terms = set(self.repository.all_terms())
            self._matcher_watermark = self.repository.watermark
            return
        if self._matcher_watermark == self.repository.watermark:
            return
        # o watermark mudou, mas com hash set não precisa reconstruir tudo --
        # só os termos que apareceram desde a última checagem entram, cada
        # um em O(1). Isso é o que o automaton Aho-Corasick não permitia:
        # lá, termo novo forçava recomputar os fail-links do vocabulário
        # inteiro de novo.
        current_terms = set(self.repository.all_terms())
        for term in current_terms - self._known_terms:
            self._matcher.add_term(term)
        self._known_terms = current_terms
        self._matcher_watermark = self.repository.watermark

    def _get_candidates(self, term: str, as_of: datetime | None) -> list[OnimoEntry]:
        if as_of is not None:
            return self.repository.get_candidates(term, as_of=as_of)
        cached = self.cache.get(term)
        if cached is not None:
            return cached
        candidates = self.repository.get_candidates(term)
        self.cache.set(term, candidates)
        return candidates

    @staticmethod
    def _match_score(entry: OnimoEntry, context_signals: dict) -> int | None:
        score = 0
        for key, value in entry.scope.items():
            if key not in context_signals or context_signals[key] != value:
                return None
            score += 1
        return score

    def resolve_term(self, term: str, context_signals: dict, as_of: datetime | None = None) -> TermResolution:
        candidates = self._get_candidates(term, as_of)
        if not candidates:
            return TermResolution(
                term=term, status="not_in_glossary",
                reason="Termo não cadastrado no registro de onimos.",
            )

        scored = [(s, e) for e in candidates if (s := self._match_score(e, context_signals)) is not None]

        if not scored:
            return TermResolution(
                term=term, status="ambiguous", candidates=candidates,
                reason="Nenhuma definição bate com o contexto atual.",
            )

        max_score = max(s for s, _ in scored)
        best = [e for s, e in scored if s == max_score]

        if len(best) == 1:
            return TermResolution(
                term=term, status="resolved", chosen=best[0], candidates=[best[0]],
                reason=f"Escopo mais específico compatível (chaves casadas: {max_score}).",
            )

        return TermResolution(
            term=term, status="ambiguous", candidates=best,
            reason="Duas ou mais definições empatam em especificidade.",
        )

    def build_clarification_question(self, resolution: TermResolution) -> str:
        options = "; ".join(f"({i + 1}) {c.definition}" for i, c in enumerate(resolution.candidates))
        return (
            f"O termo '{resolution.term}' tem mais de um significado possível "
            f"neste contexto. Qual se aplica? {options}"
        )

    def ground(self, query: str, context_signals: dict, as_of: datetime | None = None) -> GroundingResult:
        self._ensure_matcher()
        terms = self._matcher.extract(query)
        resolutions = [self.resolve_term(t, context_signals, as_of) for t in terms]

        clarification_questions = []
        grounded_lines = []

        for r in resolutions:
            self.audit_sink.write({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "term": r.term,
                "status": r.status,
                "context_signals": context_signals,
                "chosen_entry_id": r.chosen.id if r.chosen else None,
                "chosen_version": r.chosen.version if r.chosen else None,
                "reason": r.reason,
            })

            if r.status == "resolved":
                line = f"- '{r.term}': {r.chosen.definition}"
                if r.chosen.excludes:
                    line += f" (não inclui: {', '.join(r.chosen.excludes)})"
                grounded_lines.append(line)
            elif r.status == "ambiguous":
                clarification_questions.append(self.build_clarification_question(r))

        grounded_context = (
            f"Definições de termos aplicáveis a este contexto ({context_signals}):\n" + "\n".join(grounded_lines)
            if grounded_lines else ""
        )

        return GroundingResult(
            query=query, context_signals=context_signals, resolutions=resolutions,
            grounded_context=grounded_context,
            needs_clarification=len(clarification_questions) > 0,
            clarification_questions=clarification_questions,
        )

    def ground_many(self, queries: list[tuple[str, dict]], as_of: datetime | None = None) -> list[GroundingResult]:
        # caminho usado por um pipeline batch (ex: reprocessar um dia de
        # tickets) -- reaproveita o mesmo automaton e o cache já aquecido
        # em vez de reconstruir tudo pra cada item
        self._ensure_matcher()
        return [self.ground(q, ctx, as_of) for q, ctx in queries]
