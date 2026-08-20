const authScreen = document.querySelector("#auth-screen");
const appShell = document.querySelector("#app-shell");
const appNav = document.querySelector("#app-nav");
const viewContent = document.querySelector("#view-content");
const headerActions = document.querySelector("#header-actions");
const modal = document.querySelector("#modal");
const modalBody = document.querySelector("#modal-body");
const modalTitle = document.querySelector("#modal-title");
const toastRegion = document.querySelector("#toast-region");

const locations = ["Cyberjaya", "Petaling Jaya", "Putrajaya", "Puchong"];
const state = {
  user: JSON.parse(sessionStorage.getItem("user") || "null"),
  view: "",
  location: "Cyberjaya",
  marketItems: [],
  chatHistory: [],
};

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
}

function money(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function quantity(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  toastRegion.appendChild(toast);
  window.setTimeout(() => toast.remove(), 4200);
}

async function api(action, payload = {}) {
  let response;
  try {
    response = await fetch("/api", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ...payload }),
    });
  } catch (error) {
    throw new Error("Network error. Check your connection and try again.");
  }

  let result;
  try {
    result = await response.json();
  } catch (error) {
    throw new Error("The API returned an unreadable response.");
  }
  if (!response.ok || !result.success) throw new Error(result.error || "The request could not be completed.");
  return result;
}

