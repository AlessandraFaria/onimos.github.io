from datetime import datetime, timedelta, timezone

from onimos import OnimoRepository


def test_add_version_creates_first_version():
    repo = OnimoRepository()
    entry = repo.add_version("cliente", "definição inicial", {"modulo": "vendas"})
    assert entry.version == 1
    assert entry.valid_to is None


def test_add_version_closes_previous_and_bumps_version():
    repo = OnimoRepository()
    repo.add_version("ativo", "def v1", {"modulo": "vendas"})
    v2 = repo.add_version("ativo", "def v2", {"modulo": "vendas"})

    candidates = repo.get_candidates("ativo")
    assert len(candidates) == 1
    assert candidates[0].version == 2
    assert candidates[0].definition == "def v2"
    assert v2.version == 2


def test_different_scopes_coexist():
    repo = OnimoRepository()
    repo.add_version("cliente", "def vendas", {"modulo": "vendas"})
    repo.add_version("cliente", "def parcerias", {"modulo": "parcerias"})

    candidates = repo.get_candidates("cliente")
    assert len(candidates) == 2


def test_point_in_time_lookup_returns_definition_valid_at_that_moment():
    repo = OnimoRepository()
    t_old = datetime.now(timezone.utc) - timedelta(days=30)
    repo.add_version("ativo", "90 dias", {"modulo": "vendas"}, as_of=t_old)
    repo.add_version("ativo", "60 dias", {"modulo": "vendas"})

    now = repo.get_candidates("ativo")
    past = repo.get_candidates("ativo", as_of=t_old + timedelta(days=1))

    assert now[0].definition == "60 dias"
    assert past[0].definition == "90 dias"


def test_watermark_increments_on_write():
    repo = OnimoRepository()
    w0 = repo.watermark
    repo.add_version("conta", "def", {"modulo": "financeiro"})
    assert repo.watermark == w0 + 1


def test_unknown_term_returns_empty_candidates():
    repo = OnimoRepository()
    assert repo.get_candidates("termo_inexistente") == []


def test_from_json_file_loads_all_entries(tmp_path):
    import json

    payload = {
        "cliente": [
            {"escopo": {"modulo": "vendas"}, "definicao": "def vendas", "exclui": ["revendedores"]},
            {"escopo": {}, "definicao": "def genérica"},
        ]
    }
    path = tmp_path / "glossario.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    repo = OnimoRepository.from_json_file(str(path))
    candidates = repo.get_candidates("cliente")
    assert len(candidates) == 2
