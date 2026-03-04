const API = "http://127.0.0.1:8000";
let taskMap = new Map();
let flatTasks = [];

const views = ["login", "register", "board"];
const navButtons = {
  login: document.getElementById("navLogin"),
  register: document.getElementById("navRegister"),
  board: document.getElementById("navBoard"),
};

const activeLane = document.getElementById("activeLane");
const finishedLane = document.getElementById("finishedLane");
const activeCount = document.getElementById("activeCount");
const finishedCount = document.getElementById("finishedCount");

function init() {
  bindNavigation();
  bindFormActions();
  bindLaneDrop(document.querySelector('[data-lane="active"]'), false);
  bindLaneDrop(document.querySelector('[data-lane="finished"]'), true);
  showView(getToken() ? "board" : "login");
}

function bindNavigation() {
  document.querySelectorAll("[data-view]").forEach((btn) => {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  });
  document.getElementById("logoutBtn").addEventListener("click", logout);
}

function bindFormActions() {
  document.getElementById("loginBtn").addEventListener("click", login);
  document.getElementById("registerBtn").addEventListener("click", register);
  document.getElementById("createBtn").addEventListener("click", createTodo);
  document.getElementById("clearCreateBtn").addEventListener("click", clearCreateForm);
  document.getElementById("updateBtn").addEventListener("click", updateTodo);
  document.getElementById("cancelEditBtn").addEventListener("click", clearEditForm);
  document.getElementById("refreshBtn").addEventListener("click", loadTodos);
  document.getElementById("clearParentsBtn").addEventListener("click", clearFinishedParentTasks);
}

function getToken() {
  return localStorage.getItem("token");
}

function authHeaders(withBody = true) {
  const headers = { Authorization: `Bearer ${getToken()}` };
  if (withBody) headers["Content-Type"] = "application/json";
  return headers;
}

function setStatus(id, msg, isError = false) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg || "";
  el.style.color = isError ? "#ff88a9" : "#8eb9d9";
}

function showView(view) {
  if (!views.includes(view)) return;
  views.forEach((name) => {
    const pane = document.getElementById(`view-${name}`);
    if (pane) pane.classList.toggle("active", name === view);
    if (navButtons[name]) navButtons[name].classList.toggle("active", name === view);
  });
  if (view === "board") {
    if (!requireAuth()) return;
    loadTodos();
  }
}

function requireAuth() {
  if (getToken()) return true;
  setStatus("boardStatus", "Please login first.", true);
  showView("login");
  return false;
}

function normalizeDatetimeForApi(localValue) {
  if (!localValue) return null;
  const d = new Date(localValue);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function formatDate(value) {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString();
}

function escapeHtml(input) {
  return String(input)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function register() {
  try {
    const res = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("r_email").value.trim(),
        password: document.getElementById("r_pass").value,
      }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Registration failed");
    }
    document.getElementById("r_pass").value = "";
    setStatus("registerStatus", "Registration successful. Please login.");
    showView("login");
  } catch (err) {
    setStatus("registerStatus", `Register error: ${err.message}`, true);
  }
}

async function login() {
  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("l_email").value.trim(),
        password: document.getElementById("l_pass").value,
      }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    setStatus("loginStatus", "Logged in.");
    showView("board");
  } catch (err) {
    setStatus("loginStatus", `Login error: ${err.message}`, true);
  }
}

function logout() {
  localStorage.removeItem("token");
  taskMap = new Map();
  flatTasks = [];
  activeLane.innerHTML = "";
  finishedLane.innerHTML = "";
  populateParentSelect([]);
  clearCreateForm();
  clearEditForm();
  setStatus("boardStatus", "");
  setStatus("loginStatus", "Logged out.");
  showView("login");
}

function clearCreateForm() {
  document.getElementById("c_title").value = "";
  document.getElementById("c_description").value = "";
  document.getElementById("c_deadline").value = "";
  document.getElementById("c_parent_id").value = "";
}

function clearEditForm() {
  document.getElementById("e_id").value = "";
  document.getElementById("e_title").value = "";
  document.getElementById("e_description").value = "";
  document.getElementById("e_completed").checked = false;
}

