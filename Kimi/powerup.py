import pygame
import math
import random
from settings import *
from utils import load_sprite, draw_glow


class PowerUp:
    TYPES = {
        'weapon': {'color': COLOR_ORANGE, 'label': 'W'},
        'life': {'color': COLOR_RED, 'label': '♥'},
        'score': {'color': COLOR_YELLOW, 'label': '$'},
        'drone': {'color': (0, 255, 100), 'label': 'D'}
    }

    def __init__(self, x, y, ptype='weapon'):
        self.x = x
        self.y = y
        self.type = ptype
        self.speed = POWERUP_SPEED
        self.radius = 18
        self.active = True
        self.spawn_time = pygame.time.get_ticks()
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.rotation = 0

        self.sprite = load_sprite(f"powerup_{ptype}", (40, 40))
        self.data = self.TYPES.get(ptype, self.TYPES['weapon'])

    def update(self):
        self.y += self.speed
        self.rotation += 1
        self.bob_offset += 0.05
        if self.y > SCREEN_HEIGHT + 30:
            self.active = False

        if pygame.time.get_ticks() - self.spawn_time > POWERUP_LIFETIME:
            self.active = False

    def draw(self, surface):
        bob = math.sin(self.bob_offset) * 4
        draw_y = self.y + bob
        
        glow_intensity = int(40 + 20 * math.sin(self.bob_offset * 2))
        draw_glow(surface, self.x, draw_y, 30, self.data['color'], glow_intensity)

        if self.sprite:
            rect = self.sprite.get_rect(center=(int(self.x), int(draw_y)))
            surface.blit(self.sprite, rect)
        else:
            pygame.draw.circle(surface, self.data['color'], (int(self.x), int(draw_y)), self.radius)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(draw_y)), self.radius, 2)
            font = pygame.font.SysFont("consolas", 22, bold=True)
            label = font.render(self.data['label'], True, COLOR_WHITE)
            rect = label.get_rect(center=(self.x, draw_y))
            surface.blit(label, rect)

    def apply(self, player):
        if self.type == 'weapon':
            player.weapon.upgrade()
        elif self.type == 'life':
            player.lives += 1
        elif self.type == 'score':
            player.score += 500
        elif self.type == 'drone':
            player.add_or_upgrade_drone()

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)
