const authScreen = document.querySelector("#auth-screen");
const appShell = document.querySelector("#app-shell");
const appNav = document.querySelector("#app-nav");
const viewContent = document.querySelector("#view-content");
const headerActions = document.querySelector("#header-actions");
const modal = document.querySelector("#modal");
const modalBody = document.querySelector("#modal-body");
const modalTitle = document.querySelector("#modal-title");
const toastRegion = document.querySelector("#toast-region");
const skipLink = document.querySelector("#skip-link");
let modalOpener = null;

const locations = ["Cyberjaya", "Petaling Jaya", "Putrajaya", "Puchong"];
const currencyFormatter = new Intl.NumberFormat("en-MY", {
  style: "currency",
  currency: "MYR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const compactCurrencyFormatter = new Intl.NumberFormat("en-MY", {
  style: "currency",
  currency: "MYR",
  notation: "compact",
  maximumFractionDigits: 1,
});

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
  return currencyFormatter.format(Number(value || 0));
}

function compactMoney(value) {
  return compactCurrencyFormatter.format(Number(value || 0));
}

function quantity(value) {
  return Number(value || 0).toLocaleString("en-MY", { maximumFractionDigits: 2 });
}

function shortDate(value) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10);
  return date.toLocaleDateString("en-MY", { day: "2-digit", month: "short", year: "numeric" });
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

  if (!response.ok || !result.success) {
    throw new Error(result.error || "The request could not be completed.");
  }
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
  return `<div class="loading-state" role="status" aria-label="Loading content">
    <span class="visually-hidden">Loading content</span>
    <div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>
  </div>`;
}

