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
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (err) {
    console.error(`Falha ao salvar "${key}" no armazenamento do navegador:`, err);
    return false;
  }
}

function showToast(message, type = "info", duration = 6000) {
  const container = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

const STORAGE_FULL_MESSAGE =
  "Isso ficou salvo só nesta sessão — o armazenamento do navegador encheu (fotos ocupam espaço). Remova alguma foto antiga em Meu Guarda-roupa ou Looks Salvos para liberar espaço.";

async function fileToCompressedDataUrl(file, maxDim = 900, quality = 0.82) {
  const rawDataUrl = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
  const img = await loadImage(rawDataUrl);
  const scale = Math.min(1, maxDim / Math.max(img.naturalWidth, img.naturalHeight));
  const w = Math.max(1, Math.round(img.naturalWidth * scale));
  const h = Math.max(1, Math.round(img.naturalHeight * scale));
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  canvas.getContext("2d").drawImage(img, 0, 0, w, h);
  return canvas.toDataURL("image/jpeg", quality);
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
itemForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = document.getElementById("item-name").value.trim();
  const category = document.getElementById("item-category").value;
  const color = document.getElementById("item-color").value.trim().toLowerCase();
  const file = document.getElementById("item-photo").files[0];

  let imageDataUrl = null;
  if (file) {
    try {
      imageDataUrl = await fileToCompressedDataUrl(file);
    } catch (err) {
      showToast("Não consegui processar essa foto. Tente outra imagem.", "error");
      return;
    }
  }

  wardrobe.push({
    id: crypto.randomUUID(),
    name,
    category,
    color,
    imageDataUrl,
  });

  const saved = saveToStorage(STORAGE_KEYS.wardrobe, wardrobe);
  renderWardrobe();
  itemForm.reset();
  if (!saved) showToast(STORAGE_FULL_MESSAGE, "error");
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
document.getElementById("save-look-btn").addEventListener("click", () => saveCurrentLook());

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
    tryonToggleBtn.disabled = true;
    tryonEditor.hidden = true;
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

  tryonToggleBtn.disabled = false;
  tryonEditor.hidden = true;
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

function saveCurrentLook(compositeImage) {
  if (!currentLook) return;
  savedLooks.push({
    id: crypto.randomUUID(),
    itemIds: currentLook.map((i) => i.id),
    createdAt: new Date().toISOString(),
    compositeImage: compositeImage || null,
  });
  const saved = saveToStorage(STORAGE_KEYS.looks, savedLooks);
  renderSavedLooks();
  if (!saved) showToast(STORAGE_FULL_MESSAGE, "error");
  else showToast("Look salvo!", "success");
}

// ---------- Provador virtual ----------
const TRYON_CANVAS_W = 800;
const TRYON_CANVAS_H = 1067;

let tryonState = {
  backgroundDataUrl: null,
  stickers: [], // { id, itemId, x, y, w, h, z }
  lookSignature: null,
};
let tryonNextZ = 1;

const tryonToggleBtn = document.getElementById("tryon-toggle-btn");
const tryonEditor = document.getElementById("tryon-editor");
const tryonStage = document.getElementById("tryon-stage");
const tryonStageEmpty = document.getElementById("tryon-stage-empty");
const tryonPhotoInput = document.getElementById("tryon-photo-input");
const tryonResetBtn = document.getElementById("tryon-reset-btn");
const tryonExportBtn = document.getElementById("tryon-export-btn");
const tryonSaveLookBtn = document.getElementById("tryon-save-look-btn");

tryonToggleBtn.addEventListener("click", () => {
  if (!currentLook) return;
  const signature = currentLook.map((i) => i.id).join(",");
  if (tryonState.lookSignature !== signature) {
    tryonState.stickers = buildDefaultStickers(currentLook);
    tryonState.lookSignature = signature;
  }
  tryonEditor.hidden = !tryonEditor.hidden;
  if (!tryonEditor.hidden) renderTryonStage();
});

tryonResetBtn.addEventListener("click", () => {
  if (!currentLook) return;
  tryonState.stickers = buildDefaultStickers(currentLook);
  renderTryonStage();
});

tryonPhotoInput.addEventListener("change", async () => {
  const file = tryonPhotoInput.files[0];
  if (!file) return;
  try {
    tryonState.backgroundDataUrl = await fileToCompressedDataUrl(file, 1200, 0.85);
    renderTryonStage();
  } catch (err) {
    showToast("Não consegui processar essa foto. Tente outra imagem.", "error");
  }
});

function buildDefaultStickers(items) {
  tryonNextZ = 1;
  return items.map((item, index) => ({
    id: crypto.randomUUID(),
    itemId: item.id,
    x: 20 + (index % 2) * 130,
    y: 20 + Math.floor(index / 2) * 150,
    w: 120,
    h: 120,
    z: tryonNextZ++,
  }));
}

function getStickerImageSrc(item) {
  return item.imageDataUrl || generatePlaceholderDataUrl(item);
}

function generatePlaceholderDataUrl(item) {
  const canvas = document.createElement("canvas");
  canvas.width = 240;
  canvas.height = 240;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#f1e6db";
  ctx.fillRect(0, 0, 240, 240);
  ctx.font = "90px sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(CATEGORY_ICONS[item.category] || "👚", 120, 105);
  ctx.font = "16px sans-serif";
  ctx.fillStyle = "#8a7f78";
  ctx.fillText(item.name.slice(0, 16), 120, 190);
  return canvas.toDataURL("image/png");
}

function renderTryonStage() {
  tryonStage.innerHTML = "";

  if (!tryonState.backgroundDataUrl) {
    tryonStage.appendChild(tryonStageEmpty);
    tryonResetBtn.disabled = true;
    tryonExportBtn.disabled = true;
    tryonSaveLookBtn.disabled = true;
    return;
  }

  const bg = document.createElement("img");
  bg.className = "bg-photo";
  bg.src = tryonState.backgroundDataUrl;
  bg.alt = "Sua foto";
  tryonStage.appendChild(bg);

  tryonState.stickers.forEach((sticker) => {
    const item = wardrobe.find((i) => i.id === sticker.itemId);
    if (!item) return;

    const el = document.createElement("div");
    el.className = "sticker";
    el.style.left = `${sticker.x}px`;
    el.style.top = `${sticker.y}px`;
    el.style.width = `${sticker.w}px`;
    el.style.height = `${sticker.h}px`;
    el.style.zIndex = sticker.z;

    const img = document.createElement("img");
    img.src = getStickerImageSrc(item);
    img.alt = item.name;
    img.draggable = false;
    el.appendChild(img);

    const toolbar = document.createElement("div");
    toolbar.className = "sticker-toolbar";

    const frontBtn = document.createElement("button");
    frontBtn.type = "button";
    frontBtn.textContent = "⬆";
    frontBtn.title = "Trazer para frente";
    frontBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      sticker.z = ++tryonNextZ;
      el.style.zIndex = sticker.z;
    });

    const backBtn = document.createElement("button");
    backBtn.type = "button";
    backBtn.textContent = "⬇";
    backBtn.title = "Enviar para trás";
    backBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      sticker.z = Math.min(0, ...tryonState.stickers.map((s) => s.z)) - 1;
      el.style.zIndex = sticker.z;
    });

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "✕";
    removeBtn.title = "Remover do provador";
    removeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      tryonState.stickers = tryonState.stickers.filter((s) => s.id !== sticker.id);
      renderTryonStage();
    });

    toolbar.append(frontBtn, backBtn, removeBtn);
    el.appendChild(toolbar);

    const handle = document.createElement("div");
    handle.className = "resize-handle";
    el.appendChild(handle);

    attachDragBehavior(el, sticker);
    attachResizeBehavior(handle, el, sticker);

    tryonStage.appendChild(el);
  });

  tryonResetBtn.disabled = false;
  tryonExportBtn.disabled = false;
  tryonSaveLookBtn.disabled = false;
}

