const STORAGE_KEY = "mini-crm-contacts";

const STATUS_LABELS = {
  lead: "Lead",
  contato: "Em contato",
  negociacao: "Negociação",
  cliente: "Cliente",
  perdido: "Perdido",
};

const form = document.getElementById("contact-form");
const idInput = document.getElementById("contact-id");
const nameInput = document.getElementById("name");
const companyInput = document.getElementById("company");
const emailInput = document.getElementById("email");
const phoneInput = document.getElementById("phone");
const statusInput = document.getElementById("status");
const notesInput = document.getElementById("notes");

const formTitle = document.getElementById("form-title");
const submitBtn = document.getElementById("submit-btn");
const cancelEditBtn = document.getElementById("cancel-edit");

const listEl = document.getElementById("contact-list");
const emptyState = document.getElementById("empty-state");
const countEl = document.getElementById("count");
const searchInput = document.getElementById("search");
const filterStatus = document.getElementById("filter-status");

function loadContacts() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveContacts(contacts) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(contacts));
}

let contacts = loadContacts();

function resetForm() {
  form.reset();
  idInput.value = "";
  statusInput.value = "lead";
  formTitle.textContent = "Novo contato";
  submitBtn.textContent = "Salvar contato";
  cancelEditBtn.hidden = true;
}

function startEdit(id) {
  const contact = contacts.find((c) => c.id === id);
  if (!contact) return;

  idInput.value = contact.id;
  nameInput.value = contact.name;
  companyInput.value = contact.company || "";
  emailInput.value = contact.email || "";
  phoneInput.value = contact.phone || "";
  statusInput.value = contact.status;
  notesInput.value = contact.notes || "";

  formTitle.textContent = "Editar contato";
  submitBtn.textContent = "Atualizar contato";
  cancelEditBtn.hidden = false;
  nameInput.focus();
}

function deleteContact(id) {
  const contact = contacts.find((c) => c.id === id);
  if (!contact) return;
  if (!confirm(`Remover "${contact.name}" da lista de contatos?`)) return;

  contacts = contacts.filter((c) => c.id !== id);
  saveContacts(contacts);
  if (idInput.value === id) resetForm();
  render();
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function render() {
  const query = searchInput.value.trim().toLowerCase();
  const statusFilter = filterStatus.value;

  const filtered = contacts.filter((c) => {
    const matchesQuery =
      !query ||
      c.name.toLowerCase().includes(query) ||
      (c.company || "").toLowerCase().includes(query) ||
      (c.email || "").toLowerCase().includes(query);
    const matchesStatus = !statusFilter || c.status === statusFilter;
    return matchesQuery && matchesStatus;
  });

  countEl.textContent = contacts.length;
  listEl.innerHTML = "";

  if (contacts.length === 0) {
    emptyState.hidden = false;
    emptyState.textContent =
      "Nenhum contato cadastrado ainda. Use o formulário ao lado para adicionar o primeiro.";
    return;
  }

  if (filtered.length === 0) {
    emptyState.hidden = false;
    emptyState.textContent = "Nenhum contato encontrado para esse filtro.";
    return;
  }

  emptyState.hidden = true;

  const sorted = [...filtered].sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  for (const contact of sorted) {
    const li = document.createElement("li");
    li.className = "contact-card";
    li.innerHTML = `
      <div class="contact-main">
        <div class="contact-name">
          ${escapeHtml(contact.name)}
          <span class="badge badge-${contact.status}">${STATUS_LABELS[contact.status]}</span>
        </div>
        ${contact.company ? `<div class="contact-company">${escapeHtml(contact.company)}</div>` : ""}
        <div class="contact-meta">
          ${contact.email ? `<span>${escapeHtml(contact.email)}</span>` : ""}
          ${contact.phone ? `<span>${escapeHtml(contact.phone)}</span>` : ""}
        </div>
        ${contact.notes ? `<div class="contact-notes">${escapeHtml(contact.notes)}</div>` : ""}
      </div>
      <div class="contact-actions">
        <button type="button" class="btn-edit" data-action="edit" data-id="${contact.id}">Editar</button>
        <button type="button" class="btn-delete" data-action="delete" data-id="${contact.id}">Excluir</button>
      </div>
    `;
    listEl.appendChild(li);
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();

  const name = nameInput.value.trim();
  if (!name) return;

  const data = {
    name,
    company: companyInput.value.trim(),
    email: emailInput.value.trim(),
    phone: phoneInput.value.trim(),
    status: statusInput.value,
    notes: notesInput.value.trim(),
  };

  if (idInput.value) {
    contacts = contacts.map((c) => (c.id === idInput.value ? { ...c, ...data } : c));
  } else {
    contacts.push({ id: crypto.randomUUID(), ...data });
  }

  saveContacts(contacts);
  resetForm();
  render();
});

cancelEditBtn.addEventListener("click", resetForm);

listEl.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const { action, id } = btn.dataset;
  if (action === "edit") startEdit(id);
  if (action === "delete") deleteContact(id);
});

searchInput.addEventListener("input", render);
filterStatus.addEventListener("change", render);

render();