function emptyState(title, message, action = "") {
  return `<section class="empty-state"><h2>${escapeHtml(title)}</h2><p>${escapeHtml(message)}</p>${action}</section>`;
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
  skipLink.href = "#auth-task";
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

function setSellerFields(show) {
  const fields = document.querySelector("#seller-fields");
  fields.classList.toggle("is-hidden", !show);
  fields.querySelectorAll("input, select").forEach(field => field.required = show);
}

function showApp() {
  if (!state.user || !["seller", "customer"].includes(state.user.role)) {
    logout();
    return;
  }

  authScreen.classList.add("is-hidden");
  appShell.classList.remove("is-hidden");
  skipLink.href = "#main-content";
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
  document.querySelectorAll("[data-view]").forEach(button => {
    const active = button.dataset.view === view;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  viewContent.setAttribute("aria-busy", "true");
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
    viewContent.innerHTML = emptyState(
      "We could not load this view",
      error.message,
      `<button class="button button--secondary" data-retry-view>Try again</button>`
    );
    showToast(error.message, "error");
  } finally {
    viewContent.setAttribute("aria-busy", "false");
  }
}

function aggregateRevenueByDay(sales) {
  const totals = new Map();

  sales.forEach(sale => {
    const raw = sale.created_at;
    const date = raw ? new Date(raw) : null;
    if (!date || Number.isNaN(date.getTime())) return;
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    const current = totals.get(key) || { date: key, revenue: 0, orders: 0 };
    current.revenue += Number(sale.total_amount || 0);
    current.orders += 1;
    totals.set(key, current);
  });

  return [...totals.values()]
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-10);
}

function aggregateRevenueByCategory(sales) {
  const totals = new Map();

  sales.forEach(sale => {
    const category = sale.category || "Other";
    const current = totals.get(category) || { category, revenue: 0, quantity: 0 };
    current.revenue += Number(sale.total_amount || 0);
    current.quantity += Number(sale.quantity_bought || 0);
    totals.set(category, current);
  });

  return [...totals.values()].sort((a, b) => b.revenue - a.revenue);
}

function salesLineChart(points) {
  if (!points.length) {
    return `<div class="chart-empty">No dated sales are available yet.</div>`;
  }

  const width = 760;
  const height = 270;
  const left = 54;
  const right = 20;
  const top = 20;
  const bottom = 48;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const maxRevenue = Math.max(...points.map(point => point.revenue), 1);
  const step = points.length === 1 ? 0 : plotWidth / (points.length - 1);
  const baseline = top + plotHeight;

  const coords = points.map((point, index) => ({
    ...point,
    x: left + (points.length === 1 ? plotWidth / 2 : index * step),
    y: top + plotHeight - (point.revenue / maxRevenue) * plotHeight,
  }));

  const linePath = coords.map((point, index) => `${index === 0 ? "M" : "L"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
  const areaPath = `${linePath} L${coords.at(-1).x.toFixed(1)},${baseline} L${coords[0].x.toFixed(1)},${baseline} Z`;
  const tickValues = [maxRevenue, maxRevenue / 2, 0];
  const grid = tickValues.map((value, index) => {
    const y = top + (plotHeight / 2) * index;
    return `<line class="chart-grid-line" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"></line>
      <text class="chart-axis-label" x="${left - 8}" y="${y + 4}" text-anchor="end">${escapeHtml(compactMoney(value))}</text>`;
  }).join("");

  const labels = coords.map((point, index) => {
    const show = coords.length <= 6 || index === 0 || index === coords.length - 1 || index % 2 === 0;
    if (!show) return "";
    const date = new Date(`${point.date}T00:00:00`);
    const label = date.toLocaleDateString("en-MY", { day: "numeric", month: "short" });
    return `<text class="chart-axis-label" x="${point.x}" y="${height - 14}" text-anchor="middle">${escapeHtml(label)}</text>`;
  }).join("");

  const dots = coords.map(point => `<circle class="chart-dot" cx="${point.x}" cy="${point.y}" r="4">
    <title>${escapeHtml(shortDate(point.date))}: ${escapeHtml(money(point.revenue))} · ${point.orders} order${point.orders === 1 ? "" : "s"}</title>
  </circle>`).join("");

  const accessiblePoints = points.map(point => `<li>${escapeHtml(shortDate(point.date))}: ${escapeHtml(money(point.revenue))}, ${point.orders} order${point.orders === 1 ? "" : "s"}</li>`).join("");

  return `<div class="chart-wrap">
    <svg class="sales-chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Revenue trend chart for recent sales">
      ${grid}
      <path class="chart-area" d="${areaPath}"></path>
      <path class="chart-line" d="${linePath}"></path>
      ${dots}
      ${labels}
    </svg>
    <ul class="visually-hidden">${accessiblePoints}</ul>
  </div>`;
}

function categoryBars(categories) {
  if (!categories.length) {
    return `<div class="chart-empty">Category performance will appear after the first sale.</div>`;
  }

  const maxRevenue = Math.max(...categories.map(item => item.revenue), 1);
  return `<div class="category-bars">${categories.map(item => {
    const percent = Math.max(4, (item.revenue / maxRevenue) * 100);
    return `<div class="category-bar">
      <div class="category-bar__top"><span>${escapeHtml(item.category)}</span><strong>${money(item.revenue)}</strong></div>
      <div class="category-bar__track" aria-label="${escapeHtml(item.category)} revenue ${escapeHtml(money(item.revenue))}">
        <div class="category-bar__fill" style="width:${percent.toFixed(1)}%"></div>
      </div>
    </div>`;
  }).join("")}</div>`;
}

function sellerKpis(sales, inventory, impact) {
  const totalRevenue = sales.reduce((sum, sale) => sum + Number(sale.total_amount || 0), 0);
  const transactions = sales.length;
  const averageOrder = transactions ? totalRevenue / transactions : 0;
  const totalQuantity = sales.reduce((sum, sale) => sum + Number(sale.quantity_bought || 0), 0);
  const available = inventory.filter(item => String(item.status).toUpperCase() === "AVAILABLE").length;
  const topSale = Math.max(...sales.map(sale => Number(sale.total_amount || 0)), 0);

  return { totalRevenue, transactions, averageOrder, totalQuantity, available, topSale, impact };
}

async function renderOverview() {
  setViewHeader("Revenue, stock and impact from completed sales.", "Overview", `<button class="button button--primary" data-open-add>Add item</button>`);

  const [inventoryResult, salesResult, impactResult] = await Promise.all([
    api("seller_inventory", { store_id: state.user.store_id }),
    api("sales", { store_id: state.user.store_id }),
    api("impact", { store_id: state.user.store_id }),
  ]);

  if (state.view !== "overview") return;

  const inventory = inventoryResult.items;
  const sales = salesResult.sales;
  const impact = impactResult.impact;
  const kpis = sellerKpis(sales, inventory, impact);
  const revenueTrend = aggregateRevenueByDay(sales);
  const categories = aggregateRevenueByCategory(sales);
  const topCategory = categories[0];

  viewContent.innerHTML = `
    <section class="seller-register" aria-label="Seller summary">
      <article class="revenue-register">
        <span>Revenue recovered</span>
        <strong>${money(kpis.totalRevenue)}</strong>
        <small>${kpis.transactions} completed transaction${kpis.transactions === 1 ? "" : "s"}</small>
      </article>
      <dl class="metric-ledger">
        <div><dt>Available listings</dt><dd>${kpis.available}</dd><small>${inventory.length} total listed</small></div>
        <div><dt>Average order</dt><dd>${money(kpis.averageOrder)}</dd><small>Per purchase</small></div>
        <div><dt>Food saved</dt><dd>${quantity(impact.food_saved)} kg</dd><small>Sold, not wasted</small></div>
        <div><dt>CO₂ avoided</dt><dd>${quantity(impact.co2_avoided)} kg</dd><small>Food saved × 2.5</small></div>
        <div><dt>Quantity sold</dt><dd>${quantity(kpis.totalQuantity)}</dd><small>kg / units</small></div>
        <div><dt>Highest sale</dt><dd>${money(kpis.topSale)}</dd><small>Single transaction</small></div>
      </dl>
    </section>

    <section class="analysis-ledger">
      <article class="chart-section">
        <div class="chart-head"><div><h2>Recent revenue</h2><p>Latest 10 selling days</p></div><span class="chart-unit">MYR</span></div>
        ${salesLineChart(revenueTrend)}
      </article>
      <article class="chart-section">
        <div class="chart-head"><div><h2>Category performance</h2><p>Revenue contribution by food category</p></div></div>
        ${categoryBars(categories)}
        <p class="analysis-note">${topCategory ? `<strong>${escapeHtml(topCategory.category)}</strong> currently leads at ${money(topCategory.revenue)}.` : "Category performance appears after the first completed sale."}</p>
      </article>
    </section>`;
}

function inventoryTable(items) {
  return `<div class="table-wrap"><table>
    <thead><tr><th>Name</th><th>Category</th><th>Location</th><th>Days left</th><th>Stock</th><th>Original price</th><th>Discount</th><th>Sale price</th><th>Status</th><th>Actions</th></tr></thead>
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
  setViewHeader("Current stock, pricing, expiry and availability.", "Inventory", `<button class="button button--primary" data-open-add>Add item</button>`);
  const result = await api("seller_inventory", { store_id: state.user.store_id });
  if (state.view !== "inventory") return;

  viewContent.innerHTML = result.items.length
    ? inventoryTable(result.items)
    : emptyState("Your shelf is ready", "Add the first imperfect or near-expiry item to make it available to customers.", `<button class="button button--primary" data-open-add>Add first item</button>`);
}

async function renderSales() {
  setViewHeader("Completed transactions and revenue evidence.", "Sales");
  const result = await api("sales", { store_id: state.user.store_id });
  if (state.view !== "sales") return;

  if (!result.sales.length) {
    viewContent.innerHTML = emptyState("No completed sales", "Purchases from your store will appear here with revenue, order value, category performance, and sales trends.");
    return;
  }

  const sales = result.sales;
  const revenueTrend = aggregateRevenueByDay(sales);
  const categories = aggregateRevenueByCategory(sales);
  const transactionCount = sales.length;
  const averageOrder = transactionCount ? Number(result.total_revenue) / transactionCount : 0;
  const topSale = Math.max(...sales.map(sale => Number(sale.total_amount || 0)), 0);

  viewContent.innerHTML = `
    <section class="sales-register">
      <article class="revenue-register"><span>Total revenue</span><strong>${money(result.total_revenue)}</strong><small>Recovered from rescued inventory</small></article>
      <dl class="metric-ledger metric-ledger--sales">
        <div><dt>Transactions</dt><dd>${transactionCount}</dd><small>Completed purchases</small></div>
        <div><dt>Average order</dt><dd>${money(averageOrder)}</dd><small>Per transaction</small></div>
        <div><dt>Quantity sold</dt><dd>${quantity(result.total_quantity_sold)}</dd><small>kg / units</small></div>
        <div><dt>Highest sale</dt><dd>${money(topSale)}</dd><small>Single transaction</small></div>
      </dl>
    </section>

    <section class="analysis-ledger">
      <article class="chart-section">
        <div class="chart-head"><div><h2>Sales over time</h2><p>Completed sales grouped by day</p></div><span class="chart-unit">MYR</span></div>
        ${salesLineChart(revenueTrend)}
      </article>
      <article class="chart-section">
        <div class="chart-head"><div><h2>Revenue contribution</h2><p>Revenue by food category</p></div></div>
        ${categoryBars(categories)}
      </article>
    </section>

    <section class="section-block">
      <div class="section-heading"><h2>Completed transactions</h2></div>
      <div class="table-wrap"><table>
        <thead><tr><th>Date</th><th>Item</th><th>Location</th><th>Category</th><th>Quantity</th><th>Unit price</th><th>Total</th></tr></thead>
        <tbody>${sales.map(sale => `<tr>
          <td>${escapeHtml(shortDate(sale.created_at))}</td>
          <td><span class="item-name">${escapeHtml(sale.item_name)}</span></td>
          <td>${escapeHtml(sale.location)}</td>
          <td>${escapeHtml(sale.category)}</td>
          <td>${quantity(sale.quantity_bought)}</td>
          <td>${money(sale.unit_price)}</td>
          <td class="sale-price">${money(sale.total_amount)}</td>
        </tr>`).join("")}</tbody>
      </table></div>
    </section>`;
}

async function renderImpact() {
  setViewHeader("Measured from completed rescued-food sales.", "Impact");
  const result = await api("impact", { store_id: state.user.store_id });
  if (state.view !== "impact") return;

  const impact = result.impact;
  const index = String(impact.impact_index || "NEEDS IMPROVEMENT").replace(/[🌟👍⚠️]/gu, "").trim();

  viewContent.innerHTML = `<section class="impact-layout">
    <header class="impact-index"><span>Impact index</span><strong>${escapeHtml(index)}</strong><p>Calculated from rescued food sold through this store.</p></header>
    <dl class="impact-stats">
      <div class="impact-stat"><dt>Food saved</dt><dd>${quantity(impact.food_saved)} kg</dd></div>
      <div class="impact-stat"><dt>Revenue recovered</dt><dd>${money(impact.revenue_recovered)}</dd></div>
      <div class="impact-stat"><dt>CO₂ avoided</dt><dd>${quantity(impact.co2_avoided)} kg</dd><small>Food saved × 2.5</small></div>
      <div class="impact-stat"><dt>Transactions</dt><dd>${impact.transactions}</dd></div>
    </dl>
  </section>`;
}

function productCards(items) {
  return `<div class="market-list">${items.map(item => `<article class="market-item">
    <div class="market-item__identity"><span class="category-label">${escapeHtml(item.category)}</span><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.store_name)}</p></div>
    <div class="market-item__fact"><span>Days left</span><strong class="expiry ${Number(item.days_left) <= 2 ? "expiry--urgent" : ""}">${escapeHtml(item.days_left)}</strong></div>
    <div class="market-item__fact"><span>Available</span><strong>${quantity(item.quantity)} kg/u</strong></div>
    <div class="market-item__price"><strong>${money(item.new_price)}</strong><small><span class="old-price">${money(item.original_price)}</span> original</small></div>
    <span class="discount-tag">Save ${quantity(item.discount_percent)}%</span>
    <button class="button button--primary button--small" data-buy-item="${escapeHtml(item.id)}">Buy</button>
  </article>`).join("")}</div>`;
}

