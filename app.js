
var PRODUCTS = [];
var FALLBACK = 'data:image/svg+xml;utf8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect width="400" height="400" fill="#1a1816"/><text x="200" y="210" fill="#d4b58e" font-size="26" text-anchor="middle" font-family="serif">STROY LUXE</text></svg>');

var catImages = {
  'Стройматериалы': ['https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600&q=80', 'https://images.unsplash.com/photo-1518085250840-4b301bed7a7f?w=600&q=80'],
  'Отделка': ['https://images.unsplash.com/photo-1562663474-6cbb3eaa4d14?w=600&q=80', 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600&q=80'],
  'Инструмент': ['https://images.unsplash.com/photo-1530124566582-a61cef2176e0?w=600&q=80', 'https://images.unsplash.com/photo-1572981779307-38b8cabb2407?w=600&q=80'],
  'Электрика': ['https://images.unsplash.com/photo-1558449028-b53a39d100fc?w=600&q=80', 'https://images.unsplash.com/photo-1544724569-5f546fd6f2b5?w=600&q=80'],
  'Сантехника': ['https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=600&q=80', 'https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=600&q=80'],
  'Крепёж': ['https://images.unsplash.com/photo-1605810230434-7631ac76ec81?w=600&q=80', 'https://images.unsplash.com/photo-1530124566582-a61cef2176e0?w=600&q=80']
};

var cats = [
  { name: 'Стройматериалы', brands: ['Евроцемент', 'Волма', 'Rockwool', 'Petrovich', 'Knauf'], items: [
    ['Цемент ПЦ 500 Д0', 'меш.', 380, 620, ['25 кг', '40 кг', '50 кг'], 'Портландцемент для бетонных и ремонтных работ, фундаментов и стяжек. Высокая прочность и морозостойкость.'],
    ['Кирпич керамический одинарный', 'шт.', 14, 28, ['М150', 'М175', 'М200'], 'Полнотелый кирпич для кладки стен, перегородок и каминов. Равномерный обжиг, устойчив к влаге.'],
    ['Блок газобетонный D500', 'шт.', 90, 260, ['600x200x100 мм', '600x250x300 мм', '600x200x300 мм'], 'Лёгкий стеновой блок автоклавного твердения. Хорошо держит тепло, прост в резке и кладке.'],
    ['Утеплитель минераловатный', 'упак.', 650, 1900, ['50 мм', '100 мм', '150 мм'], 'Негорючие базальтовые плиты для утепления стен, кровли и перегородок. Звукоизоляция в комплекте.'],
    ['Арматура стальная А500С', 'м', 55, 140, ['8 мм', '10 мм', '12 мм'], 'Рифлёная арматура для армирования фундаментов, плит перекрытия и стяжек.'],
    ['Доска строганая сухая', 'шт.', 280, 950, ['20x95x3000 мм', '25x120x3000 мм', '40x140x3000 мм'], 'Хвойная доска камерной сушки, обработана со всех сторон. Подходит для отделки и каркасов.']
  ] },
  { name: 'Отделка', brands: ['Dulux', 'Tikkurila', 'Knauf', 'Tarkett', 'Ceresit'], items: [
    ['Штукатурка гипсовая', 'меш.', 420, 780, ['10 кг', '25 кг', '30 кг'], 'Гипсовая смесь для машинного и ручного нанесения внутри помещений. Ровная поверхность под покраску.'],
    ['Шпаклёвка финишная', 'ведро', 350, 1450, ['5 кг', '15 кг', '25 кг'], 'Готовая полимерная шпаклёвка для тонкослойного выравнивания стен и потолков под обои и краску.'],
    ['Краска интерьерная водоэмульсионная', 'банка', 590, 4200, ['2,5 л', '5 л', '9 л'], 'Матовая моющаяся краска без резкого запаха для стен и потолков в жилых комнатах.'],
    ['Ламинат 33 класс', 'м²', 650, 1650, ['8 мм', '10 мм', '12 мм'], 'Износостойкое покрытие с замковым соединением. Подходит для тёплых полов.'],
    ['Плитка керамическая настенная', 'м²', 520, 2400, ['20x30 см', '30x60 см', '60x60 см'], 'Глазурованная плитка для ванных и кухонь. Устойчива к влаге и бытовой химии.'],
    ['Обои флизелиновые под покраску', 'рулон', 690, 2900, ['0,53x10 м', '1,06x10 м', '1,06x25 м'], 'Прочные обои с фактурным рисунком, выдерживают до 10 перекрашиваний.']
  ] },
  { name: 'Инструмент', brands: ['Bosch', 'Makita', 'DeWalt', 'Hilti', 'Зубр'], items: [
    ['Перфоратор SDS-plus', 'шт.', 6500, 28900, ['650 Вт', '800 Вт', '1100 Вт'], 'Сетевой перфоратор с тремя режимами работы: сверление, ударное сверление, долбление.'],
    ['Дрель-шуруповёрт аккумуляторная', 'шт.', 4900, 19900, ['12 В', '18 В', '18 В, 2 АКБ'], 'Компактный шуруповёрт с регулировкой момента и подсветкой рабочей зоны, в кейсе.'],
    ['Углошлифовальная машина', 'шт.', 3200, 12900, ['125 мм', '150 мм', '230 мм'], 'УШМ для резки и шлифовки металла, камня и плитки. Защитный кожух и плавный пуск.'],
    ['Лобзик электрический', 'шт.', 3900, 11500, ['500 Вт', '600 Вт', '720 Вт'], 'Точный распил дерева, ДСП и пластика. Маятниковый ход и пылеотвод.'],
    ['Лазерный нивелир', 'шт.', 3500, 24900, ['2 линии', '3 линии', 'ротационный 360°'], 'Строит ровные горизонтальные и вертикальные линии на стенах и полу. Самовыравнивание.'],
    ['Набор бит и свёрл', 'набор', 490, 3900, ['32 предмета', '56 предметов', '100 предметов'], 'Универсальный набор для дерева, металла и бетона в пластиковом кейсе.']
  ] },
  { name: 'Электрика', brands: ['Schneider Electric', 'Legrand', 'Lexman', 'IEK', 'Werkel'], items: [
    ['Кабель ВВГнг(А)-LS', 'м', 70, 210, ['3x1,5 мм²', '3x2,5 мм²', '5x2,5 мм²'], 'Силовой медный кабель с пониженным дымовыделением для внутренней проводки.'],
    ['Розетка с заземлением', 'шт.', 150, 890, ['белая', 'слоновая кость', 'антрацит'], 'Одинарная розетка скрытой установки 16 А с защитными шторками.'],
    ['Выключатель двухклавишный', 'шт.', 160, 950, ['белый', 'бежевый', 'чёрный'], 'Механизм скрытой установки с мягким ходом клавиш, срок службы до 40 000 включений.'],
    ['Автоматический выключатель 1P', 'шт.', 190, 1450, ['C16 А', 'C25 А', 'C32 А'], 'Защищает линию от перегрузки и короткого замыкания. Монтаж на DIN-рейку.'],
    ['Лампа светодиодная E27', 'шт.', 79, 420, ['8 Вт', '12 Вт', '15 Вт'], 'Энергосберегающая лампа тёплого света, ресурс до 25 000 часов.'],
    ['Щиток распределительный навесной', 'шт.', 890, 6900, ['8 модулей', '12 модулей', '24 модуля'], 'Пластиковый бокс с прозрачной дверцей для автоматов и УЗО.']
  ] },
  { name: 'Сантехника', brands: ['Grohe', 'Rehau', 'Wavin', 'Roca', 'Ideal Standard'], items: [
    ['Смеситель для раковины', 'шт.', 2900, 14900, ['хром', 'чёрный матовый', 'золото'], 'Однорычажный смеситель с керамическим картриджем и аэратором, гибкая подводка в комплекте.'],
    ['Унитаз-компакт напольный', 'шт.', 5900, 21900, ['с микролифтом', 'безободковый', 'с косым выпуском'], 'Комплект с бачком, двойным смывом и крышкой-сиденьем. Санфаянс с защитным покрытием.'],
    ['Раковина накладная', 'шт.', 2500, 9900, ['50 см', '60 см', '80 см'], 'Раковина из санфаянса для установки на столешницу или тумбу.'],
    ['Ванна акриловая', 'шт.', 11900, 38900, ['150x70 см', '170x70 см', '180x80 см'], 'Прямоугольная акриловая ванна на каркасе, быстро держит тепло.'],
    ['Труба полипропиленовая PPR', 'м', 45, 290, ['20 мм', '25 мм', '32 мм'], 'Труба для холодного и горячего водоснабжения и отопления, не подвержена коррозии.'],
    ['Полотенцесушитель водяной', 'шт.', 3900, 15900, ['50x60 см', '50x80 см', '60x80 см'], 'Лесенка из нержавеющей стали с боковым подключением.']
  ] },
  { name: 'Крепёж', brands: ['Hilti', 'Fischer', 'Tech-Krep', 'Spax', 'Зубр'], items: [
    ['Саморезы по дереву оцинкованные', 'упак.', 120, 690, ['3,5x35 мм', '4,0x50 мм', '4,5x70 мм'], 'Закалённые саморезы с острым наконечником и крестообразным шлицем.'],
    ['Дюбель-гвоздь', 'упак.', 90, 480, ['6x40 мм', '6x60 мм', '8x80 мм'], 'Быстрый монтаж в бетон, кирпич и газоблок без предварительной подготовки.'],
    ['Анкер клиновой', 'упак.', 190, 1450, ['10x100 мм', '12x120 мм', '16x150 мм'], 'Для надёжного крепления тяжёлых конструкций к бетону.'],
    ['Гвозди строительные', 'кг', 110, 260, ['70 мм', '100 мм', '150 мм'], 'Гладкие гвозди из низкоуглеродистой стали для столярных и плотницких работ.'],
    ['Уголок крепёжный оцинкованный', 'шт.', 15, 110, ['50x50 мм', '90x90 мм', '100x100 мм'], 'Равносторонний уголок с рёбрами жёсткости для соединения деревянных деталей.'],
    ['Хомут червячный', 'упак.', 90, 580, ['10–16 мм', '25–40 мм', '60–80 мм'], 'Хомут из нержавеющей стали для шлангов и патрубков.']
  ] }
];
var slugs = [
  ['cement', 'brick', 'gasblock', 'insulation', 'armatura', 'doska'],
  ['shtukaturka', 'shpaklevka', 'kraska', 'laminat', 'plitka', 'oboi'],
  ['perforator', 'shurupovert', 'bolgarka', 'lobzik', 'nivelir', 'nabor-bit'],
  ['kabel', 'rozetka', 'vyklyuchatel', 'avtomat', 'lampa', 'shchitok'],
  ['smesitel', 'unitaz', 'rakovina', 'vanna', 'truba-ppr', 'polotentsesushitel'],
  ['samorezy', 'dyubel-gvozd', 'anker', 'gvozdi', 'ugolok', 'homut']
];
var brandCountry = { 'Bosch': 'Германия', 'Makita': 'Япония', 'DeWalt': 'США', 'Hilti': 'Лихтенштейн', 'Rockwool': 'Дания', 'Knauf': 'Германия', 'Dulux': 'Великобритания', 'Tikkurila': 'Финляндия', 'Grohe': 'Германия', 'Rehau': 'Германия', 'Roca': 'Испания', 'Ideal Standard': 'Италия', 'Schneider Electric': 'Франция', 'Legrand': 'Франция', 'Fischer': 'Германия', 'Spax': 'Германия', 'Wavin': 'Нидерланды', 'Ceresit': 'Германия' };
var idCounter = 1;

for (var c = 0; c < cats.length; c++) {
  var cat = cats[c];
  for (var i = 0; i < cat.items.length; i++) {
    var it = cat.items[i];
    for (var j = 0; j < 6; j++) {
      var br = cat.brands[j % cat.brands.length];
      var vr = it[4][j % it[4].length];
      var pr = it[2] + Math.random() * (it[3] - it[2]);
      if (pr >= 100) { pr = Math.round(pr / 10) * 10 - 1; } else { pr = Math.round(pr); }
      if (pr < it[2]) { pr = it[2]; }
      var warranty = (cat.name === 'Инструмент' || cat.name === 'Сантехника') ? '2 года' : '12 месяцев';
      PRODUCTS.push({
        id: idCounter,
        name: it[0] + ' ' + br + ' ' + vr,
        category: cat.name,
        brand: br,
        price: pr,
        unit: it[1],
        img: 'img/' + slugs[c][i] + '.jpg',
        fb: catImages[cat.name][idCounter % 2],
        desc: it[5],
        specs: { 'Артикул': String(82000000 + idCounter * 73), 'Производитель': br, 'Вариант': vr, 'Страна производства': (brandCountry[br] || 'Россия'), 'Гарантия': warranty, 'Единица продажи': it[1] },
        badge: Math.random() > 0.85 ? ['Хит', 'Новинка'][Math.floor(Math.random() * 2)] : null
      });
      idCounter++;
    }
  }
}

var SHOP = { deliveryPrice: 500, freeFrom: 0, payPublicId: '' };
var state;
var cart = {};
try { cart = JSON.parse(localStorage.getItem('cart_v11')) || {}; } catch (e) { cart = {}; }

function fmt(n) {
  var s = String(n), r = '';
  for (var i = 0; i < s.length; i++) {
    if (i > 0 && (s.length - i) % 3 === 0) { r += ' '; }
    r += s.charAt(i);
  }
  return r + ' ₽';
}
function imgErr(el, id) {
  if (!el.getAttribute('data-t') && PRODUCTS[id - 1]) { el.setAttribute('data-t', '1'); el.src = PRODUCTS[id - 1].fb; }
  else { el.onerror = null; el.src = FALLBACK; }
}

function saveCart() {
  try { localStorage.setItem('cart_v11', JSON.stringify(cart)); } catch (e) {}
  updateCart();
}
function updateCart() {
  var count = 0;
  for (var key in cart) { count += cart[key]; }
  document.getElementById('cartCount').innerText = count;
  renderCart();
}

function renderCart() {
  var html = '', total = 0, has = false;
  for (var key in cart) {
    var p = PRODUCTS[parseInt(key, 10) - 1];
    if (!p) { continue; }
    has = true;
    var q = cart[key];
    total += p.price * q;
    html += '<div class="cart-item"><div class="cart-item-img"><img src="' + p.img + '" alt="" onerror="imgErr(this,' + p.id + ')"></div>' +
      '<div class="cart-item-info"><div class="cart-item-name">' + p.name + '</div>' +
      '<div class="cart-item-price">' + fmt(p.price * q) + '</div>' +
      '<div class="qty"><button onclick="changeQty(' + p.id + ',-1)">−</button><span>' + q + '</span><button onclick="changeQty(' + p.id + ',1)">+</button></div></div>' +
      '<button class="x-btn" onclick="removeItem(' + p.id + ')">✕</button></div>';
  }
  if (!has) { html = '<p class="empty">Корзина пуста</p>'; }
  document.getElementById('cartBody').innerHTML = html;
  document.getElementById('cartTotal').innerText = fmt(total);
}

function addToCart(id, e, btn) {
  if (e) { e.stopPropagation(); }
  cart[id] = (cart[id] || 0) + 1;
  saveCart();
  if (btn && !btn.getAttribute('data-busy')) {
    var old = btn.innerText;
    btn.setAttribute('data-busy', '1');
    btn.innerText = 'Добавлено ✓';
    setTimeout(function () { btn.innerText = old; btn.removeAttribute('data-busy'); }, 1000);
  }
}
function changeQty(id, d) {
  cart[id] = (cart[id] || 0) + d;
  if (cart[id] <= 0) { delete cart[id]; }
  saveCart();
}
function removeItem(id) { delete cart[id]; saveCart(); }

function openCart() { document.getElementById('cart').classList.add('open'); document.getElementById('overlay').classList.add('open'); }
function closeCart() { document.getElementById('cart').classList.remove('open'); document.getElementById('overlay').classList.remove('open'); }
function openCheckout() {
  if (!Object.keys(cart).length) { alert('Корзина пуста. Добавьте товары.'); return; }
  closeCart();
  updateOrderSum();
  document.getElementById('checkoutModal').classList.add('open');
}
function closeCheckout() { document.getElementById('checkoutModal').classList.remove('open'); }
function buyNow(id, e, btn) { addToCart(id, e, null); openCheckout(); }

function createCard(p) {
  var badge = p.badge ? '<div class="badge">' + p.badge + '</div>' : '';
  return '<div class="card" onclick="window.location.href=\'product.html?id=' + p.id + '\'">' + badge + favBtn(p.id) +
    '<div class="card-img"><img src="' + p.img + '" alt="" loading="lazy" onerror="imgErr(this,' + p.id + ')"></div>' +
    '<div class="card-body"><div class="card-cat">' + p.category + '</div>' +
    '<div class="card-name">' + p.name + '</div>' +
    '<div class="card-price">' + fmt(p.price) + ' <small>/ ' + p.unit + '</small></div>' +
    '<button class="btn-add" onclick="addToCart(' + p.id + ',event,this)">В корзину</button></div></div>';
}


var PAGE = document.body.getAttribute('data-page');
var appEl = document.getElementById('app');
state = { cat: 'Все', q: '', sort: 'def', brand: '', min: 0, max: 0, shown: 24 };

function getParam(n) {
  var m = window.location.search.match(new RegExp('[?&]' + n + '=([^&]*)'));
  return m ? decodeURIComponent(m[1].replace(/\+/g, ' ')) : '';
}

var favs = [];
try { favs = JSON.parse(localStorage.getItem('fav_v1')) || []; } catch (e) { favs = []; }
function isFav(id) { return favs.indexOf(id) !== -1; }
function favBtn(id) { return '<button class="fav' + (isFav(id) ? ' on' : '') + '" onclick="toggleFav(' + id + ',event,this)" aria-label="В избранное">♥</button>'; }
function toggleFav(id, e, btn) {
  if (e) { e.stopPropagation(); }
  var k = favs.indexOf(id);
  if (k === -1) { favs.push(id); } else { favs.splice(k, 1); }
  try { localStorage.setItem('fav_v1', JSON.stringify(favs)); } catch (x) {}
  if (btn) { btn.classList.toggle('on'); }
  updateFavCount();
  if (PAGE === 'favorites') { renderFavorites(); }
}
function updateFavCount() { document.getElementById('favCount').innerText = favs.length; }

function renderHome() {
  var html = '<section class="hero"><h1>STROY<br>LUXE</h1><p>Стройматериалы и инструмент</p>';
  html += '<div class="search-wrap"><input type="search" id="searchInput" placeholder="Поиск по каталогу..." /></div>';
  html += '<div class="filters" style="justify-content:center">';
  for (var c = 0; c < cats.length; c++) { html += '<a class="chip" href="catalog.html?cat=' + encodeURIComponent(cats[c].name) + '">' + cats[c].name + '</a>'; }
  html += '</div><div style="padding:10px 20px 0"><a href="catalog.html" class="btn-gold" style="width:auto">Перейти в каталог</a></div></section>';
  html += '<div class="container page-section"><h2 class="page-title">Популярное</h2><div class="grid">';
  for (var i = 0; i < 8; i++) { html += createCard(PRODUCTS[i * 27]); }
  html += '</div><div class="contact-grid" style="margin-top:50px">' +
    '<div class="contact-card"><div class="ic">🚚</div><small>Доставка</small><b>От 500 ₽ по городу</b></div>' +
    '<div class="contact-card"><div class="ic">🛡️</div><small>Гарантия</small><b>От 12 месяцев</b></div>' +
    '<div class="contact-card"><div class="ic">💬</div><small>Консультация</small><b>Ответим в WhatsApp</b></div></div></div>';
  appEl.innerHTML = html;
  document.getElementById('searchInput').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { window.location.href = 'catalog.html?q=' + encodeURIComponent(this.value); }
  });
}