function setButtonLoading(button, loading, label = "Working...") {
  if (!button) return;
  if (loading) {
    button.dataset.originalText = button.textContent;
    button.textContent = label;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}

function loadingState() {
  return `<div class="loading-state" aria-label="Loading content">
    <div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>
  </div>`;
}

function emptyState(title, message, action = "") {
  return `<div class="empty-state"><p class="eyebrow">Nothing here yet</p><h2>${escapeHtml(title)}</h2><p>${escapeHtml(message)}</p>${action}</div>`;
}

function statusLabel(status) {
  const label = String(status || "AVAILABLE").toUpperCase();
  const available = label === "AVAILABLE";
  return `<span class="status ${available ? "status--available" : "status--sold"}">${escapeHtml(label)}</span>`;
}

function setViewHeader(kicker, title, actions = "") {
  document.querySelector("#view-kicker").textContent = kicker;
  document.querySelector("#view-title").textContent = title;
  headerActions.innerHTML = actions;
}

function showAuth(mode = "login") {
  appShell.classList.add("is-hidden");
  authScreen.classList.remove("is-hidden");
  switchAuth(mode);
}

function switchAuth(mode) {
  document.querySelectorAll("[data-auth-tab]").forEach(tab => {
    const active = tab.dataset.authTab === mode;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll("[data-auth-form]").forEach(form => {
    form.classList.toggle("is-hidden", form.dataset.authForm !== mode);
  });
}

function showApp() {
  if (!state.user || !["seller", "customer"].includes(state.user.role)) {
    logout();
    return;
  }
  authScreen.classList.add("is-hidden");
  appShell.classList.remove("is-hidden");
  document.querySelector("#account-name").textContent = state.user.full_name || state.user.email;
  document.querySelector("#account-role").textContent = state.user.role;
  const sellerViews = ["Overview", "Inventory", "Sales", "Impact"];
  const customerViews = ["Market", "My Purchases", "Support"];
  const views = state.user.role === "seller" ? sellerViews : customerViews;
  appNav.innerHTML = views.map(label => {
    const view = label.toLowerCase().replaceAll(" ", "-");
    return `<button class="nav-button" type="button" data-view="${view}">${label}</button>`;
  }).join("") + `<button class="nav-button" type="button" data-logout>Logout</button>`;
  loadView(state.user.role === "seller" ? "overview" : "market");
}

function logout() {
  sessionStorage.removeItem("user");
  state.user = null;
  state.chatHistory = [];
  closeModal();
  showAuth("login");
}

async function loadView(view) {
  state.view = view;
  document.querySelectorAll("[data-view]").forEach(button => button.classList.toggle("is-active", button.dataset.view === view));
  viewContent.innerHTML = loadingState();
  const renderers = {
    overview: renderOverview,
    inventory: renderInventory,
    sales: renderSales,
    impact: renderImpact,
    market: renderMarket,
    "my-purchases": renderPurchases,
    support: renderSupport,
  };
  try {
    await renderers[view]();
  } catch (error) {
    setViewHeader("Request failed", "Something went wrong");
    viewContent.innerHTML = emptyState("We could not load this view", error.message, `<button class="button button--secondary" data-retry-view>Try again</button>`);
    showToast(error.message, "error");
  }
}

async function renderOverview() {
  setViewHeader("Seller workspace", "Overview", `<button class="button button--primary" data-open-add>Add item</button>`);
  const [inventoryResult, salesResult, impactResult] = await Promise.all([
    api("seller_inventory", { store_id: state.user.store_id }),
    api("sales", { store_id: state.user.store_id }),
    api("impact", { store_id: state.user.store_id }),
  ]);
  if (state.view !== "overview") return;
  const inventory = inventoryResult.items;
  const available = inventory.filter(item => String(item.status).toUpperCase() === "AVAILABLE").length;
  const impact = impactResult.impact;
  viewContent.innerHTML = `<div class="overview-grid">
    <article class="overview-lead">
      <p class="eyebrow">Inventory at a glance</p>
      <span class="overview-lead__number">${inventory.length}</span>
      <h2>listed food items</h2>
      <p>${available} currently available for customers to rescue.</p>
    </article>
    <div class="metric-list">
      <div class="metric-row"><span>Available items</span><strong>${available}</strong></div>
      <div class="metric-row"><span>Revenue recovered</span><strong>${money(salesResult.total_revenue)}</strong></div>
      <div class="metric-row"><span>Food saved</span><strong>${quantity(impact.food_saved)} kg</strong></div>
    </div>
  </div>
  <section class="section-block">
    <div class="section-heading"><div><p class="eyebrow">Next action</p><h2>Keep good food moving.</h2></div></div>
    <p class="market-note">Add stock as it approaches its sell-by date, then let the evaluator and discount rules prepare it for the market.</p>
  </section>`;
}

function inventoryTable(items) {
  return `<div class="table-wrap"><table>
    <thead><tr><th>Name</th><th>Category</th><th>Location</th><th>Days left</th><th>Stock</th><th>Original</th><th>Discount</th><th>Sale price</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody>${items.map(item => `<tr>
      <td><span class="item-name">${escapeHtml(item.name)}</span></td>
      <td>${escapeHtml(item.category)}</td>
      <td>${escapeHtml(item.location)}</td>
      <td>${escapeHtml(item.days_left)}</td>
      <td>${quantity(item.quantity)}</td>
      <td class="old-price">${money(item.original_price)}</td>
      <td><span class="discount-tag">${quantity(item.discount_percent)}% off</span></td>
      <td class="sale-price">${money(item.new_price)}</td>
      <td>${statusLabel(item.status)}</td>
      <td><div class="row-actions">
        <button class="button button--secondary button--small" data-sold-out="${escapeHtml(item.id)}" ${String(item.status).toUpperCase() === "SOLD OUT" ? "disabled" : ""}>Sold out</button>
        <button class="button button--danger button--small" data-delete-item="${escapeHtml(item.id)}">Delete</button>
      </div></td>
    </tr>`).join("")}</tbody>
  </table></div>`;
}

async function renderInventory() {
  setViewHeader("Seller workspace", "Inventory", `<button class="button button--primary" data-open-add>Add item</button>`);
  const result = await api("seller_inventory", { store_id: state.user.store_id });
  if (state.view !== "inventory") return;
  viewContent.innerHTML = result.items.length
    ? inventoryTable(result.items)
    : emptyState("Your shelf is ready", "Add the first imperfect or near-expiry item to make it available to customers.", `<button class="button button--primary" data-open-add>Add first item</button>`);
}

async function renderSales() {
  setViewHeader("Seller workspace", "Sales");
  const result = await api("sales", { store_id: state.user.store_id });
  if (state.view !== "sales") return;
  if (!result.sales.length) {
    viewContent.innerHTML = emptyState("No completed sales", "Purchases from your store will appear here with revenue and quantity totals.");
    return;
  }
  viewContent.innerHTML = `<div class="summary-bar">
    <article><span>Total revenue</span><strong>${money(result.total_revenue)}</strong></article>
    <article><span>Quantity sold</span><strong>${quantity(result.total_quantity_sold)} kg/u</strong></article>
  </div>
  <div class="table-wrap"><table>
    <thead><tr><th>Item</th><th>Location</th><th>Category</th><th>Quantity</th><th>Unit price</th><th>Total</th></tr></thead>
    <tbody>${result.sales.map(sale => `<tr><td><span class="item-name">${escapeHtml(sale.item_name)}</span></td><td>${escapeHtml(sale.location)}</td><td>${escapeHtml(sale.category)}</td><td>${quantity(sale.quantity_bought)}</td><td>${money(sale.unit_price)}</td><td class="sale-price">${money(sale.total_amount)}</td></tr>`).join("")}</tbody>
  </table></div>`;
}

async function renderImpact() {
  setViewHeader("SDG 2 progress", "Impact");
  const result = await api("impact", { store_id: state.user.store_id });
  if (state.view !== "impact") return;
  const impact = result.impact;
  const index = String(impact.impact_index || "NEEDS IMPROVEMENT").replace(/[🌟👍⚠️]/gu, "").trim();
  viewContent.innerHTML = `<div class="impact-layout">
    <article class="impact-index"><div><p class="eyebrow">Impact index</p><strong>${escapeHtml(index)}</strong></div><p>Calculated from the amount of rescued food sold through your store.</p></article>
    <div class="impact-stats">
      <article class="impact-stat"><span>Food saved</span><strong>${quantity(impact.food_saved)} kg</strong></article>
      <article class="impact-stat"><span>Revenue recovered</span><strong>${money(impact.revenue_recovered)}</strong></article>
      <article class="impact-stat"><span>CO2 avoided</span><strong>${quantity(impact.co2_avoided)} kg</strong></article>
      <article class="impact-stat"><span>Transactions</span><strong>${impact.transactions}</strong></article>
    </div>
  </div>`;
}

function productCards(items) {
  return `<div class="product-grid">${items.map(item => `<article class="product-card">
    <div class="product-card__meta"><span>${escapeHtml(item.category)}</span><span>${escapeHtml(item.days_left)} days left</span></div>
    <h3>${escapeHtml(item.name)}</h3>
    <p class="product-card__store">${escapeHtml(item.store_name)}</p>
    <div class="product-card__price">
      <div><strong>${money(item.new_price)}</strong><small><span class="old-price">${money(item.original_price)}</span> each</small></div>
      <span class="discount-tag">${quantity(item.discount_percent)}% off</span>
    </div>
    <div class="product-card__footer"><span>${quantity(item.quantity)} kg/u available</span><button class="button button--primary button--small" data-buy-item="${escapeHtml(item.id)}">Buy</button></div>
  </article>`).join("")}</div>`;
}

async function renderMarket() {
  setViewHeader("Customer market", "Rescue something good");
  viewContent.innerHTML = `<div class="market-toolbar">
    <label>Shopping location<select id="market-location">${locations.map(location => `<option ${location === state.location ? "selected" : ""}>${location}</option>`).join("")}</select></label>
    <p class="market-note">Available stock changes after each purchase. Prices already include the dynamic rescue discount.</p>
  </div>${loadingState()}`;
  const result = await api("market", { location: state.location });
  if (state.view !== "market") return;
  state.marketItems = result.items;
  viewContent.querySelector(".loading-state").outerHTML = result.items.length
    ? productCards(result.items)
    : emptyState("No food available here today", `There are currently no available items in ${state.location}. Try another location.`);
}

async function renderPurchases() {
  setViewHeader("Customer account", "My Purchases");
  const result = await api("purchase_history", { customer_id: state.user.id });
  if (state.view !== "my-purchases") return;
  if (!result.purchases.length) {
    viewContent.innerHTML = emptyState("No purchases yet", "When you rescue an item from the market, your receipt will appear here.", `<button class="button button--primary" data-view="market">Browse market</button>`);
    return;
  }
  viewContent.innerHTML = `<div class="table-wrap"><table>
    <thead><tr><th>Item</th><th>Store</th><th>Location</th><th>Quantity</th><th>Unit price</th><th>Total</th><th>Date</th></tr></thead>
    <tbody>${result.purchases.map(purchase => `<tr><td><span class="item-name">${escapeHtml(purchase.item_name)}</span></td><td>${escapeHtml(purchase.store_name)}</td><td>${escapeHtml(purchase.location)}</td><td>${quantity(purchase.quantity_bought)}</td><td>${money(purchase.unit_price)}</td><td class="sale-price">${money(purchase.total_amount)}</td><td>${escapeHtml(String(purchase.created_at || "").slice(0, 16).replace("T", " ") || "N/A")}</td></tr>`).join("")}</tbody>
  </table></div>`;
}

async function renderSupport() {
  setViewHeader("Customer help", "Support");
  const welcome = state.chatHistory.length ? "" : `<div class="chat-message">Ask about discounts, food storage, notifications, or how the rescued-food market works.</div>`;
  viewContent.innerHTML = `<div class="chat-shell">
    <div id="chat-log" class="chat-log">${welcome}${state.chatHistory.map(message => `<div class="chat-message chat-message--${message.role === "user" ? "user" : "assistant"}">${escapeHtml(message.content)}</div>`).join("")}</div>
    <form id="chat-form" class="chat-form"><label class="is-hidden" for="chat-input">Message</label><input id="chat-input" name="message" placeholder="Type your question..." autocomplete="off" required><button class="button button--primary" type="submit">Send</button></form>
  </div>`;
  document.querySelector("#chat-log").scrollTop = document.querySelector("#chat-log").scrollHeight;
}

function openModal(title, content) {
  modalTitle.textContent = title;
  modalBody.innerHTML = content;
  modal.classList.remove("is-hidden");
  document.body.style.overflow = "hidden";
  window.setTimeout(() => modal.querySelector("input, select, button")?.focus(), 20);
}

function closeModal() {
  modal.classList.add("is-hidden");
  document.body.style.overflow = "";
  modalBody.innerHTML = "";
}

function openAddItem() {
  openModal("Add a rescued item", `<form id="add-item-form" class="modal-form">
    <div class="form-grid">
      <label>Location<select name="location" required>${locations.map(location => `<option>${location}</option>`).join("")}</select></label>
      <label>Category<select name="category" required><option>Produce</option><option>Bakery & Grains</option><option>Dairy & Chilled Items</option><option>Prepared / Packaged Meals</option></select></label>
    </div>
    <label>Item name<input name="name" placeholder="e.g. Odd-shaped carrots" required></label>
    <div class="form-grid">
      <label>Quantity (kg/units)<input name="quantity" type="number" min="0.01" step="0.01" required></label>
      <label>Original price<input name="original_price" type="number" min="0.01" step="0.01" required></label>
    </div>
    <div class="form-grid">
      <label>Days left<input name="days_left" type="number" min="1" max="7" step="1" required></label>
      <label>Cosmetic grade<select name="grade" required><option value="A">A — Minor flaw</option><option value="B">B — Moderate flaw</option><option value="C">C — High flaw</option></select></label>
    </div>
    <div id="item-evaluation" aria-live="polite"></div>
    <div class="modal-actions"><button class="button button--secondary" type="button" data-close-modal>Cancel</button><button class="button button--primary" type="submit">Evaluate & add</button></div>
  </form>`);
}

function openPurchase(item) {
  openModal("Purchase item", `<form id="purchase-form" class="modal-form" data-item-id="${escapeHtml(item.id)}">
    <div class="purchase-summary"><div><strong>${escapeHtml(item.name)}</strong><span class="product-card__store">${escapeHtml(item.store_name)}</span></div><strong>${money(item.new_price)}</strong></div>
    <label>Quantity (available: ${quantity(item.quantity)} kg/units)<input id="purchase-quantity" name="quantity" type="number" min="0.01" max="${Number(item.quantity)}" step="0.01" value="1" required></label>
    <div class="purchase-total"><span>Calculated total</span><strong id="purchase-total">${money(item.new_price)}</strong></div>
    <div class="modal-actions"><button class="button button--secondary" type="button" data-close-modal>Cancel</button><button class="button button--primary" type="submit">Purchase</button></div>
  </form>`);
}

document.querySelectorAll("[data-auth-tab]").forEach(button => button.addEventListener("click", () => switchAuth(button.dataset.authTab)));

document.querySelectorAll('input[name="role"]').forEach(input => input.addEventListener("change", () => {
  const seller = input.value === "seller" && input.checked;
  const fields = document.querySelector("#seller-fields");
  fields.classList.toggle("is-hidden", !seller);
  fields.querySelectorAll("input, select").forEach(field => field.required = seller);
}));

document.querySelector("#login-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type='submit']");
  const status = form.querySelector("[data-form-status]");
  status.textContent = "";
  setButtonLoading(button, true, "Signing in...");
  try {
    const data = Object.fromEntries(new FormData(form));
    const result = await api("login", data);
    state.user = result.user;
    sessionStorage.setItem("user", JSON.stringify(state.user));
    showApp();
    showToast(`Welcome back, ${state.user.full_name || "friend"}.`);
  } catch (error) {
    status.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setButtonLoading(button, false);
  }
});

document.querySelector("#signup-form").addEventListener("submit", async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("button[type='submit']");
  const status = form.querySelector("[data-form-status]");
  status.textContent = "";
  setButtonLoading(button, true, "Creating account...");
  try {
    const data = Object.fromEntries(new FormData(form));
    const result = await api("signup", data);
    showToast(result.message || "Account created. You can now log in.");
    form.reset();
    document.querySelector("#seller-fields").classList.add("is-hidden");
    switchAuth("login");
    document.querySelector("#login-form input[name='email']").value = data.email;
  } catch (error) {
    status.textContent = error.message;
    showToast(error.message, "error");
  } finally {
    setButtonLoading(button, false);
  }
});

