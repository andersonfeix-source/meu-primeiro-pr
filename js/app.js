const STORAGE_KEYS = {
  wardrobe: "montaLook.wardrobe",
  looks: "montaLook.looks",
};

const CATEGORY_LABELS = {
  "parte-de-cima": "Parte de cima",
  "parte-de-baixo": "Parte de baixo",
  vestido: "Vestido",
  casaco: "Casaco / Jaqueta",
  calcado: "Calçado",
  acessorio: "Acessório",
};

const CATEGORY_ICONS = {
  "parte-de-cima": "👕",
  "parte-de-baixo": "👖",
  vestido: "👗",
  casaco: "🧥",
  calcado: "👟",
  acessorio: "👜",
};

const NEUTRAL_COLORS = [
  "branco",
  "off-white",
  "preto",
  "cinza",
  "bege",
  "marrom",
  "jeans",
  "azul marinho",
  "nude",
];

const COMPLEMENTARY_PAIRS = [
  ["azul", "laranja"],
  ["amarelo", "roxo"],
  ["vermelho", "verde"],
  ["rosa", "verde"],
];

let wardrobe = loadFromStorage(STORAGE_KEYS.wardrobe, []);
let savedLooks = loadFromStorage(STORAGE_KEYS.looks, []);
let currentLook = null;

function loadFromStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (err) {
    return fallback;
  }
}

function saveToStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

// ---------- Tabs ----------
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// ---------- Add item ----------
const itemForm = document.getElementById("item-form");
itemForm.addEventListener("submit", (e) => {
  e.preventDefault();

  const name = document.getElementById("item-name").value.trim();
  const category = document.getElementById("item-category").value;
  const color = document.getElementById("item-color").value.trim().toLowerCase();
  const photoInput = document.getElementById("item-photo");
  const file = photoInput.files[0];

  const addItem = (imageDataUrl) => {
    wardrobe.push({
      id: crypto.randomUUID(),
      name,
      category,
      color,
      imageDataUrl: imageDataUrl || null,
    });
    saveToStorage(STORAGE_KEYS.wardrobe, wardrobe);
    renderWardrobe();
    itemForm.reset();
  };

  if (file) {
    const reader = new FileReader();
    reader.onload = () => addItem(reader.result);
    reader.readAsDataURL(file);
  } else {
    addItem(null);
  }
});

function removeItem(id) {
  wardrobe = wardrobe.filter((item) => item.id !== id);
  saveToStorage(STORAGE_KEYS.wardrobe, wardrobe);
  renderWardrobe();
}

function renderWardrobe() {
  const grid = document.getElementById("wardrobe-grid");
  const empty = document.getElementById("wardrobe-empty");
  const count = document.getElementById("item-count");
  count.textContent = wardrobe.length;

  grid.innerHTML = "";
  empty.style.display = wardrobe.length === 0 ? "block" : "none";

  wardrobe.forEach((item) => {
    const card = document.createElement("div");
    card.className = "item-card";
    card.appendChild(buildThumb(item));

    const info = document.createElement("div");
    info.className = "info";
    info.innerHTML = `<strong>${escapeHtml(item.name)}</strong><span>${CATEGORY_LABELS[item.category]} · ${escapeHtml(item.color)}</span>`;
    card.appendChild(info);

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.textContent = "Remover";
    removeBtn.addEventListener("click", () => removeItem(item.id));
    card.appendChild(removeBtn);

    grid.appendChild(card);
  });
}

