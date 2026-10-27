/* ============================================
   STROY LUXE — Полный движок (200+ товаров)
============================================ */

// Генератор базы товаров (имитация базы данных)
const generateProducts = () => {
  const categories = [
    { name: 'Стройматериалы', keywords: ['cement', 'brick', 'concrete', 'lumber', 'sand'] },
    { name: 'Отделка', keywords: ['paint', 'wallpaper', 'tile', 'laminate', 'plaster'] },
    { name: 'Инструмент', keywords: ['drill', 'screwdriver', 'hammer', 'saw', 'tool'] },
    { name: 'Электрика', keywords: ['cable', 'socket', 'switch', 'lamp', 'wire'] },
    { name: 'Сантехника', keywords: ['faucet', 'sink', 'toilet', 'pipe', 'shower'] },
    { name: 'Крепёж', keywords: ['screw', 'nail', 'bolt', 'anchor', 'fastener'] },
    { name: 'Сад и отдых', keywords: ['garden', 'shovel', 'rake', 'hose', 'grass'] },
    { name: 'Климат', keywords: ['heater', 'fan', 'conditioner', 'radiator', 'air'] }
  ];

  const brands = ['Bosch', 'Makita', 'Knauf', 'Ceresit', 'Tarkett', 'Grohe', 'Schneider Electric', 'Petrovich', 'Rockwool', 'Tikkurila', 'Husqvarna', 'Ballu'];
  const products = [];
  let id = 1;

  categories.forEach(cat => {
    cat.keywords.forEach((keyword, idx) => {
      for (let i = 0; i < 6; i++) { // По 6 вариаций на ключевое слово
        const brand = brands[Math.floor(Math.random() * brands.length)];
        const price = Math.floor(Math.random() * 15000) + 100;
        const hasBadge = Math.random() > 0.7;
        const badgeType = ['Хит', 'Скидка', 'Новинка'][Math.floor(Math.random() * 3)];
        
        products.push({
          id: id++,
          name: `${keyword.charAt(0).toUpperCase() + keyword.slice(1)} ${brand} ${Math.floor(Math.random() * 100)}`,
          category: cat.name,
          brand: brand,
          price: price,
          description: `Высококачественный товар от бренда ${brand}. Отлично подходит для профессионального и бытового использования. Гарантия качества от производителя.`,
          images: [
            `https://source.unsplash.com/400x400/?${keyword},construction,material&sig=${id}a`,
            `https://source.unsplash.com/400x400/?${keyword},tool,work&sig=${id}b`,
            `https://source.unsplash.com/400x400/?${keyword},industry&sig=${id}c`
          ],
          specs: {
            'Производитель': brand,
            'Категория': cat.name,
            'Вес': `${Math.floor(Math.random() * 15) + 1} кг`,
            'Гарантия': `${Math.floor(Math.random() * 3) + 1} год(а)`,
            'Страна': 'Россия',
            'Артикул': `ART-${id}`
          },
          badge: hasBadge ? badgeType : null
        });
      }
    });
  });
  return products;
};

const PRODUCTS = generateProducts();

const state = { category: 'Все', search: '', sort: 'default' };
let cart = loadCart();

const $ = (id) => document.getElementById(id);
const app = $('app');
const cartCountEl = $('cartCount');
const cartEl = $('cart');
const overlay = $('overlay');
const cartBody = $('cartBody');
const cartTotalEl = $('cartTotal');
const toast = $('toast');
const searchInput = $('searchInput');

// ===== LOCALSTORAGE =====
function loadCart() {
  try { return JSON.parse(localStorage.getItem('stroyluxe_cart_v3')) || {}; }
  catch { return {}; }
}
function saveCart() {
  localStorage.setItem('stroyluxe_cart_v3', JSON.stringify(cart));
}

// ===== РОУТИНГ =====
function router() {
  const hash = window.location.hash || '#/';
  app.innerHTML = '';
  window.scrollTo(0, 0);

  if (hash === '#/') {
    renderHomePage();
  } else if (hash === '#/catalog') {
    renderCatalogPage();
  } else if (hash.startsWith('#/product/')) {
    const id = parseInt(hash.split('/')[2]);
    renderProductPage(id);
  } else if (hash === '#/privacy') {
    renderPrivacyPage();
  } else if (hash === '#/delivery') {
    renderDeliveryPage();
  } else if (hash === '#/contacts') {
    renderContactsPage();
  } else {
    app.innerHTML = '<div class="page-section"><div class="container"><h1>404 — Страница не найдена</h1><br><a href="#/" class="btn-primary">На главную</a></div></div>';
  }
  updateCartCount();
}

