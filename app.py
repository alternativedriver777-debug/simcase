import json
import os
import random
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


DATA_FILE = "case_simulator_data.json"


@dataclass
class Rarity:
    id: str
    name: str
    min_roll: float
    max_roll: float
    color: str = "#888888"
    drop_sound: str = ""   # путь к wav или URL, можно оставить пустым
    drop_effect: str = ""  # "" или "neon" (можно расширить)


@dataclass
class Item:
    id: str
    name: str
    rarity_id: str
    weight: float
    image_path: str = ""
    description: str = ""


class DataStore:
    def __init__(self, path: str = DATA_FILE):
        self.path = path
        self.data = {
            "rarities": [],
            "items": [],
            "inventory": {},
            "history": [],
            "stats": {
                "total_opened": 0,
                "total_spent": 0,
                "by_rarity": {},
                "by_item": {},
            },
            "settings": {
                "roll_min": 0,
                "roll_max": 100,
                "open_price": 1,
                "filters": {
                    "rarity_visible": {},
                    "item_visible": {},
                },
            },
        }
        self._load_or_create_defaults()

    def _load_or_create_defaults(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # merge loaded into defaults so new fields survive
                # do shallow update for top-level keys
                for k, v in loaded.items():
                    self.data[k] = v
                # ensure filters keys exist
                self.data["settings"].setdefault("filters", {"rarity_visible": {}, "item_visible": {}})
                self.data["settings"]["filters"].setdefault("rarity_visible", {})
                self.data["settings"]["filters"].setdefault("item_visible", {})
            except (json.JSONDecodeError, OSError):
                pass

        # If rarities absent, create defaults (with drop_sound and drop_effect keys)
        if not self.data.get("rarities"):
            self.data["rarities"] = [
                asdict(Rarity(str(uuid.uuid4()), "Обычная", 0, 60, "#b0b0b0", "", "")),
                asdict(Rarity(str(uuid.uuid4()), "Редкая", 60, 85, "#4f8cff", "", "")),
                asdict(Rarity(str(uuid.uuid4()), "Эпическая", 85, 97, "#bb6eff", "", "")),
                asdict(Rarity(str(uuid.uuid4()), "Легендарная", 97, 100, "#ff9f1a", "", "")),
            ]

        # If items absent, create defaults
        if not self.data.get("items"):
            r = self.data["rarities"]
            self.data["items"] = [
                asdict(Item(str(uuid.uuid4()), "Старый нож", r[0]["id"], 10, "", "Простой предмет")),
                asdict(Item(str(uuid.uuid4()), "Сияющий пистолет", r[1]["id"], 6, "", "Редкая находка")),
                asdict(Item(str(uuid.uuid4()), "Кристальный меч", r[2]["id"], 3, "", "Очень ценный")),
                asdict(Item(str(uuid.uuid4()), "Драконья корона", r[3]["id"], 1, "", "Почти не выпадает")),
            ]

        # Ensure each rarity has the new keys (for backwards compatibility with старого JSON)
        for r in self.data["rarities"]:
            if "drop_sound" not in r:
                r["drop_sound"] = ""
            if "drop_effect" not in r:
                r["drop_effect"] = ""

        self.save()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _rarity_map(self) -> Dict[str, dict]:
        return {r["id"]: r for r in self.data["rarities"]}

    def _item_map(self) -> Dict[str, dict]:
        return {i["id"]: i for i in self.data["items"]}

    def _append_history(self, action: str, payload: dict):
        self.data["history"].insert(0, {
            "id": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "action": action,
            "payload": payload,
        })
        # keep history bounded
        self.data["history"] = self.data["history"][:500]

    def _roll_rarity(self, roll: float) -> Optional[dict]:
        for r in self.data["rarities"]:
            if r["min_roll"] <= roll <= r["max_roll"]:
                return r
        return None

    def _pick_item_by_rarity(self, rarity_id: str) -> Optional[dict]:
        candidates = [i for i in self.data["items"] if i["rarity_id"] == rarity_id and i["weight"] > 0]
        if not candidates:
            return None
        total_weight = sum(i["weight"] for i in candidates)
        point = random.uniform(0, total_weight)
        current = 0
        for item in candidates:
            current += item["weight"]
            if point <= current:
                return item
        return candidates[-1]

    def _validate_rarity_ranges(self) -> Tuple[bool, str]:
        roll_min = self.data["settings"]["roll_min"]
        roll_max = self.data["settings"]["roll_max"]
        if roll_min >= roll_max:
            return False, "roll_min должен быть меньше roll_max"
        for r in self.data["rarities"]:
            if r["min_roll"] > r["max_roll"]:
                return False, f"У редкости {r['name']} min_roll > max_roll"
        ranges = sorted((r["min_roll"], r["max_roll"], r["name"]) for r in self.data["rarities"])
        for i in range(1, len(ranges)):
            # проверяем отсутствие пересечений (допускаем касание)
            if ranges[i][0] < ranges[i - 1][1]:
                return False, f"Диапазоны {ranges[i - 1][2]} и {ranges[i][2]} пересекаются"
        return True, "ok"

    def open_case(self, times: int = 1) -> dict:
        times = max(1, int(times))
        valid, msg = self._validate_rarity_ranges()
        if not valid:
            return {"ok": False, "message": msg}

        result = []
        settings = self.data["settings"]
        # Чтобы не засорять историю целиком, в историю кладу первые 100 результатов и общее количество
        for _ in range(times):
            roll = random.uniform(settings["roll_min"], settings["roll_max"])
            rarity = self._roll_rarity(roll)
            if rarity is None:
                continue
            item = self._pick_item_by_rarity(rarity["id"])
            if item is None:
                continue

            inv = self.data["inventory"]
            inv[item["id"]] = inv.get(item["id"], 0) + 1
            self.data["stats"]["total_opened"] += 1
            self.data["stats"]["total_spent"] += settings["open_price"]
            self.data["stats"]["by_rarity"][rarity["id"]] = self.data["stats"]["by_rarity"].get(rarity["id"], 0) + 1
            self.data["stats"]["by_item"][item["id"]] = self.data["stats"]["by_item"].get(item["id"], 0) + 1
            result.append({
                "roll": round(roll, 3),
                "rarity": rarity,
                "item": item,
            })

        # сохраняем в историю только первые 100 результатов и общее число
        self._append_history("open_case", {"times": times, "results": result[:100], "count_results": len(result)})
        self.save()
        return {"ok": True, "results": result, "state": self.state()}

    def add_rarity(self, rarity: dict) -> dict:
        entry = asdict(Rarity(
            id=str(uuid.uuid4()),
            name=rarity["name"],
            min_roll=float(rarity["min_roll"]),
            max_roll=float(rarity["max_roll"]),
            color=rarity.get("color", "#888888"),
            drop_sound=rarity.get("drop_sound", ""),
            drop_effect=rarity.get("drop_effect", ""),
        ))
        self.data["rarities"].append(entry)
        valid, msg = self._validate_rarity_ranges()
        if not valid:
            self.data["rarities"].pop()
            return {"ok": False, "message": msg}
        self._append_history("add_rarity", entry)
        self.save()
        return {"ok": True, "state": self.state()}

    def update_rarity(self, rarity_id: str, payload: dict) -> dict:
        for rarity in self.data["rarities"]:
            if rarity["id"] == rarity_id:
                rarity["name"] = payload.get("name", rarity["name"])
                rarity["min_roll"] = float(payload.get("min_roll", rarity["min_roll"]))
                rarity["max_roll"] = float(payload.get("max_roll", rarity["max_roll"]))
                rarity["color"] = payload.get("color", rarity["color"])
                # новые поля
                rarity["drop_sound"] = payload.get("drop_sound", rarity.get("drop_sound", ""))
                rarity["drop_effect"] = payload.get("drop_effect", rarity.get("drop_effect", ""))
                valid, msg = self._validate_rarity_ranges()
                if not valid:
                    return {"ok": False, "message": msg}
                self._append_history("update_rarity", rarity)
                self.save()
                return {"ok": True, "state": self.state()}
        return {"ok": False, "message": "Редкость не найдена"}

    def delete_rarity(self, rarity_id: str) -> dict:
        if any(i["rarity_id"] == rarity_id for i in self.data["items"]):
            return {"ok": False, "message": "Нельзя удалить редкость, пока есть связанные предметы"}
        before = len(self.data["rarities"])
        self.data["rarities"] = [r for r in self.data["rarities"] if r["id"] != rarity_id]
        if len(self.data["rarities"]) == before:
            return {"ok": False, "message": "Редкость не найдена"}
        # удалить фильтр для этой редкости, если был
        fv = self.data["settings"].get("filters", {}).get("rarity_visible", {})
        if rarity_id in fv:
            fv.pop(rarity_id, None)
        self._append_history("delete_rarity", {"rarity_id": rarity_id})
        self.save()
        return {"ok": True, "state": self.state()}

    def add_item(self, payload: dict) -> dict:
        rarity_map = self._rarity_map()
        if payload["rarity_id"] not in rarity_map:
            return {"ok": False, "message": "Указанная редкость не существует"}
        item = asdict(Item(
            id=str(uuid.uuid4()),
            name=payload["name"],
            rarity_id=payload["rarity_id"],
            weight=float(payload.get("weight", 1)),
            image_path=payload.get("image_path", ""),
            description=payload.get("description", ""),
        ))
        self.data["items"].append(item)
        self._append_history("add_item", item)
        self.save()
        return {"ok": True, "state": self.state()}

    def update_item(self, item_id: str, payload: dict) -> dict:
        rarity_map = self._rarity_map()
        for item in self.data["items"]:
            if item["id"] == item_id:
                if "rarity_id" in payload and payload["rarity_id"] not in rarity_map:
                    return {"ok": False, "message": "Указанная редкость не существует"}
                item["name"] = payload.get("name", item["name"])
                item["rarity_id"] = payload.get("rarity_id", item["rarity_id"])
                item["weight"] = float(payload.get("weight", item["weight"]))
                item["image_path"] = payload.get("image_path", item["image_path"])
                item["description"] = payload.get("description", item["description"])
                self._append_history("update_item", item)
                self.save()
                return {"ok": True, "state": self.state()}
        return {"ok": False, "message": "Предмет не найден"}

    def delete_item(self, item_id: str) -> dict:
        before = len(self.data["items"])
        self.data["items"] = [i for i in self.data["items"] if i["id"] != item_id]
        if len(self.data["items"]) == before:
            return {"ok": False, "message": "Предмет не найден"}
        self.data["inventory"].pop(item_id, None)
        # удалить фильтр по предмету, если был
        iv = self.data["settings"].get("filters", {}).get("item_visible", {})
        if item_id in iv:
            iv.pop(item_id, None)
        self._append_history("delete_item", {"item_id": item_id})
        self.save()
        return {"ok": True, "state": self.state()}

    def adjust_inventory(self, item_id: str, delta: int) -> dict:
        items = self._item_map()
        if item_id not in items:
            return {"ok": False, "message": "Предмет не найден"}
        cur = self.data["inventory"].get(item_id, 0)
        new_val = cur + delta
        if new_val < 0:
            return {"ok": False, "message": "Недостаточно предметов в инвентаре"}
        if new_val == 0:
            self.data["inventory"].pop(item_id, None)
        else:
            self.data["inventory"][item_id] = new_val
        action = "consume_item" if delta < 0 else "add_inventory"
        self._append_history(action, {"item_id": item_id, "delta": delta})
        self.save()
        return {"ok": True, "state": self.state()}

    def clear_inventory(self) -> dict:
        self.data["inventory"] = {}
        self._append_history("clear_inventory", {})
        self.save()
        return {"ok": True, "state": self.state()}

    def set_filter_rarity(self, rarity_id: str, value: bool) -> dict:
        fl = self.data["settings"].setdefault("filters", {})
        rv = fl.setdefault("rarity_visible", {})
        if value:
            rv[rarity_id] = True
        else:
            rv.pop(rarity_id, None)
        self._append_history("set_filter_rarity", {"rarity_id": rarity_id, "value": value})
        self.save()
        return {"ok": True, "state": self.state()}

    def set_filter_item(self, item_id: str, value: bool) -> dict:
        fl = self.data["settings"].setdefault("filters", {})
        iv = fl.setdefault("item_visible", {})
        if value:
            iv[item_id] = True
        else:
            iv.pop(item_id, None)
        self._append_history("set_filter_item", {"item_id": item_id, "value": value})
        self.save()
        return {"ok": True, "state": self.state()}

    def update_settings(self, payload: dict) -> dict:
        s = self.data["settings"]
        for key in ("roll_min", "roll_max", "open_price"):
            if key in payload:
                s[key] = float(payload[key])
        valid, msg = self._validate_rarity_ranges()
        if not valid:
            return {"ok": False, "message": msg}
        self._append_history("update_settings", s)
        self.save()
        return {"ok": True, "state": self.state()}

    def clear_history(self):
        self.data["history"] = []
        self.save()
        return {"ok": True, "state": self.state()}

    def reset_stats(self):
        self.data["stats"] = {
            "total_opened": 0,
            "total_spent": 0,
            "by_rarity": {},
            "by_item": {},
        }
        self._append_history("reset_stats", {})
        self.save()
        return {"ok": True, "state": self.state()}

    def state(self):
        return self.data

    def play_rarity_sound(self, rarity_id: str) -> dict:
        """
        Попытаться проиграть звук для заданной редкости через winsound (Windows).
        Если winsound недоступен или проигрыш завершился ошибкой, возвращаем информацию для fallback-а на клиенте.
        """
        rarity = None
        for r in self.data["rarities"]:
            if r["id"] == rarity_id:
                rarity = r
                break
        if rarity is None:
            return {"ok": False, "message": "Редкость не найдена", "played": False}

        path = rarity.get("drop_sound", "") or ""
        if not path:
            return {"ok": True, "message": "No sound configured", "played": False}

        # Попытка проиграть через winsound
        try:
            import winsound
            # проигрывание асинхронное, если это локальный .wav файл и winsound доступен
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return {"ok": True, "played": True}
        except Exception as e:
            # Например, ImportError (не Windows) или файл не найден
            return {"ok": False, "played": False, "message": str(e), "sound": path}


class API:
    def __init__(self):
        self.store = DataStore()

    def get_state(self):
        return {"ok": True, "state": self.store.state()}

    def open_case(self, times=1):
        return self.store.open_case(times)

    def add_rarity(self, rarity):
        return self.store.add_rarity(rarity)

    def update_rarity(self, rarity_id, payload):
        return self.store.update_rarity(rarity_id, payload)

    def delete_rarity(self, rarity_id):
        return self.store.delete_rarity(rarity_id)

    def add_item(self, payload):
        return self.store.add_item(payload)

    def update_item(self, item_id, payload):
        return self.store.update_item(item_id, payload)

    def delete_item(self, item_id):
        return self.store.delete_item(item_id)

    def adjust_inventory(self, item_id, delta):
        return self.store.adjust_inventory(item_id, int(delta))

    def clear_inventory(self):
        return self.store.clear_inventory()

    def set_filter_rarity(self, rarity_id, value):
        return self.store.set_filter_rarity(rarity_id, bool(value))

    def set_filter_item(self, item_id, value):
        return self.store.set_filter_item(item_id, bool(value))

    def update_settings(self, payload):
        return self.store.update_settings(payload)

    def clear_history(self):
        return self.store.clear_history()

    def reset_stats(self):
        return self.store.reset_stats()

    def play_rarity_sound(self, rarity_id):
        return self.store.play_rarity_sound(rarity_id)


HTML = r"""
<!doctype html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<title>Симулятор кейсов</title>
<style>
  body { font-family: Inter, Arial, sans-serif; margin: 0; background: #0b1220; color: #f8fafc; }
  header { padding: 16px 22px; border-bottom: 1px solid #263042; display:flex; justify-content:space-between; align-items:center; }
  .container { padding: 18px 22px; }
  .row { display:flex; gap:12px; flex-wrap:wrap; align-items:center; }
  .card { background: #0f1724; border:1px solid #1f2937; border-radius:10px; padding:14px; margin-bottom:14px; }
  .card h3 { margin-top:0; }
  input, select, button, textarea { background:#0b1220; color:#f8fafc; border:1px solid #243041; border-radius:8px; padding:8px; }
  button { cursor:pointer; }
  button.primary { background:#2563eb; border-color:#2563eb; color:white; }
  table { width:100%; border-collapse: collapse; }
  th,td { border-bottom:1px solid #1f2a3a; padding:8px; text-align:left; font-size: 13px; vertical-align:middle; }
  .tabs button { margin-right: 8px; }
  .hidden { display:none; }
  .badge { padding:4px 10px; border-radius:999px; font-size:12px; display:inline-block; }
  .mini { font-size:12px; color:#cbd5e1; }
  .img-thumb { width:44px; height:44px; object-fit:cover; border-radius:8px; border:1px solid #243041; vertical-align:middle; }
  .filters { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
  .filter-item { display:flex; gap:6px; align-items:center; padding:4px 6px; border-radius:6px; border:1px solid #1f2a3a; }
  .small { font-size:12px; padding:6px; }

  /* Эффекты для выпадения */
  .drop-row { padding:8px; border-radius:8px; transition: transform 0.15s ease, box-shadow 0.2s ease; margin-bottom:6px; background: rgba(255,255,255,0.01); }
  .drop-row:hover { transform: translateY(-3px); }
  .effect-neon {
    animation: neonPulse 1.2s ease-in-out infinite;
    box-shadow: 0 0 8px 3px rgba(255,160,60,0.12), 0 0 20px 6px rgba(255,160,60,0.06);
    border:1px solid rgba(255,160,60,0.18);
  }

  @keyframes neonPulse {
    0% { box-shadow: 0 0 6px 2px rgba(255,160,60,0.06); transform: scale(1) }
    50% { box-shadow: 0 0 18px 6px rgba(255,160,60,0.16); transform: scale(1.01) }
    100% { box-shadow: 0 0 6px 2px rgba(255,160,60,0.06); transform: scale(1) }
  }

  /* подсказки внутри результата */
  .result-meta { margin-left:10px; color:#cbd5e1; font-size:12px; }
</style>
</head>
<body>
<header>
  <strong>🎁 Полнофункциональный симулятор кейсов</strong>
  <span id="status" class="mini"></span>
</header>
<div class="container">
  <div class="tabs card">
    <button onclick="showTab('open')">Открытие</button>
    <button onclick="showTab('items')">Предметы</button>
    <button onclick="showTab('rarities')">Редкости</button>
    <button onclick="showTab('filters')">Фильтры</button>
    <button onclick="showTab('inventory')">Инвентарь</button>
    <button onclick="showTab('history')">История</button>
    <button onclick="showTab('stats')">Статистика</button>
    <button onclick="showTab('settings')">Настройки</button>
  </div>

  <section id="tab-open" class="card">
    <h3>Открытие кейсов</h3>
    <div class="row" style="align-items:center">
      <label>Количество <input id="open-times" type="number" min="1" value="1" style="width:120px" /></label>
      <button class="primary" onclick="openCases()">Открыть</button>
      <label class="small">Показать только отфильтрованные: <input id="only-show-filtered" type="checkbox" /></label>
      <div style="flex:1"></div>
      <div id="filter-summary" class="mini"></div>
    </div>

    <div id="open-results" style="margin-top:10px; max-height:420px; overflow:auto"></div>
  </section>

  <section id="tab-items" class="card hidden">
    <h3>Управление предметами</h3>
    <div class="row">
      <input id="item-name" placeholder="Название" />
      <select id="item-rarity"></select>
      <input id="item-weight" type="number" step="0.1" value="1" placeholder="Вес" style="width:90px" />
      <input id="item-image" placeholder="Путь/URL изображения" />
      <input id="item-description" placeholder="Описание" />
      <button onclick="addItem()">Добавить</button>
    </div>
    <table id="items-table" style="margin-top:12px"></table>
  </section>

  <section id="tab-rarities" class="card hidden">
    <h3>Категории редкости и диапазоны</h3>
    <div class="row">
      <input id="rarity-name" placeholder="Название" />
      <input id="rarity-min" type="number" step="0.1" placeholder="min" />
      <input id="rarity-max" type="number" step="0.1" placeholder="max" />
      <input id="rarity-color" type="color" value="#888888" />
      <input id="rarity-sound" placeholder="Путь к звуку (wav) или URL" style="width:260px" />
      <select id="rarity-effect">
        <option value="">Эффект: нет</option>
        <option value="neon">Неоновое свечение</option>
      </select>
      <button onclick="addRarity()">Добавить</button>
    </div>
    <table id="rarities-table" style="margin-top:12px"></table>
  </section>

  <section id="tab-filters" class="card hidden">
    <h3>Фильтры</h3>

    <div style="margin-top:10px">
      <strong>Фильтр по редкости:</strong>
      <div id="rarity-filters" class="filters" style="margin-top:8px"></div>
    </div>

    <div style="margin-top:12px">
      <strong>Фильтр по предмету:</strong>
      <div id="item-filters" class="filters" style="margin-top:8px"></div>
    </div>

    <div style="margin-top:12px" class="mini">
      Отметьте редкости и/или предметы, которые хотите видеть при открытии кейсов. Пустой набор фильтров означает — показать всё.
    </div>
  </section>

  <section id="tab-inventory" class="card hidden">
    <h3>Инвентарь и массовые операции</h3>
    <div class="row" style="margin-bottom:8px">
      <button onclick="clearInventory()" class="small">Очистить весь инвентарь</button>
      <div style="flex:1"></div>
      <div class="mini">Подсказка: используйте флажки рядом с предметами для фильтрации при открытии.</div>
    </div>
    <table id="inventory-table"></table>
  </section>

  <section id="tab-history" class="card hidden">
    <h3>История действий</h3>
    <button onclick="clearHistory()">Очистить историю</button>
    <table id="history-table" style="margin-top:8px"></table>
  </section>

  <section id="tab-stats" class="card hidden">
    <h3>Статистика</h3>
    <button onclick="resetStats()">Сброс статистики</button>
    <div id="stats-box" style="margin-top:12px"></div>
  </section>

  <section id="tab-settings" class="card hidden">
    <h3>Настройки симулятора</h3>
    <div class="row">
      <label>roll_min <input id="set-roll-min" type="number" step="0.1"></label>
      <label>roll_max <input id="set-roll-max" type="number" step="0.1"></label>
      <label>Цена открытия <input id="set-open-price" type="number" step="0.1"></label>
      <button onclick="saveSettings()">Сохранить</button>
    </div>
  </section>
</div>

<script>
let state = null;

function setStatus(text, err=false) {
  const el = document.getElementById('status');
  el.textContent = text;
  el.style.color = err ? '#fca5a5' : '#93c5fd';
}

function showTab(name) {
  for (const sec of document.querySelectorAll('section[id^="tab-"]')) sec.classList.add('hidden');
  const el = document.getElementById('tab-' + name);
  if (el) el.classList.remove('hidden');
}

function rarityById(id) { return state.rarities.find(r => r.id === id); }
function itemById(id) { return state.items.find(i => i.id === id); }

async function apiCall(name, ...args) {
  const res = await window.pywebview.api[name](...args);
  if (!res.ok) { setStatus(res.message || 'Ошибка', true); throw new Error(res.message || 'Ошибка'); }
  if (res.state) state = res.state;
  setStatus('Готово');
  renderAll();
  return res;
}

function rarityBadge(r) {
  return `<span class="badge" style="background:${r.color}22;border:1px solid ${r.color};color:${r.color}">${r.name}</span>`;
}

function renderRarityFilters() {
  const container = document.getElementById('rarity-filters');
  if (!container) return;
  const f = state.settings && state.settings.filters ? state.settings.filters.rarity_visible || {} : {};
  // сортируем редкости по min_roll desc (чтобы редкие сверху)
  const rarities = [...state.rarities].sort((a,b) => (a.min_roll === b.min_roll) ? a.name.localeCompare(b.name) : b.min_roll - a.min_roll);
  const html = rarities.map(r => {
    const checked = f[r.id] ? 'checked' : '';
    return `<label class="filter-item"><input type="checkbox" onchange="toggleRarityFilter('${r.id}', this.checked)" ${checked}/> ${rarityBadge(r)}</label>`;
  }).join('');
  container.innerHTML = html;
  updateFilterSummary();
}

function renderItemFilters() {
  const container = document.getElementById('item-filters');
  if (!container) return;
  const f = state.settings && state.settings.filters ? state.settings.filters.item_visible || {} : {};
  // sort items by rarity (rare first) then name
  const rarityOrder = {};
  state.rarities.forEach(r => rarityOrder[r.id] = r.min_roll || 0);
  const itemsSorted = [...state.items].sort((a,b) => {
    const ra = rarityOrder[a.rarity_id] || 0;
    const rb = rarityOrder[b.rarity_id] || 0;
    if (ra !== rb) return rb - ra;
    return a.name.localeCompare(b.name);
  });
  const html = itemsSorted.map(i => {
    const checked = f[i.id] ? 'checked' : '';
    const r = rarityById(i.rarity_id);
    const small = r ? `<span class="mini" style="margin-left:6px">${r.name}</span>` : '';
    return `<label class="filter-item"><input type="checkbox" onchange="toggleItemFilter('${i.id}', this.checked)" ${checked}/> ${i.name} ${small}</label>`;
  }).join('');
  container.innerHTML = html;
  updateFilterSummary();
}

function updateFilterSummary(){
  const f = state.settings && state.settings.filters ? state.settings.filters : {rarity_visible:{}, item_visible:{}}; 
  const rcount = Object.keys(f.rarity_visible || {}).length;
  const icount = Object.keys(f.item_visible || {}).length;
  const el = document.getElementById('filter-summary');
  if(rcount===0 && icount===0) el.textContent = 'Фильтры: не заданы (показываются все выпадения)';
  else el.textContent = `Фильтры: редкости ${rcount>0?rcount+' отмеч.':''} ${icount>0?'; предметы '+icount+' отмеч.':''}`;
}

// Items table (sorted by rarity)
function renderItems() {
  const sel = document.getElementById('item-rarity');
  sel.innerHTML = state.rarities.map(r => `<option value="${r.id}">${r.name}</option>`).join('');

  const tbl = document.getElementById('items-table');
  const head = `<tr><th></th><th>Изобр.</th><th>Название</th><th>Редкость</th><th>Вес</th><th>Описание</th><th></th></tr>`;
  // сортируем items по редкости (min_roll desc), затем по имени
  const rarityOrder = {};
  state.rarities.forEach(r => rarityOrder[r.id] = r.min_roll || 0);
  const itemsSorted = [...state.items].sort((a,b) => {
    const ra = rarityOrder[a.rarity_id] || 0;
    const rb = rarityOrder[b.rarity_id] || 0;
    if (ra !== rb) return rb - ra;
    return a.name.localeCompare(b.name);
  });

  const itemFilters = state.settings && state.settings.filters ? state.settings.filters.item_visible || {} : {};
  const rows = itemsSorted.map(i => {
    const r = rarityById(i.rarity_id);
    const img = i.image_path ? `<img class="img-thumb" src="${i.image_path}"/>` : '-';
    const checked = itemFilters[i.id] ? 'checked' : '';
    return `<tr>
      <td style="width:40px"><input type="checkbox" onchange="toggleItemFilter('${i.id}', this.checked)" ${checked} /></td>
      <td style="width:54px">${img}</td>
      <td>${i.name}</td>
      <td>${r ? rarityBadge(r) : '-'}</td>
      <td>${i.weight}</td>
      <td>${i.description || ''}</td>
      <td>
        <button onclick="editItem('${i.id}')">Ред.</button>
        <button onclick="deleteItem('${i.id}')">Удалить</button>
      </td>
    </tr>`;
  }).join('');
  tbl.innerHTML = head + rows;
}

function renderRarities() {
  const tbl = document.getElementById('rarities-table');
  const head = `<tr><th>Название</th><th>Диапазон</th><th>Цвет</th><th>Звук</th><th>Эффект</th><th></th></tr>`;
  // sort rarities by min_roll desc
  const rows = [...state.rarities].sort((a,b)=> b.min_roll - a.min_roll).map(r => `<tr>
    <td>${r.name}</td>
    <td>${r.min_roll} - ${r.max_roll}</td>
    <td>${rarityBadge(r)}</td>
    <td style="max-width:260px; overflow:hidden; text-overflow:ellipsis;">${r.drop_sound || '<i>нет</i>'}</td>
    <td>${r.drop_effect || '<i>нет</i>'}</td>
    <td>
      <button onclick="editRarity('${r.id}')">Ред.</button>
      <button onclick="deleteRarity('${r.id}')">Удалить</button>
    </td>
  </tr>`).join('');
  tbl.innerHTML = head + rows;
}

function renderInventory() {
  const tbl = document.getElementById('inventory-table');
  const head = `<tr><th></th><th>Предмет</th><th>Редкость</th><th>Количество</th><th>Массово вычесть</th><th></th></tr>`;
  // Sort inventory by rarity (rare first), then by name
  const rarityOrder = {};
  state.rarities.forEach(r => rarityOrder[r.id] = r.min_roll || 0);
  const invEntries = Object.entries(state.inventory || {});
  const rows = invEntries.map(([itemId, qty]) => {
    const i = itemById(itemId);
    if (!i) return '';
    const r = rarityById(i.rarity_id);
    const checked = (state.settings && state.settings.filters && state.settings.filters.item_visible && state.settings.filters.item_visible[itemId]) ? 'checked' : '';
    return {
      sortKey: (rarityOrder[i.rarity_id] || 0),
      html: `<tr>
      <td style="width:40px"><input type="checkbox" onchange="toggleItemFilter('${i.id}', this.checked)" ${checked} /></td>
      <td>${i.name}</td>
      <td>${r ? rarityBadge(r) : '-'}</td>
      <td id="inv-qty-${i.id}">${qty}</td>
      <td style="width:200px">
        <input id="dec-${i.id}" type="number" min="1" placeholder="кол-во" style="width:100px" />
        <button onclick="massAdjust('${i.id}')">Вычесть</button>
      </td>
      <td><button onclick="adjustInv('${i.id}',1)">+1</button> <button onclick="adjustInv('${i.id}',-1)">-1</button></td>
    </tr>`
    };
  }).filter(Boolean);

  // sort by rarity desc then join
  rows.sort((a,b)=> b.sortKey - a.sortKey);
  const rowsHtml = rows.map(r => r.html).join('');
  tbl.innerHTML = head + rowsHtml;
}

function renderHistory() {
  const tbl = document.getElementById('history-table');
  const head = `<tr><th>Время</th><th>Действие</th><th>Данные</th></tr>`;
  const rows = (state.history || []).slice(0, 200).map(h => `<tr>
    <td>${new Date(h.timestamp * 1000).toLocaleString()}</td>
    <td>${h.action}</td>
    <td><code>${JSON.stringify(h.payload)}</code></td>
  </tr>`).join('');
  tbl.innerHTML = head + rows;
}

function renderStats() {
  const box = document.getElementById('stats-box');
  const s = state.stats || {total_opened:0, total_spent:0, by_rarity:{}, by_item:{}} ;
  const rarityStats = Object.entries(s.by_rarity || {}).map(([rid, cnt]) => {
    const r = rarityById(rid);
    return `<li>${r ? r.name : rid}: ${cnt}</li>`;
  }).join('');
  const itemStats = Object.entries(s.by_item || {}).map(([iid, cnt]) => {
    const i = itemById(iid);
    return `<li>${i ? i.name : iid}: ${cnt}</li>`;
  }).join('');

  box.innerHTML = `
    <p>Всего открытий: <strong>${s.total_opened}</strong></p>
    <p>Потрачено валюты: <strong>${s.total_spent}</strong></p>
    <h4>По редкостям</h4><ul>${rarityStats}</ul>
    <h4>По предметам</h4><ul>${itemStats}</ul>
  `;
}

function renderSettings() {
  document.getElementById('set-roll-min').value = state.settings.roll_min;
  document.getElementById('set-roll-max').value = state.settings.roll_max;
  document.getElementById('set-open-price').value = state.settings.open_price;
}

function renderAll() {
  if (!state) return;
  renderRarityFilters();
  renderItemFilters();
  renderItems();
  renderRarities();
  renderInventory();
  renderHistory();
  renderStats();
  renderSettings();
}

// openCases: рендер результатов + проигрывание звуков и применение визуальных эффектов
async function openCases() {
  const times = parseInt(document.getElementById('open-times').value || '1', 10);
  const res = await apiCall('open_case', times);
  const onlyShowFiltered = document.getElementById('only-show-filtered').checked;
  const filters = state.settings && state.settings.filters ? state.settings.filters : {rarity_visible:{}, item_visible:{}};
  const rarityFilt = filters.rarity_visible || {};
  const itemFilt = filters.item_visible || {};

  // Decide visibility: if no filters set at all -> show all.
  const anyFilters = (Object.keys(rarityFilt).length + Object.keys(itemFilt).length) > 0;

  // Build summary counts and filtered view
  const counts = {}; // rarityId -> count
  for (const row of res.results) {
    const rid = row.rarity.id;
    counts[rid] = (counts[rid] || 0) + 1;
  }

  // Show summary (counts by rarity)
  const summaryHtml = Object.entries(counts).map(([rid, cnt])=>{
    const r = rarityById(rid);
    return `<div style="display:inline-block; margin-right:8px;">${r ? rarityBadge(r) : rid} <span class="mini">x${cnt}</span></div>`;
  }).join('');

  // Now detailed list (possibly filtered)
  const toShow = [];
  const hiddenCounts = {};
  for (const row of res.results) {
    const item = row.item;
    const rarity = row.rarity;
    const isRarityChecked = !!rarityFilt[rarity.id];
    const isItemChecked = !!itemFilt[item.id];
    const visible = !anyFilters ? true : (isRarityChecked || isItemChecked);
    if (visible) toShow.push(row);
    else {
      hiddenCounts[rarity.id] = (hiddenCounts[rarity.id] || 0) + 1;
    }
  }

  // Create HTML for shown items. Добавляем data-аттрибуты для звука/эффекта
  const MAX_DETAILS = 500; // safety cap for rendering
  const detailsHtml = toShow.slice(0, MAX_DETAILS).map((row, idx) => {
    const item = row.item;
    const rarity = row.rarity;
    const img = item.image_path
      ? `<img class="img-thumb" src="${item.image_path}" style="margin-right:8px;">`
      : '<span style="display:inline-block; width:44px; height:44px; margin-right:8px;"></span>';
    const effectClass = rarity.drop_effect ? `effect-${rarity.drop_effect}` : '';
    // дроп-строка с data-аттрибутами
    return `<div class="drop-row ${effectClass}" data-rarity-id="${rarity.id}" data-sound="${encodeURIComponent(rarity.drop_sound || '')}">
      ${img}
      <div><div>${rarityBadge(rarity)} <strong>${item.name}</strong> <span class="mini">(roll ${row.roll})</span></div>
      <div class="result-meta">${item.description || ''}${rarity.drop_sound ? ' · звук: ' + (rarity.drop_sound) : ''}${rarity.drop_effect ? ' · эффект: ' + rarity.drop_effect : ''}</div>
      </div>
    </div>`;
  }).join('');

  const hiddenSummaryHtml = Object.entries(hiddenCounts).map(([rid, cnt])=>{
    const r = rarityById(rid);
    return `<div style="display:inline-block; margin-right:8px; opacity:0.6;">${r ? rarityBadge(r) : rid} <span class="mini">скрыто x${cnt}</span></div>`;
  }).join('');

  const total = res.results.length;
  const shown = toShow.length;
  const hidden = total - shown;

  const finalHtml = `
    <div style="margin-bottom:8px"><strong>Итого</strong>: всего ${total}. Показано: ${shown}. Скрыто: ${hidden}.</div>
    <div style="margin-bottom:8px">${summaryHtml}</div>
    <div id="results-list">${detailsHtml}</div>
    <div style="margin-top:8px; color:#9aa4b2">${hiddenSummaryHtml}</div>
    ${toShow.length > MAX_DETAILS ? `<div class="mini">Показаны первые ${MAX_DETAILS} совпадений.</div>` : ''}
  `;
  document.getElementById('open-results').innerHTML = finalHtml || '<i>Нет выпавших предметов</i>';

  // После вставки DOM — запустить звуки и эффекты
  playSoundsForResults();
}

async function playSoundsForResults() {
  // Найти все .drop-row и попытаться проиграть звук для каждого.
  const rows = Array.from(document.querySelectorAll('.drop-row'));
  // Ограничение на одновременное проигрывание, чтобы не перегружать систему
  const MAX_PLAY = 200;
  for (let i = 0; i < Math.min(rows.length, MAX_PLAY); i++) {
    const row = rows[i];
    const rarityId = row.dataset.rarityId;
    const soundEnc = row.dataset.sound || '';
    const sound = soundEnc ? decodeURIComponent(soundEnc) : '';

    if (!sound) continue; // звук не настроен — пропускаем

    // Попытаться через серверный winsound (если доступен). Если сервер вернул played=false, делаем fallback с HTML5 Audio
    try {
      window.pywebview.api.play_rarity_sound(rarityId).then(res=>{
        if (res && res.ok && res.played) {
          // проигрывается на стороне Python (winsound) — ничего не делаем в браузере
        } else {
          // fallback: попробовать HTML5 Audio (если путь выглядит как URL или поддерживаемый локальный путь)
          try {
            const audio = new Audio(sound);
            // не ожидаем завершения, воспроизводим асинхронно
            audio.play().catch(err=>{
              // игнорируем ошибки воспроизведения
              console.warn('Audio playback failed (fallback):', err);
            });
          } catch (e) {
            console.warn('Audio fallback error', e);
          }
        }
      }).catch(e=>{
        // если вызов сервера не удался, пробуем HTML5 audio
        try {
          const audio = new Audio(sound);
          audio.play().catch(err => console.warn('Audio playback failed (fallback2):', err));
        } catch (ee) {
          console.warn('Audio fallback error 2', ee);
        }
      });
    } catch (e) {
      // синхронная ошибка, пробуем html5
      try {
        const audio = new Audio(sound);
        audio.play().catch(err => console.warn('Audio playback failed (fallback3):', err));
      } catch (ee) {
        console.warn('Audio fallback error 3', ee);
      }
    }
    // Заметим: не ждём завершения звука — даём звукам накладываться
  }
}

async function addItem() {
  await apiCall('add_item', {
    name: document.getElementById('item-name').value,
    rarity_id: document.getElementById('item-rarity').value,
    weight: parseFloat(document.getElementById('item-weight').value || '1'),
    image_path: document.getElementById('item-image').value,
    description: document.getElementById('item-description').value,
  });
  // clear inputs
  document.getElementById('item-name').value = '';
  document.getElementById('item-weight').value = '1';
  document.getElementById('item-image').value = '';
  document.getElementById('item-description').value = '';
}

async function editItem(id) {
  const i = itemById(id);
  const name = prompt('Название', i.name); if (name === null) return;
  const weight = prompt('Вес', i.weight); if (weight === null) return;
  const image_path = prompt('Изображение', i.image_path || '') ?? '';
  const description = prompt('Описание', i.description || '') ?? '';
  const rarity_id = prompt('ID редкости', i.rarity_id); if (rarity_id === null) return;
  await apiCall('update_item', id, {name, weight: parseFloat(weight), image_path, description, rarity_id});
}

async function deleteItem(id) { if (confirm('Удалить предмет?')) await apiCall('delete_item', id); }

async function addRarity() {
  await apiCall('add_rarity', {
    name: document.getElementById('rarity-name').value,
    min_roll: parseFloat(document.getElementById('rarity-min').value),
    max_roll: parseFloat(document.getElementById('rarity-max').value),
    color: document.getElementById('rarity-color').value,
    drop_sound: document.getElementById('rarity-sound').value || '',
    drop_effect: document.getElementById('rarity-effect').value || '',
  });
  // clear inputs
  document.getElementById('rarity-name').value = '';
  document.getElementById('rarity-min').value = '';
  document.getElementById('rarity-max').value = '';
  document.getElementById('rarity-sound').value = '';
  document.getElementById('rarity-effect').value = '';
}

async function editRarity(id) {
  const r = rarityById(id);
  const name = prompt('Название', r.name); if (name === null) return;
  const min_roll = prompt('Минимум', r.min_roll); if (min_roll === null) return;
  const max_roll = prompt('Максимум', r.max_roll); if (max_roll === null) return;
  const color = prompt('Цвет (hex)', r.color); if (color === null) return;
  const drop_sound = prompt('Путь к звуку (wav) или URL', r.drop_sound || '') ?? '';
  const drop_effect = prompt('Эффект при выпадении (пусто или neon)', r.drop_effect || '') ?? '';
  await apiCall('update_rarity', id, {name, min_roll: parseFloat(min_roll), max_roll: parseFloat(max_roll), color, drop_sound, drop_effect});
}

async function deleteRarity(id) { if (confirm('Удалить редкость?')) await apiCall('delete_rarity', id); }

async function adjustInv(id, delta) {
  await apiCall('adjust_inventory', id, delta);
}

async function massAdjust(id) {
  const el = document.getElementById('dec-' + id);
  if (!el) return;
  const val = parseInt(el.value || '0', 10);
  if (!val || val <= 0) { alert('Введите корректное количество (>0)'); return; }
  // вычесть val
  await apiCall('adjust_inventory', id, -Math.abs(val));
  el.value = '';
}

async function clearInventory() {
  if (!confirm('Полностью очистить инвентарь?')) return;
  await apiCall('clear_inventory');
}

async function clearHistory() { if (confirm('Очистить историю?')) await apiCall('clear_history'); }
async function resetStats() { if (confirm('Сбросить статистику?')) await apiCall('reset_stats'); }
async function saveSettings() {
  await apiCall('update_settings', {
    roll_min: parseFloat(document.getElementById('set-roll-min').value),
    roll_max: parseFloat(document.getElementById('set-roll-max').value),
    open_price: parseFloat(document.getElementById('set-open-price').value),
  });
}

// Filters toggles
async function toggleRarityFilter(rid, checked) {
  await apiCall('set_filter_rarity', rid, checked);
  updateFilterSummary();
}
async function toggleItemFilter(iid, checked) {
  await apiCall('set_filter_item', iid, checked);
  updateFilterSummary();
}

window.addEventListener('pywebviewready', async () => {
  const res = await window.pywebview.api.get_state();
  state = res.state;
  renderAll();
});
</script>
</body>
</html>
"""


def main():
    import webview

    api = API()
    window = webview.create_window(
        "Симулятор кейсов",
        html=HTML,
        js_api=api,
        width=1400,
        height=900,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
