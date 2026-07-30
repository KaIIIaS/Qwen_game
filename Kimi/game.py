import pygame
import random
import math
from settings import *
from utils import Star, draw_text, ScreenShake, draw_progress_bar
from player import Player
from enemy import Enemy, Egg
from powerup import PowerUp
from particle import ParticleSystem


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.FULLSCREEN | pygame.SCALED
        )
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"

        self.stars = [Star(layer=random.choice([1, 1, 1, 2, 2, 3])) for _ in range(300)]
        self.particles = ParticleSystem()
        self.shake = ScreenShake()

        self.player = None
        self.bullets = []
        self.enemies = []
        self.eggs = []
        self.powerups = []

        self.wave = 1
        self.wave_timer = 0
        self.enemies_to_spawn = 0
        self.spawn_timer = 0
        self.boss_warning_timer = 0

        self.font_large = pygame.font.SysFont("consolas", 90, bold=True)
        self.font_medium = pygame.font.SysFont("consolas", 44, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 26, bold=True)

        self.btn_resume = None
        self.btn_quit = None
        
        self.combo_count = 0
        self.combo_timer = 0
        self.combo_multiplier = 1.0
        self.floating_texts = []

    def reset_game(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.eggs = []
        self.powerups = []
        self.wave = 1
        self.wave_timer = pygame.time.get_ticks()
        self.enemies_to_spawn = 6
        self.spawn_timer = 0
        self.state = "playing"
        self.combo_count = 0
        self.combo_multiplier = 1.0
        self.floating_texts = []
        pygame.mouse.set_visible(False)

    def spawn_wave(self):
        now = pygame.time.get_ticks()
        if now - self.wave_timer < WAVE_COOLDOWN:
            return

        if self.enemies_to_spawn > 0 and now - self.spawn_timer > 650:
            if self.wave % 5 == 0:
                etype = 'boss'
                count = 1
            elif self.wave % 3 == 0:
                etype = 'heavy'
                count = random.randint(2, 4)
            else:
                etype = 'normal'
                count = random.randint(5, 9)

            for _ in range(count):
                if self.enemies_to_spawn <= 0:
                    break
                x = random.randint(ENEMY_SPAWN_MARGIN, SCREEN_WIDTH - ENEMY_SPAWN_MARGIN)
                y = random.randint(-140, -60)
                self.enemies.append(Enemy(x, y, etype))
                self.enemies_to_spawn -= 1

            self.spawn_timer = now

        if self.enemies_to_spawn <= 0 and len(self.enemies) == 0:
            self.wave += 1
            self.enemies_to_spawn = 5 + self.wave * 3
            self.wave_timer = now
            bonus = int(self.wave * 50 * self.combo_multiplier)
            self.player.score += bonus
            self.floating_texts.append({
                'text': f"WAVE {self.wave} CLEAR! +{bonus}",
                'x': SCREEN_WIDTH // 2, 'y': SCREEN_HEIGHT // 2 - 100,
                'life': 120, 'color': COLOR_GOLD, 'size': 40
            })

    def handle_collisions(self):
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                dx = bullet.x - enemy.x
                dy = bullet.y - enemy.y
                if math.hypot(dx, dy) < bullet.radius + enemy.radius:
                    self.particles.spawn_hit(bullet.x, bullet.y, COLOR_YELLOW, 5)
                    
                    if enemy.hit(bullet.damage):
                        self.particles.spawn_explosion(enemy.x, enemy.y, enemy.color, 22)
                        self.particles.spawn_sparks(enemy.x, enemy.y, COLOR_WHITE, 10)
                        self.particles.spawn_smoke(enemy.x, enemy.y, enemy.color, 6)
                        self.particles.spawn_debris(enemy.x, enemy.y, enemy.color, 5)
                        
                        self.combo_count += 1
                        self.combo_timer = pygame.time.get_ticks()
                        self.update_combo_multiplier()
                        
                        score_gain = int(enemy.score * self.combo_multiplier)
                        self.player.score += score_gain
                        
                        self.floating_texts.append({
                            'text': f"+{score_gain}" + (f" x{self.combo_multiplier:.1f}" if self.combo_multiplier > 1 else ""),
                            'x': enemy.x, 'y': enemy.y,
                            'life': 60, 'color': COLOR_YELLOW if self.combo_multiplier == 1 else COLOR_GOLD, 'size': 22
                        })
                        
                        self.shake.shake(4 if enemy.etype != 'boss' else 12)

                        if random.random() < 0.15:
                            ptype = random.choice(['weapon', 'life', 'score', 'drone'])
                            self.powerups.append(PowerUp(enemy.x, enemy.y, ptype))

                    else:
                        self.particles.spawn_hit(enemy.x, enemy.y, COLOR_WHITE, 3)
                        self.shake.shake(2)

                    bullet.active = False
                    break

        for egg in self.eggs[:]:
            dx = egg.x - self.player.x
            dy = egg.y - self.player.y
            if math.hypot(dx, dy) < egg.radius + self.player.radius:
                if self.player.hit():
                    self.state = "gameover"
                    pygame.mouse.set_visible(True)
                self.particles.spawn_explosion(egg.x, egg.y, COLOR_WHITE, 10)
                self.shake.shake(6)
                self.combo_count = 0
                self.combo_multiplier = 1.0
                egg.active = False

        for enemy in self.enemies[:]:
            dx = enemy.x - self.player.x
            dy = enemy.y - self.player.y
            if math.hypot(dx, dy) < enemy.radius + self.player.radius:
                if self.player.hit():
                    self.state = "gameover"
                    pygame.mouse.set_visible(True)
                self.particles.spawn_explosion(enemy.x, enemy.y, enemy.color, 28)
                self.particles.spawn_sparks(enemy.x, enemy.y, COLOR_WHITE, 15)
                self.shake.shake(10)
                self.combo_count = 0
                self.combo_multiplier = 1.0
                enemy.active = False

        for pu in self.powerups[:]:
            dx = pu.x - self.player.x
            dy = pu.y - self.player.y
            if math.hypot(dx, dy) < pu.radius + self.player.radius:
                pu.apply(self.player)
                pu.active = False
                self.particles.spawn_explosion(pu.x, pu.y, pu.data['color'], 12)
                self.particles.spawn_sparks(pu.x, pu.y, COLOR_WHITE, 8)
                self.shake.shake(3)
                
                text = ""
                if pu.type == 'weapon': text = "WEAPON UP!"
                elif pu.type == 'life': text = "+1 LIFE"
                elif pu.type == 'score': text = "+500"
                elif pu.type == 'drone': text = "DRONE UP!"
                self.floating_texts.append({
                    'text': text, 'x': pu.x, 'y': pu.y - 20,
                    'life': 50, 'color': pu.data['color'], 'size': 20
                })

    def update_combo_multiplier(self):
        self.combo_multiplier = 1.0
        for threshold, mult in sorted(COMBO_MULTIPLIERS.items()):
            if self.combo_count >= threshold:
                self.combo_multiplier = mult

    def update(self):
        self.shake.update()
        
        for star in self.stars:
            star.update()
        self.particles.update()

        if self.combo_count > 0 and pygame.time.get_ticks() - self.combo_timer > COMBO_TIMEOUT:
            self.combo_count = 0
            self.combo_multiplier = 1.0

        for ft in self.floating_texts[:]:
            ft['y'] -= 1
            ft['life'] -= 1
            if ft['life'] <= 0:
                self.floating_texts.remove(ft)

        if self.state != "playing":
            return

        self.player.update()

        new_bullets = self.player.shoot()
        self.bullets.extend(new_bullets)

        if self.player.drone:
            self.player.drone.update()
            drone_bullets = self.player.drone.shoot()
            self.bullets.extend(drone_bullets)

        for b in self.bullets[:]:
            b.update()
            if not b.active:
                self.bullets.remove(b)

        self.spawn_wave()
        for e in self.enemies[:]:
            e.update()
            if random.random() < 0.003 and e.etype != 'boss':
                self.eggs.append(Egg(e.x, e.y))
            if not e.active:
                self.enemies.remove(e)

        for egg in self.eggs[:]:
            egg.update()
            if not egg.active:
                self.eggs.remove(egg)

        for pu in self.powerups[:]:
            pu.update()
            if not pu.active:
                self.powerups.remove(pu)

        self.handle_collisions()

    def draw_hud(self):
        x, y = 30, 30
        shadow = 2

        draw_text(self.screen, f"SCORE: {self.player.score}", 28, x + shadow, y + shadow, (0, 0, 0), center=False)
        draw_text(self.screen, f"SCORE: {self.player.score}", 28, x, y, COLOR_YELLOW, center=False)

        y += 42
        draw_text(self.screen, f"LIVES: {self.player.lives}", 28, x + shadow, y + shadow, (0, 0, 0), center=False)
        draw_text(self.screen, f"LIVES: {self.player.lives}", 28, x, y, COLOR_GREEN, center=False)

        y += 42
        draw_text(self.screen, f"WAVE: {self.wave}", 28, x + shadow, y + shadow, (0, 0, 0), center=False)
        draw_text(self.screen, f"WAVE: {self.wave}", 28, x, y, COLOR_CYAN, center=False)

        y += 42
        draw_text(self.screen, f"GUN: {self.player.weapon.level}/{self.player.weapon.MAX_LEVEL}",
                  24, x + shadow, y + shadow, (0, 0, 0), center=False)
        draw_text(self.screen, f"GUN: {self.player.weapon.level}/{self.player.weapon.MAX_LEVEL}",
                  24, x, y, COLOR_ORANGE, center=False)

        if self.player.drone:
            y += 38
            dcol = (0, 255, 100)
            draw_text(self.screen, f"DRONE: {self.player.drone.level}/{self.player.drone.MAX_LEVEL}",
                      22, x + shadow, y + shadow, (0, 0, 0), center=False)
            draw_text(self.screen, f"DRONE: {self.player.drone.level}/{self.player.drone.MAX_LEVEL}",
                      22, x, y, dcol, center=False)
        
        if self.combo_count >= 2:
            combo_y = SCREEN_HEIGHT - 80
            combo_text = f"{self.combo_count}x COMBO"
            if self.combo_multiplier > 1:
                combo_text += f" (x{self.combo_multiplier:.1f})"
            draw_text(self.screen, combo_text, 32, SCREEN_WIDTH // 2, combo_y, COLOR_GOLD, glow=True, glow_color=COLOR_ORANGE)

    def draw_crosshair(self):
        mx, my = pygame.mouse.get_pos()
        size = 16
        pygame.draw.line(self.screen, COLOR_GREEN, (mx - size, my), (mx + size, my), 2)
        pygame.draw.line(self.screen, COLOR_GREEN, (mx, my - size), (mx, my + size), 2)
        pygame.draw.circle(self.screen, COLOR_GREEN, (mx, my), 10, 1)

    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 360, 70

        y1 = SCREEN_HEIGHT // 2 - 60
        self.btn_resume = pygame.Rect(cx - btn_w // 2, y1, btn_w, btn_h)
        pygame.draw.rect(self.screen, COLOR_GREEN, self.btn_resume, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_WHITE, self.btn_resume, 3, border_radius=10)
        draw_text(self.screen, "ПРОДОЛЖИТЬ", 34, cx, y1 + btn_h // 2, COLOR_WHITE)

        y2 = SCREEN_HEIGHT // 2 + 50
        self.btn_quit = pygame.Rect(cx - btn_w // 2, y2, btn_w, btn_h)
        pygame.draw.rect(self.screen, COLOR_RED, self.btn_quit, border_radius=10)
        pygame.draw.rect(self.screen, COLOR_WHITE, self.btn_quit, 3, border_radius=10)
        draw_text(self.screen, "ВЫХОД", 34, cx, y2 + btn_h // 2, COLOR_WHITE)

        draw_text(self.screen, "Или нажмите ESC", 22, cx, y2 + btn_h + 35, COLOR_GRAY)

    def draw_floating_texts(self):
        for ft in self.floating_texts:
            alpha = min(255, ft['life'] * 4)
            s = pygame.Surface((400, 60), pygame.SRCALPHA)
            font = pygame.font.SysFont("consolas", ft['size'], bold=True)
            label = font.render(ft['text'], True, ft['color'])
            label.set_alpha(alpha)
            rect = label.get_rect(center=(200, 30))
            s.blit(label, rect)
            self.screen.blit(s, (int(ft['x'] - 200), int(ft['y'] - 30)))

    def draw(self):
        self.screen.fill(COLOR_BG)

        for star in self.stars:
            star.draw(self.screen)

        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_game()
        elif self.state == "paused":
            self.draw_game()
            self.draw_pause_menu()
        elif self.state == "gameover":
            self.draw_game()
            self.draw_gameover()

        self.particles.draw(self.screen)
        self.draw_floating_texts()

        if self.state == "playing":
            self.draw_crosshair()

        if self.shake.intensity > 0.5:
            offset_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            offset_surf.blit(self.screen, (self.shake.offset_x, self.shake.offset_y))
            self.screen.blit(offset_surf, (0, 0))

        pygame.display.flip()

    def draw_menu(self):
        title = self.font_large.render("CHICKEN INVADERS", True, COLOR_YELLOW)
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self.screen.blit(title, rect)

        draw_text(self.screen, "Нажмите ENTER чтобы начать", 34,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, COLOR_WHITE)
        draw_text(self.screen, "Мышь — движение  |  Стрельба автоматическая", 24,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80, COLOR_GRAY)
        draw_text(self.screen, "ESC — пауза  |  W — бонус оружия  |  D — бонус дрона", 22,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 115, COLOR_GRAY)

    def draw_game(self):
        self.player.draw(self.screen)

        if self.player.drone:
            self.player.drone.draw(self.screen)

        for b in self.bullets:
            b.draw(self.screen)

        for e in self.enemies:
            e.draw(self.screen)

        for egg in self.eggs:
            egg.draw(self.screen)

        for pu in self.powerups:
            pu.draw(self.screen)

        self.draw_hud()

    def draw_gameover(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        over = self.font_large.render("GAME OVER", True, COLOR_RED)
        rect = over.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(over, rect)

        draw_text(self.screen, f"Итоговый счёт: {self.player.score}", 32,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30, COLOR_WHITE)
        draw_text(self.screen, f"Макс. комбо: {getattr(self, 'combo_count', 0)}", 26,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70, COLOR_GRAY)
        draw_text(self.screen, "R — рестарт  |  ESC — меню", 26,
                  SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 115, COLOR_GRAY)

    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.KEYDOWN:
                    if self.state == "menu" and event.key == pygame.K_RETURN:
                        self.reset_game()
                    elif self.state == "gameover" and event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        if self.state == "playing":
                            self.state = "paused"
                            pygame.mouse.set_visible(True)
                        elif self.state == "paused":
                            self.state = "playing"
                            pygame.mouse.set_visible(False)
                        elif self.state == "gameover":
                            self.state = "menu"
                            pygame.mouse.set_visible(True)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "paused":
                        if self.btn_resume and self.btn_resume.collidepoint(mouse_pos):
                            self.state = "playing"
                            pygame.mouse.set_visible(False)
                        elif self.btn_quit and self.btn_quit.collidepoint(mouse_pos):
                            self.running = False

            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
