# Changelog

## 0.1.0

- Primeira versão pública: `OnimoRepository` versionado com correção ponto-no-tempo, `TermMatcher` baseado em hash set com filtro por primeira palavra, `TTLCache` como camada online, `ContextGroundingAgent` orquestrando o pipeline completo.
- Extração de termo passou por três implementações antes desta: regex por termo (O(vocabulário)), automaton Aho-Corasick, e o hash set atual — ver `docs/ONIMOS.md` §6 para a comparação com números.
