import pygame
import math
import random
from settings import *
from utils import load_sprite, Trail


class Bullet:
    def __init__(self, x, y, damage=1, speed=BULLET_SPEED, btype='normal', color=COLOR_YELLOW, radius=5):
        self.x = x
        self.y = y
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.btype = btype
        self.color = color
        self.active = True
        self.vx = 0
        self.sprite = load_sprite(f"bullet_{btype}", (radius * 3, radius * 4))
        self.electric_jitter = 0
        self.trail = Trail(max_length=8, color=color, width=radius)
        self.rotation = 0

    def update(self):
        self.x += self.vx
        self.y -= self.speed
        self.electric_jitter += 1
        self.rotation += 5
        self.trail.add(self.x, self.y + self.radius)
        if self.y < -60 or self.x < -60 or self.x > SCREEN_WIDTH + 60:
            self.active = False

    def draw(self, surface):
        self.trail.draw(surface)
        
        if self.sprite:
            if self.btype in ['missile', 'fire', 'plasma']:
                rot = pygame.transform.rotate(self.sprite, self.vx * 3)
                rect = rot.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(rot, rect)
            else:
                rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(self.sprite, rect)
            return

        if self.btype == 'laser':
            pygame.draw.rect(surface, self.color, (int(self.x) - 3, int(self.y) - 20, 6, 40))
            pygame.draw.rect(surface, COLOR_WHITE, (int(self.x) - 1, int(self.y) - 20, 2, 40))

        elif self.btype == 'missile':
            pygame.draw.ellipse(surface, self.color, (int(self.x) - 8, int(self.y) - 16, 16, 32))
            pygame.draw.ellipse(surface, COLOR_WHITE, (int(self.x) - 3, int(self.y) - 10, 6, 16))
            pygame.draw.polygon(surface, COLOR_ORANGE, [
                (self.x - 6, self.y + 14), (self.x + 6, self.y + 14), (self.x, self.y + 30)
            ])

        elif self.btype == 'plasma':
            glow = pygame.Surface((self.radius * 5, self.radius * 5), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color[:3], 70), (self.radius * 2, self.radius * 2), self.radius * 2)
            surface.blit(glow, (int(self.x) - self.radius * 2, int(self.y) - self.radius * 2))
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), self.radius // 2)

        elif self.btype == 'wave':
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)

        elif self.btype == 'fire':
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_YELLOW, (int(self.x), int(self.y)), self.radius - 2)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 3)

        elif self.btype == 'ice':
            pygame.draw.rect(surface, self.color, (int(self.x) - 3, int(self.y) - 18, 6, 36))
            pygame.draw.rect(surface, COLOR_WHITE, (int(self.x) - 1, int(self.y) - 18, 2, 36))
            pygame.draw.polygon(surface, (200, 230, 255), [
                (self.x - 7, self.y - 10), (self.x - 12, self.y - 5), (self.x - 7, self.y)
            ])
            pygame.draw.polygon(surface, (200, 230, 255), [
                (self.x + 7, self.y - 10), (self.x + 12, self.y - 5), (self.x + 7, self.y)
            ])

        elif self.btype == 'electric':
            jx = math.sin(self.electric_jitter * 0.8) * 4
            points = [(self.x + jx, self.y - 16)]
            for i in range(5):
                points.append((self.x + jx + random.randint(-7, 7), self.y - 10 + i * 7))
            points.append((self.x + jx, self.y + 16))
            pygame.draw.lines(surface, self.color, False, points, 4)
            pygame.draw.lines(surface, COLOR_WHITE, False, points, 2)

        else:  # normal / spread
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), max(1, self.radius // 2))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


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
            bullets.append(Bullet(x, y, 1, BULLET_SPEED, 'normal', COLOR_YELLOW, 5))

        elif L == 2:
            bullets.append(Bullet(x - 14, y, 1, BULLET_SPEED, 'normal', COLOR_YELLOW, 5))
            bullets.append(Bullet(x + 14, y, 1, BULLET_SPEED, 'normal', COLOR_YELLOW, 5))

        elif L == 3:
            bullets.append(Bullet(x, y, 1, BULLET_SPEED, 'normal', COLOR_YELLOW, 5))
            bullets.append(Bullet(x - 22, y, 1, BULLET_SPEED - 1, 'normal', COLOR_YELLOW, 5))
            bullets.append(Bullet(x + 22, y, 1, BULLET_SPEED - 1, 'normal', COLOR_YELLOW, 5))

        elif L == 4:
            for ang in [0, -12, 12, -24, 24]:
                rad = math.radians(ang)
                b = Bullet(x + math.sin(rad) * 10, y - 10, 1, BULLET_SPEED - 1, 'spread', COLOR_ORANGE, 5)
                b.vx = math.sin(rad) * 3
                bullets.append(b)

        elif L == 5:
            bullets.append(Bullet(x - 18, y, 2, BULLET_SPEED + 6, 'laser', COLOR_RED, 3))
            bullets.append(Bullet(x + 18, y, 2, BULLET_SPEED + 6, 'laser', COLOR_RED, 3))

        elif L == 6:
            bullets.append(Bullet(x - 22, y, 4, BULLET_SPEED - 4, 'missile', COLOR_ORANGE, 9))
            bullets.append(Bullet(x + 22, y, 4, BULLET_SPEED - 4, 'missile', COLOR_ORANGE, 9))

        elif L == 7:
            bullets.append(Bullet(x - 28, y, 2, BULLET_SPEED + 2, 'plasma', COLOR_CYAN, 12))
            bullets.append(Bullet(x, y, 2, BULLET_SPEED + 2, 'plasma', COLOR_CYAN, 12))
            bullets.append(Bullet(x + 28, y, 2, BULLET_SPEED + 2, 'plasma', COLOR_CYAN, 12))

        elif L == 8:
            for ang in [0, -6, 6, -13, 13, -20, 20]:
                rad = math.radians(ang)
                b = Bullet(x + math.sin(rad) * 8, y - 8, 2, BULLET_SPEED + 2, 'wave', COLOR_PURPLE, 6)
                b.vx = math.sin(rad) * 4
                bullets.append(b)

        elif L == 9:
            for ang in range(-40, 41, 10):
                rad = math.radians(ang)
                b = Bullet(x, y, 1, BULLET_SPEED - 3, 'fire', (255, 80, 0), 6)
                b.vx = math.sin(rad) * 5
                bullets.append(b)

        elif L == 10:
            bullets.append(Bullet(x - 20, y, 3, BULLET_SPEED + 8, 'ice', COLOR_ICE, 4))
            bullets.append(Bullet(x + 20, y, 3, BULLET_SPEED + 8, 'ice', COLOR_ICE, 4))

        elif L == 11:
            for ox in [-30, 0, 30]:
                b = Bullet(x + ox, y, 3, BULLET_SPEED + 4, 'electric', COLOR_ELECTRIC, 7)
                b.vx = random.uniform(-1.5, 1.5)
                bullets.append(b)

        else:  # L == 12 УЛЬТИМА
            bullets.append(Bullet(x, y, 3, BULLET_SPEED + 3, 'plasma', COLOR_CYAN, 14))
            bullets.append(Bullet(x - 35, y, 2, BULLET_SPEED + 7, 'laser', COLOR_RED, 3))
            bullets.append(Bullet(x + 35, y, 2, BULLET_SPEED + 7, 'laser', COLOR_RED, 3))
            self.ultima_counter += 1
            if self.ultima_counter % 3 == 0:
                bullets.append(Bullet(x - 50, y, 5, BULLET_SPEED - 3, 'missile', COLOR_ORANGE, 10))
                bullets.append(Bullet(x + 50, y, 5, BULLET_SPEED - 3, 'missile', COLOR_ORANGE, 10))

        return bullets

    def upgrade(self):
        if self.level < self.MAX_LEVEL:
            self.level += 1

    def reset(self):
        self.level = 1
        self.ultima_counter = 0