function attachDragBehavior(el, sticker) {
  el.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".resize-handle") || e.target.closest(".sticker-toolbar")) return;
    e.preventDefault();
    el.setPointerCapture(e.pointerId);
    el.classList.add("active");
    const startX = e.clientX;
    const startY = e.clientY;
    const startLeft = sticker.x;
    const startTop = sticker.y;

    const onMove = (moveEvent) => {
      sticker.x = startLeft + (moveEvent.clientX - startX);
      sticker.y = startTop + (moveEvent.clientY - startY);
      el.style.left = `${sticker.x}px`;
      el.style.top = `${sticker.y}px`;
    };
    const onUp = (upEvent) => {
      el.releasePointerCapture(upEvent.pointerId);
      el.classList.remove("active");
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerup", onUp);
    };
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerup", onUp);
  });
}

function attachResizeBehavior(handle, el, sticker) {
  handle.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    e.stopPropagation();
    handle.setPointerCapture(e.pointerId);
    const startX = e.clientX;
    const startY = e.clientY;
    const startW = sticker.w;
    const startH = sticker.h;

    const onMove = (moveEvent) => {
      sticker.w = Math.max(40, startW + (moveEvent.clientX - startX));
      sticker.h = Math.max(40, startH + (moveEvent.clientY - startY));
      el.style.width = `${sticker.w}px`;
      el.style.height = `${sticker.h}px`;
    };
    const onUp = (upEvent) => {
      handle.releasePointerCapture(upEvent.pointerId);
      handle.removeEventListener("pointermove", onMove);
      handle.removeEventListener("pointerup", onUp);
    };
    handle.addEventListener("pointermove", onMove);
    handle.addEventListener("pointerup", onUp);
  });
}

