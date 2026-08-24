const DEFINITIONS = {
  vendas: {
    status: "resolvido",
    state: "resolved",
    text: "Pessoa ou empresa que já efetuou pelo menos uma compra. Não inclui revendedores.",
  },
  parcerias: {
    status: "resolvido",
    state: "resolved",
    text: "Revendedor autorizado que compra para revenda, não para consumo final.",
  },
  financeiro: {
    status: "resolvido · fallback genérico",
    state: "resolved",
    text: "Qualquer pessoa ou empresa cadastrada na base, independentemente de ter comprado.",
  },
  "": {
    status: "resolvido · fallback genérico",
    state: "resolved",
    text: "Qualquer pessoa ou empresa cadastrada na base, independentemente de ter comprado.",
  },
};

const chips = document.querySelectorAll(".chip");
const statusEl = document.getElementById("status");
const textEl = document.getElementById("definitionText");

function render(scope, animate) {
  const entry = DEFINITIONS[scope];
  statusEl.textContent = entry.status;
  statusEl.dataset.state = entry.state;
  if (!animate) {
    textEl.textContent = `"${entry.text}"`;
    return;
  }
  textEl.style.opacity = 0;
  window.setTimeout(() => {
    textEl.textContent = `"${entry.text}"`;
    textEl.style.opacity = 1;
  }, 120);
}

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    chips.forEach((c) => c.setAttribute("aria-pressed", "false"));
    chip.setAttribute("aria-pressed", "true");
    render(chip.dataset.scope, true);
  });
});

textEl.style.transition = "opacity 0.15s ease";
render("vendas", false);
