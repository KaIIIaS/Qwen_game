"""Дрон-помощник."""
import math
import random

import pygame

import settings
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
        tx = self.player.x + self.side * DRONE_OFFSET
        ty = self.player.y + 10
        self.x += (tx - self.x) * 0.12
        self.y += (ty - self.y) * 0.12
        self.pulse += 0.15
        self.angle += 3

    def shoot(self):
        now = pygame.time.get_ticks()
        cooldown = max(90, DRONE_COOLDOWN_BASE - (self.level - 1) * 45)
        if now - self.last_shot < cooldown:
            return []
        self.last_shot = now

        b = []
        L = self.level
        if L == 1:
            b.append(Bullet(self.x, self.y - 14, 1, BULLET_SPEED - 1, "normal", COLOR_GREEN, 4))
        elif L == 2:
            b.append(Bullet(self.x - 10, self.y - 12, 1, BULLET_SPEED, "normal", COLOR_GREEN, 4))
            b.append(Bullet(self.x + 10, self.y - 12, 1, BULLET_SPEED, "normal", COLOR_GREEN, 4))
        elif L == 3:
            for ox in (-12, 0, 12):
                b.append(Bullet(self.x + ox, self.y - 14, 1, BULLET_SPEED + 3, "laser", (100, 255, 100), 3))
        elif L == 4:
            for ox in (-14, 14):
                b.append(Bullet(self.x + ox, self.y - 12, 2, BULLET_SPEED + 2, "plasma", COLOR_CYAN, 7))
        elif L == 5:
            for ang in (-15, 0, 15):
                bb = Bullet(self.x, self.y - 10, 1, BULLET_SPEED, "spread", COLOR_GREEN, 5)
                bb.vx = math.sin(math.radians(ang)) * 2.5
                b.append(bb)
        elif L == 6:
            for ox in (-20, 0, 20):
                b.append(Bullet(self.x + ox, self.y - 10, 3, BULLET_SPEED - 4, "missile",
                                (150, 255, 100), 7, homing=0.12))
        elif L == 7:
            for ox in (-18, 18):
                bb = Bullet(self.x + ox, self.y - 12, 2, BULLET_SPEED + 1, "electric", COLOR_PURPLE, 6, pierce=1)
                bb.vx = random.uniform(-1.5, 1.5)
                b.append(bb)
        else:
            for ox in (-28, 0, 28):
                b.append(Bullet(self.x + ox, self.y - 14, 2, BULLET_SPEED + 9, "laser", (255, 100, 255), 3, pierce=1))
        return b

    def upgrade(self):
        if self.level < self.MAX_LEVEL:
            self.level += 1
        self.side *= -1

    def draw(self, surface):
        if self.sprite:
            surface.blit(self.sprite, self.sprite.get_rect(center=(int(self.x), int(self.y))))
        else:
            pygame.draw.circle(surface, (40, 180, 40), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y - 3)), 5)
            pygame.draw.circle(surface, (0, 200, 0), (int(self.x), int(self.y - 3)), 2)

        w = int(math.sin(self.pulse * 2) * 6)
        pygame.draw.line(surface, COLOR_GREEN, (self.x - self.radius, self.y),
                         (self.x - self.radius - 12, self.y + w), 3)
        pygame.draw.line(surface, COLOR_GREEN, (self.x + self.radius, self.y),
                         (self.x + self.radius + 12, self.y - w), 3)
        draw_glow(surface, self.x, self.y, 25, (0, 255, 100), int(30 + 20 * math.sin(self.pulse)))
