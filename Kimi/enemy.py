"""Враги: 8 типов и 7 моделей поведения вместо одного «падать вниз синусом»."""
import math
import random

import pygame

import settings
from settings import *
from bullet import EnemyBullet
from utils import load_sprite, clamp


# ---------------------------------------------------------------- типы
# sprite    — базовая текстура из assets
# tint      — умножение цвета, чтобы получить визуально разные виды из одной текстуры
# fire      — None | aimed | spread3 | burst3 | rain
ENEMY_TYPES = {
    "normal": {"hp": 1, "speed": 2.5, "radius": 26, "score": 100, "color": COLOR_WHITE,
               "sprite": "enemy_normal", "tint": None, "fire": None, "cd": 0},
    "scout":  {"hp": 1, "speed": 4.6, "radius": 21, "score": 150, "color": COLOR_CYAN,
               "sprite": "enemy_normal", "tint": (140, 235, 255), "fire": None, "cd": 0},
    "heavy":  {"hp": 4, "speed": 1.8, "radius": 34, "score": 300, "color": COLOR_ORANGE,
               "sprite": "enemy_heavy", "tint": None, "fire": None, "cd": 0},
    "shooter": {"hp": 2, "speed": 1.9, "radius": 28, "score": 260, "color": COLOR_PURPLE,
                "sprite": "enemy_normal", "tint": (215, 150, 255), "fire": "aimed", "cd": 1700},
    "gunner": {"hp": 5, "speed": 1.5, "radius": 33, "score": 450, "color": COLOR_GOLD,
               "sprite": "enemy_heavy", "tint": (255, 220, 120), "fire": "spread3", "cd": 2100},
    "kamikaze": {"hp": 2, "speed": 3.0, "radius": 25, "score": 220, "color": COLOR_RED,
                 "sprite": "enemy_normal", "tint": (255, 120, 110), "fire": None, "cd": 0},
    "shielded": {"hp": 4, "speed": 1.7, "radius": 32, "score": 500, "color": COLOR_ICE,
                 "sprite": "enemy_heavy", "tint": (150, 210, 255), "fire": "burst3", "cd": 2600,
                 "shield": 4},
    "tank":   {"hp": 14, "speed": 1.1, "radius": 46, "score": 900, "color": (255, 90, 60),
               "sprite": "enemy_heavy", "tint": (255, 130, 90), "fire": "rain", "cd": 2400},
}

BEHAVIORS = ("dive", "hold", "kamikaze", "strafe", "orbit", "swoop", "zigzag")


