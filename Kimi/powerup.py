"""Бонусы. Добавлены щит, бомба и магнит."""
import math
import random

import pygame

import settings
from settings import *
from utils import load_sprite, draw_glow, get_font


class PowerUp:
    TYPES = {
        "weapon": {"color": COLOR_ORANGE, "label": "W", "text": "ОРУЖИЕ +1"},
        "life":   {"color": COLOR_RED, "label": "+", "text": "+1 ЖИЗНЬ"},
        "score":  {"color": COLOR_YELLOW, "label": "$", "text": "+500"},
        "drone":  {"color": (0, 255, 100), "label": "D", "text": "ДРОН +1"},
        "shield": {"color": COLOR_CYAN, "label": "O", "text": "ЩИТ"},
        "bomb":   {"color": COLOR_PINK, "label": "B", "text": "+1 БОМБА"},
        "magnet": {"color": COLOR_PURPLE, "label": "M", "text": "МАГНИТ"},
    }
    # шансы выпадения
    WEIGHTS = {"weapon": 30, "life": 6, "score": 20, "drone": 14, "shield": 12, "bomb": 10, "magnet": 8}

    @classmethod
    def random_type(cls):
        keys = list(cls.WEIGHTS.keys())
        return random.choices(keys, weights=[cls.WEIGHTS[k] for k in keys], k=1)[0]

    def __init__(self, x, y, ptype="weapon"):
        self.x = x
        self.y = y
        self.type = ptype
        self.speed = POWERUP_SPEED
        self.radius = 18
        self.active = True
        self.spawn_time = pygame.time.get_ticks()
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.rotation = 0
        self.vx = 0.0
        self.vy = 0.0
        self.sprite = load_sprite("powerup_%s" % ptype, (40, 40))
        self.data = self.TYPES.get(ptype, self.TYPES["weapon"])

    def update(self, player=None):
        if player is not None and getattr(player, "magnet", False):
            d = math.hypot(player.x - self.x, player.y - self.y)
            if d < MAGNET_RADIUS and d > 1:
                pull = 0.9 * (1.0 - d / MAGNET_RADIUS) + 0.25
                self.vx += (player.x - self.x) / d * pull
                self.vy += (player.y - self.y) / d * pull
        self.vx *= 0.93
        self.vy *= 0.93
        self.x += self.vx
        self.y += self.speed + self.vy
        self.rotation += 1
        self.bob_offset += 0.05

        if self.y > settings.SCREEN_HEIGHT + 40:
            self.active = False
        if pygame.time.get_ticks() - self.spawn_time > POWERUP_LIFETIME:
            self.active = False

    def draw(self, surface):
        left = POWERUP_LIFETIME - (pygame.time.get_ticks() - self.spawn_time)
        if left < 2200 and (pygame.time.get_ticks() // 110) % 2 == 0:
            return

        bob = math.sin(self.bob_offset) * 4
        dy = self.y + bob
        draw_glow(surface, self.x, dy, 30, self.data["color"], int(40 + 20 * math.sin(self.bob_offset * 2)))

        if self.sprite:
            surface.blit(self.sprite, self.sprite.get_rect(center=(int(self.x), int(dy))))
            return

        pygame.draw.circle(surface, self.data["color"], (int(self.x), int(dy)), self.radius)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(dy)), self.radius, 2)
        label = get_font(22).render(self.data["label"], True, COLOR_WHITE)
        surface.blit(label, label.get_rect(center=(self.x, dy)))

    def apply(self, player):
        t = self.type
        if t == "weapon":
            player.weapon.upgrade()
        elif t == "life":
            player.lives += 1
        elif t == "score":
            player.score += 500
        elif t == "drone":
            player.add_or_upgrade_drone()
        elif t == "shield":
            player.add_shield()
        elif t == "bomb":
            player.bombs = min(BOMB_MAX, player.bombs + 1)
        elif t == "magnet":
            player.magnet = True
        return self.data["text"]

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