async function renderMarket() {
  setViewHeader(`Available food in ${state.location}.`, "Market");
  viewContent.innerHTML = `<div class="market-toolbar">
    <label>Shopping location<select id="market-location">${locations.map(location => `<option ${location === state.location ? "selected" : ""}>${location}</option>`).join("")}</select></label>
    <p class="market-note">Available stock changes after each purchase. Prices are shown in Malaysian Ringgit and already include the dynamic rescue discount.</p>
  </div>${loadingState()}`;

  const result = await api("market", { location: state.location });
  if (state.view !== "market") return;

  state.marketItems = result.items;
  viewContent.querySelector(".loading-state").outerHTML = result.items.length
    ? productCards(result.items)
    : emptyState("No food available here today", `There are currently no available items in ${state.location}. Try another location.`);
}

async function renderPurchases() {
  setViewHeader("Receipts from completed purchases.", "My purchases");
  const result = await api("purchase_history", { customer_id: state.user.id });
  if (state.view !== "my-purchases") return;

  if (!result.purchases.length) {
    viewContent.innerHTML = emptyState("No purchases yet", "When you rescue an item from the market, your receipt will appear here.", `<button class="button button--primary" data-view="market">Browse market</button>`);
    return;
  }

  viewContent.innerHTML = `<div class="table-wrap"><table>
    <thead><tr><th>Item</th><th>Store</th><th>Location</th><th>Quantity</th><th>Unit price</th><th>Total</th><th>Date</th></tr></thead>
    <tbody>${result.purchases.map(purchase => `<tr>
      <td><span class="item-name">${escapeHtml(purchase.item_name)}</span></td>
      <td>${escapeHtml(purchase.store_name)}</td>
      <td>${escapeHtml(purchase.location)}</td>
      <td>${quantity(purchase.quantity_bought)}</td>
      <td>${money(purchase.unit_price)}</td>
      <td class="sale-price">${money(purchase.total_amount)}</td>
      <td>${escapeHtml(shortDate(purchase.created_at))}</td>
    </tr>`).join("")}</tbody>
  </table></div>`;
}

