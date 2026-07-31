import math
import pygame
from settings import *
from utils import Button, draw_text, draw_panel, load_sprite

UPGRADES = {
    'hull': ('БРОНЯ', '+ максимум жизней', 70, 5),
    'power': ('СИЛА ОРУЖИЯ', '+ урон оружия', 90, 5),
    'fire_rate': ('ТЕМП СТРЕЛЬБЫ', 'быстрее атака', 120, 5),
    'ship_speed': ('ДВИГАТЕЛИ', 'быстрее движение', 90, 5),
    'drone_power': ('СИЛА ДРОНА', '+ урон дрона', 110, 5),
    'drone_rate': ('ЯДРО ДРОНА', 'быстрее дрон', 100, 5),
}
SKINS = [
    ('player', 'СТАНДАРТ', 0, (0, 220, 255)),
    ('player_neon', 'НЕОН', 3, (255, 70, 220)),
    ('player_royal', 'КОРОЛЕВСКИЙ', 5, (255, 210, 60)),
    ('player_void', 'ПУСТОТА', 8, (170, 90, 255)),
    ('player_titan', 'ТИТАН', 12, (255, 100, 60)),
]

class Station:
    def __init__(self, game):
        self.game = game
        self.tab = 'skins'
        self.buttons = []
        self.preview_t = 0.0
        self.build()

    def build(self):
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        self.buttons = []
        if self.tab == 'skins':
            # Скины строго вертикально слева. Цена видна, даже если корабль закрыт.
            for i, (key, name, cost, color) in enumerate(SKINS):
                self.buttons.append(Button(70, 205 + i * 92, 340, 72, name, color, 22, 'skin:' + key, enabled=True))
            self.buttons.append(Button(70, H - 105, 340, 58, 'АПГРЕЙДЫ', (70, 110, 170), 24, 'upgrades'))
        else:
            for i, key in enumerate(UPGRADES):
                self.buttons.append(Button(W - 120, 205 + i * 70, 58, 54, '+', COLOR_GREEN, 30, 'buy:' + key))
            self.buttons.append(Button(70, H - 105, 340, 58, 'СКИНЫ', (90, 70, 150), 24, 'skins'))
        self.buttons.append(Button(W - 330, H - 105, 240, 58, 'НАЗАД', (80, 90, 120), 24, 'back'))

    def click(self, pos):
        for button in self.buttons:
            if button.hit(pos):
                return button.value
        return None

    def unlocked(self, key):
        return key in self.game.config.progress.get('skins', ['player'])

    def buy(self, key):
        try:
            p = self.game.config.progress
            level = int(p.get('upgrades', {}).get(key, 0))
            _, _, base, maximum = UPGRADES[key]
            cost = base * (level + 1)
            if level < maximum and int(p.get('coins', 0)) >= cost:
                p['coins'] -= cost
                p.setdefault('upgrades', {})[key] = level + 1
                self.game.config.save()
                return True
        except (KeyError, TypeError, ValueError, OSError):
            pass
        return False

    def select_skin(self, key):
        try:
            p = self.game.config.progress
            item = next(item for item in SKINS if item[0] == key)
            owned = p.setdefault('skins', ['player'])
            if key not in owned:
                if int(p.get('faberge', 0)) < item[2]:
                    return False
                p['faberge'] = int(p.get('faberge', 0)) - item[2]
                owned.append(key)
            p['skin'] = key
            self.game.config.save()
            return True
        except (StopIteration, KeyError, TypeError, ValueError, OSError):
            return False

    # Совместимость со старым game.py, чтобы фикс больше ничего не ломал.
    def skin(self, key):
        return self.select_skin(key)

    def draw(self, surface):
        self.preview_t += 0.08
        W, H = SCREEN_WIDTH, SCREEN_HEIGHT
        p = self.game.config.progress
        draw_text(surface, 'КОСМИЧЕСКАЯ СТАНЦИЯ', 54, W // 2, 70, COLOR_WHITE, glow=True, glow_color=COLOR_CYAN)
        draw_text(surface, 'МОНЕТЫ: %d     ЯЙЦА ФАБЕРЖЕ: %d' % (p.get('coins', 0), p.get('faberge', 0)), 24, W // 2, 128, COLOR_GOLD)

        # Левая колонка: только список. Никакого пересечения с preview.
        draw_panel(surface, pygame.Rect(35, 175, 410, H - 300), (8, 14, 30), 225, (45, 110, 160), 18, 2)
        draw_text(surface, 'СКИНЫ КОРАБЛЯ' if self.tab == 'skins' else 'СИСТЕМЫ КОРАБЛЯ', 22, 240, 198, COLOR_CYAN)

        # Центральный preview отделён рамкой.
        cx, cy = W // 2 - 30, int(H * 0.39)
        draw_panel(surface, pygame.Rect(cx - 230, 175, 460, 480), (8, 14, 30), 225, (45, 110, 160), 20, 2)
        draw_text(surface, 'ПРЕДПРОСМОТР В ПОЛЁТЕ', 19, cx, 207, COLOR_CYAN)
        key = p.get('skin', 'player')
        ship = load_sprite(key, (170, 215))
        if ship:
            surface.blit(ship, ship.get_rect(center=(cx, cy + math.sin(self.preview_t) * 4)))
        else:
            pygame.draw.polygon(surface, COLOR_CYAN, [(cx, cy - 80), (cx - 65, cy + 70), (cx, cy + 40), (cx + 65, cy + 70)])
        level = min(12, int(p.get('upgrades', {}).get('power', 0)) + 1)
        draw_text(surface, 'УРОВЕНЬ ОРУЖИЯ: %d' % level, 20, cx, cy + 160, COLOR_ORANGE)
        draw_text(surface, 'СТВОЛОВ: %d' % min(8, level), 19, cx, cy + 195, COLOR_ORANGE)

        if self.tab == 'skins':
            for i, (key, name, cost, color) in enumerate(SKINS):
                y = 205 + i * 92
                rect = pygame.Rect(70, y, 340, 72)
                selected = p.get('skin', 'player') == key
                owned = self.unlocked(key)
                draw_panel(surface, rect, (18, 25, 45), 235, color if selected else (70, 80, 100), 12, 3)
                draw_text(surface, name, 20, rect.centerx, y + 23, color)
                status = 'ВЫБРАН' if selected else ('КУПЛЕНО' if owned else 'ЦЕНА: %d ЯИЦ ФАБЕРЖЕ' % cost)
                draw_text(surface, status, 15, rect.centerx, y + 51, COLOR_WHITE)
        else:
            x, y = W - 650, 205
            for i, (key, (name, description, base, maximum)) in enumerate(UPGRADES.items()):
                yy = y + i * 70
                level = int(p.get('upgrades', {}).get(key, 0))
                draw_panel(surface, pygame.Rect(x, yy, 520, 60), (18, 22, 38), 225, (60, 80, 120), 10, 2)
                draw_text(surface, name, 20, x + 15, yy + 16, COLOR_WHITE, center=False)
                draw_text(surface, description, 14, x + 15, yy + 39, (150, 160, 180), center=False)
                draw_text(surface, '%d/%d' % (level, maximum), 18, x + 370, yy + 18, COLOR_CYAN)
                draw_text(surface, 'ЦЕНА: %d МОНЕТ' % (base * (level + 1)), 14, x + 15, yy + 55, COLOR_GOLD, center=False)

        for button in self.buttons:
            button.update(pygame.mouse.get_pos())
            button.draw(surface)
