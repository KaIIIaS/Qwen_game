import pygame
import math
import random
from settings import *
from bullet import Bullet
from utils import load_sprite, draw_glow


class Drone:
    MAX_LEVEL = 8

    def __init__(self, player):
        self.player = player
        self.level = 1
        self.x = player.x - DRONE_OFFSET
        self.y = player.y
        self.radius = 16
        self.last_shot = 0
        self.side = -1
        self.sprite = load_sprite("drone", (40, 40))
        self.pulse = 0
        self.angle = 0

    def update(self):
        target_x = self.player.x + self.side * DRONE_OFFSET
        target_y = self.player.y + 10
        self.x += (target_x - self.x) * 0.12
        self.y += (target_y - self.y) * 0.12
        self.pulse += 0.15
        self.angle += 3

    def shoot(self):
        now = pygame.time.get_ticks()
        cooldown = max(90, DRONE_COOLDOWN_BASE - (self.level - 1) * 45)
        if now - self.last_shot < cooldown:
            return []
        self.last_shot = now

        bullets = []
        L = self.level

        if L == 1:
            bullets.append(Bullet(self.x, self.y - 14, 1, BULLET_SPEED - 1, 'normal', COLOR_GREEN, 4))

        elif L == 2:
            bullets.append(Bullet(self.x - 10, self.y - 12, 1, BULLET_SPEED, 'normal', COLOR_GREEN, 4))
            bullets.append(Bullet(self.x + 10, self.y - 12, 1, BULLET_SPEED, 'normal', COLOR_GREEN, 4))

        elif L == 3:
            for ox in [-12, 0, 12]:
                bullets.append(Bullet(self.x + ox, self.y - 14, 1, BULLET_SPEED + 3, 'laser', (100, 255, 100), 3))

        elif L == 4:
            bullets.append(Bullet(self.x - 14, self.y - 12, 2, BULLET_SPEED + 2, 'plasma', COLOR_CYAN, 7))
            bullets.append(Bullet(self.x + 14, self.y - 12, 2, BULLET_SPEED + 2, 'plasma', COLOR_CYAN, 7))

        elif L == 5:
            for ang in [-15, 0, 15]:
                rad = math.radians(ang)
                b = Bullet(self.x, self.y - 10, 1, BULLET_SPEED, 'spread', COLOR_GREEN, 5)
                b.vx = math.sin(rad) * 2.5
                bullets.append(b)

        elif L == 6:
            for ox in [-20, 0, 20]:
                bullets.append(Bullet(self.x + ox, self.y - 10, 3, BULLET_SPEED - 4, 'missile', (150, 255, 100), 7))

        elif L == 7:
            for ox in [-18, 18]:
                b = Bullet(self.x + ox, self.y - 12, 2, BULLET_SPEED + 1, 'electric', COLOR_PURPLE, 6)
                b.vx = random.uniform(-1.5, 1.5)
                bullets.append(b)

        else:  # L == 8
            for ox in [-28, 0, 28]:
                bullets.append(Bullet(self.x + ox, self.y - 14, 2, BULLET_SPEED + 9, 'laser', (255, 100, 255), 3))

        return bullets

    def upgrade(self):
        if self.level < self.MAX_LEVEL:
            self.level += 1
            self.side *= -1

    def draw(self, surface):
        if self.sprite:
            rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.sprite, rect)
        else:
            pygame.draw.circle(surface, (40, 180, 40), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)

            glow_r = self.radius + int(math.sin(self.pulse) * 5) + 4
            glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (0, 255, 0, 50), (glow_r, glow_r), glow_r)
            surface.blit(glow, (int(self.x) - glow_r, int(self.y) - glow_r))

            w = int(math.sin(self.pulse * 2) * 6)
            pygame.draw.line(surface, COLOR_GREEN,
                             (self.x - self.radius, self.y),
                             (self.x - self.radius - 12, self.y + w), 3)
            pygame.draw.line(surface, COLOR_GREEN,
                             (self.x + self.radius, self.y),
                             (self.x + self.radius + 12, self.y - w), 3)

            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y - 3)), 5)
            pygame.draw.circle(surface, (0, 200, 0), (int(self.x), int(self.y - 3)), 2)
        
        pulse_alpha = int(30 + 20 * math.sin(self.pulse))
        draw_glow(surface, self.x, self.y, 25, (0, 255, 100), pulse_alpha)