appNav.addEventListener("click", event => {
  const viewButton = event.target.closest("[data-view]");
  if (viewButton) loadView(viewButton.dataset.view);
  if (event.target.closest("[data-logout]")) logout();
});

document.addEventListener("click", async event => {
  if (event.target.closest("[data-close-modal]")) closeModal();
  if (event.target.closest("[data-open-add]")) openAddItem();
  const retry = event.target.closest("[data-retry-view]");
  if (retry) loadView(state.view);
  const viewButton = event.target.closest("[data-view]");
  if (viewButton && !viewButton.closest("#app-nav")) loadView(viewButton.dataset.view);

  const soldButton = event.target.closest("[data-sold-out]");
  if (soldButton) {
    setButtonLoading(soldButton, true, "Updating...");
    try {
      await api("mark_sold_out", { item_id: soldButton.dataset.soldOut });
      showToast("Item marked as SOLD OUT.");
      loadView(state.view);
    } catch (error) {
      showToast(error.message, "error");
      setButtonLoading(soldButton, false);
    }
  }

  const deleteButton = event.target.closest("[data-delete-item]");
  if (deleteButton && window.confirm("Delete this item permanently?")) {
    setButtonLoading(deleteButton, true, "Deleting...");
    try {
      await api("delete_item", { store_id: state.user.store_id, item_id: deleteButton.dataset.deleteItem });
      showToast("Item deleted successfully.");
      loadView(state.view);
    } catch (error) {
      showToast(`Item deletion failed: ${error.message}`, "error");
      setButtonLoading(deleteButton, false);
    }
  }

  const buyButton = event.target.closest("[data-buy-item]");
  if (buyButton) {
    const item = state.marketItems.find(candidate => String(candidate.id) === buyButton.dataset.buyItem);
    if (item) openPurchase(item);
  }
});

