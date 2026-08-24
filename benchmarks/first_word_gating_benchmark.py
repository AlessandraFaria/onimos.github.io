"""Compara extract() com e sem o filtro por primeira palavra (_first_words).
Ver seção 6.4 de ONIMOS.md."""
import time
from onimos.term_matcher import TermMatcher

terms = [f"termo{i}" for i in range(5000)]
terms += ["cliente", "ativo", "ciclo", "conta", "cliente ativo", "taxa de conversao"]
text = "Preciso ver os clientes ativos deste mês pra fechar o relatório de vendas."
n_runs = 30000

m = TermMatcher(terms)
t0 = time.perf_counter()
for _ in range(n_runs):
    m.extract(text)
dt = time.perf_counter() - t0
print(f"com filtro por primeira palavra   {dt * 1000 / n_runs:.5f} ms/extração  ({m.extract(text)})")

# versão sem o filtro, só pra comparação -- monta toda janela sempre
class MatcherSemFiltro(TermMatcher):
    def extract(self, text):
        import re
        words = re.findall(r"\w+", text.lower())
        found = set()
        n = len(words)
        for start in range(n):
            for length in range(1, min(self._max_words, n - start) + 1):
                candidate = " ".join(words[start:start + length])
                canonical = self._variant_to_term.get(candidate)
                if canonical:
                    found.add(canonical)
        return sorted(found)

m2 = MatcherSemFiltro(terms)
t0 = time.perf_counter()
for _ in range(n_runs):
    m2.extract(text)
dt2 = time.perf_counter() - t0
print(f"sem filtro (todas as janelas)     {dt2 * 1000 / n_runs:.5f} ms/extração  ({m2.extract(text)})")