function renderCatalog() {
  state.cat = getParam('cat') || 'Все';
  state.q = getParam('q');
  var names = ['Все'], brandList = [];
  for (var i = 0; i < PRODUCTS.length; i++) {
    if (names.indexOf(PRODUCTS[i].category) === -1) { names.push(PRODUCTS[i].category); }
    if (brandList.indexOf(PRODUCTS[i].brand) === -1) { brandList.push(PRODUCTS[i].brand); }
  }
  brandList.sort();
  var h = '<div class="container page-section"><h2 class="page-title">Каталог</h2><div class="search-wrap"><input type="search" id="searchInput" placeholder="Поиск по товарам..."></div><div class="filters" id="chips">';
  for (var k = 0; k < names.length; k++) { h += '<button class="chip" data-c="' + names[k] + '" onclick="setCat(this.getAttribute(\'data-c\'))">' + names[k] + '</button>'; }
  h += '</div><div class="toolbar"><select id="sortSel"><option value="def">По умолчанию</option><option value="asc">Сначала дешевле</option><option value="desc">Сначала дороже</option><option value="name">По названию</option></select>';
  h += '<select id="brandSel"><option value="">Все бренды</option>';
  for (var b = 0; b < brandList.length; b++) { h += '<option>' + brandList[b] + '</option>'; }
  h += '</select><input type="number" id="minP" placeholder="Цена от" min="0"><input type="number" id="maxP" placeholder="Цена до" min="0"></div>';
  h += '<div class="count" id="count"></div><div class="grid" id="grid"></div><div id="more"></div></div>';
  appEl.innerHTML = h;
  var si = document.getElementById('searchInput');
  si.value = state.q;
  si.addEventListener('input', function () { state.q = si.value; state.shown = 24; applyFilters(); });
  document.getElementById('sortSel').addEventListener('change', function () { state.sort = this.value; applyFilters(); });
  document.getElementById('brandSel').addEventListener('change', function () { state.brand = this.value; state.shown = 24; applyFilters(); });
  document.getElementById('minP').addEventListener('input', function () { state.min = parseInt(this.value, 10) || 0; state.shown = 24; applyFilters(); });
  document.getElementById('maxP').addEventListener('input', function () { state.max = parseInt(this.value, 10) || 0; state.shown = 24; applyFilters(); });
  applyFilters();
}
function setCat(c) { state.cat = c; state.shown = 24; applyFilters(); }
function showMore() { state.shown += 24; applyFilters(); }

