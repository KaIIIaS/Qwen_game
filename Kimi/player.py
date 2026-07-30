import pygame
import math
from settings import *
from utils import load_sprite, Trail
from bullet import WeaponSystem


class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 150
        self.speed = PLAYER_SPEED
        self.radius = PLAYER_SIZE // 2
        self.lives = PLAYER_LIVES
        self.score = 0
        self.weapon = WeaponSystem()
        self.invulnerable_until = 0
        self.sprite = load_sprite("player", (PLAYER_SIZE + 20, PLAYER_SIZE + 30))
        self.flame_timer = 0
        self.target_x = self.x
        self.target_y = self.y
        self.drone = None
        self.engine_trail = Trail(max_length=20, color=(0, 200, 255), width=6)
        self.hit_flash = 0

    def update(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.target_x = max(self.radius, min(SCREEN_WIDTH - self.radius, mouse_x))
        self.target_y = max(self.radius, min(SCREEN_HEIGHT - self.radius, mouse_y))

        old_x, old_y = self.x, self.y
        self.x += (self.target_x - self.x) * self.speed
        self.y += (self.target_y - self.y) * self.speed
        self.flame_timer += 0.3
        
        dist = math.hypot(self.x - old_x, self.y - old_y)
        if dist > 0.5:
            self.engine_trail.add(self.x, self.y + self.radius)

    def draw(self, surface):
        if pygame.time.get_ticks() < self.invulnerable_until:
            if (pygame.time.get_ticks() // 100) % 2 == 0:
                return

        self.engine_trail.draw(surface)
        
        if self.sprite:
            rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(self.sprite, rect)
        else:
            points = [
                (self.x, self.y - self.radius),
                (self.x - self.radius, self.y + self.radius),
                (self.x, self.y + self.radius // 2),
                (self.x + self.radius, self.y + self.radius)
            ]
            pygame.draw.polygon(surface, COLOR_CYAN, points)
            pygame.draw.polygon(surface, COLOR_WHITE, points, 2)
            pygame.draw.circle(surface, COLOR_WHITE, (int(self.x), int(self.y)), 8)

            flame_h = 14 + int(math.sin(self.flame_timer) * 7)
            pygame.draw.polygon(surface, COLOR_ORANGE, [
                (self.x - 10, self.y + self.radius),
                (self.x + 10, self.y + self.radius),
                (self.x, self.y + self.radius + flame_h)
            ])

    def shoot(self):
        if self.weapon.can_shoot():
            return self.weapon.shoot(self.x, self.y - self.radius)
        return []

    def hit(self):
        now = pygame.time.get_ticks()
        if now < self.invulnerable_until:
            return False

        self.lives -= 1
        self.invulnerable_until = now + PLAYER_INVULNERABLE_TIME
        self.hit_flash = 10
        return self.lives <= 0

    def add_or_upgrade_drone(self):
        if self.drone is None:
            from drone import Drone
            self.drone = Drone(self)
        else:
            self.drone.upgrade()

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)
