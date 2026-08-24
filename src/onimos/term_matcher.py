from __future__ import annotations
import re

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
MAX_TERM_WORDS = 6  # termo de glossário mais longo que isso provavelmente é frase, não termo


class TermMatcher:
    """
    Extrai termos do glossário comparando janelas de palavras consecutivas
    do texto contra um hash set de termos conhecidos. Tokeniza o texto em
    palavras (O(tamanho do texto)) e, pra cada posição, testa janelas de
    1 até MAX_TERM_WORDS palavras contra o set -- cada teste é um hash
    lookup O(1), então o custo total continua independente do tamanho do
    vocabulário, igual valia pro automaton Aho-Corasick da versão anterior.

    A diferença prática está na atualização: um dict/set em Python cresce
    incrementalmente sem custo (add_term é O(1)), enquanto reconstruir os
    fail-links do automaton exige percorrer o vocabulário inteiro de novo.
    Num repositório que recebe termo novo com frequência, isso importa mais
    do que a diferença de velocidade na leitura -- ver benchmark em demo.py.

    Ordenar a lista de termos antes de inserir não muda nada aqui -- lookup
    em hash set é O(1) independente da ordem de inserção, medido e
    confirmado (ver bench_order.py). O que ganha desempenho de verdade é
    indexar por primeira palavra: _first_words guarda só as palavras que
    iniciam algum termo de mais de uma palavra, e extract() só monta
    janela de 2+ palavras quando a palavra atual está nesse conjunto. Como
    a maioria das palavras de um texto não inicia termo composto nenhum,
    isso evita montar e testar janela que quase nunca vai bater -- medido
    ~3x mais rápido que testar todas as janelas incondicionalmente, com o
    mesmo resultado (ver bench_gating.py).
    """

    def __init__(self, terms: list[str]):
        self._variant_to_term: dict[str, str] = {}
        self._first_words: set[str] = set()
        self._max_words = 1
        for term in terms:
            self.add_term(term)

    def add_term(self, term: str) -> None:
        canonical = term.lower()
        for variant in self._variants(canonical):
            words = variant.split()
            if len(words) > MAX_TERM_WORDS:
                raise ValueError(
                    f"termo '{variant}' tem {len(words)} palavras, acima do limite "
                    f"de {MAX_TERM_WORDS}. Aumente MAX_TERM_WORDS se isso for esperado."
                )
            self._variant_to_term[variant] = canonical
            self._max_words = max(self._max_words, len(words))
            if len(words) > 1:
                self._first_words.add(words[0])

    @staticmethod
    def _variants(term: str) -> set[str]:
        return {term, term[:-1] if term.endswith("s") else term + "s"}

    def extract(self, text: str) -> list[str]:
        words = _TOKEN_RE.findall(text.lower())
        found = set()
        n = len(words)
        for start in range(n):
            # janela de 1 palavra sempre testada -- é o caso mais comum
            canonical = self._variant_to_term.get(words[start])
            if canonical:
                found.add(canonical)
            # janela de 2+ só é montada se a palavra atual é conhecida
            # como início de algum termo composto -- corta a esmagadora
            # maioria das checagens que não iam bater mesmo
            if words[start] not in self._first_words:
                continue
            limit = min(self._max_words, n - start)
            for length in range(2, limit + 1):
                candidate = " ".join(words[start:start + length])
                canonical = self._variant_to_term.get(candidate)
                if canonical:
                    found.add(canonical)
        return sorted(found)