async function createTodo() {
  if (!requireAuth()) return;

  const title = document.getElementById("c_title").value.trim();
  if (!title) {
    setStatus("boardStatus", "Title is required.", true);
    return;
  }

  const parentId = document.getElementById("c_parent_id").value || null;

  const payload = {
    title,
    description: document.getElementById("c_description").value.trim() || null,
    deadline: normalizeDatetimeForApi(document.getElementById("c_deadline").value),
    parent_id: parentId,
  };

  try {
    const res = await fetch(`${API}/todos/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Create failed");
    }
    clearCreateForm();
    setStatus("boardStatus", "Task created.");
    await loadTodos();
  } catch (err) {
    setStatus("boardStatus", `Create error: ${err.message}`, true);
  }
}

async function loadTodos() {
  if (!requireAuth()) return;

  try {
    const res = await fetch(`${API}/todos/`, { headers: authHeaders(false) });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Load failed");
    }

    const tree = await res.json();
    flatTasks = flattenTodos(tree);
    taskMap = new Map(flatTasks.map((todo) => [todo.id, todo]));
    renderBoard(flatTasks);
    populateParentSelect(flatTasks.filter((t) => !t.completed));
    setStatus("boardStatus", `${flatTasks.length} tasks loaded.`);
  } catch (err) {
    setStatus("boardStatus", `Load error: ${err.message}`, true);
  }
}

function flattenTodos(nodes, level = 0, parentTitle = null) {
  if (!Array.isArray(nodes)) return [];
  const out = [];
  nodes.forEach((todo) => {
    out.push({
      ...todo,
      level,
      parentTitle,
    });
    if (Array.isArray(todo.subtasks) && todo.subtasks.length > 0) {
      out.push(...flattenTodos(todo.subtasks, level + 1, todo.title));
    }
  });
  return out;
}

function renderBoard(todos) {
  activeLane.innerHTML = "";
  finishedLane.innerHTML = "";

  const active = todos.filter((t) => !t.completed);
  const finished = todos.filter((t) => !!t.completed);

  activeCount.textContent = String(active.length);
  finishedCount.textContent = String(finished.length);

  if (active.length === 0) {
    activeLane.innerHTML = `<div class="empty">No active tasks.</div>`;
  } else {
    active.forEach((todo) => activeLane.appendChild(createCard(todo)));
  }

  if (finished.length === 0) {
    finishedLane.innerHTML = `<div class="empty">No finished tasks.</div>`;
  } else {
    finished.forEach((todo) => finishedLane.appendChild(createCard(todo)));
  }
}

function createCard(todo) {
  const card = document.createElement("article");
  card.className = "card";
  card.draggable = true;
  card.dataset.todoId = todo.id;

  const indentTag = todo.level > 0 ? `<span class="tag">Subtask L${todo.level}</span>` : "";
  const parentTag = todo.parentTitle ? `<span class="tag">Parent: ${escapeHtml(todo.parentTitle)}</span>` : "";
  const deadlineTag = todo.deadline ? `<span class="tag">Due: ${escapeHtml(formatDate(todo.deadline))}</span>` : "";

  card.innerHTML = `
    <h4>${escapeHtml(todo.title || "(untitled)")}</h4>
    <p class="meta">${escapeHtml(todo.description || "No description")}</p>
    <p class="meta">Created: ${escapeHtml(formatDate(todo.created_at))}</p>
    <p class="meta">ID: ${escapeHtml(todo.id)}</p>
    <div class="tags">
      ${indentTag}
      ${parentTag}
      ${deadlineTag}
    </div>
    <div class="actions">
      <button class="mini" data-action="edit">Edit</button>
      <button class="mini" data-action="subtask">Subtask</button>
      <button class="mini warn" data-action="finish">${todo.completed ? "Reopen" : "Finish"}</button>
    </div>
  `;

  card.addEventListener("dragstart", onDragStart);
  card.addEventListener("dragend", onDragEnd);
  card.querySelector('[data-action="edit"]').addEventListener("click", () => fillEditForm(todo.id));
  card.querySelector('[data-action="subtask"]').addEventListener("click", () => prepareSubtask(todo.id));
  card.querySelector('[data-action="finish"]').addEventListener("click", () => quickToggle(todo.id, !todo.completed));

  return card;
}

function populateParentSelect(todos) {
  const select = document.getElementById("c_parent_id");
  const current = select.value;
  select.innerHTML = '<option value="">No parent</option>';
  todos.forEach((todo) => {
    const option = document.createElement("option");
    option.value = todo.id;
    option.textContent = `${"  ".repeat(Math.min(todo.level, 4))}${todo.title} (${todo.id.slice(0, 8)})`;
    select.appendChild(option);
  });
  if ([...select.options].some((o) => o.value === current)) {
    select.value = current;
  }
}

function fillEditForm(todoId) {
  const todo = taskMap.get(todoId);
  if (!todo) return;
  document.getElementById("e_id").value = todo.id;
  document.getElementById("e_title").value = todo.title || "";
  document.getElementById("e_description").value = todo.description || "";
  document.getElementById("e_completed").checked = !!todo.completed;
  setStatus("boardStatus", `Editing task ${todo.id}`);
}

function prepareSubtask(parentId) {
  document.getElementById("c_parent_id").value = parentId;
  document.getElementById("c_title").focus();
  setStatus("boardStatus", `Creating subtask under ${parentId}`);
}

async function updateTodo() {
  if (!requireAuth()) return;

  const id = document.getElementById("e_id").value;
  if (!id) {
    setStatus("boardStatus", "Select a card to edit.", true);
    return;
  }

  const payload = {
    title: document.getElementById("e_title").value.trim() || null,
    description: document.getElementById("e_description").value.trim() || null,
    completed: !!document.getElementById("e_completed").checked,
  };

  try {
    const res = await fetch(`${API}/todos/${id}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Update failed");
    }
    clearEditForm();
    setStatus("boardStatus", "Task updated.");
    await loadTodos();
  } catch (err) {
    setStatus("boardStatus", `Update error: ${err.message}`, true);
  }
}

