import os
import pygame
import random
import math
from settings import *

_sprite_cache = {}


def load_sprite(name, size=None):
    """Загружает спрайт из assets/. Если нет — возвращает None."""
    global _sprite_cache
    if name in _sprite_cache:
        return _sprite_cache[name]

    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        _sprite_cache[name] = img
        return img
    return None


def circle_collision(a, b):
    """Коллизия двух объектов с .x, .y, .radius"""
    dx = a.x - b.x
    dy = a.y - b.y
    return math.hypot(dx, dy) < (a.radius + b.radius)


def draw_text(surface, text, size, x, y, color=COLOR_WHITE, center=True, glow=False, glow_color=None, glow_radius=3):
    """Рисует текст на экране. Возвращает rect."""
    font = pygame.font.SysFont("consolas", size, bold=True)
    label = font.render(str(text), True, color)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    
    if glow:
        gc = glow_color if glow_color else color
        for offset in range(glow_radius, 0, -1):
            alpha = max(20, 80 - offset * 15)
            glow_surf = font.render(str(text), True, gc)
            glow_surf.set_alpha(alpha)
            glow_rect = glow_surf.get_rect(center=rect.center)
            surface.blit(glow_surf, glow_rect)
    
    surface.blit(label, rect)
    return rect


class ScreenShake:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.intensity = 0

    def shake(self, intensity=SCREEN_SHAKE_INTENSITY):
        self.intensity = max(self.intensity, intensity)

    def update(self):
        if self.intensity > 0.5:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity *= SCREEN_SHAKE_DECAY
        else:
            self.offset_x = 0
            self.offset_y = 0
            self.intensity = 0

    def apply(self, surface):
        if self.intensity > 0.5:
            return surface, (self.offset_x, self.offset_y)
        return surface, (0, 0)


class Star:
    def __init__(self, layer=1):
        self.layer = layer
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.speed = random.uniform(0.5, 3.5) * layer
        self.size = random.randint(1, 3)
        self.brightness = random.randint(100, 255)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.twinkle_offset = random.uniform(0, math.pi * 2)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        twinkle = math.sin(pygame.time.get_ticks() * self.twinkle_speed + self.twinkle_offset)
        brightness = int(self.brightness * (0.6 + 0.4 * twinkle))
        brightness = max(50, min(255, brightness))
        color = (brightness, brightness, brightness)
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)


class Trail:
    def __init__(self, max_length=TRAIL_LENGTH, color=COLOR_CYAN, width=3):
        self.points = []
        self.max_length = max_length
        self.color = color
        self.width = width

    def add(self, x, y):
        self.points.append((x, y, pygame.time.get_ticks()))
        if len(self.points) > self.max_length:
            self.points.pop(0)

    def draw(self, surface):
        if len(self.points) < 2:
            return
        now = pygame.time.get_ticks()
        for i in range(len(self.points) - 1):
            x1, y1, t1 = self.points[i]
            x2, y2, t2 = self.points[i + 1]
            age = (now - t1) / 1000.0
            alpha = max(0, 1.0 - age * 2)
            if alpha > 0:
                w = int(self.width * alpha)
                if w > 0:
                    c = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
                    pygame.draw.line(surface, c, (int(x1), int(y1)), (int(x2), int(y2)), w)

    def clear(self):
        self.points = []


def draw_glow(surface, x, y, radius, color, intensity=60):
    """Рисует свечение вокруг точки."""
    glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color[:3], intensity), (radius, radius), radius)
    surface.blit(glow, (int(x) - radius, int(y) - radius))


def draw_progress_bar(surface, x, y, width, height, progress, color_fg, color_bg=(60, 60, 60), border_color=None, border_width=2):
    """Рисует полосу прогресса."""
    pygame.draw.rect(surface, color_bg, (x, y, width, height), border_radius=height // 2)
    if progress > 0:
        fill_width = int(width * progress)
        pygame.draw.rect(surface, color_fg, (x, y, fill_width, height), border_radius=height // 2)
    if border_color:
        pygame.draw.rect(surface, border_color, (x, y, width, height), border_width, border_radius=height // 2)
