"""Меню: главный экран, выбор уровня кампании, настройки, справка."""
import math

import pygame

import campaign
import settings
from settings import *
from utils import Button, draw_text, draw_panel, get_font, lerp_color, clamp


class Menus:
    def __init__(self, game):
        self.game = game
        self.buttons = []
        self.state = "main"
        self.t = 0.0
        self.title_sprite = None

    # ============================================================ построение
    def build(self, state):
        self.state = state
        self.buttons = []
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        getattr(self, "_build_" + state, self._build_main)(W, H)

    def _build_main(self, W, H):
        bw, bh = int(W * 0.26), 78
        x = W // 2 - bw // 2
        y = int(H * 0.42)
        gap = 96
        cfg = self.game.config
        best = cfg.progress.get("endless_best_wave", 0)
        self.buttons = [
            Button(x, y, bw, bh, "КАМПАНИЯ", (58, 110, 210), 36, value="campaign",
                   subtitle="5 секторов · 5 боссов"),
            Button(x, y + gap, bw, bh, "БЕСКОНЕЧНЫЙ РЕЖИМ", (200, 120, 40), 32, value="endless",
                   subtitle=("рекорд: волна %d" % best) if best else "выживай сколько сможешь"),
            Button(x, y + gap * 2, bw, bh, "НАСТРОЙКИ", (80, 90, 120), 34, value="settings"),
            Button(x, y + gap * 3, bw, bh, "ВЫХОД", (170, 55, 55), 34, value="quit"),
        ]

    def _build_campaign(self, W, H):
        cfg = self.game.config
        levels = campaign.LEVELS
        n = len(levels)
        cw = int(min(330, (W * 0.86) / n - 24))
        ch = int(H * 0.44)
        gap = 26
        total = n * cw + (n - 1) * gap
        x0 = (W - total) // 2
        y = int(H * 0.30)
        for i, lv in enumerate(levels):
            unlocked = cfg.is_unlocked(lv["id"])
            b = Button(x0 + i * (cw + gap), y, cw, ch, "", lv["theme"], 30,
                       value="level:%d" % lv["id"], enabled=unlocked)
            b.level = lv
            b.stars = cfg.level_stars(lv["id"])
            b.best = cfg.progress.get("best_scores", {}).get(str(lv["id"]), 0)
            b.unlocked = unlocked
            self.buttons.append(b)
        self.buttons.append(Button(W // 2 - 140, int(H * 0.83), 280, 66, "НАЗАД", (80, 90, 120), 30, value="back"))

    def _build_settings(self, W, H):
        rows = self.option_rows()
        rw = int(W * 0.5)
        x = W // 2 - rw // 2
        y = int(H * 0.24)
        rh = 62
        for i, row in enumerate(rows):
            ry = y + i * (rh + 14)
            self.buttons.append(Button(x + rw - 200, ry, 54, rh, "<", (60, 70, 100), 30,
                                       value="opt-:%s" % row["key"]))
            self.buttons.append(Button(x + rw - 60, ry, 54, rh, ">", (60, 70, 100), 30,
                                       value="opt+:%s" % row["key"]))
        self.buttons.append(Button(W // 2 - 300, int(H * 0.82), 280, 66, "СПРАВКА", (70, 110, 90), 28, value="help"))
        self.buttons.append(Button(W // 2 + 20, int(H * 0.82), 280, 66, "НАЗАД", (80, 90, 120), 30, value="back"))

    def _build_help(self, W, H):
        self.buttons.append(Button(W // 2 - 140, int(H * 0.82), 280, 66, "НАЗАД", (80, 90, 120), 30, value="back"))

    # ============================================================ настройки
    def option_rows(self):
        cfg = self.game.config
        o = cfg.opt
        return [
            {"key": "difficulty", "label": "СЛОЖНОСТЬ",
             "value": settings.DIFFICULTIES[o["difficulty"]]["name"],
             "hint": "влияет на HP врагов, темп стрельбы и число жизней"},
            {"key": "control", "label": "УПРАВЛЕНИЕ",
             "value": "МЫШЬ" if o["control"] == "mouse" else "КЛАВИАТУРА",
             "hint": "мышь — корабль летит к курсору; клавиатура — WASD/стрелки"},
            {"key": "fullscreen", "label": "ПОЛНЫЙ ЭКРАН", "value": "ВКЛ" if o["fullscreen"] else "ВЫКЛ",
             "hint": "переключение применяется сразу"},
            {"key": "master_volume", "label": "ОБЩАЯ ГРОМКОСТЬ", "value": "%d%%" % int(o["master_volume"] * 100),
             "hint": ""},
            {"key": "sfx_volume", "label": "ГРОМКОСТЬ ЭФФЕКТОВ", "value": "%d%%" % int(o["sfx_volume"] * 100),
             "hint": ""},
            {"key": "screen_shake", "label": "ТРЯСКА ЭКРАНА", "value": "ВКЛ" if o["screen_shake"] else "ВЫКЛ",
             "hint": ""},
            {"key": "particles", "label": "ЧАСТИЦЫ", "value": o["particles"].upper(),
             "hint": "снизьте, если проседает FPS"},
            {"key": "show_fps", "label": "СЧЁТЧИК FPS", "value": "ВКЛ" if o["show_fps"] else "ВЫКЛ", "hint": ""},
        ]

    def change_option(self, key, step):
        cfg = self.game.config
        o = cfg.opt
        if key == "difficulty":
            cfg.cycle_difficulty(step)
        elif key == "control":
            o["control"] = "keyboard" if o["control"] == "mouse" else "mouse"
        elif key == "fullscreen":
            o["fullscreen"] = not o["fullscreen"]
            self.game.apply_display()
        elif key in ("master_volume", "sfx_volume", "music_volume"):
            o[key] = round(clamp(o[key] + 0.1 * step, 0.0, 1.0), 2)
        elif key == "screen_shake":
            o["screen_shake"] = not o["screen_shake"]
            self.game.shake.enabled = o["screen_shake"]
        elif key == "particles":
            order = ["low", "medium", "high"]
            o["particles"] = order[(order.index(o["particles"]) + step) % 3]
            self.game.apply_particles()
        elif key == "show_fps":
            o["show_fps"] = not o["show_fps"]
        cfg.save()
        self.build(self.state)

    # ============================================================ ввод
    def update(self, mouse_pos):
        self.t += 1.0 / FPS
        for b in self.buttons:
            b.update(mouse_pos)

    def click(self, pos):
        for b in self.buttons:
            if b.hit(pos):
                self.game.audio.play("click", 0.6)
                return b.value
        return None

    # ============================================================ отрисовка
    def draw(self, surface):
        getattr(self, "draw_" + self.state, self.draw_main)(surface)

    # ------------------------------------------------------------ главное
    def draw_main(self, surface):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        pulse = 0.5 + 0.5 * math.sin(self.t * 1.6)

        draw_text(surface, "CHICKEN", 118, W // 2, int(H * 0.15),
                  lerp_color(COLOR_YELLOW, COLOR_ORANGE, pulse), glow=True,
                  glow_color=COLOR_ORANGE, glow_radius=5)
        draw_text(surface, "I N V A D E R S", 62, W // 2, int(H * 0.24),
                  COLOR_WHITE, glow=True, glow_color=COLOR_CYAN, glow_radius=3)
        draw_text(surface, "GALACTIC CAMPAIGN", 26, W // 2, int(H * 0.30), (150, 170, 210))

        for b in self.buttons:
            b.draw(surface)

        cfg = self.game.config
        d = settings.DIFFICULTIES[cfg.opt["difficulty"]]["name"]
        draw_text(surface, "Сложность: %s   ·   Управление: %s" %
                  (d, "мышь" if cfg.opt["control"] == "mouse" else "клавиатура"),
                  22, W // 2, int(H * 0.88), (140, 150, 175))
        draw_text(surface, "ENTER — кампания   ·   E — бесконечный   ·   ESC — выход",
                  20, W // 2, int(H * 0.92), (100, 110, 135))

    # ------------------------------------------------------------ уровни
    def draw_campaign(self, surface):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        draw_text(surface, "ВЫБОР СЕКТОРА", 62, W // 2, int(H * 0.13), COLOR_WHITE,
                  glow=True, glow_color=(70, 130, 255))
        cfg = self.game.config
        total_stars = sum(cfg.level_stars(lv["id"]) for lv in campaign.LEVELS)
        draw_text(surface, "Звёзд собрано: %d / %d" % (total_stars, len(campaign.LEVELS) * 3),
                  26, W // 2, int(H * 0.19), COLOR_GOLD)

        for b in self.buttons:
            if not hasattr(b, "level"):
                b.draw(surface)
                continue
            lv = b.level
            b.draw(surface)
            r = b.rect
            cx = r.centerx
            if not b.unlocked:
                draw_text(surface, "ЗАКРЫТО", 30, cx, r.centery, (140, 140, 150))
                draw_text(surface, "пройди предыдущий сектор", 16, cx, r.centery + 34, (100, 100, 115))
                continue

            draw_text(surface, "СЕКТОР %d" % lv["id"], 24, cx, r.top + 40, lv["theme"])
            name = lv["name"].split("—")[-1].strip()
            draw_text(surface, name, 30, cx, r.top + 78, COLOR_WHITE, shadow=True)
            draw_text(surface, lv["subtitle"], 18, cx, r.top + 110, (170, 180, 200))

            # звёзды
            sy = r.top + 160
            for i in range(3):
                col = COLOR_GOLD if i < b.stars else (70, 70, 80)
                self._star(surface, cx - 46 + i * 46, sy, 18, col)

            draw_text(surface, "БОСС", 18, cx, r.bottom - 108, (150, 160, 185))
            from boss import get_boss
            draw_text(surface, get_boss(lv["boss"]).NAME, 22, cx, r.bottom - 80, lv["theme"])
            draw_text(surface, "волн: %d" % len(lv["waves"]), 18, cx, r.bottom - 50, (150, 160, 185))
            if b.best:
                draw_text(surface, "рекорд: %d" % b.best, 18, cx, r.bottom - 26, COLOR_YELLOW)

    @staticmethod
    def _star(surface, x, y, r, color):
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = math.radians(-90 + i * 36)
            pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
        pygame.draw.polygon(surface, color, pts)

    # ------------------------------------------------------------ настройки
    def draw_settings(self, surface):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        draw_text(surface, "НАСТРОЙКИ", 62, W // 2, int(H * 0.13), COLOR_WHITE,
                  glow=True, glow_color=(90, 120, 200))

        rows = self.option_rows()
        rw = int(W * 0.5)
        x = W // 2 - rw // 2
        y = int(H * 0.24)
        rh = 62
        mouse = pygame.mouse.get_pos()
        for i, row in enumerate(rows):
            ry = y + i * (rh + 14)
            rect = pygame.Rect(x, ry, rw, rh)
            hovered = rect.collidepoint(mouse)
            draw_panel(surface, rect, (18, 22, 38), 210 if hovered else 160,
                       (90, 120, 200) if hovered else (50, 60, 90), 12, 2)
            draw_text(surface, row["label"], 26, x + 24, ry + rh // 2 - 12, COLOR_WHITE, center=False)
            draw_text(surface, row["value"], 28, x + rw - 127, ry + rh // 2, COLOR_GOLD)
            if row["hint"] and hovered:
                draw_text(surface, row["hint"], 17, x + 24, ry + rh - 4, (140, 150, 175), center=False)

        for b in self.buttons:
            b.draw(surface)

    # ------------------------------------------------------------ справка
    def draw_help(self, surface):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        draw_text(surface, "УПРАВЛЕНИЕ И МЕХАНИКИ", 52, W // 2, int(H * 0.12), COLOR_WHITE)
        lines = [
            ("Мышь / WASD", "движение корабля"),
            ("Огонь", "автоматический, ускоряется с уровнем оружия"),
            ("SHIFT", "точный режим: медленно, но видно хитбокс"),
            ("ПРОБЕЛ", "бомба: сносит все снаряды и бьёт по всем врагам"),
            ("ESC", "пауза"),
            ("", ""),
            ("Комбо", "убивайте без пауз — множитель растёт до x5"),
            ("Щит", "поглощает одно попадание"),
            ("Магнит", "бонусы сами летят к вам"),
            ("Смерть", "минус один уровень оружия, так что не умирайте"),
            ("Боссы", "3-4 фазы, на каждой добавляются новые атаки"),
            ("Лучи", "сначала мигают — это предупреждение, потом жгут"),
        ]
        y = int(H * 0.22)
        for k, v in lines:
            if k:
                draw_text(surface, k, 28, W // 2 - 40, y, COLOR_CYAN, center=False)
                draw_text(surface, v, 24, W // 2 + 20, y, (200, 205, 220), center=False)
            y += 44
        for b in self.buttons:
            b.draw(surface)
