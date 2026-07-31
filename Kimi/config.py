"""Сохранение настроек и прогресса кампании в savegame.json."""
import json
import os
import copy
import settings

_DEFAULTS = {
    "options": {
        "difficulty": "normal",
        "fullscreen": True,
        "master_volume": 0.7,
        "sfx_volume": 0.8,
        "music_volume": 0.4,
        "screen_shake": True,
        "show_fps": False,
        "control": "mouse",        # mouse | keyboard
        "particles": "high",       # low | medium | high
    },
    "progress": {
        "unlocked": 1,
        "stars": {},               # {"1": 3, "2": 2, ...}
        "best_scores": {},         # {"1": 12345}
        "endless_best_score": 0,
        "endless_best_wave": 0,
        "total_kills": 0,
        "coins": 0, "faberge": 0, "upgrades": {}, "skins": ["player"], "skin": "player",
    },
}


class Config:
    def __init__(self):
        self.data = copy.deepcopy(_DEFAULTS)
        self.load()

    # --------------------------------------------------------- io
    def load(self):
        try:
            with open(settings.SAVE_PATH, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            for section in ("options", "progress"):
                self.data[section].update(raw.get(section, {}))
            self.data["progress"].setdefault("coins", 0)
            self.data["progress"].setdefault("faberge", 0)
            self.data["progress"].setdefault("upgrades", {})
            self.data["progress"].setdefault("skins", ["player"])
            self.data["progress"].setdefault("skin", "player")
        except Exception:
            pass

    def save(self):
        try:
            with open(settings.SAVE_PATH, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # --------------------------------------------------------- options
    @property
    def opt(self):
        return self.data["options"]

    @property
    def progress(self):
        return self.data["progress"]

    def get(self, key, default=None):
        return self.opt.get(key, default)

    def set(self, key, value):
        self.opt[key] = value
        self.save()

    @property
    def difficulty(self):
        return settings.DIFFICULTIES[self.opt.get("difficulty", "normal")]

    def cycle_difficulty(self, step=1):
        order = settings.DIFFICULTY_ORDER
        i = (order.index(self.opt["difficulty"]) + step) % len(order)
        self.set("difficulty", order[i])

    # --------------------------------------------------------- progress
    def level_stars(self, level_id):
        return int(self.progress["stars"].get(str(level_id), 0))

    def is_unlocked(self, level_id):
        return level_id <= int(self.progress.get("unlocked", 1))

    def complete_level(self, level_id, stars, score):
        key = str(level_id)
        st = self.progress["stars"]
        st[key] = max(int(st.get(key, 0)), int(stars))
        bs = self.progress["best_scores"]
        bs[key] = max(int(bs.get(key, 0)), int(score))
        self.progress["unlocked"] = max(int(self.progress.get("unlocked", 1)), level_id + 1)
        self.save()

    def record_endless(self, score, wave):
        p = self.progress
        p["endless_best_score"] = max(int(p.get("endless_best_score", 0)), int(score))
        p["endless_best_wave"] = max(int(p.get("endless_best_wave", 0)), int(wave))
        self.save()
