"""Вспомогательные штуки: загрузка спрайтов, текст, кнопки, фон, эффекты."""
import math
import os
import random

import pygame

import settings
from settings import *

_sprite_cache = {}
_font_cache = {}


# ------------------------------------------------------------------ шрифты
def get_font(size, bold=True, name="consolas"):
    key = (name, size, bold)
    font = _font_cache.get(key)
    if font is None:
        font = pygame.font.SysFont(name, size, bold=bold)
        _font_cache[key] = font
    return font


# ------------------------------------------------------------------ спрайты
def load_sprite(name, size=None, tint=None, alpha=None):
    """Загружает assets/<name>.png. Возвращает None, если файла нет."""
    key = (name, size, tint, alpha)
    if key in _sprite_cache:
        return _sprite_cache[key]

    path = os.path.join(settings.ASSETS_DIR, "%s.png" % name)
    if not os.path.exists(path):
        _sprite_cache[key] = None
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        _sprite_cache[key] = None
        return None

    if size:
        img = pygame.transform.smoothscale(img, size)
    if tint:
        img = img.copy()
        layer = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        layer.fill((tint[0], tint[1], tint[2], 255))
        img.blit(layer, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    if alpha is not None:
        img = img.copy()
        img.set_alpha(alpha)
    _sprite_cache[key] = img
    return img


def load_sprite_fit(name, max_w, max_h, tint=None):
    """Как load_sprite, но сохраняет пропорции и вписывает в рамку."""
    path = os.path.join(settings.ASSETS_DIR, "%s.png" % name)
    if not os.path.exists(path):
        return None
    probe = load_sprite(name)
    if probe is None:
        return None
    w, h = probe.get_size()
    k = min(max_w / float(w), max_h / float(h))
    return load_sprite(name, (max(1, int(w * k)), max(1, int(h * k))), tint=tint)


# ------------------------------------------------------------------ математика
def clamp(v, lo, hi):
    return lo if v < lo else (hi if v > hi else v)


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(a, b, t):
    t = clamp(t, 0.0, 1.0)
    return (int(lerp(a[0], b[0], t)), int(lerp(a[1], b[1], t)), int(lerp(a[2], b[2], t)))


def ease_out(t):
    return 1.0 - (1.0 - t) ** 3


def circle_collision(a, b):
    return math.hypot(a.x - b.x, a.y - b.y) < (a.radius + b.radius)


def angle_to(x1, y1, x2, y2):
    return math.atan2(y2 - y1, x2 - x1)


# ------------------------------------------------------------------ рисование
def draw_text(surface, text, size, x, y, color=COLOR_WHITE, center=True,
              glow=False, glow_color=None, glow_radius=3, shadow=False, alpha=None):
    font = get_font(size)
    label = font.render(str(text), True, color)
    if alpha is not None:
        label = label.copy()
        label.set_alpha(alpha)
    rect = label.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    if shadow:
        sh = font.render(str(text), True, (0, 0, 0))
        if alpha is not None:
            sh.set_alpha(alpha)
        surface.blit(sh, (rect.x + 2, rect.y + 2))

    if glow:
        gc = glow_color if glow_color else color
        for offset in range(glow_radius, 0, -1):
            g = font.render(str(text), True, gc)
            g.set_alpha(max(18, 80 - offset * 15))
            surface.blit(g, g.get_rect(center=rect.center))

    surface.blit(label, rect)
    return rect


_glow_cache = {}


def draw_glow(surface, x, y, radius, color, intensity=60):
    radius = max(1, int(radius))
    key = (radius, int(color[0]), int(color[1]), int(color[2]), int(intensity) // 6)
    glow = _glow_cache.get(key)
    if glow is None:
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (color[0], color[1], color[2], int(intensity)), (radius, radius), radius)
        if len(_glow_cache) < 600:
            _glow_cache[key] = glow
    surface.blit(glow, (int(x) - radius, int(y) - radius))


def draw_panel(surface, rect, color=(14, 16, 30), alpha=200, border=None, radius=16, border_width=2):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (color[0], color[1], color[2], alpha), panel.get_rect(), border_radius=radius)
    surface.blit(panel, rect.topleft)
    if border:
        pygame.draw.rect(surface, border, rect, border_width, border_radius=radius)


