from .service import CaseSimulator


class API:
    def __init__(self):
        self.store = CaseSimulator()

    def get_state(self):
        return {"ok": True, "state": self.store.state()}

    def open_case(self, times=1):
        return self.store.open_case(times)

    def add_rarity(self, rarity):
        return self.store.add_rarity(rarity)

    def update_rarity(self, rarity_id, payload):
        return self.store.update_rarity(rarity_id, payload)

    def update_rarities_bulk(self, rows):
        return self.store.update_rarities_bulk(rows)

    def normalize_rarity_ranges(self):
        return self.store.normalize_rarity_ranges()

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


    def pick_sound_file(self):
        try:
            import webview

            windows = webview.windows
            if not windows:
                return {"ok": False, "message": "Окно не найдено"}
            paths = windows[0].create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=("Audio files (*.wav;*.mp3;*.ogg;*.flac)",))
            if not paths:
                return {"ok": True, "path": ""}
            return {"ok": True, "path": paths[0]}
        except Exception as err:
            return {"ok": False, "message": str(err), "path": ""}
