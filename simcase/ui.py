HTML = r"""
<!doctype html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Симулятор кейсов</title>
<style>
:root {
  --bg: #090f1d;
  --panel: #111a2e;
  --surface: #0b1324;
  --line: #263655;
  --text: #e4ecfb;
  --muted: #a6b5d3;
  --accent: #3b82f6;
  --status-ok: #93c5fd;
  --status-err: #fda4af;
}

body.theme-light {
  --bg: #f3f6ff;
  --panel: #ffffff;
  --surface: #f7f9ff;
  --line: #d6dff2;
  --text: #1f2a44;
  --muted: #56627f;
  --accent: #2563eb;
  --status-ok: #2563eb;
  --status-err: #dc2626;
}

* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font-family: Inter, Arial, sans-serif; }
header { padding: 16px 20px; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.container { padding: 18px; display: grid; gap: 14px; }
.grid { display: grid; grid-template-columns: 1.4fr .9fr; gap: 14px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 14px; }
.row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
input, select, button { background: var(--surface); color: var(--text); border: 1px solid var(--line); border-radius: 8px; padding: 8px; }
button { cursor: pointer; }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
button.danger { background: #b91c1c; border-color: #b91c1c; color: #fff; }
.tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.hidden { display: none; }
.level { display: flex; align-items: center; gap: 10px; }
.bar { height: 10px; background: var(--surface); border: 1px solid var(--line); border-radius: 999px; overflow: hidden; flex: 1; }
.bar > div { height: 100%; background: linear-gradient(90deg, #22d3ee, #3b82f6); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 7px; border-bottom: 1px solid var(--line); font-size: 13px; text-align: left; }
.badge { padding: 2px 8px; border-radius: 999px; border: 1px solid; display: inline-block; font-size: 12px; }
small { color: var(--muted); }
.drop-row { margin: 6px 0; padding: 8px 10px; border: 1px solid var(--line); border-radius: 10px; background: color-mix(in oklab, var(--panel), transparent 12%); transition: transform .2s ease, box-shadow .25s ease; }
.drop-row:hover { transform: translateY(-1px); }
.drop-row .qty { margin-left: 8px; display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; color: #fff; background: color-mix(in oklab, var(--accent), black 12%); }
.drop-row.effect-neon { box-shadow: 0 0 12px color-mix(in oklab, var(--drop-color, var(--accent)), transparent 45%), 0 0 22px color-mix(in oklab, var(--drop-color, var(--accent)), transparent 72%); }
.drop-row.effect-pulse { animation: pulseGlow 1.8s ease-in-out infinite; }
.drop-row.effect-shimmer { background-image: linear-gradient(110deg, transparent 25%, color-mix(in oklab, var(--drop-color, var(--accent)), white 80%) 48%, transparent 72%); background-size: 220% 100%; animation: shimmerMove 2.6s linear infinite; }
.drop-row.effect-ultra { border-color: #ffd54a; box-shadow: 0 0 14px color-mix(in oklab, #ffd54a, transparent 45%), 0 0 26px color-mix(in oklab, #ff5ec9, transparent 65%); background: radial-gradient(circle at top right, color-mix(in oklab, #ffd54a, transparent 72%), transparent 42%), color-mix(in oklab, var(--panel), transparent 10%); }
.item-cell { display: inline-flex; align-items: center; gap: 8px; }
.item-thumb { width: 34px; height: 34px; border-radius: 7px; object-fit: cover; border: 1px solid var(--line); background: var(--surface); }

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 transparent; }
  50% { box-shadow: 0 0 16px color-mix(in oklab, var(--drop-color, var(--accent)), transparent 50%); }
}

@keyframes shimmerMove {
  0% { background-position: 180% 0; }
  100% { background-position: -40% 0; }
}

@media (max-width: 1050px) {
  .grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>
<header>
  <div><strong>🎁 Симулятор кейсов 2.0</strong><br><small>Модульная версия с прогрессией игрока</small></div>
  <div class="row">
    <button onclick="toggleTheme()">Сменить тему</button>
    <div id="status"></div>
  </div>
</header>
<div class="container">
  <div class="tabs card">
    <button onclick="tab('open')">Открытие</button>
    <button onclick="tab('items')">Предметы</button>
    <button onclick="tab('rarities')">Редкости</button>
    <button onclick="tab('filters')">Лут-фильтр</button>
    <button onclick="tab('inventory')">Инвентарь</button>
    <button onclick="tab('settings')">Настройки</button>
  </div>

  <div class="grid">
    <section id="tab-open" class="card">
      <h3>Открытие кейсов</h3>
      <div class="row">
        <input id="open-times" type="number" min="1" value="1" style="width:100px">
        <button class="primary" onclick="openCases()">Открыть</button>
      </div>
      <div id="open-results" style="margin-top:10px;max-height:420px;overflow:auto"></div>
    </section>
    <aside class="card">
      <h3>Прогресс игрока</h3>
      <div class="level"><strong id="player-level">Lv.1</strong><div class="bar"><div id="xp-bar" style="width:0%"></div></div></div>
      <small id="xp-meta"></small>
      <hr style="border-color:var(--line)">
      <div id="quick-stats"></div>
    </aside>
  </div>

  <section id="tab-items" class="card hidden">
    <h3>Предметы</h3>
    <div class="row">
      <input id="item-name" placeholder="Название">
      <select id="item-rarity"></select>
      <input id="item-weight" type="number" step="0.1" value="1" style="width:90px">
      <input id="item-image" placeholder="URL картинки">
      <input id="item-description" placeholder="Описание">
      <button onclick="addItem()">Добавить</button>
    </div>
    <div class="row" style="margin-top:8px">
      <button class="primary" onclick="saveItemsBulk()">Сохранить правки предметов</button>
    </div>
    <table id="items-table"></table>
  </section>

  <section id="tab-rarities" class="card hidden">
    <h3>Редкости (гибкое редактирование)</h3>
    <div class="row">
      <button onclick="normalizeRanges()">Авто-нормализация диапазонов</button>
      <button onclick="saveRarityBulk()" class="primary">Сохранить все правки</button>
    </div>
    <table id="rarities-table"></table>
    <h4>Новая редкость</h4>
    <div class="row">
      <input id="rarity-name" placeholder="Название">
      <input id="rarity-min" type="number" step="0.1" placeholder="min">
      <input id="rarity-max" type="number" step="0.1" placeholder="max">
      <input id="rarity-color" type="color" value="#888888">
      <input id="rarity-sound" placeholder="Файл звука" style="min-width:260px">
      <button onclick="pickSoundForNewRarity()">Выбрать звук…</button>
      <select id="rarity-effect"><option value="">Без эффекта</option><option value="neon">Neon</option><option value="pulse">Pulse</option><option value="shimmer">Shimmer</option></select>
      <button onclick="addRarity()">Добавить</button>
    </div>
  </section>

  <section id="tab-inventory" class="card hidden">
    <div class="row" style="justify-content:space-between">
      <h3 style="margin:0">Инвентарь</h3>
      <button class="danger" onclick="clearInventory()">Очистить инвентарь</button>
    </div>
    <table id="inventory-table"></table>
  </section>

  <section id="tab-filters" class="card hidden">
    <h3>Лут-фильтр</h3>
    <small>Выберите редкости и предметы, которые нужно скрывать в результатах выпадения.</small>
    <h4>Скрывать по редкости</h4>
    <div id="filters-rarity" class="row"></div>
    <h4>Скрывать конкретные предметы</h4>
    <table id="filters-items-table"></table>
  </section>

  <section id="tab-settings" class="card hidden">
    <h3>Настройки симулятора и уровней</h3>
    <div class="row"><label>roll_min <input id="set-roll-min" type="number"></label><label>roll_max <input id="set-roll-max" type="number"></label><label>Цена открытия <input id="set-open-price" type="number"></label></div>
    <h4>Внешний вид</h4>
    <div class="row"><label>Тема <select id="set-theme"><option value="dark">Тёмная</option><option value="light">Светлая</option></select></label></div>
    <h4>Система опыта</h4>
    <div class="row"><label>Базовый XP на уровень <input id="set-base-xp" type="number" min="1"></label><label>Рост XP (множитель) <input id="set-xp-growth" type="number" step="0.01" min="1.01"></label><button class="primary" onclick="saveSettings()">Сохранить</button></div>
  </section>
</div>
<script>
let state = null;

function escapeHtml(value) {
  const raw = `${value ?? ''}`;
  return raw
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function imageSrc(path) {
  if (!path) return '';
  if (/^(https?:|data:|file:|\/)/i.test(path)) return path;
  return `file://${encodeURI(path.replaceAll('\\', '/'))}`;
}

function itemThumb(path, alt = '') {
  const src = imageSrc(path);
  if (!src) return '';
  return `<img class="item-thumb" src="${escapeHtml(src)}" alt="${escapeHtml(alt)}" loading="lazy" onerror="this.style.display='none'">`;
}

function setStatus(text, isError = false) {
  const el = document.getElementById('status');
  el.textContent = text;
  el.style.color = isError ? 'var(--status-err)' : 'var(--status-ok)';
}

function tab(name) {
  for (const el of document.querySelectorAll('[id^="tab-"]')) {
    el.classList.add('hidden');
  }
  const chosen = document.getElementById(`tab-${name}`);
  if (chosen) {
    chosen.classList.remove('hidden');
  }
}

function rarityById(id) {
  return state.rarities.find((r) => r.id === id);
}

function badge(r) {
  if (!r) return '—';
  return `<span class="badge" style="color:${r.color};border-color:${r.color}">${r.name}</span>`;
}

function applyTheme(theme) {
  const safeTheme = theme === 'light' ? 'light' : 'dark';
  document.body.classList.toggle('theme-light', safeTheme === 'light');
}

function renderPlayer() {
  const l = state.level;
  document.getElementById('player-level').textContent = `Lv.${l.level}`;
  document.getElementById('xp-bar').style.width = `${Math.round(l.progress * 100)}%`;
  document.getElementById('xp-meta').textContent = `${l.xp_in_level}/${l.xp_for_next} XP до следующего уровня`;
  document.getElementById('quick-stats').innerHTML = `<div>Открыто кейсов: <b>${state.stats.total_opened}</b></div><div>Потрачено: <b>${state.stats.total_spent}</b></div>`;
}

function itemRaritySelect(value) {
  return `<select data-k="rarity_id">${state.rarities.map((r) => `<option value="${r.id}" ${r.id === value ? 'selected' : ''}>${r.name}</option>`).join('')}</select>`;
}

function renderItems() {
  document.getElementById('item-rarity').innerHTML = state.rarities.map((r) => `<option value="${r.id}">${r.name}</option>`).join('');
  const rows = state.items.map((i) => `<tr data-id="${i.id}"><td><input data-k="name" value="${escapeHtml(i.name)}"></td><td>${itemRaritySelect(i.rarity_id)}</td><td><input data-k="weight" type="number" step="0.1" min="0" value="${i.weight}" style="width:90px"></td><td><div class="row">${itemThumb(i.image_path, i.name)}<input data-k="image_path" value="${escapeHtml(i.image_path || '')}" placeholder="URL картинки"></div></td><td><input data-k="description" value="${escapeHtml(i.description || '')}" placeholder="Описание"></td><td><button onclick="delItem('${i.id}')">Удалить</button></td></tr>`).join('');
  document.getElementById('items-table').innerHTML = `<tr><th>Название</th><th>Редкость</th><th>Вес</th><th>Картинка + превью</th><th>Описание</th><th></th></tr>${rows}`;
}

function effectSelect(value) {
  return `<select data-k="drop_effect"><option value="" ${!value ? 'selected' : ''}>—</option><option value="neon" ${value === 'neon' ? 'selected' : ''}>neon</option><option value="pulse" ${value === 'pulse' ? 'selected' : ''}>pulse</option><option value="shimmer" ${value === 'shimmer' ? 'selected' : ''}>shimmer</option></select>`;
}

function renderRarities() {
  const rows = [...state.rarities]
    .sort((a, b) => a.min_roll - b.min_roll)
    .map((r) => `<tr data-id="${r.id}"><td><input data-k="name" value="${r.name}"></td><td><input data-k="min_roll" type="number" step="0.1" value="${r.min_roll}" style="width:90px"></td><td><input data-k="max_roll" type="number" step="0.1" value="${r.max_roll}" style="width:90px"></td><td><input data-k="color" type="color" value="${r.color}"></td><td><div class="row"><input data-k="drop_sound" value="${r.drop_sound || ''}" style="min-width:220px"><button onclick="pickSoundForRow('${r.id}')">…</button></div></td><td>${effectSelect(r.drop_effect)}</td><td>${badge(r)}</td><td><button onclick="delRarity('${r.id}')">Удалить</button></td></tr>`)
    .join('');
  document.getElementById('rarities-table').innerHTML = `<tr><th>Название</th><th>Min</th><th>Max</th><th>Цвет</th><th>Звук</th><th>Эффект</th><th>Превью</th><th></th></tr>${rows}`;
}

function renderInventory() {
  const rows = Object.entries(state.inventory)
    .map(([id, c]) => {
      const i = state.items.find((x) => x.id === id);
      if (!i) return '';
      return `<tr><td><span class="item-cell">${itemThumb(i.image_path, i.name)}${i.name}</span></td><td>${c}</td><td><button onclick="adj('${id}',1)">+1</button> <button onclick="adj('${id}',-1)">-1</button></td></tr>`;
    })
    .join('');
  document.getElementById('inventory-table').innerHTML = `<tr><th>Предмет</th><th>Кол-во</th><th></th></tr>${rows || '<tr><td colspan="3"><i>Инвентарь пуст</i></td></tr>'}`;
}

function renderFilters() {
  const f = state.settings.filters || {};
  const rh = f.rarity_hidden || {};
  const ih = f.item_hidden || {};

  document.getElementById('filters-rarity').innerHTML = state.rarities
    .map((r) => `<label style="display:flex;align-items:center;gap:6px;background:var(--surface);padding:6px 10px;border:1px solid var(--line);border-radius:8px"><input type="checkbox" ${rh[r.id] ? 'checked' : ''} onchange="toggleRarityFilter('${r.id}',this.checked)"> ${badge(r)}</label>`)
    .join('') || '<i>Нет редкостей</i>';

  const rows = state.items
    .map((i) => {
      const r = rarityById(i.rarity_id);
      return `<tr><td>${i.name}</td><td>${r ? badge(r) : '—'}</td><td><label><input type="checkbox" ${ih[i.id] ? 'checked' : ''} onchange="toggleItemFilter('${i.id}',this.checked)"> скрывать</label></td></tr>`;
    })
    .join('');
  document.getElementById('filters-items-table').innerHTML = `<tr><th>Предмет</th><th>Редкость</th><th>Фильтр</th></tr>${rows}`;
}

function renderSettings() {
  const s = state.settings;
  document.getElementById('set-roll-min').value = s.roll_min;
  document.getElementById('set-roll-max').value = s.roll_max;
  document.getElementById('set-open-price').value = s.open_price;
  document.getElementById('set-base-xp').value = s.levels.base_xp;
  document.getElementById('set-xp-growth').value = s.levels.xp_growth;
  document.getElementById('set-theme').value = (s.appearance && s.appearance.theme) || 'dark';
  applyTheme(document.getElementById('set-theme').value);
}

function renderAll() {
  renderPlayer();
  renderItems();
  renderRarities();
  renderFilters();
  renderInventory();
  renderSettings();
}

async function api(name, ...args) {
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api[name]) {
    setStatus(`API ${name} недоступен`, true);
    return null;
  }
  const result = await window.pywebview.api[name](...args);
  if (!result || result.ok === false) {
    setStatus(result && result.message ? result.message : 'Ошибка запроса', true);
    return result;
  }
  if (result.state) {
    state = result.state;
    renderAll();
  }
  setStatus('OK');
  return result;
}

async function openCases() {
  const res = await api('open_case', parseInt(document.getElementById('open-times').value || '1', 10));
  if (!res || !res.ok) return;

  const grouped = res.grouped_visible_results || [];
  const isUltraRare = (rarity) => rarity && rarity.drop_effect === 'shimmer';

  const html = grouped.map((x) => {
    const effectClass = x.rarity.drop_effect ? `effect-${x.rarity.drop_effect}` : '';
    const ultraClass = isUltraRare(x.rarity) ? 'effect-ultra' : '';
    const qtyHtml = x.qty > 1 ? `<span class="qty">x${x.qty}</span>` : '';
    return `<div class="drop-row ${effectClass} ${ultraClass}" style="--drop-color:${x.rarity.color || '#3b82f6'}">${badge(x.rarity)} <span class="item-cell">${itemThumb(x.item.image_path, x.item.name)}<b>${x.item.name}</b>${qtyHtml}</span> <small>лучший roll ${x.best_roll}</small></div>`;
  }).join('') || '<i>Все выпадения скрыты фильтром</i>';

  const hiddenInfo = res.hidden_results_count ? `<small>Скрыто фильтром: ${res.hidden_results_count}</small>` : '';
  document.getElementById('open-results').innerHTML = hiddenInfo + html;

  for (const drop of grouped.slice(0, 5)) {
    if (drop.rarity && drop.rarity.drop_sound) {
      await api('play_rarity_sound', drop.rarity.id);
    }
  }
}

async function addItem() {
  await api('add_item', {
    name: document.getElementById('item-name').value,
    rarity_id: document.getElementById('item-rarity').value,
    weight: parseFloat(document.getElementById('item-weight').value || '1'),
    image_path: document.getElementById('item-image').value,
    description: document.getElementById('item-description').value,
  });
}

async function delItem(id) {
  if (confirm('Удалить предмет?')) await api('delete_item', id);
}

async function saveItemsBulk() {
  const rows = [...document.querySelectorAll('#items-table tr[data-id]')].map((tr) => {
    const obj = { id: tr.dataset.id };
    for (const el of tr.querySelectorAll('[data-k]')) obj[el.dataset.k] = el.value;
    return obj;
  });
  await api('update_items_bulk', rows);
}

async function addRarity() {
  await api('add_rarity', {
    name: document.getElementById('rarity-name').value,
    min_roll: parseFloat(document.getElementById('rarity-min').value),
    max_roll: parseFloat(document.getElementById('rarity-max').value),
    color: document.getElementById('rarity-color').value,
    drop_sound: document.getElementById('rarity-sound').value,
    drop_effect: document.getElementById('rarity-effect').value,
  });
}

async function delRarity(id) {
  if (confirm('Удалить редкость?')) await api('delete_rarity', id);
}

async function adj(id, d) {
  await api('adjust_inventory', id, d);
}

async function clearInventory() {
  if (!confirm('Очистить весь инвентарь? Это действие нельзя отменить.')) return;
  await api('clear_inventory');
}

async function normalizeRanges() {
  await api('normalize_rarity_ranges');
}

async function saveRarityBulk() {
  const rows = [...document.querySelectorAll('#rarities-table tr[data-id]')].map((tr) => {
    const obj = { id: tr.dataset.id };
    for (const el of tr.querySelectorAll('[data-k]')) obj[el.dataset.k] = el.value;
    return obj;
  });
  await api('update_rarities_bulk', rows);
}

async function toggleRarityFilter(id, hidden) {
  await api('set_filter_rarity', id, hidden);
}

async function toggleItemFilter(id, hidden) {
  await api('set_filter_item', id, hidden);
}

async function saveSettings() {
  await api('update_settings', {
    roll_min: parseFloat(document.getElementById('set-roll-min').value),
    roll_max: parseFloat(document.getElementById('set-roll-max').value),
    open_price: parseFloat(document.getElementById('set-open-price').value),
    appearance: { theme: document.getElementById('set-theme').value },
    levels: {
      base_xp: parseInt(document.getElementById('set-base-xp').value, 10),
      xp_growth: parseFloat(document.getElementById('set-xp-growth').value),
    },
  });
}

async function pickSoundFile() {
  const res = await api('pick_sound_file');
  if (!res || !res.ok) return '';
  return res.path || '';
}

async function pickSoundForNewRarity() {
  const path = await pickSoundFile();
  if (path) document.getElementById('rarity-sound').value = path;
}

async function pickSoundForRow(rarityId) {
  const path = await pickSoundFile();
  if (!path) return;
  const row = document.querySelector(`#rarities-table tr[data-id="${rarityId}"]`);
  if (!row) return;
  const input = row.querySelector('input[data-k="drop_sound"]');
  if (input) input.value = path;
}

async function toggleTheme() {
  const current = (state.settings.appearance && state.settings.appearance.theme) || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  await api('update_settings', { appearance: { theme: next } });
}

window.addEventListener('pywebviewready', async () => {
  tab('open');
  const res = await window.pywebview.api.get_state();
  if (res && res.ok) {
    state = res.state;
    renderAll();
  }
});
</script>
</body></html>
"""
