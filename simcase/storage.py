import json
import os
from copy import deepcopy
from typing import Any


class SplitJsonStorage:
    """Хранилище состояния симулятора в нескольких JSON-файлах."""

    def __init__(self, base_path: str = "case_simulator_data.json"):
        base_dir = os.path.dirname(base_path) or "."
        self.base_dir = base_dir
        self.rarities_path = os.path.join(base_dir, "case_rarities.json")
        self.items_path = os.path.join(base_dir, "case_items.json")
        self.inventory_path = os.path.join(base_dir, "case_inventory.json")
        self.stats_path = os.path.join(base_dir, "case_stats.json")
        self.settings_path = os.path.join(base_dir, "case_settings.json")

    def _read_json(self, path: str) -> Any:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write_json(self, path: str, payload: Any) -> None:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def load(self, defaults: dict) -> dict:
        data = deepcopy(defaults)

        split_sources = (
            ("rarities", self.rarities_path),
            ("items", self.items_path),
            ("inventory", self.inventory_path),
            ("stats", self.stats_path),
            ("settings", self.settings_path),
        )
        for key, path in split_sources:
            if not os.path.exists(path):
                continue
            try:
                loaded = self._read_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data.get(key), dict) and isinstance(loaded, dict):
                data[key] = loaded
            elif isinstance(data.get(key), list) and isinstance(loaded, list):
                data[key] = loaded

        return data

    def save(self, data: dict) -> None:
        os.makedirs(self.base_dir, exist_ok=True)

        self._write_json(self.rarities_path, data.get("rarities", []))
        self._write_json(self.items_path, data.get("items", []))
        self._write_json(self.inventory_path, data.get("inventory", {}))
        self._write_json(self.stats_path, data.get("stats", {}))
        self._write_json(self.settings_path, data.get("settings", {}))