async function renderSupport() {
  setViewHeader("Ask about food, discounts, notifications or complaints.", "Support");
  const welcome = state.chatHistory.length ? "" : `<div class="chat-message">Ask JimatRasa about discounts, food storage, notifications, complaints, or how the rescued-food market works.</div>`;

  viewContent.innerHTML = `<div class="chat-shell">
    <div id="chat-log" class="chat-log">${welcome}${state.chatHistory.map(message => `<div class="chat-message chat-message--${message.role === "user" ? "user" : "assistant"}">${escapeHtml(message.content)}</div>`).join("")}</div>
    <form id="chat-form" class="chat-form"><label class="is-hidden" for="chat-input">Message</label><input id="chat-input" name="message" placeholder="Type your question..." autocomplete="off" required><button class="button button--primary" type="submit">Send</button></form>
  </div>`;

  const log = document.querySelector("#chat-log");
  log.scrollTop = log.scrollHeight;
}

function openModal(title, content) {
  modalOpener = document.activeElement;
  modalTitle.textContent = title;
  modalBody.innerHTML = content;
  modal.classList.remove("is-hidden");
  appShell.setAttribute("inert", "");
  authScreen.setAttribute("inert", "");
  document.body.style.overflow = "hidden";
  window.setTimeout(() => modal.querySelector("input, select, button")?.focus(), 20);
}