function applyFilters() {
  var q = state.q.toLowerCase(), list = [];
  for (var i = 0; i < PRODUCTS.length; i++) {
    var p = PRODUCTS[i];
    if (state.cat !== 'Все' && p.category !== state.cat) { continue; }
    if (state.brand && p.brand !== state.brand) { continue; }
    if (state.min && p.price < state.min) { continue; }
    if (state.max && p.price > state.max) { continue; }
    if (q && (p.name + ' ' + p.brand + ' ' + p.category).toLowerCase().indexOf(q) === -1) { continue; }
    list.push(p);
  }
  if (state.sort === 'asc') { list.sort(function (a, b) { return a.price - b.price; }); }
  else if (state.sort === 'desc') { list.sort(function (a, b) { return b.price - a.price; }); }
  else if (state.sort === 'name') { list.sort(function (a, b) { return a.name.localeCompare(b.name); }); }
  var html = '', max = Math.min(state.shown, list.length);
  for (var n = 0; n < max; n++) { html += createCard(list[n]); }
  document.getElementById('grid').innerHTML = html || '<p class="empty">Ничего не найдено</p>';
  document.getElementById('count').innerText = 'Найдено товаров: ' + list.length;
  document.getElementById('more').innerHTML = max < list.length ? '<button class="btn-line more" onclick="showMore()">Показать ещё</button>' : '';
  var chips = document.getElementById('chips').children;
  for (var k = 0; k < chips.length; k++) { chips[k].classList.toggle('active', chips[k].getAttribute('data-c') === state.cat); }
}