// ===== ГЛАВНАЯ =====
function renderHomePage() {
  const bannerHtml = `
    <div class="hero-banner">
      <div>
        <h2>🔥 Грандиозная распродажа!</h2>
        <p>Скидки до 40% на электроинструмент и отделочные материалы. Только до конца месяца.</p>
        <a href="#/catalog" class="btn-primary">Перейти в каталог</a>
      </div>
      <div class="hero-banner-img">🛠️</div>
    </div>
  `;

  const popular = PRODUCTS.slice(0, 8);
  const cardsHtml = popular.map(p => createProductCard(p)).join('');

  app.innerHTML = `
    <div class="page-section">
      <div class="container">
        ${bannerHtml}
        <h2 class="page-title">Популярные товары</h2>
        <div class="grid">${cardsHtml}</div>
        <div style="text-align: center; margin-top: 30px;">
          <a href="#/catalog" class="btn-primary" style="padding: 14px 40px;">Смотреть весь каталог</a>
        </div>
      </div>
    </div>
  `;
}

// ===== КАТАЛОГ =====
function renderCatalogPage() {
  const cats = ['Все', ...new Set(PRODUCTS.map(p => p.category))];
  const filtersHtml = cats.map(c =>
    `<button class="chip ${c === state.category ? 'active' : ''}" data-cat="${c}">${c}</button>`
  ).join('');

  app.innerHTML = `
    <div class="page-section">
      <div class="container">
        <h2 class="page-title">Каталог товаров</h2>
        <nav class="filters" id="filters">${filtersHtml}</nav>
        <div class="toolbar">
          <span id="resultsCount">Найдено: 0</span>
          <select id="sortSelect">
            <option value="default">По умолчанию</option>
            <option value="price-asc">Цена ↑</option>
            <option value="price-desc">Цена ↓</option>
            <option value="name">По названию</option>
          </select>
        </div>
        <div class="grid" id="grid"></div>
      </div>
    </div>
  `;

  document.querySelectorAll('.chip').forEach(btn => {
    btn.onclick = () => {
      state.category = btn.dataset.cat;
      renderCatalogPage();
    };
  });

  $('sortSelect').onchange = (e) => { state.sort = e.target.value; renderProductsGrid(); };
  renderProductsGrid();
}

function renderProductsGrid() {
  const grid = $('grid');
  if (!grid) return;

  let list = PRODUCTS.filter(p => {
    const byCat = state.category === 'Все' || p.category === state.category;
    const bySearch = p.name.toLowerCase().includes(state.search.toLowerCase()) || p.brand.toLowerCase().includes(state.search.toLowerCase());
    return byCat && bySearch;
  });

  if (state.sort === 'price-asc') list.sort((a, b) => a.price - b.price);
  if (state.sort === 'price-desc') list.sort((a, b) => b.price - a.price);
  if (state.sort === 'name') list.sort((a, b) => a.name.localeCompare(b.name, 'ru'));

  $('resultsCount').textContent = `Найдено: ${list.length}`;

  if (!list.length) {
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px; color: #64748b;">Ничего не найдено 😕</div>`;
    return;
  }

  // Показываем первые 80 для скорости
  const limitedList = list.slice(0, 80);
  grid.innerHTML = limitedList.map(p => createProductCard(p)).join('');

  grid.querySelectorAll('.card').forEach(card => {
    card.onclick = (e) => {
      if (e.target.classList.contains('btn-add')) return;
      window.location.hash = `#/product/${card.dataset.id}`;
    };
  });

  grid.querySelectorAll('.btn-add').forEach(btn => {
    btn.onclick = (e) => {
      e.stopPropagation();
      addToCart(Number(btn.dataset.id));
    };
  });
}

function createProductCard(p) {
  const badgeHtml = p.badge ? `<div class="badge badge-${p.badge === 'Хит' ? 'hit' : p.badge === 'Скидка' ? 'sale' : 'new'}">${p.badge}</div>` : '';
  return `
    <div class="card" data-id="${p.id}">
      ${badgeHtml}
      <div class="card-img">
        <img src="${p.images[0]}" alt="${p.name}" loading="lazy" onerror="this.src='https://source.unsplash.com/400x400/?construction'">
      </div>
      <div class="card-body">
        <div class="card-cat">${p.category}</div>
        <div style="font-size: 11px; color: #94a3b8; margin-bottom: 4px;">${p.brand}</div>
        <div class="card-name">${p.name}</div>
        <div class="card-price">${formatPrice(p.price)}</div>
        <button class="btn-add" data-id="${p.id}">В корзину</button>
      </div>
    </div>
  `;
}

