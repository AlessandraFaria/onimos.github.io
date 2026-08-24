import random
import re
import string
import time
from collections import deque
from datetime import datetime, timezone, timedelta

from onimos.repository import OnimoRepository
from onimos.grounding_agent import ContextGroundingAgent
from onimos.term_matcher import TermMatcher


def naive_extract(text: str, terms: list[str]) -> list[str]:
    # abordagem original: um regex por termo do glossário, custo O(vocabulário)
    text_lower = text.lower()
    found = []
    for term in terms:
        variants = {term, term[:-1] if term.endswith("s") else term + "s"}
        for v in variants:
            if re.search(r"\b" + re.escape(v) + r"\b", text_lower):
                found.append(term)
                break
    return found


# implementação do Aho-Corasick só pra comparação neste benchmark -- a
# versão em produção trocou isso pelo hash set em term_matcher.py
class _Node:
    __slots__ = ("children", "fail", "output")

    def __init__(self):
        self.children = {}
        self.fail = None
        self.output = []


class _AhoCorasickForBenchmark:
    def __init__(self, terms):
        self.root = _Node()
        for term in terms:
            for variant in ({term, term[:-1] if term.endswith("s") else term + "s"}):
                self.add(variant, term)
        self.build()

    def add(self, pattern, canonical):
        node = self.root
        for ch in pattern:
            node = node.children.setdefault(ch, _Node())
        node.output.append(canonical)

    def build(self):
        self.root.fail = self.root
        queue = deque()
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)
        while queue:
            current = queue.popleft()
            for ch, child in current.children.items():
                queue.append(child)
                fail = current.fail
                while fail is not self.root and ch not in fail.children:
                    fail = fail.fail
                child.fail = fail.children.get(ch, self.root)
                if child.fail is child:
                    child.fail = self.root
                child.output = child.output + child.fail.output

    def extract(self, text):
        node = self.root
        found = set()
        for ch in text.lower():
            while node is not self.root and ch not in node.children:
                node = node.fail
            node = node.children.get(ch, self.root)
            found.update(node.output)
        return sorted(found)


def make_synthetic_repository(n_terms: int) -> OnimoRepository:
    repo = OnimoRepository()
    repo.add_version("cliente", "Pessoa ou empresa que já efetuou pelo menos uma compra.",
                      {"modulo": "vendas"}, excludes=["revendedores"])
    repo.add_version("cliente", "Revendedor autorizado que compra para revenda.",
                      {"modulo": "parcerias"})
    repo.add_version("ativo", "Cliente que fez ao menos uma compra nos últimos 90 dias.",
                      {"modulo": "vendas"})
    rng = random.Random(42)
    for i in range(n_terms):
        term = "termo" + "".join(rng.choices(string.ascii_lowercase, k=8)) + str(i)
        repo.add_version(term, f"definição sintética {i}", {"modulo": "vendas"})
    return repo


def benchmark_extraction():
    repo = make_synthetic_repository(5000)
    terms = repo.all_terms()
    text = "Preciso ver os clientes ativos deste mês pra fechar o relatório de vendas."

    naive_runs = 20
    t0 = time.perf_counter()
    for _ in range(naive_runs):
        naive_extract(text, terms)
    naive_per_run = (time.perf_counter() - t0) / naive_runs

    fast_runs = 5000  # regex-por-termo é lento demais pra rodar esse tanto

    ac = _AhoCorasickForBenchmark(terms)  # construção fora do laço, custo único
    t0 = time.perf_counter()
    for _ in range(fast_runs):
        ac.extract(text)
    ac_per_run = (time.perf_counter() - t0) / fast_runs

    hashm = TermMatcher(terms)
    t0 = time.perf_counter()
    for _ in range(fast_runs):
        hashm.extract(text)
    hash_per_run = (time.perf_counter() - t0) / fast_runs

    print(f"leitura: glossário com {len(terms)} termos, tempo médio por extração")
    print(f"  regex por termo (original):   {naive_per_run * 1000:.4f} ms  ({naive_runs} execuções)")
    print(f"  aho-corasick (char a char):   {ac_per_run * 1000:.4f} ms  ({fast_runs} execuções)")
    print(f"  hash set (palavra a palavra): {hash_per_run * 1000:.4f} ms  ({fast_runs} execuções)")
    print()


def benchmark_incremental_update():
    terms = [f"termo{i}" for i in range(5000)]
    n_new_terms = 50

    t0 = time.perf_counter()
    ac = _AhoCorasickForBenchmark(terms)
    for i in range(n_new_terms):
        ac.add(f"novo{i}", f"novo{i}")
        ac.build()  # fail-links dependem do vocabulário inteiro, precisa refazer tudo
    ac_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    hashm = TermMatcher(terms)
    for i in range(n_new_terms):
        hashm.add_term(f"novo{i}")  # O(1), sem tocar no resto do vocabulário
    hash_time = time.perf_counter() - t0

    print(f"escrita: adicionar {n_new_terms} termos um de cada vez, glossário já com {len(terms)}")
    print(f"  aho-corasick (rebuild a cada termo novo): {ac_time:.4f}s")
    print(f"  hash set (add_term incremental):          {hash_time:.4f}s")
    print()


def point_in_time_demo():
    repo = OnimoRepository()
    t_old = datetime.now(timezone.utc) - timedelta(days=30)
    repo.add_version("ativo", "Cliente que comprou nos últimos 90 dias.", {"modulo": "vendas"}, as_of=t_old)
    # 30 dias depois o time redefine a métrica pra uma janela mais curta
    repo.add_version("ativo", "Cliente que comprou nos últimos 60 dias.", {"modulo": "vendas"})

    agent = ContextGroundingAgent(repo)

    now_result = agent.resolve_term("ativo", {"modulo": "vendas"})
    old_result = agent.resolve_term("ativo", {"modulo": "vendas"}, as_of=t_old + timedelta(days=1))

    print("definição vigente agora:", now_result.chosen.definition)
    print("definição vigente há 29 dias, pra reconstituir um log antigo:", old_result.chosen.definition)
    print()


def main():
    benchmark_extraction()
    benchmark_incremental_update()
    point_in_time_demo()

    repo = make_synthetic_repository(200)
    agent = ContextGroundingAgent(repo)

    print("resolução com cache")
    r1 = agent.resolve_term("cliente", {"modulo": "vendas"})
    print(r1.status, "-", r1.chosen.definition)
    agent.resolve_term("cliente", {"modulo": "vendas"})  # deve vir do cache
    print("cache hits:", agent.cache.hits, "misses:", agent.cache.misses)
    print()

    print("ground_many processando um lote")
    batch = [
        ("Liste os clientes ativos", {"modulo": "vendas"}),
        ("Quais clientes esse revendedor atende?", {"modulo": "parcerias"}),
    ]
    for result in agent.ground_many(batch):
        print(result.query, "->", result.grounded_context or "(sem termo resolvido)")


if __name__ == "__main__":
    main()