def draw_progress_bar(surface, x, y, width, height, progress, color_fg,
                      color_bg=(60, 60, 60), border_color=None, border_width=2):
    progress = clamp(progress, 0.0, 1.0)
    r = max(1, height // 2)
    pygame.draw.rect(surface, color_bg, (x, y, width, height), border_radius=r)
    if progress > 0:
        pygame.draw.rect(surface, color_fg, (x, y, max(2, int(width * progress)), height), border_radius=r)
    if border_color:
        pygame.draw.rect(surface, border_color, (x, y, width, height), border_width, border_radius=r)


# ------------------------------------------------------------------ тряска
class ScreenShake:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.intensity = 0
        self.enabled = True

    def shake(self, intensity=SCREEN_SHAKE_INTENSITY):
        if self.enabled:
            self.intensity = max(self.intensity, intensity)

    def update(self):
        if self.intensity > 0.5:
            self.offset_x = random.uniform(-self.intensity, self.intensity)
            self.offset_y = random.uniform(-self.intensity, self.intensity)
            self.intensity *= SCREEN_SHAKE_DECAY
        else:
            self.offset_x = self.offset_y = 0
            self.intensity = 0


# ------------------------------------------------------------------ фон
class Star:
    def __init__(self, layer=1):
        self.layer = layer
        self.x = random.randint(0, settings.SCREEN_WIDTH)
        self.y = random.randint(0, settings.SCREEN_HEIGHT)
        self.speed = random.uniform(0.4, 2.4) * layer
        self.size = random.randint(1, 3)
        self.brightness = random.randint(90, 255)
        self.twinkle_speed = random.uniform(0.02, 0.08)
        self.twinkle_offset = random.uniform(0, math.pi * 2)

    def update(self, speed_mult=1.0):
        self.y += self.speed * speed_mult
        if self.y > settings.SCREEN_HEIGHT:
            self.y = -2
            self.x = random.randint(0, settings.SCREEN_WIDTH)

    def draw(self, surface):
        tw = math.sin(pygame.time.get_ticks() * self.twinkle_speed + self.twinkle_offset)
        b = int(clamp(self.brightness * (0.6 + 0.4 * tw), 50, 255))
        pygame.draw.circle(surface, (b, b, b), (int(self.x), int(self.y)), self.size)


class Nebula:
    """Мягкое цветное пятно на фоне — даёт уровням разный «характер»."""

    def __init__(self, color):
        self.color = color
        self.radius = random.randint(240, 520)
        self.x = random.randint(0, settings.SCREEN_WIDTH)
        self.y = random.randint(-200, settings.SCREEN_HEIGHT)
        self.speed = random.uniform(0.08, 0.3)
        self.alpha = random.randint(14, 34)
        self._surf = None
        self._rebuild()

    def _rebuild(self):
        r = self.radius
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        steps = 10
        for i in range(steps, 0, -1):
            rr = int(r * i / steps)
            a = int(self.alpha * (1.0 - i / float(steps)) ** 1.4) + 2
            pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], a), (r, r), rr)
        self._surf = s

    def set_color(self, color):
        if color != self.color:
            self.color = color
            self._rebuild()

    def update(self, speed_mult=1.0):
        self.y += self.speed * speed_mult
        if self.y - self.radius > settings.SCREEN_HEIGHT:
            self.y = -self.radius
            self.x = random.randint(0, settings.SCREEN_WIDTH)

    def draw(self, surface):
        surface.blit(self._surf, (int(self.x - self.radius), int(self.y - self.radius)))


