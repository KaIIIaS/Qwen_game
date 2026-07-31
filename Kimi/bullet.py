"""Снаряды игрока и врагов + система оружия."""
import math
import random

import pygame

import settings
from settings import *
from utils import load_sprite, Trail, draw_glow


class Bullet:
    """Снаряд игрока. Летит вверх, может самонаводиться."""

    def __init__(self, x, y, damage=1, speed=BULLET_SPEED, btype="normal",
                 color=COLOR_YELLOW, radius=5, homing=0.0, pierce=0):
        self.x = x
        self.y = y
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.btype = btype
        self.color = color
        self.active = True
        self.vx = 0.0
        self.homing = homing          # 0 = нет, 0.1..0.3 = сила доворота
        self.pierce = pierce          # сколько врагов пробивает насквозь
        self.hit_ids = set()
        self.sprite = load_sprite("bullet_%s" % btype, (radius * 3, radius * 4))
        self.electric_jitter = 0
        self.trail = Trail(max_length=8, color=color, width=radius)
        self.rotation = random.uniform(0,360)
        self.target = None

    def _seek(self, enemies):
        if not enemies:
            return
        if self.target is None or not getattr(self.target, "active", False):
            best, bd = None, 1e9
            for e in enemies:
                if not getattr(e, "active", True):
                    continue
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < bd and e.y < self.y + 80:
                    best, bd = e, d
            self.target = best
        if self.target is None:
            return
        desired = math.atan2(self.target.x - self.x, max(1.0, self.y - self.target.y))
        self.vx += (math.sin(desired) * self.speed - self.vx) * self.homing
        self.vx = max(-self.speed, min(self.speed, self.vx))

    def update(self, enemies=None):
        if self.homing > 0:
            self._seek(enemies)
        self.x += self.vx
        self.y -= self.speed
        self.electric_jitter += 1
        self.rotation += 7
        self.trail.add(self.x, self.y + self.radius)
        if self.y < -80 or self.x < -80 or self.x > settings.SCREEN_WIDTH + 80:
            self.active = False

    def draw(self, surface):
        self.trail.draw(surface)

        if self.sprite:
            if self.btype in ("missile", "fire", "plasma"):
                rot = pygame.transform.rotate(self.sprite, -self.vx * 3)
                surface.blit(rot, rot.get_rect(center=(int(self.x), int(self.y))))
            else:
                surface.blit(self.sprite, self.sprite.get_rect(center=(int(self.x), int(self.y))))
            return

        if self.btype == "laser":
            pygame.draw.rect(surface, self.color, (int(self.x) - 3, int(self.y) - 20, 6, 40))
            pygame.draw.rect(surface, COLOR_WHITE, (int(self.x) - 1, int(self.y) - 20, 2, 40))
        elif self.btype == "missile":
            pygame.draw.ellipse(surface, self.color, (int(self.x) - 8, int(self.y) - 16, 16, 32))
            pygame.draw.ellipse(surface, COLOR_WHITE, (int(self.x) - 3, int(self.y) - 10, 6, 16))
            pygame.draw.polygon(surface, COLOR_ORANGE, [(self.x - 6, self.y + 14),
                                                        (self.x + 6, self.y + 14), (self.x, self.y + 30)])
        elif self.btype == "plasma":
            draw_glow(surface, self.x, self.y, self.radius * 2, self.color, 70)
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), max(1, self.radius // 2))
        elif self.btype == "wave":
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)
        elif self.btype == "fire":
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_YELLOW, (int(self.x), int(self.y)), max(1, self.radius - 2))
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 3)
        elif self.btype == "ice":
            pygame.draw.rect(surface, self.color, (int(self.x) - 3, int(self.y) - 18, 6, 36))
            pygame.draw.rect(surface, COLOR_WHITE, (int(self.x) - 1, int(self.y) - 18, 2, 36))
        elif self.btype == "electric":
            jx = math.sin(self.electric_jitter * 0.8) * 4
            pts = [(self.x + jx, self.y - 16)]
            for i in range(5):
                pts.append((self.x + jx + random.randint(-7, 7), self.y - 10 + i * 7))
            pts.append((self.x + jx, self.y + 16))
            pygame.draw.lines(surface, self.color, False, pts, 4)
            pygame.draw.lines(surface, COLOR_WHITE, False, pts, 2)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), max(1, self.radius // 2))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class EnemyBullet:
    """Универсальный вражеский снаряд: летит в любом направлении.

    btype: egg | orb | shard | slime | laser | feather | star
    """

    def __init__(self, x, y, vx, vy, btype="egg", color=COLOR_WHITE, radius=9,
                 damage=1, accel=0.0, homing=0.0, life=9000, spin=6):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.btype = btype
        self.color = color
        self.radius = radius
        self.damage = damage
        self.accel = accel
        self.homing = homing
        self.active = True
        self.born = pygame.time.get_ticks()
        self.life = life
        self.rotation = random.uniform(0, 360)
        self.spin = spin
        self.sprite = load_sprite("egg", (22, 26)) if btype == "egg" else None
        self.trail = []

    def update(self, player=None):
        if self.homing > 0 and player is not None:
            desired = math.atan2(player.y - self.y, player.x - self.x)
            speed = math.hypot(self.vx, self.vy)
            cur = math.atan2(self.vy, self.vx)
            diff = (desired - cur + math.pi) % (math.pi * 2) - math.pi
            cur += diff * self.homing
            self.vx = math.cos(cur) * speed
            self.vy = math.sin(cur) * speed
        if self.accel:
            k = 1.0 + self.accel
            self.vx *= k
            self.vy *= k
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.spin

        self.trail.append((self.x, self.y))
        if len(self.trail) > 7:
            self.trail.pop(0)

        m = 120
        if (self.y > settings.SCREEN_HEIGHT + m or self.y < -m * 3
                or self.x < -m or self.x > settings.SCREEN_WIDTH + m
                or pygame.time.get_ticks() - self.born > self.life):
            self.active = False

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            a = (i + 1) / float(len(self.trail))
            r = max(1, int(self.radius * 0.55 * a))
            c = (int(self.color[0] * a * 0.6), int(self.color[1] * a * 0.6), int(self.color[2] * a * 0.6))
            pygame.draw.circle(surface, c, (int(tx), int(ty)), r)

        if self.btype == "egg" and self.sprite:
            rot = pygame.transform.rotate(self.sprite, self.rotation)
            surface.blit(rot, rot.get_rect(center=(int(self.x), int(self.y))))
            return

        if self.btype == "laser":
            ang = math.degrees(math.atan2(-self.vy, self.vx)) - 90
            surf = pygame.Surface((8, self.radius * 5), pygame.SRCALPHA)
            pygame.draw.rect(surf, self.color, (1, 0, 6, self.radius * 5), border_radius=3)
            pygame.draw.rect(surf, COLOR_WHITE, (3, 0, 2, self.radius * 5))
            rot = pygame.transform.rotate(surf, ang)
            surface.blit(rot, rot.get_rect(center=(int(self.x), int(self.y))))
            return

        if self.btype == "shard":
            ang = math.atan2(self.vy, self.vx)
            pts = []
            for k, (dr, da) in enumerate(((1.6, 0.0), (0.7, 2.2), (0.7, -2.2))):
                pts.append((self.x + math.cos(ang + da) * self.radius * dr,
                            self.y + math.sin(ang + da) * self.radius * dr))
            pygame.draw.polygon(surface, self.color, pts)
            pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
            return

        if self.btype == "star":
            pts = []
            for i in range(10):
                rr = self.radius if i % 2 == 0 else self.radius * 0.45
                a = math.radians(self.rotation + i * 36)
                pts.append((self.x + math.cos(a) * rr, self.y + math.sin(a) * rr))
            pygame.draw.polygon(surface, self.color, pts)
            return

        draw_glow(surface, self.x, self.y, self.radius * 2, self.color, 60)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), max(1, self.radius // 2))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)


class WeaponSystem:
    MAX_LEVEL = 12

    def __init__(self):
        self.last_shot = 0
        self.level = 1
        self.ultima_counter = 0

    def can_shoot(self):
        now = pygame.time.get_ticks()
        cooldown = max(40, BULLET_COOLDOWN - (self.level - 1) * 8)
        if now - self.last_shot >= cooldown:
            self.last_shot = now
            return True
        return False

    def shoot(self, x, y):
        bullets = []
        L = self.level

        if L == 1:
            bullets.append(Bullet(x, y, 1, BULLET_SPEED, "normal", COLOR_YELLOW, 5))
        elif L == 2:
            bullets.append(Bullet(x - 14, y, 1, BULLET_SPEED, "normal", COLOR_YELLOW, 5))
            bullets.append(Bullet(x + 14, y, 1, BULLET_SPEED, "normal", COLOR_YELLOW, 5))
        elif L == 3:
            bullets.append(Bullet(x, y, 1, BULLET_SPEED, "normal", COLOR_YELLOW, 5))
            bullets.append(Bullet(x - 22, y, 1, BULLET_SPEED - 1, "normal", COLOR_YELLOW, 5))
            bullets.append(Bullet(x + 22, y, 1, BULLET_SPEED - 1, "normal", COLOR_YELLOW, 5))
        elif L == 4:
            for ang in (0, -12, 12, -24, 24):
                rad = math.radians(ang)
                b = Bullet(x + math.sin(rad) * 10, y - 10, 1, BULLET_SPEED - 1, "spread", COLOR_ORANGE, 5)
                b.vx = math.sin(rad) * 3
                bullets.append(b)
        elif L == 5:
            bullets.append(Bullet(x - 18, y, 2, BULLET_SPEED + 6, "laser", COLOR_RED, 3, pierce=1))
            bullets.append(Bullet(x + 18, y, 2, BULLET_SPEED + 6, "laser", COLOR_RED, 3, pierce=1))
        elif L == 6:
            bullets.append(Bullet(x - 22, y, 4, BULLET_SPEED - 4, "missile", COLOR_ORANGE, 9, homing=0.10))
            bullets.append(Bullet(x + 22, y, 4, BULLET_SPEED - 4, "missile", COLOR_ORANGE, 9, homing=0.10))
        elif L == 7:
            for ox in (-28, 0, 28):
                bullets.append(Bullet(x + ox, y, 2, BULLET_SPEED + 2, "plasma", COLOR_CYAN, 12))
        elif L == 8:
            for ang in (0, -6, 6, -13, 13, -20, 20):
                rad = math.radians(ang)
                b = Bullet(x + math.sin(rad) * 8, y - 8, 2, BULLET_SPEED + 2, "wave", COLOR_PURPLE, 6)
                b.vx = math.sin(rad) * 4
                bullets.append(b)
        elif L == 9:
            for ang in range(-40, 41, 10):
                b = Bullet(x, y, 1, BULLET_SPEED - 3, "fire", (255, 80, 0), 6)
                b.vx = math.sin(math.radians(ang)) * 5
                bullets.append(b)
        elif L == 10:
            bullets.append(Bullet(x - 20, y, 3, BULLET_SPEED + 8, "ice", COLOR_ICE, 4, pierce=2))
            bullets.append(Bullet(x + 20, y, 3, BULLET_SPEED + 8, "ice", COLOR_ICE, 4, pierce=2))
        elif L == 11:
            for ox in (-30, 0, 30):
                b = Bullet(x + ox, y, 3, BULLET_SPEED + 4, "electric", COLOR_ELECTRIC, 7, pierce=1)
                b.vx = random.uniform(-1.5, 1.5)
                bullets.append(b)
        else:  # 12 — УЛЬТИМА
            bullets.append(Bullet(x, y, 3, BULLET_SPEED + 3, "plasma", COLOR_CYAN, 14, pierce=1))
            bullets.append(Bullet(x - 35, y, 2, BULLET_SPEED + 7, "laser", COLOR_RED, 3, pierce=1))
            bullets.append(Bullet(x + 35, y, 2, BULLET_SPEED + 7, "laser", COLOR_RED, 3, pierce=1))
            self.ultima_counter += 1
            if self.ultima_counter % 3 == 0:
                bullets.append(Bullet(x - 50, y, 5, BULLET_SPEED - 3, "missile", COLOR_ORANGE, 10, homing=0.18))
                bullets.append(Bullet(x + 50, y, 5, BULLET_SPEED - 3, "missile", COLOR_ORANGE, 10, homing=0.18))
        return bullets

    def upgrade(self):
        if self.level < self.MAX_LEVEL:
            self.level += 1
            return True
        return False

    def downgrade(self):
        self.level = max(1, self.level - 1)

    def reset(self):
        self.level = 1
        self.ultima_counter = 0
