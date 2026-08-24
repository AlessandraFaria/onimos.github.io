"""Testa se a ordem de inserção dos termos no TermMatcher afeta a leitura.
Hipótese: não deveria, porque lookup em hash set é O(1) independente da
ordem de inserção. Ver seção 6.4 de ONIMOS.md."""
import random
import time
from onimos.term_matcher import TermMatcher

rng = random.Random(7)
terms = [f"termo{i}" for i in range(5000)] + ["cliente", "ativo", "ciclo", "conta"]
text = "Preciso ver os clientes ativos deste mês pra fechar o relatório de vendas."

order_a = list(terms)
rng.shuffle(order_a)
order_b = sorted(terms)
order_c = sorted(terms, key=len, reverse=True)

for label, order in [("original (embaralhada)", order_a), ("alfabética", order_b), ("por tamanho desc", order_c)]:
    m = TermMatcher(order)
    t0 = time.perf_counter()
    for _ in range(20000):
        m.extract(text)
    dt = time.perf_counter() - t0
    print(f"{label:28s}  {dt * 1000 / 20000:.5f} ms/extração")
