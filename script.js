// --- widget interativo (seção "experimente") ---

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
    textEl.textContent = '"' + entry.text + '"';
    return;
  }
  textEl.style.opacity = 0;
  window.setTimeout(function () {
    textEl.textContent = '"' + entry.text + '"';
    textEl.style.opacity = 1;
  }, 120);
}

if (chips.length) {
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      chips.forEach(function (c) { c.setAttribute("aria-pressed", "false"); });
      chip.setAttribute("aria-pressed", "true");
      render(chip.dataset.scope, true);
    });
  });
  textEl.style.transition = "opacity 0.15s ease";
  render("vendas", false);
}

// --- sidebar mobile ---

const sidebar = document.getElementById("sidebar");
const toggle = document.getElementById("sidebarToggle");

if (toggle) {
  toggle.addEventListener("click", function () {
    const isOpen = sidebar.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  document.querySelectorAll(".sidebar__nav a").forEach(function (link) {
    link.addEventListener("click", function () {
      sidebar.classList.remove("open");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

// --- destaque do link ativo no sumário, por seção visível ---

const sections = document.querySelectorAll(".doc-section[id]");
const navLinks = document.querySelectorAll(".sidebar__nav a");

if ("IntersectionObserver" in window && sections.length) {
  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        const id = entry.target.getAttribute("id");
        navLinks.forEach(function (link) {
          link.classList.toggle("active", link.getAttribute("href") === "#" + id);
        });
      });
    },
    { rootMargin: "-10% 0px -70% 0px" }
  );
  sections.forEach(function (section) { observer.observe(section); });
}

// --- mermaid ---

if (window.mermaid) {
  mermaid.initialize({
    startOnLoad: true,
    theme: "base",
    fontFamily: "IBM Plex Mono, monospace",
    themeVariables: {
      background: "#f6f5f2",
      primaryColor: "#eeece6",
      primaryTextColor: "#5f2736",
      primaryBorderColor: "#5f2736",
      lineColor: "#5f2736",
      secondaryColor: "#98b1c8",
      tertiaryColor: "#f6f5f2",
      fontSize: "14px",
    },
  });
}
