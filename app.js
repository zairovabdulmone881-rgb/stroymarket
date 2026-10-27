/* ============================================
   STROY LUXE — Логика каталога + корзина
============================================ */

const PRODUCTS = [
  { id: 1,  name: 'Цемент М500, 50 кг',           category: 'Стройматериалы', price: 450,  emoji: '🧱' },
  { id: 2,  name: 'Кирпич керамический, шт',       category: 'Стройматериалы', price: 35,   emoji: '🧱' },
  { id: 3,  name: 'Пескобетон М300, 40 кг',        category: 'Стройматериалы', price: 320,  emoji: '⚪' },
  { id: 4,  name: 'Гипсокартон 2500×1200×12.5',    category: 'Отделка',        price: 620,  emoji: '📐' },
  { id: 5,  name: 'Штукатурка гипсовая, 30 кг',    category: 'Отделка',        price: 540,  emoji: '🎨' },
  { id: 6,  name: 'Плитка керамическая, м²',       category: 'Отделка',        price: 890,  emoji: '🔲' },
  { id: 7,  name: 'Грунтовка глубокого проник., 10 л', category: 'Отделка',    price: 480,  emoji: '🪣' },
  { id: 8,  name: 'Перфоратор SDS-Plus 800 Вт',    category: 'Инструмент',     price: 6900, emoji: '🔧' },
  { id: 9,  name: 'Шуруповёрт аккум. 18В',         category: 'Инструмент',     price: 5400, emoji: '🪛' },
  { id: 10, name: 'Уровень лазерный',              category: 'Инструмент',     price: 3200, emoji: '📏' },
  { id: 11, name: 'Кабель ВВГнг 3×2.5, м',         category: 'Электрика',      price: 95,   emoji: '⚡' },
  { id: 12, name: 'Розетка с заземлением',         category: 'Электрика',      price: 210,  emoji: '🔌' },
];

const state = { category: 'Все', search: '', sort: 'default' };
let cart = loadCart();

const $ = (id) => document.getElementById(id);
const grid = $('grid');
const filtersEl = $('filters');
const searchInput = $('searchInput');
const sortSelect = $('sortSelect');
const resultsCount = $('resultsCount');
const cartCount = $('cartCount');
const cartEl = $('cart');
const overlay = $('overlay');
const cartBody = $('cartBody');
const cartTotal = $('cartTotal');
const toast = $('toast');

function loadCart() {
  try { return JSON.parse(localStorage.getItem('stroyluxe_cart')) || {}; }
  catch { return {}; }
}
function saveCart() {
  localStorage.setItem('stroyluxe_cart', JSON.stringify(cart));
}

function renderFilters() {
  const cats = ['Все', ...new Set(PRODUCTS.map(p => p.category))];
  filtersEl.innerHTML = cats.map(c =>
    `<button class="chip ${c === state.category ? 'active' : ''}" data-cat="${c}">${c}</button>`
  ).join('');
  
  filtersEl.querySelectorAll('.chip').forEach(btn => {
    btn.onclick = () => {
      state.category = btn.dataset.cat;
      renderFilters();
      renderProducts();
    };
  });
}

function getVisibleProducts() {
  let list = PRODUCTS.filter(p => {
    const byCat = state.category === 'Все' || p.category === state.category;
    const bySearch = p.name.toLowerCase().includes(state.search.toLowerCase());
    return byCat && bySearch;
  });

  if (state.sort === 'price-asc')  list.sort((a, b) => a.price - b.price);
  if (state.sort === 'price-desc') list.sort((a, b) => b.price - a.price);
  if (state.sort === 'name')       list.sort((a, b) => a.name.localeCompare(b.name, 'ru'));

  return list;
}

function renderProducts() {
  const list = getVisibleProducts();
  resultsCount.textContent = `Товаров: ${list.length}`;

  if (!list.length) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px; color: #888;">Ничего не найдено 😕</div>`;
    return;
  }

  grid.innerHTML = list.map(p => `
    <div class="card">
      <div class="card-img">${p.emoji}</div>
      <div class="card-body">
        <div class="card-cat">${p.category}</div>
        <div class="card-name">${p.name}</div>
        <div class="card-price">${formatPrice(p.price)}</div>
        <button class="btn-add ${cart[p.id] ? 'in-cart' : ''}" data-id="${p.id}">
          ${cart[p.id] ? '✓ В корзине' : 'В корзину'}
        </button>
      </div>
    </div>
  `).join('');

  grid.querySelectorAll('.btn-add').forEach(btn => {
    btn.onclick = () => addToCart(Number(btn.dataset.id));
  });
}

function addToCart(id) {
  cart[id] = (cart[id] || 0) + 1;
  saveCart();
  updateCartCount();
  renderProducts();
  renderCart();
  showToast(`✓ Товар добавлен`);
}

function changeQty(id, delta) {
  cart[id] = (cart[id] || 0) + delta;
  if (cart[id] <= 0) delete cart[id];
  saveCart();
  updateCartCount();
  renderCart();
  renderProducts();
}

function cartTotalSum() {
  return Object.entries(cart).reduce((sum, [id, qty]) => {
    const p = PRODUCTS.find(x => x.id === Number(id));
    return sum + (p ? p.price * qty : 0);
  }, 0);
}

function updateCartCount() {
  const count = Object.values(cart).reduce((a, b) => a + b, 0);
  cartCount.textContent = count;
  cartCount.style.display = count ? 'inline-block' : 'none';
}

function renderCart() {
  const ids = Object.keys(cart);
  if (!ids.length) {
    cartBody.innerHTML = `<div style="text-align:center; padding: 30px; color: #888;">Корзина пуста 🛒</div>`;
    cartTotal.textContent = '0 ₽';
    $('checkoutBtn').disabled = true;
    return;
  }

  cartBody.innerHTML = ids.map(id => {
    const p = PRODUCTS.find(x => x.id === Number(id));
    if (!p) return '';
    return `
      <div class="cart-item">
        <div class="cart-item-emoji">${p.emoji}</div>
        <div class="cart-item-info">
          <div class="cart-item-name">${p.name}</div>
          <div class="cart-item-price">${formatPrice(p.price)}</div>
        </div>
        <div class="qty">
          <button data-act="minus" data-id="${id}">−</button>
          <span>${cart[id]}</span>
          <button data-act="plus" data-id="${id}">+</button>
        </div>
      </div>
    `;
  }).join('');

  cartTotal.textContent = formatPrice(cartTotalSum());
  $('checkoutBtn').disabled = false;

  cartBody.querySelectorAll('button').forEach(btn => {
    const id = Number(btn.dataset.id);
    const act = btn.dataset.act;
    btn.onclick = () => {
      if (act === 'plus') changeQty(id, 1);
      if (act === 'minus') changeQty(id, -1);
    };
  });
}

function openCart() {
  cartEl.classList.add('open');
  overlay.classList.add('open');
}
function closeCartPanel() {
  cartEl.classList.remove('open');
  overlay.classList.remove('open');
}

let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2000);
}

function formatPrice(n) {
  return n.toLocaleString('ru-RU') + ' ₽';
}

searchInput.oninput = (e) => { state.search = e.target.value; renderProducts(); };
sortSelect.onchange = (e) => { state.sort = e.target.value; renderProducts(); };
$('cartBtn').onclick = openCart;
$('closeCart').onclick = closeCartPanel;
overlay.onclick = closeCartPanel;
$('checkoutBtn').onclick = () => { showToast('Скоро здесь будет оформление заказа!'); };

renderFilters();
renderProducts();
renderCart();
updateCartCount();