// ===== СТРАНИЦА ТОВАРА =====
function renderProductPage(id) {
  const product = PRODUCTS.find(p => p.id === id);
  if (!product) {
    app.innerHTML = '<div class="page-section"><div class="container"><h1>Товар не найден</h1></div></div>';
    return;
  }

  const specsHtml = Object.entries(product.specs).map(([key, value]) =>
    `<tr><td>${key}</td><td>${value}</td></tr>`
  ).join('');

  const thumbsHtml = product.images.map((img, idx) =>
    `<img src="${img}" class="${idx === 0 ? 'active' : ''}" data-index="${idx}" onerror="this.src='https://source.unsplash.com/400x400/?construction'">`
  ).join('');

  app.innerHTML = `
    <div class="page-section">
      <div class="container">
        <div class="product-page">
          <div class="product-gallery">
            <div class="product-main-img">
              <img id="mainImage" src="${product.images[0]}" alt="${product.name}" onerror="this.src='https://source.unsplash.com/400x400/?construction'">
            </div>
            <div class="product-thumbs" id="thumbs">
              ${thumbsHtml}
            </div>
          </div>
          <div class="product-info">
            <div class="product-brand">${product.brand} | Артикул: ${product.specs['Артикул']}</div>
            <h1>${product.name}</h1>
            <div class="product-price">${formatPrice(product.price)}</div>
            <p style="font-size: 15px; color: #64748b; line-height: 1.6;">${product.description}</p>
            
            <div class="product-actions">
              <button class="btn-primary" id="addToCartBtn" style="flex:1;">В корзину</button>
              <button class="btn-secondary" id="buyNowBtn" style="flex:1;">Купить сейчас</button>
            </div>

            <div class="product-specs">
              <h3>Характеристики</h3>
              <table class="specs-table">
                ${specsHtml}
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.querySelectorAll('#thumbs img').forEach(thumb => {
    thumb.onclick = () => {
      document.querySelectorAll('#thumbs img').forEach(t => t.classList.remove('active'));
      thumb.classList.add('active');
      $('mainImage').src = product.images[thumb.dataset.index];
    };
  });

  $('addToCartBtn').onclick = () => addToCart(product.id);
  $('buyNowBtn').onclick = () => { addToCart(product.id); openCart(); };
}

// ===== КОНТАКТЫ =====
function renderContactsPage() {
  app.innerHTML = `
    <div class="page-section">
      <div class="container">
        <div class="contacts-page">
          <h2 class="page-title">Контакты</h2>
          
          <div class="contact-card">
            <h3>📞 Прямой номер телефона</h3>
            <a href="tel:+79966889979" style="font-size: 20px; font-weight: bold; color: #1e293b;">+7 (966) 888-99-79</a>
          </div>

          <div class="contact-card">
            <h3>💬 WhatsApp</h3>
            <p style="margin-bottom: 10px; color: #64748b; font-size: 14px;">Напишите нам, и мы ответим в течение 15 минут.</p>
            <a href="https://wa.me/79966889979" target="_blank" style="display:inline-block; padding: 12px 24px; background: #25D366; color: white; border-radius: 8px; text-decoration: none; font-weight: bold;">Открыть WhatsApp</a>
          </div>

          <div class="contact-card">
            <h3>✉️ Электронная почта</h3>
            <a href="mailto:zairovabdulmone01@gmail.com" style="font-size: 18px;">zairovabdulmone01@gmail.com</a>
          </div>
        </div>
      </div>
    </div>
  `;
}

// ===== ТЕКСТОВЫЕ СТРАНИЦЫ =====
function renderPrivacyPage() {
  app.innerHTML = `
    <div class="page-section">
      <div class="container">
        <div class="text-page">
          <h1>Политика конфиденциальности</h1>
          <p>Настоящая Политика конфиденциальности действует в отношении всей информации, которую сайт STROY LUXE может получить о Пользователе.</p>
          <h3>1. Какие данные мы собираем</h3>
          <p>Мы собираем только те данные, которые вы добровольно оставляете при оформлении заказа: имя, номер телефона. Корзина сохраняется в вашем браузере (localStorage).</p>
          <h3>2. Как мы используем данные</h3>
          <p>Ваши данные используются исключительно для связи с вами и подтверждения заказа. Мы не передаем их третьим лицам.</p>
          <h3>3. Контакты</h3>
          <p>По вопросам: zairovabdulmone01@gmail.com</p>
          <br><a href="#/" class="btn-primary">На главную</a>
        </div>
      </div>
    </div>
  `;
}

function renderDeliveryPage() {
  app.innerHTML = `
    <div class="page-section">
      <div class="container">
        <div class="text-page">
          <h1>Доставка и оплата</h1>
          <h3>Доставка</h3>
          <ul>
            <li>Курьерская доставка по городу — от 500 ₽.</li>
            <li>Самовывоз со склада — бесплатно.</li>
            <li>Транспортные компании по России.</li>
          </ul>
          <h3>Оплата</h3>
          <ul>
            <li>Наличными при получении.</li>
            <li>Картой онлайн (скоро).</li>
            <li>Безналичный расчет для юрлиц.</li>
          </ul>
          <br><a href="#/" class="btn-primary">На главную</a>
        </div>
      </div>
    </div>
  `;
}

// ===== КОРЗИНА =====
function addToCart(id) {
  cart[id] = (cart[id] || 0) + 1;
  saveCart();
  updateCartCount();
  if (window.location.hash === '#/catalog') renderProductsGrid();
  renderCart();
  showToast('✓ Товар добавлен в корзину');
}

function changeQty(id, delta) {
  cart[id] = (cart[id] || 0) + delta;
  if (cart[id] <= 0) delete cart[id];
  saveCart();
  updateCartCount();
  renderCart();
  if (window.location.hash === '#/catalog') renderProductsGrid();
}

function cartTotalSum() {
  return Object.entries(cart).reduce((sum, [id, qty]) => {
    const p = PRODUCTS.find(x => x.id === Number(id));
    return sum + (p ? p.price * qty : 0);
  }, 0);
}

function updateCartCount() {
  const count = Object.values(cart).reduce((a, b) => a + b, 0);
  cartCountEl.textContent = count;
}

function renderCart() {
  const ids = Object.keys(cart);
  if (!ids.length) {
    cartBody.innerHTML = `<div style="text-align:center; padding: 30px; color: #94a3b8;">Корзина пуста 🛒</div>`;
    cartTotalEl.textContent = '0 ₽';
    $('checkoutBtn').disabled = true;
    return;
  }

  cartBody.innerHTML = ids.map(id => {
    const p = PRODUCTS.find(x => x.id === Number(id));
    if (!p) return '';
    return `
      <div class="cart-item">
        <div class="cart-item-img">
          <img src="${p.images[0]}" alt="${p.name}" onerror="this.src='https://source.unsplash.com/400x400/?construction'">
        </div>
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

  cartTotalEl.textContent = formatPrice(cartTotalSum());
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

function openCart() { cartEl.classList.add('open'); overlay.classList.add('open'); }
function closeCartPanel() { cartEl.classList.remove('open'); overlay.classList.remove('open'); }

// ===== ОФОРМЛЕНИЕ =====
$('checkoutBtn').onclick = () => {
  closeCartPanel();
  $('checkoutModal').classList.add('open');
};
$('closeModal').onclick = () => $('checkoutModal').classList.remove('open');

$('orderForm').onsubmit = (e) => {
  e.preventDefault();
  const name = $('orderName').value;
  const total = formatPrice(cartTotalSum());
  showToast(`Спасибо, ${name}! Заказ на ${total} принят.`);
  cart = {};
  saveCart();
  updateCartCount();
  renderCart();
  if (window.location.hash === '#/catalog') renderProductsGrid();
  $('checkoutModal').classList.remove('open');
  $('orderForm').reset();
};

// ===== УТИЛИТЫ =====
let toastTimer;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 2500);
}
function formatPrice(n) { return n.toLocaleString('ru-RU') + ' ₽'; }

// ===== СОБЫТИЯ =====
searchInput.oninput = (e) => {
  state.search = e.target.value;
  if (window.location.hash !== '#/catalog') window.location.hash = '#/catalog';
  setTimeout(renderProductsGrid, 10);
};
$('cartBtn').onclick = openCart;
$('closeCart').onclick = closeCartPanel;
overlay.onclick = closeCartPanel;

// ===== ЗАПУСК =====
window.addEventListener('hashchange', router);
router();
renderCart();
updateCartCount();
