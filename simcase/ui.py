HTML = r"""
<!doctype html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Симулятор кейсов</title>
<style>
:root{--bg:#090f1d;--panel:#111a2e;--line:#263655;--text:#e4ecfb;--muted:#a6b5d3;--accent:#3b82f6}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,Arial,sans-serif}
header{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px;align-items:center}
.container{padding:18px;display:grid;gap:14px} .grid{display:grid;grid-template-columns:1.4fr .9fr;gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap} input,select,button{background:#0b1324;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:8px}
button{cursor:pointer} button.primary{background:var(--accent);border-color:var(--accent)}
.tabs{display:flex;gap:8px;flex-wrap:wrap} .hidden{display:none}
.level{display:flex;align-items:center;gap:10px}.bar{height:10px;background:#0b1324;border:1px solid var(--line);border-radius:999px;overflow:hidden;flex:1}.bar>div{height:100%;background:linear-gradient(90deg,#22d3ee,#3b82f6)}
table{width:100%;border-collapse:collapse} th,td{padding:7px;border-bottom:1px solid #22304b;font-size:13px;text-align:left}
.badge{padding:2px 8px;border-radius:999px;border:1px solid;display:inline-block;font-size:12px}
small{color:var(--muted)}
</style>
</head>
<body>
<header>
 <div><strong>🎁 Симулятор кейсов 2.0</strong><br><small>Модульная версия с прогрессией игрока</small></div>
 <div id="status"></div>
</header>
<div class="container">
  <div class="tabs card">
    <button onclick="tab('open')">Открытие</button><button onclick="tab('items')">Предметы</button><button onclick="tab('rarities')">Редкости</button><button onclick="tab('inventory')">Инвентарь</button><button onclick="tab('settings')">Настройки</button>
  </div>
  <div class="grid">
    <section id="tab-open" class="card">
      <h3>Открытие кейсов</h3>
      <div class="row"><input id="open-times" type="number" min="1" value="1" style="width:100px"><button class="primary" onclick="openCases()">Открыть</button></div>
      <div id="open-results" style="margin-top:10px;max-height:420px;overflow:auto"></div>
    </section>
    <aside class="card">
      <h3>Прогресс игрока</h3>
      <div class="level"><strong id="player-level">Lv.1</strong><div class="bar"><div id="xp-bar" style="width:0%"></div></div></div>
      <small id="xp-meta"></small>
      <hr style="border-color:#20304e">
      <div id="quick-stats"></div>
    </aside>
  </div>

  <section id="tab-items" class="card hidden">
    <h3>Предметы</h3>
    <div class="row"><input id="item-name" placeholder="Название"><select id="item-rarity"></select><input id="item-weight" type="number" step="0.1" value="1" style="width:90px"><input id="item-image" placeholder="URL картинки"><input id="item-description" placeholder="Описание"><button onclick="addItem()">Добавить</button></div>
    <table id="items-table"></table>
  </section>

  <section id="tab-rarities" class="card hidden">
    <h3>Редкости (гибкое редактирование)</h3>
    <div class="row"><button onclick="normalizeRanges()">Авто-нормализация диапазонов</button><button onclick="saveRarityBulk()" class="primary">Сохранить все правки</button></div>
    <table id="rarities-table"></table>
    <h4>Новая редкость</h4>
    <div class="row"><input id="rarity-name" placeholder="Название"><input id="rarity-min" type="number" step="0.1" placeholder="min"><input id="rarity-max" type="number" step="0.1" placeholder="max"><input id="rarity-color" type="color" value="#888888"><input id="rarity-sound" placeholder="Звук"><select id="rarity-effect"><option value="">Без эффекта</option><option value="neon">Neon</option></select><button onclick="addRarity()">Добавить</button></div>
  </section>

  <section id="tab-inventory" class="card hidden"><h3>Инвентарь</h3><table id="inventory-table"></table></section>

  <section id="tab-settings" class="card hidden">
    <h3>Настройки симулятора и уровней</h3>
    <div class="row"><label>roll_min <input id="set-roll-min" type="number"></label><label>roll_max <input id="set-roll-max" type="number"></label><label>Цена открытия <input id="set-open-price" type="number"></label></div>
    <h4>Система опыта</h4>
    <div class="row"><label>Базовый XP на уровень <input id="set-base-xp" type="number" min="1"></label><label>Рост XP (множитель) <input id="set-xp-growth" type="number" step="0.01" min="1.01"></label><button class="primary" onclick="saveSettings()">Сохранить</button></div>
  </section>
</div>
<script>
let state=null; const hasPy=()=>window.pywebview&&window.pywebview.api;
function setStatus(t,e=false){const el=document.getElementById('status');el.textContent=t;el.style.color=e?'#fda4af':'#93c5fd'}
function rarityById(id){return state.rarities.find(r=>r.id===id)}
function badge(r){return `<span class="badge" style="color:${r.color};border-color:${r.color};background:${r.color}22">${r.name}</span>`}
function tab(name){for(const s of document.querySelectorAll('section[id^="tab-"]'))s.classList.add('hidden');document.getElementById('tab-'+name)?.classList.remove('hidden')}
async function api(name,...args){if(!hasPy()) throw new Error('pywebview API unavailable'); const r=await window.pywebview.api[name](...args); if(!r.ok){setStatus(r.message||'Ошибка',true); throw new Error(r.message||'err')} if(r.state) state=r.state; renderAll(); setStatus('Готово'); return r;}
function renderPlayer(){const lv=state.level;document.getElementById('player-level').textContent=`Lv.${lv.level}`;document.getElementById('xp-bar').style.width=`${Math.round(lv.progress*100)}%`;document.getElementById('xp-meta').textContent=`XP: ${lv.xp_current}/${lv.xp_needed} · всего открыто: ${lv.xp_total}`;document.getElementById('quick-stats').innerHTML=`<div>Открыто кейсов: <b>${state.stats.total_opened}</b></div><div>Потрачено: <b>${state.stats.total_spent}</b></div>`}
function renderItems(){document.getElementById('item-rarity').innerHTML=state.rarities.map(r=>`<option value="${r.id}">${r.name}</option>`).join(''); document.getElementById('items-table').innerHTML='<tr><th>Название</th><th>Редкость</th><th>Вес</th><th></th></tr>'+state.items.map(i=>`<tr><td>${i.name}</td><td>${badge(rarityById(i.rarity_id))}</td><td>${i.weight}</td><td><button onclick="delItem(\'${i.id}\')">Удалить</button></td></tr>`).join('')}
function renderRarities(){const rows=state.rarities.sort((a,b)=>a.min_roll-b.min_roll).map(r=>`<tr data-id="${r.id}"><td><input data-k="name" value="${r.name}"></td><td><input data-k="min_roll" type="number" step="0.1" value="${r.min_roll}" style="width:90px"></td><td><input data-k="max_roll" type="number" step="0.1" value="${r.max_roll}" style="width:90px"></td><td><input data-k="color" type="color" value="${r.color}"></td><td><input data-k="drop_sound" value="${r.drop_sound||''}"></td><td><select data-k="drop_effect"><option ${!r.drop_effect?'selected':''} value="">—</option><option ${r.drop_effect==='neon'?'selected':''} value="neon">neon</option></select></td><td><button onclick="delRarity('${r.id}')">Удалить</button></td></tr>`).join('');document.getElementById('rarities-table').innerHTML=`<tr><th>Название</th><th>Min</th><th>Max</th><th>Цвет</th><th>Звук</th><th>Эффект</th><th></th></tr>${rows}`}
function renderInventory(){const rows=Object.entries(state.inventory).map(([id,c])=>{const i=state.items.find(x=>x.id===id);if(!i)return '';return `<tr><td>${i.name}</td><td>${c}</td><td><button onclick="adj('${id}',1)">+1</button> <button onclick="adj('${id}',-1)">-1</button></td></tr>`}).join('');document.getElementById('inventory-table').innerHTML='<tr><th>Предмет</th><th>Кол-во</th><th></th></tr>'+rows}
function renderSettings(){const s=state.settings;document.getElementById('set-roll-min').value=s.roll_min;document.getElementById('set-roll-max').value=s.roll_max;document.getElementById('set-open-price').value=s.open_price;document.getElementById('set-base-xp').value=s.levels.base_xp;document.getElementById('set-xp-growth').value=s.levels.xp_growth}
function renderAll(){renderPlayer();renderItems();renderRarities();renderInventory();renderSettings()}
async function openCases(){const res=await api('open_case',parseInt(document.getElementById('open-times').value||'1',10));document.getElementById('open-results').innerHTML=res.results.slice(0,150).map(x=>`<div>${badge(x.rarity)} <b>${x.item.name}</b> <small>roll ${x.roll}</small></div>`).join('')||'<i>Ничего не выпало</i>'}
async function addItem(){await api('add_item',{name:document.getElementById('item-name').value,rarity_id:document.getElementById('item-rarity').value,weight:parseFloat(document.getElementById('item-weight').value||'1'),image_path:document.getElementById('item-image').value,description:document.getElementById('item-description').value})}
async function delItem(id){if(confirm('Удалить?')) await api('delete_item',id)}
async function addRarity(){await api('add_rarity',{name:document.getElementById('rarity-name').value,min_roll:parseFloat(document.getElementById('rarity-min').value),max_roll:parseFloat(document.getElementById('rarity-max').value),color:document.getElementById('rarity-color').value,drop_sound:document.getElementById('rarity-sound').value,drop_effect:document.getElementById('rarity-effect').value})}
async function delRarity(id){if(confirm('Удалить?')) await api('delete_rarity',id)}
async function adj(id,d){await api('adjust_inventory',id,d)}
async function normalizeRanges(){await api('normalize_rarity_ranges')}
async function saveRarityBulk(){const rows=[...document.querySelectorAll('#rarities-table tr[data-id]')].map(tr=>{const obj={id:tr.dataset.id};for(const el of tr.querySelectorAll('[data-k]')) obj[el.dataset.k]=el.value;return obj});await api('update_rarities_bulk',rows)}
async function saveSettings(){await api('update_settings',{roll_min:parseFloat(document.getElementById('set-roll-min').value),roll_max:parseFloat(document.getElementById('set-roll-max').value),open_price:parseFloat(document.getElementById('set-open-price').value),levels:{base_xp:parseInt(document.getElementById('set-base-xp').value,10),xp_growth:parseFloat(document.getElementById('set-xp-growth').value)}})}
window.addEventListener('pywebviewready',async()=>{const res=await window.pywebview.api.get_state();state=res.state;renderAll();});
</script>
</body></html>
"""
