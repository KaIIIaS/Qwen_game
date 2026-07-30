import pygame
import random
import math
import settings
from utils import load_sprite


class Enemy:
    def __init__(self, x, y, etype='normal'):
        self.x = x
        self.y = y
        self.etype = etype
        self.active = True
        self.angle = 0
        self.spawn_scale = 0.0
        self.spawn_anim_speed = 0.08

        if etype == 'normal':
            self.hp = 1
            self.speed = 2.5
            self.radius = 26
            self.score = 100
            self.color = settings.COLOR_WHITE
        elif etype == 'heavy':
            self.hp = 3
            self.speed = 1.8
            self.radius = 34
            self.score = 300
            self.color = settings.COLOR_ORANGE
        elif etype == 'boss':
            self.hp = 25
            self.speed = 1.2
            self.radius = 65
            self.score = 5000
            self.color = settings.COLOR_RED

        self.max_hp = self.hp
        self.sprite = load_sprite(f"enemy_{etype}", (self.radius * 2, self.radius * 2))
        self.hit_flash = 0

        self.base_x = x
        self.time = random.uniform(0, math.pi * 2)
        self.amp = random.randint(40, 140)
        self.freq = random.uniform(0.015, 0.04)

    def update(self):
        if self.spawn_scale < 1.0:
            self.spawn_scale = min(1.0, self.spawn_scale + self.spawn_anim_speed)

        self.time += self.freq
        self.y += self.speed

        desired_x = self.base_x + math.sin(self.time) * self.amp
        self.x = max(self.radius, min(settings.SCREEN_WIDTH - self.radius, desired_x))
        self.angle += 2

        if self.y > settings.SCREEN_HEIGHT + 80:
            self.active = False

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, surface):
        scale = self.spawn_scale
        if scale < 1.0:
            temp_sprite = None
            if self.sprite:
                new_size = (int(self.sprite.get_width() * scale), int(self.sprite.get_height() * scale))
                temp_sprite = pygame.transform.scale(self.sprite, new_size)
                rect = temp_sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(temp_sprite, rect)
            else:
                pygame.draw.ellipse(surface, self.color,
                                    (int(self.x - self.radius * scale), int(self.y - self.radius // 2 * scale),
                                     self.radius * 2 * scale, self.radius * scale))
            return

        if self.sprite:
            if self.hit_flash > 0 and (self.hit_flash // 2) % 2 == 0:
                flash = self.sprite.copy()
                flash.fill((255, 255, 255), special_flags=pygame.BLEND_ADD)
                rect = flash.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(flash, rect)
            else:
                rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(self.sprite, rect)
        else:
            body_color = (255, 255, 255) if self.hit_flash > 0 and (self.hit_flash // 2) % 2 == 0 else self.color
            pygame.draw.ellipse(surface, body_color,
                                (int(self.x - self.radius), int(self.y - self.radius // 2),
                                 self.radius * 2, self.radius))
            pygame.draw.circle(surface, settings.COLOR_RED,
                               (int(self.x), int(self.y - self.radius)), self.radius // 3)
            pygame.draw.circle(surface, settings.COLOR_YELLOW,
                               (int(self.x + self.radius // 2), int(self.y - self.radius // 4)), 7)
            pygame.draw.circle(surface, settings.COLOR_BG,
                               (int(self.x + self.radius // 2 + 2), int(self.y - self.radius // 4)), 3)

        if self.hp < self.max_hp and self.max_hp > 1:
            bar_w = self.radius * 2.2
            bar_h = 5
            fill = bar_w * (self.hp / self.max_hp)
            pygame.draw.rect(surface, settings.COLOR_RED,
                             (int(self.x - bar_w // 2), int(self.y - self.radius - 12), int(bar_w), bar_h))
            pygame.draw.rect(surface, settings.COLOR_GREEN,
                             (int(self.x - bar_w // 2), int(self.y - self.radius - 12), int(fill), bar_h))

    def hit(self, damage=1):
        self.hp -= damage
        self.hit_flash = 6
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


class Egg:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.radius = 9
        self.active = True
        self.sprite = load_sprite("egg", (22, 26))
        self.rotation = 0
        self.trail = []

    def update(self):
        self.y += self.speed
        self.rotation += 5
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        if self.y > settings.SCREEN_HEIGHT + 30:
            self.active = False

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.3) if self.trail else 0
            if alpha > 0:
                s = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, alpha), (3, 3), 3)
                surface.blit(s, (int(tx - 3), int(ty - 3)))

        if self.sprite:
            rot = pygame.transform.rotate(self.sprite, self.rotation)
            rect = rot.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rot, rect)
        else:
            pygame.draw.ellipse(surface, settings.COLOR_WHITE,
                                (int(self.x - 7), int(self.y - 9), 14, 18))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


import pygame
import random
import math
import settings
from utils import load_sprite


class Enemy:
    def __init__(self, x, y, etype='normal'):
        self.x = x
        self.y = y
        self.etype = etype
        self.active = True
        self.angle = 0
        self.spawn_scale = 0.0
        self.spawn_anim_speed = 0.08

        if etype == 'normal':
            self.hp = 1
            self.speed = 2.5
            self.radius = 26
            self.score = 100
            self.color = settings.COLOR_WHITE
        elif etype == 'heavy':
            self.hp = 3
            self.speed = 1.8
            self.radius = 34
            self.score = 300
            self.color = settings.COLOR_ORANGE
        elif etype == 'boss':
            self.hp = 25
            self.speed = 1.2
            self.radius = 65
            self.score = 5000
            self.color = settings.COLOR_RED

        self.max_hp = self.hp
        self.sprite = load_sprite(f"enemy_{etype}", (self.radius * 2, self.radius * 2))
        self.hit_flash = 0

        self.base_x = x
        self.time = random.uniform(0, math.pi * 2)
        self.amp = random.randint(40, 140)
        self.freq = random.uniform(0.015, 0.04)

    def update(self):
        if self.spawn_scale < 1.0:
            self.spawn_scale = min(1.0, self.spawn_scale + self.spawn_anim_speed)

        self.time += self.freq
        self.y += self.speed

        desired_x = self.base_x + math.sin(self.time) * self.amp
        self.x = max(self.radius, min(settings.SCREEN_WIDTH - self.radius, desired_x))
        self.angle += 2

        if self.y > settings.SCREEN_HEIGHT + 80:
            self.active = False

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self, surface):
        scale = self.spawn_scale
        if scale < 1.0:
            temp_sprite = None
            if self.sprite:
                new_size = (int(self.sprite.get_width() * scale), int(self.sprite.get_height() * scale))
                temp_sprite = pygame.transform.smoothscale(self.sprite, new_size)
                rect = temp_sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(temp_sprite, rect)
            else:
                pygame.draw.ellipse(surface, self.color,
                                    (int(self.x - self.radius * scale), int(self.y - self.radius // 2 * scale),
                                     self.radius * 2 * scale, self.radius * scale))
            return

        if self.sprite:
            if self.hit_flash > 0 and (self.hit_flash // 2) % 2 == 0:
                flash = self.sprite.copy()
                flash.fill((255, 255, 255), special_flags=pygame.BLEND_ADD)
                rect = flash.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(flash, rect)
            else:
                rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
                surface.blit(self.sprite, rect)
        else:
            body_color = (255, 255, 255) if self.hit_flash > 0 and (self.hit_flash // 2) % 2 == 0 else self.color
            pygame.draw.ellipse(surface, body_color,
                                (int(self.x - self.radius), int(self.y - self.radius // 2),
                                 self.radius * 2, self.radius))
            pygame.draw.circle(surface, settings.COLOR_RED,
                               (int(self.x), int(self.y - self.radius)), self.radius // 3)
            pygame.draw.circle(surface, settings.COLOR_YELLOW,
                               (int(self.x + self.radius // 2), int(self.y - self.radius // 4)), 7)
            pygame.draw.circle(surface, settings.COLOR_BG,
                               (int(self.x + self.radius // 2 + 2), int(self.y - self.radius // 4)), 3)

        if self.hp < self.max_hp and self.max_hp > 1:
            bar_w = self.radius * 2.2
            bar_h = 5
            fill = bar_w * (self.hp / self.max_hp)
            pygame.draw.rect(surface, settings.COLOR_RED,
                             (int(self.x - bar_w // 2), int(self.y - self.radius - 12), int(bar_w), bar_h))
            pygame.draw.rect(surface, settings.COLOR_GREEN,
                             (int(self.x - bar_w // 2), int(self.y - self.radius - 12), int(fill), bar_h))

    def hit(self, damage=1):
        self.hp -= damage
        self.hit_flash = 6
        if self.hp <= 0:
            self.active = False
            return True
        return False

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)


class Egg:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.radius = 9
        self.active = True
        self.sprite = load_sprite("egg", (22, 26))
        self.rotation = 0
        self.trail = []

    def update(self):
        self.y += self.speed
        self.rotation += 5
        self.trail.append((self.x, self.y))
        if len(self.trail) > 8:
            self.trail.pop(0)
        if self.y > settings.SCREEN_HEIGHT + 30:
            self.active = False

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)) * 0.3) if self.trail else 0
            if alpha > 0:
                s = pygame.Surface((6, 6), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, alpha), (3, 3), 3)
                surface.blit(s, (int(tx - 3), int(ty - 3)))

        if self.sprite:
            rot = pygame.transform.rotate(self.sprite, self.rotation)
            rect = rot.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rot, rect)
        else:
            pygame.draw.ellipse(surface, settings.COLOR_WHITE,
                                (int(self.x - 7), int(self.y - 9), 14, 18))

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)