document.addEventListener("change", event => {
  if (event.target.id === "market-location") {
    state.location = event.target.value;
    renderMarket().catch(error => showToast(error.message, "error"));
  }
});

document.addEventListener("input", event => {
  if (event.target.id === "purchase-quantity") {
    const item = state.marketItems.find(candidate => String(candidate.id) === event.target.closest("form").dataset.itemId);
    document.querySelector("#purchase-total").textContent = money(Number(event.target.value || 0) * Number(item.new_price));
  }
});

document.addEventListener("submit", async event => {
  if (event.target.id === "add-item-form") {
    event.preventDefault();
    const form = event.target;
    const button = form.querySelector("button[type='submit']");
    const resultPanel = form.querySelector("#item-evaluation");
    resultPanel.innerHTML = "";
    setButtonLoading(button, true, "AI evaluating...");
    try {
      const data = Object.fromEntries(new FormData(form));
      const result = await api("add_item", { ...data, store_id: state.user.store_id });
      if (result.approved) {
        resultPanel.innerHTML = `<div class="result-panel"><strong>AI approved this item.</strong><br>${quantity(result.discount)}% discount · sale price ${money(result.new_price)}</div>`;
        showToast("Item approved and added to inventory.");
        if (["inventory", "overview"].includes(state.view)) window.setTimeout(() => loadView(state.view), 900);
      } else {
        resultPanel.innerHTML = `<div class="result-panel result-panel--rejected"><strong>AI rejected this item.</strong><br>${escapeHtml(result.reason)}</div>`;
        showToast("Item rejected by the evaluator.", "error");
      }
    } catch (error) {
      resultPanel.innerHTML = `<div class="result-panel result-panel--rejected"><strong>Could not evaluate the item.</strong><br>${escapeHtml(error.message)}</div>`;
      showToast(error.message, "error");
    } finally {
      setButtonLoading(button, false);
    }
  }

  if (event.target.id === "purchase-form") {
    event.preventDefault();
    const form = event.target;
    const button = form.querySelector("button[type='submit']");
    const item = state.marketItems.find(candidate => String(candidate.id) === form.dataset.itemId);
    const amount = Number(new FormData(form).get("quantity"));
    if (!Number.isFinite(amount) || amount <= 0) {
      showToast("Enter a quantity greater than zero.", "error");
      return;
    }
    if (amount > Number(item.quantity)) {
      showToast(`Insufficient stock. Only ${quantity(item.quantity)} kg/units are available.`, "error");
      return;
    }
    setButtonLoading(button, true, "Purchasing...");
    try {
      const result = await api("buy", { customer_id: state.user.id, location: state.location, item_id: item.id, quantity: amount });
      closeModal();
      showToast(`Purchase complete: ${quantity(amount)} kg/units of ${item.name}.`);
      await renderMarket();
      if (result.status === "SOLD OUT") showToast("That purchase rescued the final available stock.");
    } catch (error) {
      showToast(error.message, "error");
      setButtonLoading(button, false);
    }
  }

  if (event.target.id === "chat-form") {
    event.preventDefault();
    const form = event.target;
    const input = form.querySelector("input");
    const button = form.querySelector("button");
    const message = input.value.trim();
    if (!message) return;
    const previousHistory = [...state.chatHistory];
    state.chatHistory.push({ role: "user", content: message });
    input.value = "";
    const log = document.querySelector("#chat-log");
    log.insertAdjacentHTML("beforeend", `<div class="chat-message chat-message--user">${escapeHtml(message)}</div><div id="chat-loading" class="chat-message chat-message--loading">Customer service is thinking...</div>`);
    log.scrollTop = log.scrollHeight;
    setButtonLoading(button, true, "Sending...");
    try {
      const result = await api("chat", { message, history: previousHistory });
      state.chatHistory.push({ role: "assistant", content: result.reply });
      document.querySelector("#chat-loading").outerHTML = `<div class="chat-message">${escapeHtml(result.reply)}</div>`;
    } catch (error) {
      document.querySelector("#chat-loading").outerHTML = `<div class="chat-message result-panel--rejected">${escapeHtml(error.message)}</div>`;
      showToast(error.message, "error");
    } finally {
      setButtonLoading(button, false);
      log.scrollTop = log.scrollHeight;
    }
  }
});

document.addEventListener("keydown", event => {
  if (event.key === "Escape" && !modal.classList.contains("is-hidden")) closeModal();
});

if (state.user) showApp();
else showAuth("login");