function renderProduct() {
  var id = parseInt(getParam('id'), 10);
  var p = PRODUCTS[id - 1];
  if (!p) { appEl.innerHTML = '<div class="container page-section"><p class="empty">Товар не найден. <a href="catalog.html" style="color:var(--gold)">В каталог</a></p></div>'; return; }
  document.title = p.name + ' — STROY LUXE';
  var rows = '<tr><td>Категория</td><td>' + p.category + '</td></tr>';
  for (var k in p.specs) { rows += '<tr><td>' + k + '</td><td>' + p.specs[k] + '</td></tr>'; }
  var start = Math.floor((p.id - 1) / 36) * 36, rel = '';
  for (var r = 1; r <= 4; r++) { rel += createCard(PRODUCTS[start + ((p.id - 1 - start) + 6 * r) % 36]); }
  appEl.innerHTML = '<div class="container page-section"><a href="catalog.html" class="back">← Назад в каталог</a><div class="product-page">' +
    '<div class="product-img">' + favBtn(p.id) + '<img src="' + p.img + '" alt="" onerror="imgErr(this,' + p.id + ')"></div>' +
    '<div class="product-info"><div class="product-brand">' + p.brand + '</div><h1>' + p.name + '</h1>' +
    '<div class="product-price">' + fmt(p.price) + ' <small>/ ' + p.unit + '</small></div><p class="product-desc">' + p.desc + '</p>' +
    '<table class="specs">' + rows + '</table>' +
    '<div class="product-actions"><button class="btn-gold" onclick="addToCart(' + p.id + ',event,this)">В корзину</button>' +
    '<button class="btn-line" onclick="buyNow(' + p.id + ',event,this)">Купить сейчас</button></div></div></div>' +
    '<h2 class="page-title" style="margin-top:50px">Похожие товары</h2><div class="grid">' + rel + '</div></div>';
}

