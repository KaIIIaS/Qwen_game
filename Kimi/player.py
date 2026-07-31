"""Игрок: движение, щит, бомбы, режим точного наведения."""
import math

import pygame

import settings
from settings import *
from utils import load_sprite, Trail, draw_glow, clamp
from bullet import WeaponSystem


class Player:
    def __init__(self, lives=None):
        self.x = settings.SCREEN_WIDTH // 2
        self.y = settings.SCREEN_HEIGHT - 180
        self.speed = PLAYER_SPEED
        self.radius = PLAYER_SIZE // 2
        self.lives = min(5, PLAYER_LIVES if lives is None else lives)
        self.score = 0
        self.weapon = WeaponSystem()
        self.invulnerable_until = 0
        self.sprite = load_sprite("player", (PLAYER_SIZE + 20, PLAYER_SIZE + 30))
        self.flame_timer = 0
        self.target_x = self.x
        self.target_y = self.y
        self.drone = None
        self.anim_t = 0.0
        self.engine_trail = Trail(max_length=20, color=(0, 200, 255), width=6)
        self.hit_flash = 0

        # новое
        self.bombs = BOMB_START
        self.shield_until = 0
        self.slow_factor = 1.0        # <1 когда игрок в ледяной зоне
        self.focus = False
        self.magnet = False
        self.deaths = 0
        self.control = "mouse"

    # -------------------------------------------------------- состояния
    @property
    def invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    @property
    def shielded(self):
        return pygame.time.get_ticks() < self.shield_until

    def add_shield(self, ms=SHIELD_TIME):
        self.shield_until = max(self.shield_until, pygame.time.get_ticks()) + ms

    # -------------------------------------------------------- апдейт
    def update(self, keys=None):
        self.anim_t += 0.18
        speed_k = self.slow_factor * (PLAYER_FOCUS_FACTOR if self.focus else 1.0)

        if self.control == "keyboard" and keys is not None:
            dx = dy = 0.0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += 1
            if dx or dy:
                n = math.hypot(dx, dy)
                dx, dy = dx / n, dy / n
            old_x, old_y = self.x, self.y
            self.x += dx * PLAYER_KEY_SPEED * speed_k
            self.y += dy * PLAYER_KEY_SPEED * speed_k
        else:
            mx, my = pygame.mouse.get_pos()
            self.target_x = clamp(mx, self.radius, settings.SCREEN_WIDTH - self.radius)
            self.target_y = clamp(my, self.radius, settings.SCREEN_HEIGHT - self.radius)
            old_x, old_y = self.x, self.y
            self.x += (self.target_x - self.x) * self.speed * speed_k
            self.y += (self.target_y - self.y) * self.speed * speed_k

        self.x = clamp(self.x, self.radius, settings.SCREEN_WIDTH - self.radius)
        self.y = clamp(self.y, self.radius, settings.SCREEN_HEIGHT - self.radius)

        self.flame_timer += 0.3
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if math.hypot(self.x - old_x, self.y - old_y) > 0.5:
            self.engine_trail.add(self.x, self.y + self.radius)

        self.slow_factor = 1.0   # сбрасывается каждый кадр, хазарды выставят заново

    # -------------------------------------------------------- отрисовка
    def draw(self, surface):
        if self.invulnerable and (pygame.time.get_ticks() // 100) % 2 == 0:
            return

        self.engine_trail.draw(surface)

        if self.sprite:
            surface.blit(self.sprite, self.sprite.get_rect(center=(int(self.x), int(self.y))))
        else:
            pts = [(self.x, self.y - self.radius),
                   (self.x - self.radius, self.y + self.radius),
                   (self.x, self.y + self.radius // 2),
                   (self.x + self.radius, self.y + self.radius)]
            pygame.draw.polygon(surface, COLOR_CYAN, pts)
            pygame.draw.polygon(surface, COLOR_WHITE, pts, 2)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 8)

        if not self.sprite:
            flame_h = 14 + int(math.sin(self.flame_timer) * 7)
            pygame.draw.polygon(surface, COLOR_ORANGE, [
            (self.x - 10, self.y + self.radius),
            (self.x + 10, self.y + self.radius),
            (self.x, self.y + self.radius + flame_h)])

        if self.shielded:
            left = self.shield_until - pygame.time.get_ticks()
            blink = left > 1500 or (pygame.time.get_ticks() // 120) % 2 == 0
            if blink:
                r = int(self.radius * 2.1 + math.sin(self.flame_timer * 1.5) * 3)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (0, 220, 255, 45), (r, r), r)
                pygame.draw.circle(s, (140, 240, 255, 190), (r, r), r, 3)
                surface.blit(s, (int(self.x) - r, int(self.y) - r))

        if self.focus:
            pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), 4)
            pygame.draw.circle(surface, COLOR_PINK, (int(self.x), int(self.y)), self.radius + 6, 1)

    # -------------------------------------------------------- бой
    def shoot(self):
        if self.weapon.can_shoot():
            return self.weapon.shoot(self.x, self.y - self.radius)
        return []

    def hit(self):
        """True — жизни кончились."""
        now = pygame.time.get_ticks()
        if now < self.invulnerable_until:
            return False
        if self.shielded:
            self.shield_until = 0
            self.invulnerable_until = now + 900
            return False

        self.lives -= 1
        self.deaths += 1
        self.invulnerable_until = now + PLAYER_INVULNERABLE_TIME
        self.hit_flash = 10
        self.weapon.downgrade()
        return self.lives <= 0

    def add_or_upgrade_drone(self):
        if self.drone is None:
            from drone import Drone
            self.drone = Drone(self)
        else:
            self.drone.upgrade()

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
