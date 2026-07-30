import pygame
import random
import math
import settings


class Particle:
    def __init__(self, x, y, color, speed=4, life=30, size=5, ptype='normal'):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(1, speed)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size
        self.decay = size / life
        self.ptype = ptype

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.ptype == 'smoke':
            self.vy -= 0.02
            self.vx *= 0.98
        elif self.ptype == 'spark':
            self.vy += 0.08
        elif self.ptype == 'debris':
            self.vy += 0.12
            self.vx *= 0.99
        self.life -= 1
        self.size = max(0, self.size - self.decay)

    def draw(self, surface):
        if self.size > 0:
            alpha = self.life / self.max_life
            size = max(1, int(self.size * alpha))
            if self.ptype == 'spark':
                end_x = self.x - self.vx * 3
                end_y = self.y - self.vy * 3
                pygame.draw.line(surface, self.color, (int(self.x), int(self.y)), (int(end_x), int(end_y)), size)
            else:
                pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), size)

    def is_dead(self):
        return self.life <= 0


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed=random.uniform(2, 6), life=random.randint(20, 40), size=random.uniform(3, 7)))

    def spawn_sparks(self, x, y, color, count=8):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed=random.uniform(4, 10), life=random.randint(10, 25), size=random.uniform(1, 3), ptype='spark'))

    def spawn_smoke(self, x, y, color, count=5):
        for _ in range(count):
            c = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
            self.particles.append(Particle(x, y, c, speed=random.uniform(1, 3), life=random.randint(30, 60), size=random.uniform(5, 12), ptype='smoke'))

    def spawn_debris(self, x, y, color, count=6):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed=random.uniform(2, 7), life=random.randint(25, 50), size=random.uniform(2, 5), ptype='debris'))

    def spawn_hit(self, x, y, color, count=6):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed=random.uniform(1, 4), life=random.randint(8, 18), size=random.uniform(2, 4)))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.is_dead():
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