function buildThumb(item) {
  if (item.imageDataUrl) {
    const img = document.createElement("img");
    img.className = "thumb";
    img.src = item.imageDataUrl;
    img.alt = item.name;
    return img;
  }
  const div = document.createElement("div");
  div.className = "thumb placeholder";
  div.textContent = CATEGORY_ICONS[item.category] || "👚";
  return div;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ---------- Generate look ----------
document.getElementById("generate-btn").addEventListener("click", generateLook);
document.getElementById("save-look-btn").addEventListener("click", saveCurrentLook);

function pickRandom(arr) {
  if (arr.length === 0) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}

function generateLook() {
  const preview = document.getElementById("look-preview");
  const saveBtn = document.getElementById("save-look-btn");

  const byCategory = (cat) => wardrobe.filter((i) => i.category === cat);
  const dresses = byCategory("vestido");
  const tops = byCategory("parte-de-cima");
  const bottoms = byCategory("parte-de-baixo");
  const coats = byCategory("casaco");
  const shoes = byCategory("calcado");
  const accessories = byCategory("acessorio");

  const canUseDress = dresses.length > 0;
  const canUseTopBottom = tops.length > 0 && bottoms.length > 0;

  if (!canUseDress && !canUseTopBottom) {
    preview.innerHTML = `<p class="empty-state">Cadastre pelo menos um vestido, ou uma peça de cima + uma de baixo, para gerar um look.</p>`;
    saveBtn.disabled = true;
    currentLook = null;
    return;
  }

  const useDress = canUseDress && (!canUseTopBottom || Math.random() < 0.5);

  const chosen = [];
  if (useDress) {
    chosen.push(pickRandom(dresses));
  } else {
    chosen.push(pickRandom(tops));
    chosen.push(pickRandom(bottoms));
  }
  if (shoes.length > 0) chosen.push(pickRandom(shoes));
  if (coats.length > 0 && Math.random() < 0.5) chosen.push(pickRandom(coats));
  if (accessories.length > 0 && Math.random() < 0.6) chosen.push(pickRandom(accessories));

  currentLook = chosen.filter(Boolean);
  renderLookPreview(currentLook);
  saveBtn.disabled = false;
}

function evaluateHarmony(items) {
  const colors = items.map((i) => i.color);
  const allNeutral = colors.every((c) => NEUTRAL_COLORS.includes(c));
  if (allNeutral) return { label: "Combinação neutra e versátil", good: true };

  const uniqueColors = new Set(colors);
  if (uniqueColors.size === 1) return { label: "Combinação monocromática", good: true };

  const hasComplementary = COMPLEMENTARY_PAIRS.some(
    ([a, b]) => colors.includes(a) && colors.includes(b)
  );
  if (hasComplementary) return { label: "Combinação com contraste proposital", good: true };

  return { label: "Combinação livre — avalie o resultado", good: false };
}

function renderLookPreview(items) {
  const preview = document.getElementById("look-preview");
  const harmony = evaluateHarmony(items);

  preview.innerHTML = "";

  const tag = document.createElement("span");
  tag.className = `look-tag ${harmony.good ? "harmony-good" : ""}`;
  tag.textContent = harmony.label;
  preview.appendChild(tag);

  const grid = document.createElement("div");
  grid.className = "look-items";

  items.forEach((item) => {
    const slot = document.createElement("div");
    slot.className = "look-slot";
    slot.appendChild(buildThumb(item));
    const small = document.createElement("small");
    small.textContent = `${item.name} (${item.color})`;
    slot.appendChild(small);
    grid.appendChild(slot);
  });

  preview.appendChild(grid);
}

function saveCurrentLook() {
  if (!currentLook) return;
  savedLooks.push({
    id: crypto.randomUUID(),
    itemIds: currentLook.map((i) => i.id),
    createdAt: new Date().toISOString(),
  });
  saveToStorage(STORAGE_KEYS.looks, savedLooks);
  renderSavedLooks();
}

// ---------- Saved looks ----------
function removeSavedLook(id) {
  savedLooks = savedLooks.filter((look) => look.id !== id);
  saveToStorage(STORAGE_KEYS.looks, savedLooks);
  renderSavedLooks();
}

function renderSavedLooks() {
  const grid = document.getElementById("saved-looks-grid");
  const empty = document.getElementById("saved-looks-empty");
  grid.innerHTML = "";
  empty.style.display = savedLooks.length === 0 ? "block" : "none";

  savedLooks.forEach((look) => {
    const items = look.itemIds
      .map((id) => wardrobe.find((i) => i.id === id))
      .filter(Boolean);
    if (items.length === 0) return;

    const card = document.createElement("div");
    card.className = "item-card";

    const mini = document.createElement("div");
    mini.className = "info";
    const date = new Date(look.createdAt).toLocaleDateString("pt-BR");
    mini.innerHTML = `<strong>Look de ${date}</strong><span>${items
      .map((i) => i.name)
      .join(", ")}</span>`;
    card.appendChild(mini);

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.textContent = "Excluir look";
    removeBtn.addEventListener("click", () => removeSavedLook(look.id));
    card.appendChild(removeBtn);

    grid.appendChild(card);
  });
}

// ---------- Init ----------
renderWardrobe();
renderSavedLooks();
