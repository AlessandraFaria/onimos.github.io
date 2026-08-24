"""Menor exemplo possível de ponta a ponta: cadastra duas definições
concorrentes pro mesmo termo e mostra o agente resolvendo de acordo com
o contexto que recebe."""
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