async function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

async function composeTryonImage() {
  const canvas = document.createElement("canvas");
  canvas.width = TRYON_CANVAS_W;
  canvas.height = TRYON_CANVAS_H;
  const ctx = canvas.getContext("2d");

  const bgImg = await loadImage(tryonState.backgroundDataUrl);
  const scale = Math.min(TRYON_CANVAS_W / bgImg.naturalWidth, TRYON_CANVAS_H / bgImg.naturalHeight);
  const drawW = bgImg.naturalWidth * scale;
  const drawH = bgImg.naturalHeight * scale;
  const offsetX = (TRYON_CANVAS_W - drawW) / 2;
  const offsetY = (TRYON_CANVAS_H - drawH) / 2;
  ctx.drawImage(bgImg, offsetX, offsetY, drawW, drawH);

  const stageRect = tryonStage.getBoundingClientRect();
  const scaleX = TRYON_CANVAS_W / stageRect.width;
  const scaleY = TRYON_CANVAS_H / stageRect.height;

  const sorted = [...tryonState.stickers].sort((a, b) => a.z - b.z);
  for (const sticker of sorted) {
    const item = wardrobe.find((i) => i.id === sticker.itemId);
    if (!item) continue;
    const img = await loadImage(getStickerImageSrc(item));
    ctx.drawImage(img, sticker.x * scaleX, sticker.y * scaleY, sticker.w * scaleX, sticker.h * scaleY);
  }

  return canvas.toDataURL("image/jpeg", 0.85);
}

tryonExportBtn.addEventListener("click", async () => {
  if (!tryonState.backgroundDataUrl) return;
  const dataUrl = await composeTryonImage();
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = "meu-look.jpg";
  link.click();
});

tryonSaveLookBtn.addEventListener("click", async () => {
  if (!tryonState.backgroundDataUrl || !currentLook) return;
  const dataUrl = await composeTryonImage();
  saveCurrentLook(dataUrl);
});

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

    if (look.compositeImage) {
      const photo = document.createElement("img");
      photo.className = "thumb";
      photo.src = look.compositeImage;
      photo.alt = "Foto do look no provador virtual";
      card.appendChild(photo);
    }

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