class Background:
    """Параллакс-звёзды + туманности + редкие метеоры."""

    def __init__(self, theme=(60, 80, 200), star_count=280):
        self.stars = [Star(layer=random.choice([1, 1, 1, 2, 2, 3])) for _ in range(star_count)]
        self.nebulas = [Nebula(theme) for _ in range(4)]
        self.meteors = []
        self.theme = theme
        self.speed_mult = 1.0

    def set_theme(self, color):
        self.theme = color
        for n in self.nebulas:
            n.set_color(color)

    def update(self):
        for s in self.stars:
            s.update(self.speed_mult)
        for n in self.nebulas:
            n.update(self.speed_mult)
        if random.random() < 0.006:
            self.meteors.append([random.randint(0, settings.SCREEN_WIDTH), -40,
                                 random.uniform(-7, 7), random.uniform(16, 26), 1.0])
        for m in self.meteors[:]:
            m[0] += m[2]
            m[1] += m[3]
            m[4] -= 0.012
            if m[4] <= 0 or m[1] > settings.SCREEN_HEIGHT + 60:
                self.meteors.remove(m)

    def draw(self, surface):
        for n in self.nebulas:
            n.draw(surface)
        for s in self.stars:
            s.draw(surface)
        for m in self.meteors:
            a = clamp(m[4], 0, 1)
            c = (int(255 * a), int(240 * a), int(200 * a))
            pygame.draw.line(surface, c, (int(m[0]), int(m[1])),
                             (int(m[0] - m[2] * 3), int(m[1] - m[3] * 3)), 2)


# ------------------------------------------------------------------ след
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
            x2, y2, _ = self.points[i + 1]
            alpha = max(0.0, 1.0 - (now - t1) / 500.0)
            if alpha <= 0:
                continue
            w = int(self.width * alpha)
            if w > 0:
                c = (int(self.color[0] * alpha), int(self.color[1] * alpha), int(self.color[2] * alpha))
                pygame.draw.line(surface, c, (int(x1), int(y1)), (int(x2), int(y2)), w)

    def clear(self):
        self.points = []


# ------------------------------------------------------------------ UI
class Button:
    def __init__(self, x, y, w, h, text, color=(52, 96, 200), size=34,
                 value=None, enabled=True, subtitle=None, text_color=COLOR_WHITE):
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.text = text
        self.subtitle = subtitle
        self.color = color
        self.text_color = text_color
        self.size = size
        self.value = value
        self.enabled = enabled
        self.hover = 0.0

    def update(self, mouse_pos):
        target = 1.0 if (self.enabled and self.rect.collidepoint(mouse_pos)) else 0.0
        self.hover += (target - self.hover) * 0.28

    def hit(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

    def draw(self, surface):
        grow = int(self.hover * 5)
        r = self.rect.inflate(grow * 2, grow)
        base = self.color if self.enabled else (55, 58, 70)
        col = lerp_color(base, (255, 255, 255), self.hover * 0.28)

        if self.hover > 0.05 and self.enabled:
            glow = pygame.Surface((r.width + 40, r.height + 40), pygame.SRCALPHA)
            pygame.draw.rect(glow, (base[0], base[1], base[2], int(70 * self.hover)),
                             glow.get_rect(), border_radius=22)
            surface.blit(glow, (r.x - 20, r.y - 20))

        pygame.draw.rect(surface, col, r, border_radius=14)
        pygame.draw.rect(surface, (12, 14, 24), r.inflate(-6, -6), border_radius=11)
        inner = lerp_color((22, 26, 44), base, 0.35 + 0.35 * self.hover)
        pygame.draw.rect(surface, inner, r.inflate(-10, -10), border_radius=10)

        tc = self.text_color if self.enabled else (130, 130, 140)
        ty = r.centery - (12 if self.subtitle else 0)
        draw_text(surface, self.text, self.size, r.centerx, ty, tc, shadow=True)
        if self.subtitle:
            draw_text(surface, self.subtitle, max(16, self.size - 14), r.centerx, r.centery + 20, (170, 180, 200))
