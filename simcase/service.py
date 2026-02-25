import json
import os
import random
import time
import uuid
from dataclasses import asdict
from typing import Dict, Optional, Tuple

from .models import Item, LevelSettings, Rarity

DATA_FILE = "case_simulator_data.json"


class CaseSimulator:
    """Domain service for case opening simulator."""

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
                    "rarity_hidden": {},
                    "item_hidden": {},
                },
                "levels": LevelSettings().to_dict(),
            },
        }
        self._load_or_create_defaults()

    def _load_or_create_defaults(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for k, v in loaded.items():
                    self.data[k] = v
            except (json.JSONDecodeError, OSError):
                pass

        self.data.setdefault("settings", {})
        self.data["settings"].setdefault("filters", {"rarity_hidden": {}, "item_hidden": {}})
        filters = self.data["settings"]["filters"]
        filters.setdefault("rarity_hidden", {})
        filters.setdefault("item_hidden", {})
        # Backward compatibility with old filter model.
        filters.pop("rarity_visible", None)
        filters.pop("item_visible", None)
        self.data["settings"].setdefault("levels", LevelSettings().to_dict())

        if not self.data.get("rarities"):
            self.data["rarities"] = [
                asdict(Rarity.create(name="Обычная", min_roll=0, max_roll=60, color="#b0b0b0")),
                asdict(Rarity.create(name="Редкая", min_roll=60, max_roll=85, color="#4f8cff")),
                asdict(Rarity.create(name="Эпическая", min_roll=85, max_roll=97, color="#bb6eff")),
                asdict(Rarity.create(name="Легендарная", min_roll=97, max_roll=100, color="#ff9f1a")),
            ]

        if not self.data.get("items"):
            r = self.data["rarities"]
            self.data["items"] = [
                asdict(Item.create(name="Старый нож", rarity_id=r[0]["id"], weight=10, description="Простой предмет")),
                asdict(Item.create(name="Сияющий пистолет", rarity_id=r[1]["id"], weight=6, description="Редкая находка")),
                asdict(Item.create(name="Кристальный меч", rarity_id=r[2]["id"], weight=3, description="Очень ценный")),
                asdict(Item.create(name="Драконья корона", rarity_id=r[3]["id"], weight=1, description="Почти не выпадает")),
            ]

        for rarity in self.data["rarities"]:
            rarity.setdefault("drop_sound", "")
            rarity.setdefault("drop_effect", "")

        self.save()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _append_history(self, action: str, payload: dict):
        self.data["history"].insert(0, {
            "id": str(uuid.uuid4()),
            "timestamp": int(time.time()),
            "action": action,
            "payload": payload,
        })
        self.data["history"] = self.data["history"][:500]

    def _rarity_map(self) -> Dict[str, dict]:
        return {r["id"]: r for r in self.data["rarities"]}

    def _item_map(self) -> Dict[str, dict]:
        return {i["id"]: i for i in self.data["items"]}

    def _roll_rarity(self, roll: float) -> Optional[dict]:
        for rarity in self.data["rarities"]:
            if rarity["min_roll"] <= roll <= rarity["max_roll"]:
                return rarity
        return None

    def _pick_item_by_rarity(self, rarity_id: str) -> Optional[dict]:
        candidates = [i for i in self.data["items"] if i["rarity_id"] == rarity_id and i["weight"] > 0]
        if not candidates:
            return None
        total_weight = sum(i["weight"] for i in candidates)
        point = random.uniform(0, total_weight)
        current = 0.0
        for item in candidates:
            current += item["weight"]
            if point <= current:
                return item
        return candidates[-1]

    def _validate_rarity_ranges(self) -> Tuple[bool, str]:
        settings = self.data["settings"]
        roll_min = settings["roll_min"]
        roll_max = settings["roll_max"]
        if roll_min >= roll_max:
            return False, "roll_min должен быть меньше roll_max"

        for rarity in self.data["rarities"]:
            if rarity["min_roll"] > rarity["max_roll"]:
                return False, f"У редкости {rarity['name']} min_roll > max_roll"

        ranges = sorted((r["min_roll"], r["max_roll"], r["name"]) for r in self.data["rarities"])
        for idx in range(1, len(ranges)):
            if ranges[idx][0] < ranges[idx - 1][1]:
                return False, f"Диапазоны {ranges[idx - 1][2]} и {ranges[idx][2]} пересекаются"
        return True, "ok"

    def normalize_rarity_ranges(self) -> dict:
        """Auto-distribute rarity ranges across roll interval preserving order."""
        settings = self.data["settings"]
        rarities = sorted(self.data["rarities"], key=lambda r: r["min_roll"])
        if not rarities:
            return {"ok": False, "message": "Нет редкостей для нормализации"}

        roll_min = settings["roll_min"]
        roll_max = settings["roll_max"]
        span = roll_max - roll_min
        step = span / len(rarities)

        cursor = roll_min
        for idx, rarity in enumerate(rarities):
            rarity["min_roll"] = round(cursor, 3)
            cursor = roll_max if idx == len(rarities) - 1 else cursor + step
            rarity["max_roll"] = round(cursor, 3)

        self._append_history("normalize_rarities", {"count": len(rarities)})
        self.save()
        return {"ok": True, "state": self.state()}

    def level_progress(self) -> dict:
        opened = int(self.data["stats"]["total_opened"])
        levels = self.data["settings"].get("levels", LevelSettings().to_dict())
        base = max(1, int(levels.get("base_xp", 8)))
        growth = max(1.01, float(levels.get("xp_growth", 1.35)))

        level = 1
        spent = 0
        need = base
        while opened >= spent + need:
            spent += need
            level += 1
            need = int(round(base * (growth ** (level - 1))))
            need = max(1, need)

        return {
            "level": level,
            "xp_total": opened,
            "xp_current": opened - spent,
            "xp_needed": need,
            "progress": round((opened - spent) / need, 4) if need else 1,
        }

    def open_case(self, times: int = 1) -> dict:
        times = max(1, int(times))
        valid, msg = self._validate_rarity_ranges()
        if not valid:
            return {"ok": False, "message": msg}

        result = []
        visible_result = []
        settings = self.data["settings"]
        for _ in range(times):
            roll = random.uniform(settings["roll_min"], settings["roll_max"])
            rarity = self._roll_rarity(roll)
            if rarity is None:
                continue
            item = self._pick_item_by_rarity(rarity["id"])
            if item is None:
                continue

            self.data["inventory"][item["id"]] = self.data["inventory"].get(item["id"], 0) + 1
            self.data["stats"]["total_opened"] += 1
            self.data["stats"]["total_spent"] += settings["open_price"]
            self.data["stats"]["by_rarity"][rarity["id"]] = self.data["stats"]["by_rarity"].get(rarity["id"], 0) + 1
            self.data["stats"]["by_item"][item["id"]] = self.data["stats"]["by_item"].get(item["id"], 0) + 1
            drop = {
                "roll": round(roll, 3),
                "rarity": rarity,
                "item": item,
                "hidden_by_filter": self._is_hidden_drop(rarity["id"], item["id"]),
            }
            result.append(drop)
            if not drop["hidden_by_filter"]:
                visible_result.append(drop)

        self._append_history("open_case", {"times": times, "results": result[:100], "count_results": len(result)})
        self.save()
        return {
            "ok": True,
            "results": result,
            "visible_results": visible_result,
            "hidden_results_count": len(result) - len(visible_result),
            "state": self.state(),
        }

    def _is_hidden_drop(self, rarity_id: str, item_id: str) -> bool:
        filters = self.data["settings"].setdefault("filters", {})
        rarity_hidden = filters.setdefault("rarity_hidden", {})
        item_hidden = filters.setdefault("item_hidden", {})
        return bool(rarity_hidden.get(rarity_id) or item_hidden.get(item_id))

    def add_rarity(self, payload: dict) -> dict:
        rarity = asdict(Rarity.create(
            name=payload["name"],
            min_roll=float(payload["min_roll"]),
            max_roll=float(payload["max_roll"]),
            color=payload.get("color", "#888888"),
            drop_sound=payload.get("drop_sound", ""),
            drop_effect=payload.get("drop_effect", ""),
        ))
        self.data["rarities"].append(rarity)
        valid, msg = self._validate_rarity_ranges()
        if not valid:
            self.data["rarities"].pop()
            return {"ok": False, "message": msg}
        self._append_history("add_rarity", rarity)
        self.save()
        return {"ok": True, "state": self.state()}

    def update_rarity(self, rarity_id: str, payload: dict) -> dict:
        for rarity in self.data["rarities"]:
            if rarity["id"] == rarity_id:
                rarity["name"] = payload.get("name", rarity["name"])
                rarity["min_roll"] = float(payload.get("min_roll", rarity["min_roll"]))
                rarity["max_roll"] = float(payload.get("max_roll", rarity["max_roll"]))
                rarity["color"] = payload.get("color", rarity["color"])
                rarity["drop_sound"] = payload.get("drop_sound", rarity.get("drop_sound", ""))
                rarity["drop_effect"] = payload.get("drop_effect", rarity.get("drop_effect", ""))
                valid, msg = self._validate_rarity_ranges()
                if not valid:
                    return {"ok": False, "message": msg}
                self._append_history("update_rarity", rarity)
                self.save()
                return {"ok": True, "state": self.state()}
        return {"ok": False, "message": "Редкость не найдена"}

    def update_rarities_bulk(self, rows: list[dict]) -> dict:
        rarity_map = self._rarity_map()
        snapshot = json.loads(json.dumps(self.data["rarities"]))
        try:
            for row in rows:
                rarity = rarity_map.get(row["id"])
                if not rarity:
                    continue
                rarity["name"] = row.get("name", rarity["name"])
                rarity["min_roll"] = float(row.get("min_roll", rarity["min_roll"]))
                rarity["max_roll"] = float(row.get("max_roll", rarity["max_roll"]))
                rarity["color"] = row.get("color", rarity["color"])
                rarity["drop_effect"] = row.get("drop_effect", rarity.get("drop_effect", ""))
                rarity["drop_sound"] = row.get("drop_sound", rarity.get("drop_sound", ""))
            valid, msg = self._validate_rarity_ranges()
            if not valid:
                self.data["rarities"] = snapshot
                return {"ok": False, "message": msg}
        except (KeyError, TypeError, ValueError):
            self.data["rarities"] = snapshot
            return {"ok": False, "message": "Ошибка в данных массового обновления редкостей"}

        self._append_history("update_rarities_bulk", {"count": len(rows)})
        self.save()
        return {"ok": True, "state": self.state()}

    def delete_rarity(self, rarity_id: str) -> dict:
        if any(i["rarity_id"] == rarity_id for i in self.data["items"]):
            return {"ok": False, "message": "Нельзя удалить редкость, пока есть связанные предметы"}
        before = len(self.data["rarities"])
        self.data["rarities"] = [r for r in self.data["rarities"] if r["id"] != rarity_id]
        if len(self.data["rarities"]) == before:
            return {"ok": False, "message": "Редкость не найдена"}
        self.data["settings"].get("filters", {}).get("rarity_hidden", {}).pop(rarity_id, None)
        self._append_history("delete_rarity", {"rarity_id": rarity_id})
        self.save()
        return {"ok": True, "state": self.state()}

    def add_item(self, payload: dict) -> dict:
        if payload["rarity_id"] not in self._rarity_map():
            return {"ok": False, "message": "Указанная редкость не существует"}
        item = asdict(Item.create(
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
        self.data["settings"].get("filters", {}).get("item_hidden", {}).pop(item_id, None)
        self._append_history("delete_item", {"item_id": item_id})
        self.save()
        return {"ok": True, "state": self.state()}

    def adjust_inventory(self, item_id: str, delta: int) -> dict:
        if item_id not in self._item_map():
            return {"ok": False, "message": "Предмет не найден"}
        cur = self.data["inventory"].get(item_id, 0)
        new_val = cur + int(delta)
        if new_val < 0:
            return {"ok": False, "message": "Недостаточно предметов в инвентаре"}
        if new_val == 0:
            self.data["inventory"].pop(item_id, None)
        else:
            self.data["inventory"][item_id] = new_val
        self._append_history("consume_item" if delta < 0 else "add_inventory", {"item_id": item_id, "delta": delta})
        self.save()
        return {"ok": True, "state": self.state()}

    def clear_inventory(self) -> dict:
        self.data["inventory"] = {}
        self._append_history("clear_inventory", {})
        self.save()
        return {"ok": True, "state": self.state()}

    def set_filter_rarity(self, rarity_id: str, value: bool) -> dict:
        rv = self.data["settings"].setdefault("filters", {}).setdefault("rarity_hidden", {})
        if value:
            rv[rarity_id] = True
        else:
            rv.pop(rarity_id, None)
        self._append_history("set_filter_rarity", {"rarity_id": rarity_id, "value": value})
        self.save()
        return {"ok": True, "state": self.state()}

    def set_filter_item(self, item_id: str, value: bool) -> dict:
        iv = self.data["settings"].setdefault("filters", {}).setdefault("item_hidden", {})
        if value:
            iv[item_id] = True
        else:
            iv.pop(item_id, None)
        self._append_history("set_filter_item", {"item_id": item_id, "value": value})
        self.save()
        return {"ok": True, "state": self.state()}

    def update_settings(self, payload: dict) -> dict:
        settings = self.data["settings"]
        for key in ("roll_min", "roll_max", "open_price"):
            if key in payload:
                settings[key] = float(payload[key])

        levels = payload.get("levels", {})
        if levels:
            settings.setdefault("levels", LevelSettings().to_dict())
            if "base_xp" in levels:
                settings["levels"]["base_xp"] = max(1, int(levels["base_xp"]))
            if "xp_growth" in levels:
                settings["levels"]["xp_growth"] = max(1.01, float(levels["xp_growth"]))

        valid, msg = self._validate_rarity_ranges()
        if not valid:
            return {"ok": False, "message": msg}
        self._append_history("update_settings", settings)
        self.save()
        return {"ok": True, "state": self.state()}

    def clear_history(self) -> dict:
        self.data["history"] = []
        self.save()
        return {"ok": True, "state": self.state()}

    def reset_stats(self) -> dict:
        self.data["stats"] = {"total_opened": 0, "total_spent": 0, "by_rarity": {}, "by_item": {}}
        self._append_history("reset_stats", {})
        self.save()
        return {"ok": True, "state": self.state()}

    def state(self) -> dict:
        snapshot = json.loads(json.dumps(self.data))
        snapshot["level"] = self.level_progress()
        return snapshot

    def play_rarity_sound(self, rarity_id: str) -> dict:
        rarity = self._rarity_map().get(rarity_id)
        if not rarity:
            return {"ok": False, "message": "Редкость не найдена", "played": False}
        path = rarity.get("drop_sound", "")
        if not path:
            return {"ok": True, "message": "No sound configured", "played": False}
        try:
            import winsound

            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return {"ok": True, "played": True}
        except Exception as err:
            return {"ok": False, "played": False, "message": str(err), "sound": path}
