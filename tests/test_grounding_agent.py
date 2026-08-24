from onimos import OnimoRepository, ContextGroundingAgent


def _repo_com_ambiguidade():
    repo = OnimoRepository()
    repo.add_version("cliente", "quem comprou", {"modulo": "vendas"}, excludes=["revendedores"])
    repo.add_version("cliente", "revendedor autorizado", {"modulo": "parcerias"})
    repo.add_version("cliente", "qualquer pessoa cadastrada", {})  # fallback genérico
    repo.add_version("conta", "conta contábil", {"modulo": "financeiro"})
    repo.add_version("conta", "conta de usuário", {"modulo": "produto"})  # sem fallback
    return repo


def test_resolves_automatically_when_scope_matches():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    r = agent.resolve_term("cliente", {"modulo": "vendas"})
    assert r.status == "resolved"
    assert r.chosen.definition == "quem comprou"


def test_falls_back_to_generic_entry_without_context():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    r = agent.resolve_term("cliente", {})
    assert r.status == "resolved"
    assert r.chosen.definition == "qualquer pessoa cadastrada"


def test_flags_ambiguous_when_no_fallback_exists():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    r = agent.resolve_term("conta", {})
    assert r.status == "ambiguous"
    assert len(r.candidates) == 2


def test_not_in_glossary_for_unregistered_term():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    r = agent.resolve_term("fornecedor", {"modulo": "vendas"})
    assert r.status == "not_in_glossary"


def test_ground_builds_clarification_question_when_ambiguous():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    result = agent.ground("mostre o saldo da conta", {})
    assert result.needs_clarification
    assert "conta" in result.clarification_questions[0]


def test_ground_builds_grounded_context_when_resolved():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    result = agent.ground("mostre o saldo da conta", {"modulo": "financeiro"})
    assert not result.needs_clarification
    assert "conta contábil" in result.grounded_context


def test_audit_sink_receives_one_entry_per_resolved_term():
    agent = ContextGroundingAgent(_repo_com_ambiguidade())
    agent.ground("cliente e conta", {"modulo": "vendas"})
    terms_logged = {e["term"] for e in agent.audit_sink.entries}
    assert "cliente" in terms_logged


def test_matcher_picks_up_terms_added_after_construction():
    repo = _repo_com_ambiguidade()
    agent = ContextGroundingAgent(repo)
    repo.add_version("ciclo", "ciclo de fechamento", {"modulo": "financeiro"})

    result = agent.ground("qual o ciclo atual", {"modulo": "financeiro"})
    assert "ciclo" in result.grounded_context