async function quickToggle(todoId, completed) {
  if (!requireAuth()) return;
  try {
    const res = await fetch(`${API}/todos/${todoId}`, {
      method: "PUT",
      headers: authHeaders(),
      body: JSON.stringify({ completed }),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Status update failed");
    }
    setStatus("boardStatus", completed ? "Task moved to Finished." : "Task moved to Active.");
    await loadTodos();
  } catch (err) {
    setStatus("boardStatus", `Move error: ${err.message}`, true);
  }
}

async function clearFinishedParentTasks() {
  if (!requireAuth()) return;
  try {
    const res = await fetch(`${API}/todos/finished/clear-parents`, {
      method: "DELETE",
      headers: authHeaders(false),
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Clear failed");
    }
    const data = await res.json();
    setStatus("boardStatus", `${data.cleared} finished parent task(s) cleared.`);
    await loadTodos();
  } catch (err) {
    setStatus("boardStatus", `Clear error: ${err.message}`, true);
  }
}

function onDragStart(event) {
  const card = event.currentTarget;
  if (!card || !card.dataset.todoId) return;
  card.classList.add("dragging");
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", card.dataset.todoId);
}

function onDragEnd(event) {
  const card = event.currentTarget;
  if (card) card.classList.remove("dragging");
  document.querySelectorAll(".lane").forEach((lane) => lane.classList.remove("dragover"));
}

function bindLaneDrop(laneElement, completedTarget) {
  laneElement.addEventListener("dragover", (event) => {
    event.preventDefault();
    laneElement.classList.add("dragover");
  });

  laneElement.addEventListener("dragleave", () => {
    laneElement.classList.remove("dragover");
  });

  laneElement.addEventListener("drop", async (event) => {
    event.preventDefault();
    laneElement.classList.remove("dragover");
    const todoId = event.dataTransfer.getData("text/plain");
    const todo = taskMap.get(todoId);
    if (!todo) return;
    if (!!todo.completed === completedTarget) return;
    await quickToggle(todoId, completedTarget);
  });
}

init();
