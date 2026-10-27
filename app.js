/* ============================================
   STROY LUXE — Логика каталога + корзина
============================================ */

const PRODUCTS = [
  // 1. Стройматериалы (20)
  { id: 1,  name: 'Цемент М500, 50 кг', category: 'Стройматериалы', brand: 'Petrovich', price: 450, emoji: '🧱', badge: 'Хит' },
  { id: 2,  name: 'Кирпич керамический полнотелый, шт', category: 'Стройматериалы', brand: 'Керамик', price: 35, emoji: '🧱' },
  { id: 3,  name: 'Пескобетон М300, 40 кг', category: 'Стройматериалы', brand: 'Petrovich', price: 320, emoji: '⚪', badge: 'Скидка' },
  { id: 4,  name: 'Газобетонный блок D500, 600x300x200', category: 'Стройматериалы', brand: 'Bonolit', price: 180, emoji: '⬜' },
  { id: 5,  name: 'Арматура 12 мм, м', category: 'Стройматериалы', brand: 'ММК', price: 85, emoji: '➖' },
  { id: 6,  name: 'Брус строганый 100х100, 3м', category: 'Стройматериалы', brand: 'ЛесПром', price: 750, emoji: '🪵' },
  { id: 7,  name: 'Песок строительный, 50 кг', category: 'Стройматериалы', brand: 'Petrovich', price: 120, emoji: '⏳' },
  { id: 8,  name: 'Керамзит фракция 10-20, 40 л', category: 'Стройматериалы', brand: 'Керамзит', price: 280, emoji: '🟤' },
  { id: 9,  name: 'Гипсокартон Knauf 2500×1200×12.5', category: 'Стройматериалы', brand: 'Knauf', price: 620, emoji: '📐' },
  { id: 10, name: 'Профиль ПН-27 Knauf, 3 м', category: 'Стройматериалы', brand: 'Knauf', price: 150, emoji: '📏' },
  { id: 11, name: 'Профиль ПС-50 Knauf, 3 м', category: 'Стройматериалы', brand: 'Knauf', price: 180, emoji: '📏' },
  { id: 12, name: 'Утеплитель Rockwool Лайт Баттс, м²', category: 'Стройматериалы', brand: 'Rockwool', price: 450, emoji: '🧊', badge: 'Хит' },
  { id: 13, name: 'Пенопласт ПСБ-С 25, 50 мм', category: 'Стройматериалы', brand: 'Penoplex', price: 180, emoji: '🧊' },
  { id: 14, name: 'Гидроизоляция Технониколь, рулон', category: 'Стройматериалы', brand: 'Технониколь', price: 1200, emoji: '🛡️' },
  { id: 15, name: 'Металлочерепица Монтеррей, м²', category: 'Стройматериалы', brand: 'Металл Профиль', price: 650, emoji: '🏠' },
  { id: 16, name: 'Профнастил С8, м²', category: 'Стройматериалы', brand: 'Металл Профиль', price: 480, emoji: '🏠' },
  { id: 17, name: 'Поликарбонат сотовый 4мм, м²', category: 'Стройматериалы', brand: 'Полигаль', price: 350, emoji: '🪟' },
  { id: 18, name: 'Сетка сварная 50х50, 1х2м', category: 'Стройматериалы', brand: 'ММК', price: 250, emoji: '🕸️' },
  { id: 19, name: 'Тротуарная плитка Брусчатка, м²', category: 'Стройматериалы', brand: 'Бехатон', price: 890, emoji: '🟫' },
  { id: 20, name: 'Стеклопластиковая арматура 8мм, м', category: 'Стройматериалы', brand: 'Гален', price: 40, emoji: '➖' },

  // 2. Отделочные материалы (25)
  { id: 21, name: 'Штукатурка гипсовая Knauf Rotband, 30 кг', category: 'Отделка', brand: 'Knauf', price: 540, emoji: '🎨', badge: 'Хит' },
  { id: 22, name: 'Шпаклевка финишная Vetonit LR+, 20 кг', category: 'Отделка', brand: 'Vetonit', price: 890, emoji: '🎨' },
  { id: 23, name: 'Грунтовка глубокого проникновения Ceresit CT 17, 10 л', category: 'Отделка', brand: 'Ceresit', price: 480, emoji: '🪣' },
  { id: 24, name: 'Краска интерьерная Lavelly Гамма, 9 л', category: 'Отделка', brand: 'Lavelly', price: 2100, emoji: '🪣', badge: 'Хит' },
  { id: 25, name: 'Краска фасадная Tikkurila, 9 л', category: 'Отделка', brand: 'Tikkurila', price: 4500, emoji: '🪣' },
  { id: 26, name: 'Обои флизелиновые, рулон 1.06х10м', category: 'Отделка', brand: 'Erismann', price: 1200, emoji: '📜', badge: 'Новинка' },
  { id: 27, name: 'Плитка керамическая для пола, м²', category: 'Отделка', brand: 'Lavelly', price: 890, emoji: '🔲' },
  { id: 28, name: 'Керамогранит 60х60, м²', category: 'Отделка', brand: 'Cersanit', price: 1100, emoji: '🔲' },
  { id: 29, name: 'Ламинат 33 класс, 8мм, м²', category: 'Отделка', brand: 'Tarkett', price: 1100, emoji: '🪵', badge: 'Скидка' },
  { id: 30, name: 'Кварцвиниловая плитка Corsa Deco, м²', category: 'Отделка', brand: 'Corsa Deco', price: 1400, emoji: '🪵', badge: 'Новинка' },
  { id: 31, name: 'Плинтус напольный, 2.5 м', category: 'Отделка', brand: 'Orac Decor', price: 220, emoji: '📏' },
  { id: 32, name: 'Натяжной потолок, м²', category: 'Отделка', brand: 'Аста', price: 850, emoji: '⬜' },
  { id: 33, name: 'Дверь межкомнатная скрытого монтажа', category: 'Отделка', brand: 'Lavelly', price: 12500, emoji: '🚪', badge: 'Хит' },
  { id: 34, name: 'Клей для плитки Ceresit CM 11, 25 кг', category: 'Отделка', brand: 'Ceresit', price: 420, emoji: '🪣' },
  { id: 35, name: 'Затирка для швов Ceresit CE 40, 2 кг', category: 'Отделка', brand: 'Ceresit', price: 280, emoji: '🪣' },
  { id: 36, name: 'Пена монтажная профессиональная, 750 мл', category: 'Отделка', brand: 'Soudal', price: 350, emoji: '💨' },
  { id: 37, name: 'Герметик силиконовый санитарный, 280 мл', category: 'Отделка', brand: 'Ceresit', price: 190, emoji: '💧' },
  { id: 38, name: 'Сетка-серпянка для швов, 45м', category: 'Отделка', brand: 'Knauf', price: 120, emoji: '🕸️' },
  { id: 39, name: 'Уголок перфорированный, 3м', category: 'Отделка', brand: 'Knauf', price: 90, emoji: '📐' },
  { id: 40, name: 'Маяк штукатурный, 3м', category: 'Отделка', brand: 'Knauf', price: 50, emoji: '📏' },
  { id: 41, name: 'Потолочный плинтус полиуретановый, 2м', category: 'Отделка', brand: 'Orac Decor', price: 180, emoji: '📏' },
  { id: 42, name: 'Плитка для ванной, м²', category: 'Отделка', brand: 'Cersanit', price: 750, emoji: '🔲' },
  { id: 43, name: 'Мозаика для бассейна, лист', category: 'Отделка', brand: 'Cersanit', price: 350, emoji: '🔳' },
  { id: 44, name: 'Декоративная штукатурка, 5 кг', category: 'Отделка', brand: 'Ceresit', price: 950, emoji: '🎨' },
  { id: 45, name: 'Жидкие гвозди, 300 мл', category: 'Отделка', brand: 'Soudal', price: 280, emoji: '💧' },

  // 3. Электроинструмент (20)
  { id: 46, name: 'Перфоратор SDS-Plus Makita HR2470, 780 Вт', category: 'Электроинструмент', brand: 'Makita', price: 12900, emoji: '🔧', badge: 'Хит' },
  { id: 47, name: 'Шуруповёрт аккумуляторный Makita DF333D, 18В', category: 'Электроинструмент', brand: 'Makita', price: 8900, emoji: '🪛' },
  { id: 48, name: 'Дрель-шуруповёрт Bosch GSR 120-LI, 12В', category: 'Электроинструмент', brand: 'Bosch', price: 7500, emoji: '🪛', badge: 'Скидка' },
  { id: 49, name: 'Угловая шлифмашина (Болгарка) Makita 125мм', category: 'Электроинструмент', brand: 'Makita', price: 6900, emoji: '⚙️' },
  { id: 50, name: 'Лобзик электрический Bosch PST 650', category: 'Электроинструмент', brand: 'Bosch', price: 4500, emoji: '🪚' },
  { id: 51, name: 'Уровень лазерный Bosch GLL 2-10', category: 'Электроинструмент', brand: 'Bosch', price: 8900, emoji: '📏', badge: 'Новинка' },
  { id: 52, name: 'Пила циркулярная DeWalt DWE560', category: 'Электроинструмент', brand: 'DeWalt', price: 11500, emoji: '🪚' },
  { id: 53, name: 'Шлифмашина эксцентриковая Makita BO5030', category: 'Электроинструмент', brand: 'Makita', price: 6200, emoji: '⚙️' },
  { id: 54, name: 'Фен строительный Makita HG5030, 2000 Вт', category: 'Электроинструмент', brand: 'Makita', price: 3500, emoji: '💨' },
  { id: 55, name: 'Краскопульт электрический Wagner W100', category: 'Электроинструмент', brand: 'Wagner', price: 4900, emoji: '🎨' },
  { id: 56, name: 'Аккумулятор Makita 18В, 3.0 Ач', category: 'Электроинструмент', brand: 'Makita', price: 3200, emoji: '🔋' },
  { id: 57, name: 'Зарядное устройство Makita DC18RC', category: 'Электроинструмент', brand: 'Makita', price: 2800, emoji: '🔌' },
  { id: 58, name: 'Набор бит и свёрл Makita, 100 предметов', category: 'Электроинструмент', brand: 'Makita', price: 1800, emoji: '🧰' },
  { id: 59, name: 'Торцовочная пила Metabo KGS 216', category: 'Электроинструмент', brand: 'Metabo', price: 14500, emoji: '🪚' },
  { id: 60, name: 'Рубанок электрический Bosch GHO 6500', category: 'Электроинструмент', brand: 'Bosch', price: 7800, emoji: '🪚' },
  { id: 61, name: 'Гайковёрт аккумуляторный Makita DTW190', category: 'Электроинструмент', brand: 'Makita', price: 9200, emoji: '🔧' },
  { id: 62, name: 'Компрессор масляный Remeza СБ 4/Ф-500', category: 'Электроинструмент', brand: 'Remeza', price: 21000, emoji: '💨' },
  { id: 63, name: 'Сварочный аппарат инверторный Ресанта САИ 190', category: 'Электроинструмент', brand: 'Ресанта', price: 8500, emoji: '⚡' },
  { id: 64, name: 'Штроборез Makita SG150', category: 'Электроинструмент', brand: 'Makita', price: 18900, emoji: '⚙️' },
  { id: 65, name: 'Пылесос строительный Karcher WD 3', category: 'Электроинструмент', brand: 'Karcher', price: 5900, emoji: '🧹' },

  // 4. Ручной инструмент (15)
  { id: 66, name: 'Молоток слесарный 500г', category: 'Ручной инструмент', brand: 'Сорокин', price: 450, emoji: '🔨' },
  { id: 67, name: 'Рулетка измерительная 5м', category: 'Ручной инструмент', brand: 'Stanley', price: 250, emoji: '📏' },
  { id: 68, name: 'Уровень строительный 600мм', category: 'Ручной инструмент', brand: 'Stanley', price: 550, emoji: '📏' },
  { id: 69, name: 'Шпатель малярный 250мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 180, emoji: '🔪' },
  { id: 70, name: 'Набор отвёрток, 6 предметов', category: 'Ручной инструмент', brand: 'Сорокин', price: 350, emoji: '🪛' },
  { id: 71, name: 'Ключ разводной 250мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 400, emoji: '🔧' },
  { id: 72, name: 'Плоскогубцы 160мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 280, emoji: '🔧' },
  { id: 73, name: 'Ножовка по дереву 450мм', category: 'Ручной инструмент', brand: 'Stanley', price: 320, emoji: '🪚' },
  { id: 74, name: 'Стремянка алюминиевая 5 ступеней', category: 'Ручной инструмент', brand: 'Alumet', price: 2900, emoji: '🪜' },
  { id: 75, name: 'Лестница-стремянка 7 ступеней', category: 'Ручной инструмент', brand: 'Alumet', price: 4200, emoji: '🪜' },
  { id: 76, name: 'Набор ключей комбинированных, 8-19мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 850, emoji: '🔧' },
  { id: 77, name: 'Кусачки боковые 160мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 260, emoji: '🔧' },
  { id: 78, name: 'Стамеска 20мм', category: 'Ручной инструмент', brand: 'Stanley', price: 180, emoji: '🪵' },
  { id: 79, name: 'Кисть малярная 100мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 90, emoji: '🖌️' },
  { id: 80, name: 'Валик малярный 250мм', category: 'Ручной инструмент', brand: 'Сорокин', price: 150, emoji: '🖌️' },

  // 5. Сантехника (15)
  { id: 81, name: 'Смеситель для кухни Corsa Deco', category: 'Сантехника', brand: 'Corsa Deco', price: 3400, emoji: '🚿', badge: 'Хит' },
  { id: 82, name: 'Смеситель для ванны с душем', category: 'Сантехника', brand: 'Corsa Deco', price: 4200, emoji: '🚿' },
  { id: 83, name: 'Унитаз-компакт с микролифтом', category: 'Сантехника', brand: 'Corsa Deco', price: 5600, emoji: '🚽' },
  { id: 84, name: 'Раковина накладная 50см', category: 'Сантехника', brand: 'Corsa Deco', price: 3900, emoji: '🛁' },
  { id: 85, name: 'Ванна акриловая 150х70', category: 'Сантехника', brand: 'Corsa Deco', price: 12500, emoji: '🛁' },
  { id: 86, name: 'Душевая система с термостатом', category: 'Сантехника', brand: 'Corsa Deco', price: 8900, emoji: '🚿' },
  { id: 87, name: 'Труба PPR 25 мм, м', category: 'Сантехника', brand: 'Valtec', price: 140, emoji: '🚰' },
  { id: 88, name: 'Труба металлопластиковая 16мм, м', category: 'Сантехника', brand: 'Valtec', price: 95, emoji: '🚰' },
  { id: 89, name: 'Фитинг PPR угол 90°, 25мм', category: 'Сантехника', brand: 'Valtec', price: 45, emoji: '🔗' },
  { id: 90, name: 'Шланг гибкий 1/2, 1м', category: 'Сантехника', brand: 'Valtec', price: 180, emoji: '〰️' },
  { id: 91, name: 'Счетчик воды крыльчатый', category: 'Сантехника', brand: 'Valtec', price: 850, emoji: '🔢' },
  { id: 92, name: 'Полотенцесушитель водяной', category: 'Сантехника', brand: 'Corsa Deco', price: 5600, emoji: '🧺' },
  { id: 93, name: 'Инсталляция для унитаза', category: 'Сантехника', brand: 'Corsa Deco', price: 7800, emoji: '🚽' },
  { id: 94, name: 'Сифон для раковины', category: 'Сантехника', brand: 'Valtec', price: 350, emoji: '🚰' },
  { id: 95, name: 'Кран шаровой 1/2', category: 'Сантехника', brand: 'Valtec', price: 280, emoji: '🔧' },

  // 6. Электрика (15)
  { id: 96, name: 'Кабель ВВГнг 3×2.5, м', category: 'Электрика', brand: 'Кабель', price: 95, emoji: '⚡' },
  { id: 97, name: 'Кабель ВВГнг 3×1.5, м', category: 'Электрика', brand: 'Кабель', price: 60, emoji: '⚡' },
  { id: 98, name: 'Розетка с заземлением Schneider Electric', category: 'Электрика', brand: 'Schneider Electric', price: 210, emoji: '🔌' },
  { id: 99, name: 'Выключатель 2-клавишный Schneider Electric', category: 'Электрика', brand: 'Schneider Electric', price: 250, emoji: '🔘' },
  { id: 100, name: 'Автомат C16 1P Schneider Electric', category: 'Электрика', brand: 'Schneider Electric', price: 320, emoji: '🎛️' },
  { id: 101, name: 'Светодиодная лампа 10Вт E27', category: 'Электрика', brand: 'Osram', price: 150, emoji: '💡', badge: 'Скидка' },
  { id: 102, name: 'Светильник точечный встраиваемый', category: 'Электрика', brand: 'Arlight', price: 380, emoji: '🔦' },
  { id: 103, name: 'Подрозетник 45 мм', category: 'Электрика', brand: 'Schneider Electric', price: 25, emoji: '⭕' },
  { id: 104, name: 'Щиток электрический на 12 модулей', category: 'Электрика', brand: 'Schneider Electric', price: 850, emoji: '🎛️' },
  { id: 105, name: 'УЗО 2P 40A Schneider Electric', category: 'Электрика', brand: 'Schneider Electric', price: 1800, emoji: '🎛️' },
  { id: 106, name: 'Светильник светодиодный 36Вт', category: 'Электрика', brand: 'Arlight', price: 1200, emoji: '💡' },
  { id: 107, name: 'Лента светодиодная 5м', category: 'Электрика', brand: 'Arlight', price: 650, emoji: '💡' },
  { id: 108, name: 'Гофра для кабеля 20мм, м', category: 'Электрика', brand: 'Кабель', price: 35, emoji: '〰️' },
  { id: 109, name: 'Распределительная коробка', category: 'Электрика', brand: 'Schneider Electric', price: 40, emoji: '📦' },
  { id: 110, name: 'Удлинитель 5м, 4 розетки', category: 'Электрика', brand: 'Schneider Electric', price: 450, emoji: '🔌' },

  // 7. Крепёж (10)
  { id: 111, name: 'Саморез по дереву 4х50 (100 шт)', category: 'Крепёж', brand: 'Крепёж', price: 150, emoji: '🔩' },
  { id: 112, name: 'Дюбель-гвоздь 6х40 (100 шт)', category: 'Крепёж', brand: 'Крепёж', price: 180, emoji: '📌' },
  { id: 113, name: 'Анкер клиновой 10х100', category: 'Крепёж', brand: 'Крепёж', price: 45, emoji: '🔗' },
  { id: 114, name: 'Гвозди строительные 3х70 (1 кг)', category: 'Крепёж', brand: 'Крепёж', price: 120, emoji: '📌' },
  { id: 115, name: 'Уголок монтажный 50х50', category: 'Крепёж', brand: 'Крепёж', price: 15, emoji: '📐' },
  { id: 116, name: 'Дюбель для гипсокартона "Бабочка" (50 шт)', category: 'Крепёж', brand: 'Крепёж', price: 90, emoji: '📌' },
  { id: 117, name: 'Шуруп-кольцо 8х60', category: 'Крепёж', brand: 'Крепёж', price: 25, emoji: '🔩' },
  { id: 118, name: 'Пластина монтажная 100х40', category: 'Крепёж', brand: 'Крепёж', price: 30, emoji: '📐' },
  { id: 119, name: 'Трос металлический 2мм, м', category: 'Крепёж', brand: 'Крепёж', price: 35, emoji: '🔗' },
  { id: 120, name: 'Хомут червячный 32-50мм', category: 'Крепёж', brand: 'Крепёж', price: 20, emoji: '🔗' },

  // 8. Спецодежда и СИЗ (8)
  { id: 121, name: 'Каска строительная', category: 'Спецодежда', brand: 'СОМЗ', price: 350, emoji: '👷', badge: 'Новинка' },
  { id: 122, name: 'Перчатки нитриловые (пара)', category: 'Спецодежда', brand: 'СОМЗ', price: 80, emoji: '🧤' },
  { id: 123, name: 'Очки защитные', category: 'Спецодежда', brand: 'СОМЗ', price: 220, emoji: '🥽' },
  { id: 124, name: 'Респиратор FFP2 (3 шт)', category: 'Спецодежда', brand: 'СОМЗ', price: 190, emoji: '😷' },
  { id: 125, name: 'Костюм рабочий х/б', category: 'Спецодежда', brand: 'СОМЗ', price: 2500, emoji: '👕' },
  { id: 126, name: 'Ботинки рабочие с металлоподноском', category: 'Спецодежда', brand: 'СОМЗ', price: 3800, emoji: '👞' },
  { id: 127, name: 'Наушники противошумные', category: 'Спецодежда', brand: 'СОМЗ', price: 450, emoji: '🎧' },
  { id: 128, name: 'Жилет сигнальный', category: 'Спецодежда', brand: 'СОМЗ', price: 350, emoji: '🦺' },

  // 9. Садовая техника (7)
  { id: 129, name: 'Газонокосилка электрическая 1200Вт', category: 'Садовая техника', brand: 'Husqvarna', price: 8900, emoji: '🌿' },
  { id: 130, name: 'Триммер электрический 500Вт', category: 'Садовая техника', brand: 'Husqvarna', price: 4500, emoji: '🌿' },
  { id: 131, name: 'Культиватор электрический 1000Вт', category: 'Садовая техника', brand: 'Husqvarna', price: 7800, emoji: '🌱' },
  { id: 132, name: 'Пила цепная электрическая 1800Вт', category: 'Садовая техника', brand: 'Husqvarna', price: 9500, emoji: '🪚' },
  { id: 133, name: 'Секатор садовый', category: 'Садовая техника', brand: 'Husqvarna', price: 650, emoji: '✂️' },
  { id: 134, name: 'Опрыскиватель садовый 5л', category: 'Садовая техника', brand: 'Husqvarna', price: 890, emoji: '💧' },
  { id: 135, name: 'Шланг поливочный 25м', category: 'Садовая техника', brand: 'Husqvarna', price: 1200, emoji: '💧' },

  // 10. Климатическая техника (7)
  { id: 136, name: 'Кондиционер настенный 7 (до 20 м²)', category: 'Климатическая техника', brand: 'Ballu', price: 18900, emoji: '❄️' },
  { id: 137, name: 'Обогреватель масляный 2000Вт', category: 'Климатическая техника', brand: 'Ballu', price: 3200, emoji: '🔥' },
  { id: 138, name: 'Тепловентилятор 2000Вт', category: 'Климатическая техника', brand: 'Ballu', price: 1500, emoji: '🔥' },
  { id: 139, name: 'Вентилятор напольный', category: 'Климатическая техника', brand: 'Ballu', price: 1800, emoji: '💨' },
  { id: 140, name: 'Увлажнитель воздуха', category: 'Климатическая техника', brand: 'Ballu', price: 2500, emoji: '💧' },
  { id: 141, name: 'Тепловая пушка электрическая 3кВт', category: 'Климатическая техника', brand: 'Ballu', price: 2800, emoji: '🔥' },
  { id: 142, name: 'Осушитель воздуха', category: 'Климатическая техника', brand: 'Ballu', price: 12500, emoji: '💧' }
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
        <div style="font-size: 11px; color: #888; margin-bottom: 5px;">${p.brand}</div>
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
