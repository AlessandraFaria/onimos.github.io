# onimos

Camada de resolução de ambiguidade de termos de negócio, pensada pra rodar antes de um agente de IA executar uma tarefa. Resolve o que um termo como "cliente" ou "ativo" significa no contexto de um pedido específico, em vez de deixar o agente assumir o significado mais comum e errar silenciosamente nos outros casos.

## O problema que isso resolve

Um agente que recebe "liste os clientes ativos" e aplica a tarefa direto, sem checar o contexto, está assumindo que "cliente" e "ativo" têm um significado único no sistema. Na prática, quase nunca têm. "Cliente" no módulo de vendas é quem já comprou; no módulo de parcerias pode ser o revendedor que compra pra revender, não pra consumir. "Ativo" no financeiro é um contrato não cancelado; em vendas é quem comprou nos últimos 90 dias. Um agente que resolve isso sempre do mesmo jeito acerta na maioria dos casos e erra sem avisar nos outros — e esse é o pior tipo de erro, porque ninguém percebe até o número sair errado em algum relatório.

O onimos trata cada termo ambíguo como teria que ser tratado: com várias definições possíveis, cada uma marcada com o contexto em que se aplica, e uma regra explícita pra quando é seguro resolver sozinho e quando é melhor perguntar.

## Instalação

Ainda não publicado no PyPI. Instala direto do repositório:

```bash
git clone <url-do-repositorio>
cd onimos
pip install -e ".[dev]"
```

Sem dependências externas em runtime — só biblioteca padrão do Python 3.10+. `pytest` entra só como dependência de desenvolvimento.

## Uso rápido

```python
from onimos import OnimoRepository, ContextGroundingAgent

repo = OnimoRepository()
repo.add_version(
    "cliente",
    "Pessoa ou empresa que já efetuou pelo menos uma compra.",
    scope={"modulo": "vendas"},
    excludes=["revendedores"],
)
repo.add_version(
    "cliente",
    "Revendedor autorizado que compra para revenda, não para consumo final.",
    scope={"modulo": "parcerias"},
)

agent = ContextGroundingAgent(repo)
result = agent.ground("liste todos os clientes", context_signals={"modulo": "parcerias"})

print(result.grounded_context)
# Definições de termos aplicáveis a este contexto ({'modulo': 'parcerias'}):
# - 'cliente': Revendedor autorizado que compra para revenda, não para consumo final.
```

Se o contexto não for suficiente pra decidir entre duas definições concorrentes, `result.needs_clarification` vem `True` e `result.clarification_questions` traz a pergunta pronta pra devolver ao usuário, em vez do agente adivinhar. Mais exemplos em [`examples/`](examples/).

## Como funciona, resumido

- **`OnimoRepository`** guarda as definições, uma ou mais por termo, cada uma com um escopo (`{"modulo": "vendas"}`, por exemplo). Nunca sobrescreve: atualizar uma definição fecha a versão anterior e abre uma nova, o que permite consultar qual definição estava vigente numa data passada — importante pra qualquer log de auditoria não ficar inconsistente quando a definição de negócio muda.
- **`TermMatcher`** extrai, do texto de um pedido, quais termos cadastrados aparecem nele. Roda em cima de um hash set com uma janela de palavras, não de um automaton — mais simples de manter e, principalmente, atualiza em O(1) por termo novo, sem precisar reconstruir nada.
- **`TTLCache`** fica na frente do repositório fazendo o papel de leitura rápida (a analogia é com o online store de um feature store); consulta ponto-no-tempo pra auditoria vai direto no repositório, sem passar pelo cache.
- **`ContextGroundingAgent`** junta tudo: extrai os termos do pedido, resolve cada um contra o contexto disponível, e devolve um texto pronto pra anexar no prompt de quem for executar a tarefa — ou uma pergunta de esclarecimento, quando o contexto não é suficiente pra decidir sozinho.

A documentação completa — estrutura de dados, os três algoritmos de extração testados até chegar no atual (com números de benchmark), e um caso de uso resolvido passo a passo — está em [`docs/ONIMOS.md`](docs/ONIMOS.md).

## Estrutura do repositório

```
src/onimos/          pacote principal
examples/            exemplos prontos pra rodar
benchmarks/          scripts de medição citados em docs/ONIMOS.md
tests/               suíte pytest
docs/                documentação de arquitetura
```

## Rodando os testes

```bash
make test
# ou: pytest -q
```

## Benchmarks

```bash
make bench
```

Roda os três scripts em `benchmarks/`: comparação entre regex por termo, automaton Aho-Corasick e o hash set atual (leitura e escrita), e o teste do filtro por primeira palavra. Os números medidos, junto com a explicação de por que cada implementação foi trocada pela seguinte, estão em `docs/ONIMOS.md`, seção 6.

## Limitações conhecidas

- `OnimoRepository` guarda tudo em memória — não sobrevive a um restart nem é compartilhado entre processos. Pra produção de verdade, precisa virar uma tabela versionada num banco relacional; a interface (`get_candidates`, `add_version`) foi desenhada pra não mudar quando isso acontecer.
- O cache é local a cada processo. Com múltiplas instâncias do agente rodando, cada uma mantém seu próprio TTL — aceitável enquanto o TTL for curto, mas exigiria um cache compartilhado (Redis, por exemplo) se a leitura precisar ser idêntica entre instâncias.
- A extração de termo só reconhece o que já está cadastrado no repositório. Um termo novo, fora do glossário, não é detectado — não há NER nem chamada a modelo de linguagem envolvida nessa etapa hoje.
- Ambiguidade é resolvida por correspondência de escopo, não por uma hierarquia de sentidos. Não existe hoje uma relação estruturada entre onimos (é-um, exclui, sinônimo); `excludes` é só uma lista de texto solta, não uma referência a outra entrada cadastrada.

## Licença

MIT — ver [`LICENSE`](LICENSE).
