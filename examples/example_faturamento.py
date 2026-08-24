"""Exemplo com uma consulta real de negócio, ambígua em três termos ao
mesmo tempo, mostrando o comportamento do agente em contextos diferentes.

Rodar de dentro do repositório, com o pacote instalado (`pip install -e .`):

    python examples/example_faturamento.py
"""
from pathlib import Path

from onimos import OnimoRepository, ContextGroundingAgent

GLOSSARY_PATH = Path(__file__).parent / "example_glossary.json"

repo = OnimoRepository.from_json_file(str(GLOSSARY_PATH))
# "ciclo" não estava no glossário de exemplo original -- adicionado aqui
# porque é tão ambíguo quanto "cliente" e "ativo" e essa consulta usa os três.
repo.add_version("ciclo", "Período de fechamento contábil, geralmente mensal.", {"modulo": "financeiro"})
repo.add_version("ciclo", "Intervalo entre metas de vendas, geralmente trimestral.", {"modulo": "vendas"})

agent = ContextGroundingAgent(repo)

query = "Calcule o faturamento médio dos clientes ativos no último ciclo"

print("pedido original:")
print(" ", query)
print()
print("termos reconhecidos:", agent._matcher.extract(query))
print()

print("=== módulo financeiro ===")
result_a = agent.ground(query, {"modulo": "financeiro"})
print("precisa esclarecer?", result_a.needs_clarification)
print(result_a.grounded_context)
print()

print("=== módulo vendas ===")
result_b = agent.ground(query, {"modulo": "vendas"})
print("precisa esclarecer?", result_b.needs_clarification)
print(result_b.grounded_context)
print()

print("=== sem contexto de módulo ===")
result_c = agent.ground(query, {})
print("precisa esclarecer?", result_c.needs_clarification)
for q in result_c.clarification_questions:
    print("pergunta:", q)
print("contexto que ainda resolveu mesmo assim:")
print(result_c.grounded_context or "(nada)")