function closeModal() {
  modal.classList.add("is-hidden");
  appShell.removeAttribute("inert");
  authScreen.removeAttribute("inert");
  document.body.style.overflow = "";
  modalBody.innerHTML = "";
  modalOpener?.focus();
  modalOpener = null;
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
      <label>Original price (MYR)<input name="original_price" type="number" min="0.01" step="0.01" required></label>
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

document.querySelectorAll("[data-auth-tab]").forEach(button => {
  button.addEventListener("click", () => switchAuth(button.dataset.authTab));
});

document.querySelectorAll('input[name="role"]').forEach(input => {
  input.addEventListener("change", () => setSellerFields(input.value === "seller" && input.checked));
});

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
    setSellerFields(false);
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
      const result = await api("buy", {
        customer_id: state.user.id,
        location: state.location,
        item_id: item.id,
        quantity: amount,
      });
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
    log.insertAdjacentHTML("beforeend", `<div class="chat-message chat-message--user">${escapeHtml(message)}</div><div id="chat-loading" class="chat-message chat-message--loading">JimatRasa support is thinking...</div>`);
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
  if (modal.classList.contains("is-hidden")) return;
  if (event.key === "Escape") closeModal();
  if (event.key === "Tab") {
    const focusable = [...modal.querySelectorAll("button, input, select, textarea, [href], [tabindex]:not([tabindex='-1'])")]
      .filter(element => !element.disabled);
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
});

if (state.user) showApp();
else showAuth("login");