function renderFavorites() {
  var html = '', n = 0;
  for (var i = 0; i < favs.length; i++) { if (PRODUCTS[favs[i] - 1]) { html += createCard(PRODUCTS[favs[i] - 1]); n++; } }
  if (!n) { html = '<p class="empty">В избранном пока пусто. <a href="catalog.html" style="color:var(--gold)">Перейти в каталог</a></p>'; }
  appEl.innerHTML = '<div class="container page-section"><h2 class="page-title">Избранное</h2><div class="grid">' + html + '</div></div>';
}

document.getElementById('cartBtn').addEventListener('click', openCart);
document.getElementById('closeCart').addEventListener('click', closeCart);
document.getElementById('overlay').addEventListener('click', closeCart);
document.getElementById('checkoutBtn').addEventListener('click', openCheckout);
document.getElementById('closeModal').addEventListener('click', closeCheckout);
document.getElementById('checkoutModal').addEventListener('click', function (e) { if (e.target === this) { closeCheckout(); } });
function radioVal(name) {
  var r = document.getElementsByName(name);
  for (var i = 0; i < r.length; i++) { if (r[i].checked) { return r[i].value; } }
  return '';
}
function cartSum() {
  var t = 0;
  for (var k in cart) { var p = PRODUCTS[parseInt(k, 10) - 1]; if (p) { t += p.price * cart[k]; } }
  return t;
}
function deliveryCost(sum) { return (SHOP.freeFrom > 0 && sum >= SHOP.freeFrom) ? 0 : SHOP.deliveryPrice; }
function getOrder() {
  var sum = cartSum(), ship = radioVal('ship');
  var d = ship === 'courier' ? deliveryCost(sum) : 0;
  return { name: document.getElementById('orderName').value, phone: document.getElementById('orderPhone').value, ship: ship, addr: document.getElementById('orderAddr').value, pay: radioVal('pay'), sum: sum, delivery: d, total: sum + d };
}
function updateOrderSum() {
  var o = getOrder(), dc = deliveryCost(o.sum);
  var addr = document.getElementById('orderAddr');
  addr.style.display = o.ship === 'courier' ? 'block' : 'none';
  addr.required = o.ship === 'courier';
  document.getElementById('courierLbl').innerText = 'Доставка курьером — ' + (dc ? fmt(dc) : 'бесплатно');
  document.getElementById('orderSum').innerHTML = '<div><span>Товары</span><span>' + fmt(o.sum) + '</span></div><div><span>Доставка</span><span>' + (o.ship === 'courier' ? (o.delivery ? fmt(o.delivery) : 'бесплатно') : 'самовывоз') + '</span></div><div><span>Итого</span><b>' + fmt(o.total) + '</b></div>';
  document.getElementById('orderBtn').innerText = o.pay === 'online' ? 'Оплатить ' + fmt(o.total) : 'Оформить заказ';
}
function sendOrder(o, payNote) {
  var lines = ['Новый заказ с сайта STROY LUXE', 'Имя: ' + o.name, 'Телефон: ' + o.phone, o.ship === 'courier' ? 'Доставка курьером: ' + o.addr : 'Самовывоз', 'Оплата: ' + payNote, ''];
  for (var key in cart) {
    var p = PRODUCTS[parseInt(key, 10) - 1];
    if (p) { lines.push(p.name + ' — ' + cart[key] + ' x ' + fmt(p.price)); }
  }
  lines.push('', 'Товары: ' + fmt(o.sum), 'Доставка: ' + fmt(o.delivery), 'Итого: ' + fmt(o.total));
  var link = 'https://wa.me/79966889979?text=' + encodeURIComponent(lines.join('\n'));
  cart = {};
  saveCart();
  closeCheckout();
  document.getElementById('orderForm').reset();
  updateOrderSum();
  alert('Спасибо, ' + o.name + '! Заказ оформлен. Нажмите «Отправить» в WhatsApp, чтобы мы его получили.');
  var w = window.open(link, '_blank');
  if (!w) { window.location.href = link; }
}
function payOnline(o) {
  if (!SHOP.payPublicId || typeof cp === 'undefined') { alert('Онлайн-оплата сейчас недоступна. Выберите оплату при получении.'); return; }
  var widget = new cp.CloudPayments();
  widget.pay('charge', {
    publicId: SHOP.payPublicId, description: 'Заказ STROY LUXE', amount: o.total, currency: 'RUB',
    invoiceId: 'SL-' + new Date().getTime(), skin: 'modern', data: { name: o.name, phone: o.phone, address: o.addr }
  }, {
    onSuccess: function () { sendOrder(o, 'ОПЛАЧЕНО картой онлайн'); },
    onFail: function (reason) { alert('Оплата не прошла: ' + reason); }
  });
}
document.getElementById('orderForm').addEventListener('submit', function (e) {
  e.preventDefault();
  var o = getOrder();
  if (o.ship === 'courier' && !o.addr) { alert('Укажите адрес доставки'); return; }
  if (o.pay === 'online') { payOnline(o); } else { sendOrder(o, 'при получении'); }
});
var radioNames = ['ship', 'pay'];
for (var rn = 0; rn < radioNames.length; rn++) {
  var radios = document.getElementsByName(radioNames[rn]);
  for (var ri = 0; ri < radios.length; ri++) { radios[ri].addEventListener('change', updateOrderSum); }
}
if (SHOP.payPublicId) {
  var sc = document.createElement('script');
  sc.src = 'https://widget.cloudpayments.ru/bundles/cloudpayments.js';
  document.head.appendChild(sc);
} else {
  var po = document.getElementById('payOnline');
  po.disabled = true;
  po.parentNode.classList.add('off');
  document.getElementById('payOnlineLbl').innerText = 'Банковской картой онлайн — скоро будет доступно';
}
document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeCart(); closeCheckout(); } });

updateCart();
updateFavCount();
if (PAGE === 'home') { renderHome(); }
else if (PAGE === 'catalog') { renderCatalog(); }
else if (PAGE === 'product') { renderProduct(); }
else if (PAGE === 'favorites') { renderFavorites(); }
