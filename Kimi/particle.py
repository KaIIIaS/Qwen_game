"""Частицы и ударные волны."""
import math
import random

import pygame

import settings


class Particle:
    def __init__(self, x, y, color, speed=4, life=30, size=5, ptype="normal", vx=None, vy=None):
        self.x = x
        self.y = y
        if vx is None or vy is None:
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(1, speed)
            self.vx = math.cos(angle) * spd
            self.vy = math.sin(angle) * spd
        else:
            self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.decay = size / float(life)
        self.ptype = ptype

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.ptype == "smoke":
            self.vy -= 0.02
            self.vx *= 0.98
        elif self.ptype == "spark":
            self.vy += 0.08
        elif self.ptype == "debris":
            self.vy += 0.12
            self.vx *= 0.99
        elif self.ptype == "snow":
            self.vy += 0.02
            self.vx += math.sin(self.life * 0.2) * 0.05
        self.life -= 1
        self.size = max(0, self.size - self.decay)

    def draw(self, surface):
        if self.size <= 0:
            return
        alpha = self.life / float(self.max_life)
        size = max(1, int(self.size * alpha))
        if self.ptype == "spark":
            pygame.draw.line(surface, self.color, (int(self.x), int(self.y)),
                             (int(self.x - self.vx * 3), int(self.y - self.vy * 3)), size)
        else:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)

    def is_dead(self):
        return self.life <= 0


class Shockwave:
    """Расширяющееся кольцо — для взрывов боссов и бомб."""

    def __init__(self, x, y, color, max_radius=320, speed=14, width=8):
        self.x = x
        self.y = y
        self.color = color
        self.radius = 8
        self.max_radius = max_radius
        self.speed = speed
        self.width = width

    def update(self):
        self.radius += self.speed
        self.speed *= 0.96

    def draw(self, surface):
        if self.radius >= self.max_radius:
            return
        t = 1.0 - self.radius / float(self.max_radius)
        w = max(1, int(self.width * t))
        c = (int(self.color[0] * t), int(self.color[1] * t), int(self.color[2] * t))
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), int(self.radius), w)

    def is_dead(self):
        return self.radius >= self.max_radius


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.waves = []
        self.quality = 1.0     # 0.35 / 0.7 / 1.0 по настройке
        self.limit = 1400

    def _n(self, count):
        return max(1, int(count * self.quality))

    def spawn_explosion(self, x, y, color, count=15):
        for _ in range(self._n(count)):
            self.particles.append(Particle(x, y, color, speed=random.uniform(2, 6),
                                           life=random.randint(20, 40), size=random.uniform(3, 7)))

    def spawn_sparks(self, x, y, color, count=8):
        for _ in range(self._n(count)):
            self.particles.append(Particle(x, y, color, speed=random.uniform(4, 10),
                                           life=random.randint(10, 25), size=random.uniform(1, 3), ptype="spark"))

    def spawn_smoke(self, x, y, color, count=5):
        for _ in range(self._n(count)):
            c = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
            self.particles.append(Particle(x, y, c, speed=random.uniform(1, 3),
                                           life=random.randint(30, 60), size=random.uniform(5, 12), ptype="smoke"))

    def spawn_debris(self, x, y, color, count=6):
        for _ in range(self._n(count)):
            self.particles.append(Particle(x, y, color, speed=random.uniform(2, 7),
                                           life=random.randint(25, 50), size=random.uniform(2, 5), ptype="debris"))

    def spawn_hit(self, x, y, color, count=6):
        for _ in range(self._n(count)):
            self.particles.append(Particle(x, y, color, speed=random.uniform(1, 4),
                                           life=random.randint(8, 18), size=random.uniform(2, 4)))

    def spawn_snow(self, x, y, color, count=6):
        for _ in range(self._n(count)):
            self.particles.append(Particle(x, y, color, speed=random.uniform(1, 3),
                                           life=random.randint(30, 70), size=random.uniform(2, 5), ptype="snow"))

    def spawn_ring(self, x, y, color, count=24, speed=6, life=34, size=4):
        n = self._n(count)
        for i in range(n):
            a = math.pi * 2 * i / n
            self.particles.append(Particle(x, y, color, life=life, size=size,
                                           vx=math.cos(a) * speed, vy=math.sin(a) * speed))

    def shockwave(self, x, y, color, max_radius=320, speed=14, width=8):
        self.waves.append(Shockwave(x, y, color, max_radius, speed, width))

    def big_explosion(self, x, y, color):
        self.spawn_explosion(x, y, color, 60)
        self.spawn_sparks(x, y, (255, 255, 255), 40)
        self.spawn_smoke(x, y, color, 24)
        self.spawn_debris(x, y, color, 22)
        self.shockwave(x, y, color, 420, 20, 12)

    def clear(self):
        self.particles = []
        self.waves = []

    def update(self):
        if len(self.particles) > self.limit:
            del self.particles[: len(self.particles) - self.limit]
        for p in self.particles[:]:
            p.update()
            if p.is_dead():
                self.particles.remove(p)
        for w in self.waves[:]:
            w.update()
            if w.is_dead():
                self.waves.remove(w)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for w in self.waves:
            w.draw(surface)