class Enemy:
    def __init__(self, x, y, etype="normal", behavior="dive", slot=None,
                 hp_mult=1.0, speed_mult=1.0, fire_mult=1.0, phase=0.0, params=None):
        cfg = ENEMY_TYPES.get(etype, ENEMY_TYPES["normal"])
        self.etype = etype
        self.behavior = behavior if behavior in BEHAVIORS else "dive"
        self.params = params or {}

        self.x = float(x)
        self.y = float(y)
        self.base_x = float(x)
        self.active = True

        self.hp = max(1, int(round(cfg["hp"] * hp_mult)))
        self.max_hp = self.hp
        self.shield = int(cfg.get("shield", 0) * hp_mult) if cfg.get("shield") else 0
        self.max_shield = self.shield
        self.speed = cfg["speed"] * speed_mult
        self.radius = cfg["radius"]
        self.score = cfg["score"]
        self.color = cfg["color"]

        d = self.radius * 2
        self.sprite = load_sprite(cfg["sprite"], (d, d), tint=cfg["tint"])

        self.fire_pattern = cfg["fire"]
        self.fire_cd = (cfg["cd"] / max(0.2, fire_mult)) if cfg["cd"] else 0
        self.next_fire = pygame.time.get_ticks() + random.randint(500, 2200)

        self.hit_flash = 0
        self.spawn_scale = 0.0
        self.spawn_anim_speed = 0.08
        self.angle = 0
        self.phase = phase if phase else random.uniform(0, math.pi * 2)
        self.time = random.uniform(0, math.pi * 2)
        self.amp = random.randint(40, 150)
        self.freq = random.uniform(0.015, 0.04)

        self.slot = slot
        self.state = "enter" if slot else "active"
        self.enter_t = 0.0
        self.start_pos = (self.x, self.y)

        # поведенческие переменные
        self.vx = 0.0
        self.vy = 0.0
        self.lock_timer = self.params.get("lock", 700)
        self.locked = False
        self.dir = self.params.get("dir", random.choice((-1, 1)))
        self.orbit_angle = self.params.get("angle", 0.0)
        self.orbit_r = self.params.get("orbit_r", 190)
        self.orbit_speed = self.params.get("orbit_speed", 0.018)
        self.center = list(self.params.get("center", (settings.SCREEN_WIDTH / 2, 260)))
        self.zig_timer = 0
        self.leaves_screen = True
        self.drift = self.params.get("drift", 0.12)

    # ------------------------------------------------------------ бой
    def hit(self, damage=1):
        self.hit_flash = 6
        if self.shield > 0:
            self.shield -= damage
            if self.shield <= 0:
                self.shield = 0
            return False
        self.hp -= damage
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def _fire(self, player):
        if not self.fire_pattern or player is None:
            return []
        now = pygame.time.get_ticks()
        if now < self.next_fire:
            return []
        self.next_fire = now + int(self.fire_cd * random.uniform(0.8, 1.25))

        out = []
        ang = math.atan2(player.y - self.y, player.x - self.x)
        if self.fire_pattern == "aimed":
            sp = 6.5
            out.append(EnemyBullet(self.x, self.y + 10, math.cos(ang) * sp, math.sin(ang) * sp,
                                   "orb", COLOR_PURPLE, 9))
        elif self.fire_pattern == "spread3":
            for da in (-0.26, 0.0, 0.26):
                sp = 6.0
                out.append(EnemyBullet(self.x, self.y + 10, math.cos(ang + da) * sp,
                                       math.sin(ang + da) * sp, "orb", COLOR_GOLD, 8))
        elif self.fire_pattern == "burst3":
            for i in range(3):
                sp = 5.0 + i * 1.6
                out.append(EnemyBullet(self.x, self.y + 10, math.cos(ang) * sp,
                                       math.sin(ang) * sp, "shard", COLOR_ICE, 8))
        elif self.fire_pattern == "rain":
            for k in range(5):
                a = math.pi / 2 + (k - 2) * 0.30
                sp = 5.2
                out.append(EnemyBullet(self.x, self.y + 14, math.cos(a) * sp, math.sin(a) * sp,
                                       "egg", COLOR_WHITE, 9))
        return out

    # ------------------------------------------------------------ движение
    def _move(self, player):
        b = self.behavior
        if b == "dive":
            self.time += self.freq
            self.y += self.speed
            self.x = clamp(self.base_x + math.sin(self.time) * self.amp,
                           self.radius, settings.SCREEN_WIDTH - self.radius)

        elif b == "hold":
            sx, sy = self.slot if self.slot else (self.base_x, 220)
            t = pygame.time.get_ticks() * 0.001
            sy = min(sy + self.drift, settings.SCREEN_HEIGHT * 0.52)
            self.slot = (sx, sy)
            self.x = clamp(sx + math.sin(t * 1.1 + self.phase) * 70, self.radius,
                           settings.SCREEN_WIDTH - self.radius)
            self.y = sy + math.sin(t * 1.7 + self.phase) * 16

        elif b == "kamikaze":
            if not self.locked:
                self.y += self.speed * 0.45
                self.lock_timer -= 1000.0 / FPS
                if self.lock_timer <= 0 and player is not None:
                    a = math.atan2(player.y - self.y, player.x - self.x)
                    boost = self.speed * 2.4
                    self.vx = math.cos(a) * boost
                    self.vy = math.sin(a) * boost
                    self.locked = True
            else:
                self.vy *= 1.012
                self.vx *= 1.012
                self.x += self.vx
                self.y += self.vy

        elif b == "strafe":
            sy = self.slot[1] if self.slot else self.y
            self.x += self.dir * self.speed * 1.7
            self.y = sy + math.sin(pygame.time.get_ticks() * 0.002 + self.phase) * 34
            if self.x < -120 or self.x > settings.SCREEN_WIDTH + 120:
                self.active = False

        elif b == "orbit":
            self.orbit_angle += self.orbit_speed
            self.center[1] += self.drift * 0.5
            self.x = clamp(self.center[0] + math.cos(self.orbit_angle) * self.orbit_r,
                           self.radius, settings.SCREEN_WIDTH - self.radius)
            self.y = self.center[1] + math.sin(self.orbit_angle) * self.orbit_r * 0.55

        elif b == "swoop":
            self.time += 0.02
            self.y += self.speed * (0.6 + abs(math.cos(self.time)) * 1.3)
            self.x = clamp(self.base_x + math.sin(self.time * 1.6) * (self.amp + 90),
                           self.radius, settings.SCREEN_WIDTH - self.radius)

        elif b == "zigzag":
            self.zig_timer -= 1
            if self.zig_timer <= 0:
                self.zig_timer = random.randint(24, 48)
                self.dir = -self.dir
            self.x = clamp(self.x + self.dir * self.speed * 1.9, self.radius,
                           settings.SCREEN_WIDTH - self.radius)
            self.y += self.speed * 0.75

        self.angle += 2

    def update(self, player=None):
        """Возвращает список вражеских снарядов, созданных в этом кадре."""
        if self.spawn_scale < 1.0:
            self.spawn_scale = min(1.0, self.spawn_scale + self.spawn_anim_speed)

        if self.state == "enter" and self.slot:
            self.enter_t = min(1.0, self.enter_t + 0.022)
            e = 1.0 - (1.0 - self.enter_t) ** 3
            self.x = self.start_pos[0] + (self.slot[0] - self.start_pos[0]) * e
            self.y = self.start_pos[1] + (self.slot[1] - self.start_pos[1]) * e
            if self.enter_t >= 1.0:
                self.state = "active"
        else:
            self._move(player)

        if self.hit_flash > 0:
            self.hit_flash -= 1

        if self.behavior != "hold":
            if (self.y > settings.SCREEN_HEIGHT + 110 or self.y < -700
                    or self.x < -400 or self.x > settings.SCREEN_WIDTH + 400):
                self.active = False

        return self._fire(player) if self.state == "active" else []

    # ------------------------------------------------------------ отрисовка
    def draw(self, surface):
        scale = self.spawn_scale
        sprite = self.sprite

        if sprite and scale < 1.0:
            w = max(1, int(sprite.get_width() * scale))
            h = max(1, int(sprite.get_height() * scale))
            tmp = pygame.transform.smoothscale(sprite, (w, h))
            surface.blit(tmp, tmp.get_rect(center=(int(self.x), int(self.y))))
            return

        if self.behavior == "kamikaze" and not self.locked:
            if (pygame.time.get_ticks() // 120) % 2 == 0:
                pygame.draw.circle(surface, COLOR_RED, (int(self.x), int(self.y)),
                                   int(self.radius * 1.5), 2)

        if sprite:
            if self.hit_flash > 0 and (self.hit_flash // 2) % 2 == 0:
                flash = sprite.copy()
                flash.fill((255, 255, 255), special_flags=pygame.BLEND_ADD)
                surface.blit(flash, flash.get_rect(center=(int(self.x), int(self.y))))
            else:
                surface.blit(sprite, sprite.get_rect(center=(int(self.x), int(self.y))))
        else:
            body = (255, 255, 255) if self.hit_flash > 0 and (self.hit_flash // 2) % 2 == 0 else self.color
            pygame.draw.ellipse(surface, body, (int(self.x - self.radius), int(self.y - self.radius // 2),
                                                self.radius * 2, self.radius))
            pygame.draw.circle(surface, COLOR_RED, (int(self.x), int(self.y - self.radius)), self.radius // 3)

        if self.shield > 0:
            r = int(self.radius * 1.35)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            a = int(60 + 40 * (self.shield / float(max(1, self.max_shield))))
            pygame.draw.circle(s, (120, 200, 255, a), (r, r), r, 3)
            surface.blit(s, (int(self.x) - r, int(self.y) - r))

        if self.hp < self.max_hp and self.max_hp > 1:
            bar_w = self.radius * 2.2
            fill = bar_w * (self.hp / float(self.max_hp))
            top = int(self.y - self.radius - 12)
            pygame.draw.rect(surface, COLOR_RED, (int(self.x - bar_w // 2), top, int(bar_w), 5))
            pygame.draw.rect(surface, COLOR_GREEN, (int(self.x - bar_w // 2), top, int(fill), 5))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class Egg(EnemyBullet):
    """Обычное падающее яйцо (совместимость со старым кодом)."""

    def __init__(self, x, y, speed=5.0):
        EnemyBullet.__init__(self, x, y, 0.0, speed, "egg", COLOR_WHITE, 9)
