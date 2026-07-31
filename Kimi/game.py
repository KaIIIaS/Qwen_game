"""Игровой цикл, состояния, коллизии, HUD."""
import math
import random

import pygame

import campaign
import settings
from settings import *
from audio import Audio
from boss import get_boss, BOSS_LIST, Beam, Mine, FrostZone, BlackHole
from bullet import EnemyBullet
from config import Config
from enemy import Enemy
from menu import Menus
from particle import ParticleSystem
from player import Player
from powerup import PowerUp
from utils import (Background, Button, ScreenShake, clamp, draw_panel, draw_progress_bar,
                   draw_text, get_font, lerp_color, load_sprite)
from wave import WaveDirector, endless_wave

MENU_STATES = ("main", "campaign", "settings", "help")


class Game:
    # ============================================================ init
    def __init__(self):
        pygame.init()
        self.config = Config()
        self.audio = Audio(self.config)

        self.screen = None
        self.apply_display(first=True)
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.particles = ParticleSystem()
        self.shake = ScreenShake()
        self.shake.enabled = self.config.opt["screen_shake"]
        self.apply_particles()

        self.menus = Menus(self)
        self.state = "main"
        self.menus.build("main")

        # мир
        self.player = None
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.hazards = []
        self.boss = None
        self.director = WaveDirector(self)

        # прогресс забега
        self.mode = "campaign"
        self.level = None
        self.level_id = 1
        self.wave_index = 0
        self.wave_number = 0
        self.phase = "idle"          # spawning | clearing | intermission | warning | boss | done
        self.phase_timer = 0.0
        self.run_deaths = 0
        self.kills = 0
        self.best_combo = 0

        # эффекты интерфейса
        self.floating_texts = []
        self.banners = []
        self.combo_count = 0
        self.combo_timer = 0
        self.combo_multiplier = 1.0
        self.flash = 0.0
        self.result = {}

        self.pause_buttons = []
        self.result_buttons = []

    # ------------------------------------------------------------ дисплей
    def apply_display(self, first=False):
        info = pygame.display.Info()
        if self.config.opt["fullscreen"]:
            w, h = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        else:
            w, h = int(info.current_w * 0.8), int(info.current_h * 0.8)
            self.screen = pygame.display.set_mode((w, h))
        settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = self.screen.get_size()
        self.canvas = pygame.Surface(self.screen.get_size()).convert()
        if not first:
            self.background = Background(self.background.theme)
            self.menus.build(self.menus.state)
        else:
            self.background = Background((60, 90, 200))

    def apply_particles(self):
        q = {"low": 0.35, "medium": 0.7, "high": 1.0}[self.config.opt["particles"]]
        self.particles.quality = q
        self.particles.limit = int(500 + 900 * q)

    # ============================================================ запуск забега
    def _mults(self):
        d = self.config.difficulty
        return d["hp"], d["speed"], d["fire"]

    def start_campaign_level(self, level_id):
        self.mode = "campaign"
        self.level_id = level_id
        self.level = campaign.get_level(level_id)
        self.background.set_theme(self.level["theme"])
        self.state = "briefing"
        self.phase_timer = 0.0

    def start_endless(self):
        self.mode = "endless"
        self.level = None
        self.background.set_theme((150, 90, 200))
        self.begin_run()

    def begin_run(self):
        d = self.config.difficulty
        self.player = Player(lives=d["lives"])
        self.player.control = self.config.opt["control"]
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.hazards = []
        self.boss = None
        self.particles.clear()
        self.floating_texts = []
        self.banners = []
        self.combo_count = 0
        self.combo_multiplier = 1.0
        self.best_combo = 0
        self.run_deaths = 0
        self.kills = 0
        self.wave_index = 0
        self.wave_number = 0
        self.state = "playing"
        pygame.mouse.set_visible(False)
        self.next_wave(first=True)

    # ------------------------------------------------------------ волны
    def next_wave(self, first=False):
        hp, sp, fr = self._mults()

        if self.mode == "campaign":
            waves = self.level["waves"]
            if self.wave_index >= len(waves):
                self.start_boss(self.level["boss"])
                return
            spec = waves[self.wave_index]
            self.wave_index += 1
            self.wave_number = self.wave_index
            title = "ВОЛНА %d/%d" % (self.wave_index, len(waves))
            self.banner(title, self.level["theme"], 1600, sub=spec["name"])
        else:
            self.wave_number += 1
            n = self.wave_number
            if n % 5 == 0:
                key = list(("warlord", "broodmother", "chrome", "frost", "omega"))[(n // 5 - 1) % 5]
                self.start_boss(key, endless_scale=1.0 + 0.28 * ((n - 1) // 25))
                return
            scale = 1.0 + 0.045 * n
            hp *= scale
            sp *= min(1.6, 1.0 + 0.012 * n)
            fr *= min(2.2, 1.0 + 0.03 * n)
            spec = endless_wave(n)
            self.banner("ВОЛНА %d" % n, (200, 140, 255), 1500, sub=spec["name"])

        self.audio.play("wave", 0.5)
        self.director.start(spec, hp, sp, fr)
        self.phase = "spawning"
        self.phase_timer = 0.0

    def start_boss(self, key, endless_scale=1.0):
        self.phase = "warning"
        self.phase_timer = 0.0
        self._boss_key = key
        self._boss_scale = endless_scale
        self.audio.play("warning", 1.0)
        cls = get_boss(key)
        self.banner("ВНИМАНИЕ", COLOR_RED, BOSS_WARNING_TIME, sub=cls.NAME)

    def _spawn_boss(self):
        hp, sp, fr = self._mults()
        cls = get_boss(self._boss_key)
        self.boss = cls(self, hp_mult=hp * self._boss_scale, fire_mult=fr, speed_mult=sp)
        self.phase = "boss"
        self.shake.shake(14)
        self.audio.play("boss_explode", 0.5)

    # ------------------------------------------------------------ помощники для боссов
    def spawn_enemy(self, x, y, etype="normal", behavior="dive"):
        hp, sp, fr = self._mults()
        if self.mode == "endless":
            hp *= 1.0 + 0.04 * self.wave_number
        self.enemies.append(Enemy(x, y, etype, behavior, hp_mult=hp, speed_mult=sp, fire_mult=fr))

    def banner(self, text, color=COLOR_WHITE, ms=1500, sub=""):
        self.banners.append({"text": text, "sub": sub, "color": color, "life": ms, "max": ms})

    def float_text(self, text, x, y, color=COLOR_WHITE, size=22, life=60):
        self.floating_texts.append({"text": text, "x": x, "y": y, "life": life,
                                    "max": life, "color": color, "size": size})

    # ============================================================ бомба
    def use_bomb(self):
        p = self.player
        if not p or p.bombs <= 0:
            return
        p.bombs -= 1
        self.audio.play("bomb", 1.0)
        self.shake.shake(20)
        self.flash = 1.0
        self.particles.shockwave(p.x, p.y, COLOR_WHITE, max(settings.SCREEN_WIDTH, 900), 40, 20)
        self.enemy_bullets = []
        for e in self.enemies[:]:
            self.particles.spawn_explosion(e.x, e.y, e.color, 12)
            if e.hit(6):
                self.on_enemy_killed(e)
        if self.boss:
            for _ in range(14):
                self.boss.hit(1)
        for h in self.hazards[:]:
            if isinstance(h, Mine):
                h.active = False

    # ============================================================ смерть врага
    def on_enemy_killed(self, e):
        self.kills += 1
        self.particles.spawn_explosion(e.x, e.y, e.color, 22)
        self.particles.spawn_sparks(e.x, e.y, COLOR_WHITE, 10)
        self.particles.spawn_smoke(e.x, e.y, e.color, 5)
        self.particles.spawn_debris(e.x, e.y, e.color, 5)
        self.audio.play("explode", 0.45)

        self.combo_count += 1
        self.best_combo = max(self.best_combo, self.combo_count)
        self.combo_timer = pygame.time.get_ticks()
        self.update_combo_multiplier()

        gain = int(e.score * self.combo_multiplier * self.config.difficulty["score"])
        self.player.score += gain
        self.float_text("+%d" % gain + (" x%.1f" % self.combo_multiplier if self.combo_multiplier > 1 else ""),
                        e.x, e.y, COLOR_YELLOW if self.combo_multiplier == 1 else COLOR_GOLD, 22)
        self.shake.shake(4)

        if random.random() < self.config.difficulty["drop"]:
            self.powerups.append(PowerUp(e.x, e.y, PowerUp.random_type()))

    def update_combo_multiplier(self):
        self.combo_multiplier = 1.0
        for threshold, mult in sorted(COMBO_MULTIPLIERS.items()):
            if self.combo_count >= threshold:
                self.combo_multiplier = mult

    def break_combo(self):
        self.combo_count = 0
        self.combo_multiplier = 1.0

    # ============================================================ коллизии
    def handle_collisions(self):
        p = self.player

        # пули игрока -> враги
        for b in self.bullets[:]:
            hit_something = False
            for e in self.enemies[:]:
                if id(e) in b.hit_ids:
                    continue
                if math.hypot(b.x - e.x, b.y - e.y) < b.radius + e.radius:
                    self.particles.spawn_hit(b.x, b.y, COLOR_YELLOW, 4)
                    if e.hit(b.damage):
                        self.on_enemy_killed(e)
                    else:
                        self.audio.play("hit", 0.18)
                    b.hit_ids.add(id(e))
                    hit_something = True
                    break
            if hit_something:
                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.active = False
                continue

            if self.boss and self.boss.state == "fighting" and self.boss.collide_point(b.x, b.y):
                self.particles.spawn_hit(b.x, b.y, COLOR_YELLOW, 4)
                if self.boss.hit(b.damage):
                    self.on_boss_defeated()
                else:
                    self.audio.play("hit", 0.12)
                if b.pierce > 0:
                    b.pierce -= 1
                else:
                    b.active = False

        self.enemies = [e for e in self.enemies if e.active]

        if p is None or self.state != "playing":
            return

        # вражеские снаряды -> игрок
        for eb in self.enemy_bullets[:]:
            if math.hypot(eb.x - p.x, eb.y - p.y) < eb.radius + p.radius * 0.8:
                eb.active = False
                self.particles.spawn_explosion(eb.x, eb.y, eb.color, 10)
                self.damage_player()

        # враги -> игрок
        for e in self.enemies[:]:
            if math.hypot(e.x - p.x, e.y - p.y) < e.radius + p.radius * 0.85:
                self.particles.spawn_explosion(e.x, e.y, e.color, 24)
                e.active = False
                self.damage_player()

        # босс -> игрок
        if self.boss and self.boss.state == "fighting" and self.boss.collide_point(p.x, p.y, pad=-20):
            self.damage_player()

        # хазарды
        for h in self.hazards:
            if h.touches(p):
                self.damage_player()
            if h.slows(p):
                p.slow_factor = 0.42

        # бонусы
        for pu in self.powerups[:]:
            if math.hypot(pu.x - p.x, pu.y - p.y) < pu.radius + p.radius:
                text = pu.apply(p)
                pu.active = False
                self.audio.play("life" if pu.type == "life" else "powerup", 0.7)
                self.particles.spawn_explosion(pu.x, pu.y, pu.data["color"], 12)
                self.particles.spawn_sparks(pu.x, pu.y, COLOR_WHITE, 8)
                self.shake.shake(3)
                self.float_text(text, pu.x, pu.y - 20, pu.data["color"], 20, 50)

        self.enemies = [e for e in self.enemies if e.active]

    def damage_player(self):
        p = self.player
        if p.invulnerable:
            return
        was_shield = p.shielded
        dead = p.hit()
        self.break_combo()
        self.shake.shake(12)
        self.flash = 0.55
        self.audio.play("hurt", 0.9)
        self.particles.spawn_ring(p.x, p.y, COLOR_CYAN if was_shield else COLOR_RED, 20, 7)
        if not was_shield:
            self.run_deaths += 1
        if dead:
            self.on_game_over()

    # ============================================================ исходы
    def on_boss_defeated(self):
        self.audio.play("boss_explode", 1.0)
        self.particles.big_explosion(self.boss.x, self.boss.y, self.boss.COLOR)
        self.shake.shake(28)
        self.flash = 0.9
        bonus = int(self.boss.SCORE * self.config.difficulty["score"])
        self.player.score += bonus
        self.float_text("БОСС ПОВЕРЖЕН +%d" % bonus, settings.SCREEN_WIDTH // 2,
                        settings.SCREEN_HEIGHT // 2, COLOR_GOLD, 44, 150)
        for _ in range(3):
            self.powerups.append(PowerUp(self.boss.x + random.uniform(-120, 120),
                                         self.boss.y, random.choice(["weapon", "life", "shield", "bomb"])))

    def on_level_cleared(self):
        stars = campaign.stars_for(self.run_deaths, len(self.level["waves"]))
        bonus = 5000 * stars
        self.player.score += bonus
        self.config.complete_level(self.level_id, stars, self.player.score)
        self.result = {"stars": stars, "score": self.player.score, "bonus": bonus,
                       "deaths": self.run_deaths, "kills": self.kills, "combo": self.best_combo}
        last = self.level_id >= campaign.count()
        self.state = "victory" if last else "level_complete"
        pygame.mouse.set_visible(True)
        self.build_result_buttons(last)

    def on_game_over(self):
        self.state = "gameover"
        pygame.mouse.set_visible(True)
        self.particles.big_explosion(self.player.x, self.player.y, COLOR_CYAN)
        self.shake.shake(24)
        if self.mode == "endless":
            self.config.record_endless(self.player.score, self.wave_number)
        self.result = {"score": self.player.score, "wave": self.wave_number,
                       "kills": self.kills, "combo": self.best_combo}
        self.build_result_buttons(False, gameover=True)

    def build_result_buttons(self, last, gameover=False):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        y = int(H * 0.72)
        bw, bh = 300, 70
        self.result_buttons = []
        if gameover:
            self.result_buttons.append(Button(W // 2 - bw - 20, y, bw, bh, "ЗАНОВО", (60, 140, 90), 30, value="retry"))
            self.result_buttons.append(Button(W // 2 + 20, y, bw, bh, "В МЕНЮ", (80, 90, 120), 30, value="menu"))
        elif last:
            self.result_buttons.append(Button(W // 2 - bw // 2, y, bw, bh, "В МЕНЮ", (80, 90, 120), 30, value="menu"))
        else:
            self.result_buttons.append(Button(W // 2 - bw - 20, y, bw, bh, "ДАЛЬШЕ", (60, 140, 90), 30, value="next"))
            self.result_buttons.append(Button(W // 2 + 20, y, bw, bh, "В МЕНЮ", (80, 90, 120), 30, value="menu"))

    def go_menu(self):
        self.state = "main"
        self.menus.build("main")
        self.background.set_theme((60, 90, 200))
        self.boss = None
        self.enemies = []
        self.enemy_bullets = []
        self.hazards = []
        self.bullets = []
        pygame.mouse.set_visible(True)

    # ============================================================ обновление
    def update(self):
        dt = 1000.0 / FPS
        self.background.update()
        self.particles.update()
        self.shake.update()
        if self.flash > 0:
            self.flash = max(0.0, self.flash - 0.06)

        for b in self.banners[:]:
            b["life"] -= dt
            if b["life"] <= 0:
                self.banners.remove(b)
        for ft in self.floating_texts[:]:
            ft["y"] -= 1
            ft["life"] -= 1
            if ft["life"] <= 0:
                self.floating_texts.remove(ft)

        if self.state in MENU_STATES:
            self.menus.update(pygame.mouse.get_pos())
            self.background.speed_mult = 0.5
            return
        self.background.speed_mult = 1.0

        if self.state in ("gameover", "level_complete", "victory"):
            for b in self.result_buttons:
                b.update(pygame.mouse.get_pos())
            return
        if self.state == "paused":
            for b in self.pause_buttons:
                b.update(pygame.mouse.get_pos())
            return
        if self.state == "briefing":
            self.phase_timer += dt
            return
        if self.state != "playing":
            return

        # ---------------------------------------------------- игрок
        keys = pygame.key.get_pressed()
        self.player.focus = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        self.player.update(keys)
        self.bullets.extend(self.player.shoot())
        if self.player.drone:
            self.player.drone.update()
            self.bullets.extend(self.player.drone.shoot())

        if self.combo_count > 0 and pygame.time.get_ticks() - self.combo_timer > COMBO_TIMEOUT:
            self.break_combo()

        # ---------------------------------------------------- снаряды
        for b in self.bullets[:]:
            b.update(self.enemies)
            if not b.active:
                self.bullets.remove(b)
        for eb in self.enemy_bullets[:]:
            eb.update(self.player)
            if not eb.active:
                self.enemy_bullets.remove(eb)

        # ---------------------------------------------------- враги
        for e in self.enemies[:]:
            shots = e.update(self.player)
            if shots:
                self.enemy_bullets.extend(shots)
            if e.etype in ("normal", "heavy", "scout") and random.random() < 0.0022:
                self.enemy_bullets.append(EnemyBullet(e.x, e.y + 10, 0, 5.4, "egg", COLOR_WHITE, 9))
            if not e.active:
                self.enemies.remove(e)

        for pu in self.powerups[:]:
            pu.update(self.player)
            if not pu.active:
                self.powerups.remove(pu)

        for h in self.hazards[:]:
            h.update(self, self.player)
            if not h.active:
                self.hazards.remove(h)

        if self.boss:
            self.boss.update(self.player)
            if not self.boss.active:
                self.boss = None
                if self.mode == "campaign":
                    self.on_level_cleared()
                    return
                self.phase = "intermission"
                self.phase_timer = 0.0

        self.handle_collisions()
        self.update_flow(dt)

    # ------------------------------------------------------------ режиссура
    def update_flow(self, dt):
        self.phase_timer += dt

        if self.phase == "spawning":
            self.director.update(dt)
            if self.director.done_spawning:
                self.phase = "clearing"

        elif self.phase == "clearing":
            mines = any(isinstance(h, Mine) for h in self.hazards)
            if not self.enemies and not mines:
                bonus = int((80 * max(1, self.wave_number)) * self.combo_multiplier)
                self.player.score += bonus
                self.float_text("ВОЛНА ЗАЧИЩЕНА  +%d" % bonus, settings.SCREEN_WIDTH // 2,
                                settings.SCREEN_HEIGHT * 0.42, COLOR_GOLD, 38, 110)
                self.audio.play("select", 0.6)
                self.phase = "intermission"
                self.phase_timer = 0.0

        elif self.phase == "intermission":
            if self.phase_timer > WAVE_COOLDOWN:
                self.next_wave()

        elif self.phase == "warning":
            if self.phase_timer > BOSS_WARNING_TIME:
                self._spawn_boss()

    # ============================================================ отрисовка
    def draw(self):
        c = self.canvas
        c.fill(COLOR_BG)
        self.background.draw(c)

        if self.state in MENU_STATES:
            self.menus.draw(c)
        elif self.state == "briefing":
            self.draw_briefing(c)
        else:
            self.draw_world(c)
            self.particles.draw(c)
            if self.player:
                self.draw_hud(c)
            if self.state == "paused":
                self.draw_pause(c)
            elif self.state == "gameover":
                self.draw_gameover(c)
            elif self.state in ("level_complete", "victory"):
                self.draw_result(c)

        self.draw_banners(c)
        self.draw_floating(c)

        if self.state == "playing" and self.config.opt["control"] == "mouse":
            self.draw_crosshair(c)

        if self.flash > 0.01:
            f = pygame.Surface(c.get_size(), pygame.SRCALPHA)
            f.fill((255, 255, 255, int(150 * self.flash)))
            c.blit(f, (0, 0))

        if self.config.opt["show_fps"]:
            draw_text(c, "FPS %d" % int(self.clock.get_fps()), 20,
                      settings.SCREEN_WIDTH - 110, 12, (140, 220, 140), center=False)

        self.screen.fill((0, 0, 0))
        self.screen.blit(c, (int(self.shake.offset_x), int(self.shake.offset_y)))
        pygame.display.flip()

    def draw_world(self, s):
        for h in self.hazards:
            if isinstance(h, (FrostZone, BlackHole)):
                h.draw(s)
        for pu in self.powerups:
            pu.draw(s)
        if self.boss:
            self.boss.draw(s)
        for e in self.enemies:
            e.draw(s)
        for h in self.hazards:
            if not isinstance(h, (FrostZone, BlackHole)):
                h.draw(s)
        if self.player:
            self.player.draw(s)
            if self.player.drone:
                self.player.drone.draw(s)
        for b in self.bullets:
            b.draw(s)
        for eb in self.enemy_bullets:
            eb.draw(s)

    # ------------------------------------------------------------ HUD
    def draw_hud(self, s):
        p = self.player
        x, y = 30, 26
        draw_text(s, "%08d" % p.score, 34, x, y, COLOR_YELLOW, center=False, shadow=True)

        y += 46
        for i in range(min(8, p.lives)):
            pygame.draw.polygon(s, COLOR_GREEN, [(x + i * 26 + 10, y),
                                                 (x + i * 26, y + 20),
                                                 (x + i * 26 + 10, y + 15),
                                                 (x + i * 26 + 20, y + 20)])
        if p.lives > 8:
            draw_text(s, "x%d" % p.lives, 20, x + 8 * 26 + 6, y, COLOR_GREEN, center=False)

        y += 34
        if self.mode == "campaign" and self.level:
            draw_text(s, "%s" % self.level["name"], 20, x, y, self.level["theme"], center=False)
            y += 28
            draw_text(s, "ВОЛНА %d / %d" % (self.wave_index, len(self.level["waves"])),
                      22, x, y, COLOR_CYAN, center=False)
        else:
            draw_text(s, "ВОЛНА %d" % self.wave_number, 24, x, y, COLOR_CYAN, center=False)
        y += 32

        draw_text(s, "ОРУЖИЕ", 18, x, y, (150, 160, 185), center=False)
        draw_progress_bar(s, x + 90, y + 2, 150, 14, p.weapon.level / float(p.weapon.MAX_LEVEL),
                          COLOR_ORANGE, (40, 40, 50), (90, 90, 110), 1)
        draw_text(s, "%d/%d" % (p.weapon.level, p.weapon.MAX_LEVEL), 18, x + 250, y, COLOR_ORANGE, center=False)
        y += 26

        if p.drone:
            draw_text(s, "ДРОН", 18, x, y, (150, 160, 185), center=False)
            draw_progress_bar(s, x + 90, y + 2, 150, 14, p.drone.level / float(p.drone.MAX_LEVEL),
                              COLOR_GREEN, (40, 40, 50), (90, 90, 110), 1)
            y += 26

        draw_text(s, "БОМБЫ", 18, x, y, (150, 160, 185), center=False)
        for i in range(p.bombs):
            pygame.draw.circle(s, COLOR_PINK, (x + 100 + i * 24, y + 9), 8)
            pygame.draw.circle(s, COLOR_WHITE, (x + 100 + i * 24, y + 9), 8, 2)
        if p.bombs == 0:
            draw_text(s, "нет", 18, x + 96, y, (110, 110, 125), center=False)

        if self.combo_count >= 2:
            txt = "%dx COMBO" % self.combo_count
            if self.combo_multiplier > 1:
                txt += "  x%.1f" % self.combo_multiplier
            draw_text(s, txt, 34, settings.SCREEN_WIDTH // 2, settings.SCREEN_HEIGHT - 70,
                      COLOR_GOLD, glow=True, glow_color=COLOR_ORANGE)

        if self.boss:
            self.boss.draw_bar(s)

        if p.shielded:
            left = (p.shield_until - pygame.time.get_ticks()) / float(SHIELD_TIME)
            draw_progress_bar(s, settings.SCREEN_WIDTH - 260, 30, 220, 12, left, COLOR_CYAN,
                              (30, 40, 50), (90, 140, 170), 1)
            draw_text(s, "ЩИТ", 18, settings.SCREEN_WIDTH - 260, 46, COLOR_CYAN, center=False)

    def draw_crosshair(self, s):
        mx, my = pygame.mouse.get_pos()
        col = COLOR_PINK if (self.player and self.player.focus) else COLOR_GREEN
        pygame.draw.line(s, col, (mx - 16, my), (mx + 16, my), 2)
        pygame.draw.line(s, col, (mx, my - 16), (mx, my + 16), 2)
        pygame.draw.circle(s, col, (mx, my), 10, 1)

    def draw_banners(self, s):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        y = int(H * 0.22)
        for b in self.banners:
            k = b["life"] / float(b["max"])
            alpha = int(255 * min(1.0, k * 3))
            draw_text(s, b["text"], 62, W // 2, y, b["color"], glow=True,
                      glow_color=b["color"], alpha=alpha)
            if b["sub"]:
                draw_text(s, b["sub"], 28, W // 2, y + 52, COLOR_WHITE, alpha=alpha)
            y += 110

    def draw_floating(self, s):
        for ft in self.floating_texts:
            alpha = int(255 * min(1.0, ft["life"] / float(max(1, ft["max"])) * 3))
            draw_text(s, ft["text"], ft["size"], int(ft["x"]), int(ft["y"]), ft["color"], alpha=alpha)

    # ------------------------------------------------------------ экраны
    def draw_briefing(self, s):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        lv = self.level
        panel = pygame.Rect(int(W * 0.2), int(H * 0.22), int(W * 0.6), int(H * 0.5))
        draw_panel(s, panel, (12, 16, 30), 220, lv["theme"], 20, 3)
        draw_text(s, lv["name"], 52, W // 2, panel.top + 60, lv["theme"], glow=True, glow_color=lv["theme"])
        draw_text(s, lv["subtitle"], 26, W // 2, panel.top + 106, (180, 190, 210))
        y = panel.top + 180
        for line in lv["briefing"]:
            draw_text(s, line, 28, W // 2, y, COLOR_WHITE)
            y += 44
        from boss import get_boss
        draw_text(s, "БОСС СЕКТОРА: %s" % get_boss(lv["boss"]).NAME, 30, W // 2,
                  panel.bottom - 110, COLOR_RED)
        blink = (pygame.time.get_ticks() // 500) % 2 == 0
        if blink:
            draw_text(s, "ПРОБЕЛ / ENTER — в бой      ESC — назад", 26, W // 2,
                      panel.bottom - 50, COLOR_GOLD)

    def draw_pause(self, s):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 185))
        s.blit(ov, (0, 0))
        draw_text(s, "ПАУЗА", 78, W // 2, int(H * 0.26), COLOR_WHITE, glow=True, glow_color=COLOR_CYAN)
        for b in self.pause_buttons:
            b.draw(s)
        draw_text(s, "ESC — продолжить", 22, W // 2, int(H * 0.82), (140, 150, 175))

    def draw_gameover(self, s):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((10, 0, 0, 200))
        s.blit(ov, (0, 0))
        draw_text(s, "GAME OVER", 96, W // 2, int(H * 0.26), COLOR_RED, glow=True, glow_color=(120, 0, 0))
        r = self.result
        draw_text(s, "Счёт: %d" % r.get("score", 0), 40, W // 2, int(H * 0.40), COLOR_WHITE)
        draw_text(s, "Волна: %d   ·   Убито: %d   ·   Лучшее комбо: %d" %
                  (r.get("wave", 0), r.get("kills", 0), r.get("combo", 0)),
                  26, W // 2, int(H * 0.47), (180, 190, 210))
        if self.mode == "endless":
            p = self.config.progress
            draw_text(s, "Рекорд: %d очков, волна %d" %
                      (p.get("endless_best_score", 0), p.get("endless_best_wave", 0)),
                      24, W // 2, int(H * 0.54), COLOR_GOLD)
        for b in self.result_buttons:
            b.draw(s)

    def draw_result(self, s):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 5, 15, 205))
        s.blit(ov, (0, 0))
        win = self.state == "victory"
        title = "КАМПАНИЯ ПРОЙДЕНА" if win else "СЕКТОР ЗАЧИЩЕН"
        draw_text(s, title, 82, W // 2, int(H * 0.20), COLOR_GOLD, glow=True, glow_color=COLOR_ORANGE)

        r = self.result
        for i in range(3):
            col = COLOR_GOLD if i < r.get("stars", 0) else (60, 60, 72)
            self.menus._star(s, W // 2 - 90 + i * 90, int(H * 0.34), 38, col)

        draw_text(s, "Счёт: %d   (бонус за звёзды +%d)" % (r.get("score", 0), r.get("bonus", 0)),
                  32, W // 2, int(H * 0.46), COLOR_WHITE)
        draw_text(s, "Потерь: %d   ·   Убито: %d   ·   Лучшее комбо: %d" %
                  (r.get("deaths", 0), r.get("kills", 0), r.get("combo", 0)),
                  26, W // 2, int(H * 0.53), (180, 190, 210))
        if win:
            draw_text(s, "Омега-Клюв повержен. Галактика снова безопасна... пока что.",
                      26, W // 2, int(H * 0.60), COLOR_CYAN)
        for b in self.result_buttons:
            b.draw(s)

    # ============================================================ ввод
    def build_pause_buttons(self):
        W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        bw, bh = 380, 74
        x = W // 2 - bw // 2
        y = int(H * 0.40)
        self.pause_buttons = [
            Button(x, y, bw, bh, "ПРОДОЛЖИТЬ", (60, 140, 90), 32, value="resume"),
            Button(x, y + 96, bw, bh, "ЗАНОВО", (70, 100, 160), 32, value="retry"),
            Button(x, y + 192, bw, bh, "В ГЛАВНОЕ МЕНЮ", (80, 90, 120), 32, value="menu"),
            Button(x, y + 288, bw, bh, "ВЫХОД ИЗ ИГРЫ", (170, 55, 55), 32, value="quit"),
        ]

    def toggle_pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.build_pause_buttons()
            pygame.mouse.set_visible(True)
        elif self.state == "paused":
            self.state = "playing"
            pygame.mouse.set_visible(False)

    def restart_run(self):
        if self.mode == "campaign":
            self.start_campaign_level(self.level_id)
            self.begin_run()
        else:
            self.start_endless()

    def handle_menu_action(self, action):
        if action is None:
            return
        if action == "campaign":
            self.state = "campaign"
            self.menus.build("campaign")
        elif action == "endless":
            self.start_endless()
        elif action == "settings":
            self.state = "settings"
            self.menus.build("settings")
        elif action == "help":
            self.state = "help"
            self.menus.build("help")
        elif action == "quit":
            self.running = False
        elif action == "back":
            nxt = "main" if self.menus.state in ("campaign", "settings") else "settings"
            self.state = nxt
            self.menus.build(nxt)
        elif action.startswith("level:"):
            self.start_campaign_level(int(action.split(":")[1]))
        elif action.startswith("opt+:"):
            self.menus.change_option(action.split(":")[1], 1)
        elif action.startswith("opt-:"):
            self.menus.change_option(action.split(":")[1], -1)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN:
            self.on_key(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state in MENU_STATES:
                self.handle_menu_action(self.menus.click(pos))
            elif self.state == "paused":
                for b in self.pause_buttons:
                    if b.hit(pos):
                        self.audio.play("click", 0.6)
                        if b.value == "resume":
                            self.toggle_pause()
                        elif b.value == "retry":
                            self.restart_run()
                        elif b.value == "menu":
                            self.go_menu()
                        elif b.value == "quit":
                            self.running = False
            elif self.state in ("gameover", "level_complete", "victory"):
                for b in self.result_buttons:
                    if b.hit(pos):
                        self.audio.play("click", 0.6)
                        if b.value == "retry":
                            self.restart_run()
                        elif b.value == "menu":
                            self.go_menu()
                        elif b.value == "next":
                            self.start_campaign_level(min(campaign.count(), self.level_id + 1))
            elif self.state == "briefing":
                self.begin_run()

    def on_key(self, event):
        k = event.key

        if self.state in MENU_STATES:
            if k == pygame.K_ESCAPE:
                if self.menus.state == "main":
                    self.running = False
                else:
                    self.handle_menu_action("back")
            elif self.menus.state == "main":
                if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.handle_menu_action("campaign")
                elif k == pygame.K_e:
                    self.handle_menu_action("endless")
                elif k == pygame.K_s:
                    self.handle_menu_action("settings")
            return

        if self.state == "briefing":
            if k == pygame.K_ESCAPE:
                self.state = "campaign"
                self.menus.build("campaign")
            elif k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.begin_run()
            return

        if self.state in ("playing", "paused"):
            if k == pygame.K_ESCAPE:
                self.toggle_pause()
            elif self.state == "playing" and k == pygame.K_SPACE:
                self.use_bomb()
            elif self.state == "playing" and k == pygame.K_F1:
                self.config.opt["show_fps"] = not self.config.opt["show_fps"]
            return

        if self.state == "gameover":
            if k == pygame.K_r:
                self.restart_run()
            elif k == pygame.K_ESCAPE:
                self.go_menu()
            return

        if self.state in ("level_complete", "victory"):
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                if self.state == "level_complete":
                    self.start_campaign_level(min(campaign.count(), self.level_id + 1))
                else:
                    self.go_menu()
            elif k == pygame.K_ESCAPE:
                self.go_menu()

    # ============================================================ главный цикл
    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            self.update()
            self.draw()
            self.clock.tick(FPS)

        self.config.save()
        pygame.quit()
