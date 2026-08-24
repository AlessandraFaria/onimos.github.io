import pytest

from onimos import TermMatcher, MAX_TERM_WORDS


def test_extracts_single_word_terms():
    matcher = TermMatcher(["cliente", "ativo"])
    found = matcher.extract("os clientes ativos deste mês")
    assert found == ["ativo", "cliente"]


def test_extracts_multi_word_terms():
    matcher = TermMatcher(["taxa de conversao"])
    found = matcher.extract("preciso da taxa de conversao de ontem")
    assert found == ["taxa de conversao"]


def test_handles_singular_plural_variants():
    matcher = TermMatcher(["cliente"])
    assert matcher.extract("um cliente") == ["cliente"]
    assert matcher.extract("vários clientes") == ["cliente"]


def test_does_not_match_substring_inside_another_word():
    matcher = TermMatcher(["conta"])
    assert matcher.extract("a recontagem foi feita") == []


def test_add_term_is_incremental():
    matcher = TermMatcher(["cliente"])
    assert matcher.extract("novo termo aqui") == []
    matcher.add_term("termo")
    assert matcher.extract("novo termo aqui") == ["termo"]


def test_rejects_term_above_max_words():
    matcher = TermMatcher([])
    long_term = " ".join(f"palavra{i}" for i in range(MAX_TERM_WORDS + 1))
    with pytest.raises(ValueError):
        matcher.add_term(long_term)


def test_first_word_gating_returns_same_result_as_brute_force():
    # o filtro por primeira palavra é uma otimização de desempenho, não
    # deveria mudar o conjunto de termos encontrados -- ver docs/ONIMOS.md §6.4
    terms = ["cliente", "ativo", "cliente ativo", "taxa de conversao"]
    matcher = TermMatcher(terms)
    text = "o cliente ativo teve a melhor taxa de conversao do trimestre"
    assert matcher.extract(text) == sorted({"ativo", "cliente", "cliente ativo", "taxa de conversao"})
