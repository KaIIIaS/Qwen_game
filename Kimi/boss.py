"""Боссы: пять уникальных противников с фазами и наборами атак.

Атаки написаны как генераторы: `yield N` означает «подождать N кадров».
Это позволяет описывать многошаговые паттерны линейным кодом.
"""
import math
import random

import pygame

import settings
from settings import *
from bullet import EnemyBullet
from enemy import Enemy
from utils import load_sprite_fit, draw_text, draw_progress_bar, clamp, lerp_color, draw_glow


# ================================================================ опасные зоны
class Hazard:
    active = True

    def update(self, game, player):
        pass

    def draw(self, surface):
        pass

    def touches(self, player):
        return False

    def slows(self, player):
        return False


class Beam(Hazard):
    """Вертикальный луч: сначала подсветка (безопасно), потом урон."""

    def __init__(self, x, width=70, telegraph=900, duration=1100, color=COLOR_CYAN, vx=0.0):
        self.x = float(x)
        self.width = width
        self.telegraph = telegraph
        self.duration = duration
        self.color = color
        self.vx = vx
        self.t = 0
        self.active = True

    @property
    def firing(self):
        return self.t >= self.telegraph

    def update(self, game, player):
        self.t += 1000.0 / FPS
        self.x += self.vx
        if self.t > self.telegraph + self.duration:
            self.active = False
        elif self.x < -200 or self.x > settings.SCREEN_WIDTH + 200:
            self.active = False

    def draw(self, surface):
        h = settings.SCREEN_HEIGHT
        if not self.firing:
            k = self.t / max(1.0, self.telegraph)
            w = max(2, int(6 + self.width * 0.15 * k))
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((self.color[0], self.color[1], self.color[2], int(60 + 80 * k)))
            surface.blit(s, (int(self.x - w / 2), 0))
        else:
            k = 1.0 - (self.t - self.telegraph) / max(1.0, self.duration)
            w = max(6, int(self.width * (0.65 + 0.35 * k)))
            s = pygame.Surface((w + 40, h), pygame.SRCALPHA)
            s.fill((self.color[0], self.color[1], self.color[2], 55))
            surface.blit(s, (int(self.x - w / 2 - 20), 0))
            pygame.draw.rect(surface, self.color, (int(self.x - w / 2), 0, w, h))
            pygame.draw.rect(surface, COLOR_WHITE, (int(self.x - w / 6), 0, max(2, w // 3), h))

    def touches(self, player):
        return self.firing and abs(player.x - self.x) < self.width / 2 + player.radius * 0.4


class FrostZone(Hazard):
    """Ледяное поле: замедляет игрока, урона нет."""

    def __init__(self, x, y, radius=190, duration=6500):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.t = 0
        self.active = True

    def update(self, game, player):
        self.t += 1000.0 / FPS
        self.y += 0.35
        if self.t > self.duration:
            self.active = False
        if random.random() < 0.4:
            a = random.uniform(0, math.pi * 2)
            r = random.uniform(0, self.radius)
            game.particles.spawn_snow(self.x + math.cos(a) * r, self.y + math.sin(a) * r, COLOR_ICE, 1)

    def draw(self, surface):
        k = clamp(1.0 - self.t / self.duration, 0, 1)
        r = int(self.radius)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (120, 200, 255, int(38 * k)), (r, r), r)
        pygame.draw.circle(s, (200, 240, 255, int(120 * k)), (r, r), r, 3)
        surface.blit(s, (int(self.x - r), int(self.y - r)))

    def slows(self, player):
        return math.hypot(player.x - self.x, player.y - self.y) < self.radius


class Mine(Hazard):
    """Яйцо-мина: падает, потом вылупляется во врага."""

    def __init__(self, x, y, hatch_type="normal", fall=2.6):
        self.x = x
        self.y = y
        self.fall = fall
        self.radius = 18
        self.hatch_type = hatch_type
        self.timer = random.randint(1600, 2600)
        self.active = True
        self.sprite = None
        self.spin = random.uniform(-4, 4)
        self.rot = 0

    def update(self, game, player):
        self.y += self.fall
        self.fall *= 0.985
        self.rot += self.spin
        self.timer -= 1000.0 / FPS
        if self.timer <= 0 or self.y > settings.SCREEN_HEIGHT * 0.72:
            self.active = False
            game.particles.spawn_explosion(self.x, self.y, COLOR_TOXIC, 16)
            game.spawn_enemy(self.x, self.y, self.hatch_type, behavior="kamikaze")

    def draw(self, surface):
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
        draw_glow(surface, self.x, self.y, 30, COLOR_TOXIC, int(30 + 50 * pulse))
        pygame.draw.ellipse(surface, (230, 250, 200),
                            (int(self.x - 14), int(self.y - 18), 28, 36))
        pygame.draw.ellipse(surface, lerp_color((90, 160, 40), COLOR_TOXIC, pulse),
                            (int(self.x - 14), int(self.y - 18), 28, 36), 3)

    def touches(self, player):
        return math.hypot(player.x - self.x, player.y - self.y) < self.radius + player.radius


class BlackHole(Hazard):
    """Тянет игрока к себе. Финальный босс."""

    def __init__(self, x, y, radius=420, duration=5000, power=0.85):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.power = power
        self.t = 0
        self.active = True

    def update(self, game, player):
        self.t += 1000.0 / FPS
        if self.t > self.duration:
            self.active = False
            return
        d = math.hypot(player.x - self.x, player.y - self.y)
        if 1 < d < self.radius:
            k = (1.0 - d / self.radius) * self.power
            player.x += (self.x - player.x) / d * k * 9
            player.y += (self.y - player.y) / d * k * 9

    def draw(self, surface):
        k = clamp(1.0 - self.t / self.duration, 0, 1)
        r = int(self.radius)
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(7):
            rr = int(r * (i + 1) / 7.0)
            pygame.draw.circle(s, (150, 40, 220, int(9 * k)), (r, r), rr)
        surface.blit(s, (int(self.x - r), int(self.y - r)))
        core = 42 + int(math.sin(pygame.time.get_ticks() * 0.01) * 6)
        pygame.draw.circle(surface, (12, 0, 24), (int(self.x), int(self.y)), core)
        pygame.draw.circle(surface, COLOR_PURPLE, (int(self.x), int(self.y)), core, 4)


# ================================================================ базовый босс
class Boss:
    NAME = "БОСС"
    TITLE = ""
    SPRITE = "enemy_boss"
    BASE_HP = 420
    WIDTH = 420
    HEIGHT = 300
    COLOR = COLOR_RED
    SCORE = 12000
    PHASE_COUNT = 3

    def __init__(self, game, hp_mult=1.0, fire_mult=1.0, speed_mult=1.0):
        self.game = game
        self.max_hp = max(60, int(self.BASE_HP * hp_mult))
        self.hp = self.max_hp
        self.fire_mult = fire_mult
        self.speed_mult = speed_mult

        self.sprite = load_sprite_fit(self.SPRITE, self.WIDTH, self.HEIGHT)
        if self.sprite:
            self.w, self.h = self.sprite.get_size()
        else:
            self.w, self.h = self.WIDTH, self.HEIGHT
        self.radius = int(min(self.w, self.h) * 0.42)

        self.x = settings.SCREEN_WIDTH / 2.0
        self.y = -self.h
        self.home_y = max(190, settings.SCREEN_HEIGHT * 0.22)
        self.move_target = [self.x, self.home_y]
        self.state = "entering"
        self.phase = 1
        self.active = True
        self.hit_flash = 0
        self.invuln = 0
        self.death_t = 0
        self.bob = random.uniform(0, math.pi * 2)

        self.routine = None
        self.wait = 0
        self.cooldown = 900
        self.last_attack = None
        self.spawned_score = False

    # ------------------------------------------------------------ утилиты
    @staticmethod
    def _w(ms):
        return max(1, int(ms / 1000.0 * FPS))

    def attacks_for_phase(self):
        return []

    def collide_point(self, x, y, pad=0):
        dx = (x - self.x) / max(1.0, (self.w * 0.42 + pad))
        dy = (y - self.y) / max(1.0, (self.h * 0.42 + pad))
        return dx * dx + dy * dy <= 1.0

    # ------------------------------------------------------------ стрельба
    def shoot(self, x, y, angle, speed, btype="orb", color=None, radius=10, **kw):
        self.game.enemy_bullets.append(
            EnemyBullet(x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                        btype, color or self.COLOR, radius, **kw))

    def fire_radial(self, count, speed, offset=0.0, btype="orb", color=None, radius=10, y_off=0):
        for i in range(count):
            a = math.pi * 2 * i / count + offset
            self.shoot(self.x, self.y + y_off, a, speed, btype, color, radius)

    def fire_arc(self, count, speed, center_angle, spread, btype="orb", color=None, radius=10, x=None, y=None):
        x = self.x if x is None else x
        y = self.y if y is None else y
        if count == 1:
            self.shoot(x, y, center_angle, speed, btype, color, radius)
            return
        for i in range(count):
            a = center_angle - spread / 2 + spread * i / (count - 1)
            self.shoot(x, y, a, speed, btype, color, radius)

    def aim(self, x=None, y=None):
        p = self.game.player
        x = self.x if x is None else x
        y = self.y if y is None else y
        if p is None:
            return math.pi / 2
        return math.atan2(p.y - y, p.x - x)

    def summon(self, etype, count, behavior="dive", spread=520):
        for i in range(count):
            x = self.x + random.uniform(-spread, spread)
            x = clamp(x, 90, settings.SCREEN_WIDTH - 90)
            self.game.spawn_enemy(x, self.y + random.uniform(-40, 60), etype, behavior=behavior)

    def hazard(self, h):
        self.game.hazards.append(h)

    def move_to(self, x, y=None):
        self.move_target[0] = clamp(x, self.w * 0.45, settings.SCREEN_WIDTH - self.w * 0.45)
        if y is not None:
            self.move_target[1] = y

    # ------------------------------------------------------------ логика
    def hit(self, damage=1):
        if self.state != "fighting" or self.invuln > 0:
            return False
        self.hp -= damage
        self.hit_flash = 4
        if self.hp <= 0:
            self.hp = 0
            self.state = "dying"
            self.routine = None
            return True
        self._check_phase()
        return False

    def _check_phase(self):
        frac = self.hp / float(self.max_hp)
        want = 1
        for i in range(1, self.PHASE_COUNT):
            if frac <= 1.0 - i / float(self.PHASE_COUNT):
                want = i + 1
        if want > self.phase:
            self.phase = want
            self.on_phase_change()

    def on_phase_change(self):
        g = self.game
        self.routine = None
        self.invuln = 900
        self.cooldown = 800
        g.particles.big_explosion(self.x, self.y, self.COLOR)
        g.particles.shockwave(self.x, self.y, COLOR_WHITE, 620, 26, 14)
        g.shake.shake(16)
        g.audio.play("boss_explode", 0.6)
        g.banner("ФАЗА %d" % self.phase, self.COLOR, 1200)
        for i in range(26):
            self.shoot(self.x, self.y, math.pi * 2 * i / 26, 5.5, "orb", self.COLOR, 11)

    def update(self, player):
        dt = 1000.0 / FPS
        self.bob += 0.03
        if self.hit_flash > 0:
            self.hit_flash -= 1
        if self.invuln > 0:
            self.invuln -= dt

        if self.state == "entering":
            self.y += (self.home_y - self.y) * 0.05
            if abs(self.y - self.home_y) < 6:
                self.y = self.home_y
                self.state = "fighting"
            return

        if self.state == "dying":
            self.death_t += dt
            self.y += 0.35
            self.x += math.sin(self.death_t * 0.006) * 2.2
            if random.random() < 0.5:
                ex = self.x + random.uniform(-self.w * 0.4, self.w * 0.4)
                ey = self.y + random.uniform(-self.h * 0.35, self.h * 0.35)
                self.game.particles.spawn_explosion(ex, ey, self.COLOR, 14)
                self.game.particles.spawn_sparks(ex, ey, COLOR_WHITE, 6)
                self.game.shake.shake(5)
            if self.death_t > 2200:
                self.active = False
            return

        # плавное перемещение
        self.x += (self.move_target[0] - self.x) * 0.045 * self.speed_mult
        self.y += (self.move_target[1] - self.y) * 0.05
        self.y += math.sin(self.bob) * 0.6

        # выполнение атаки-генератора
        if self.routine is not None:
            self.wait -= 1
            if self.wait <= 0:
                try:
                    self.wait = next(self.routine)
                except StopIteration:
                    self.routine = None
                    self.wait = 0
        else:
            self.cooldown -= dt
            if self.cooldown <= 0:
                self._pick_attack()

    def _pick_attack(self):
        pool = self.attacks_for_phase()
        if not pool:
            self.cooldown = 1200
            return
        options = [a for a in pool if a[0] is not self.last_attack] or pool
        total = sum(a[2] for a in options)
        r = random.uniform(0, total)
        acc = 0
        chosen = options[-1]
        for a in options:
            acc += a[2]
            if r <= acc:
                chosen = a
                break
        func, cd, _ = chosen
        self.last_attack = func
        self.routine = func()
        self.wait = 1
        self.cooldown = cd / max(0.3, self.fire_mult) * (1.0 - 0.12 * (self.phase - 1))

    # ------------------------------------------------------------ отрисовка
    def draw(self, surface):
        sprite = self.sprite
        if self.state == "entering":
            pass
        if sprite:
            img = sprite
            if self.state == "dying":
                img = sprite.copy()
                img.fill((255, 200, 160), special_flags=pygame.BLEND_ADD)
            elif self.hit_flash > 0 and self.hit_flash % 2 == 0:
                img = sprite.copy()
                img.fill((90, 90, 90), special_flags=pygame.BLEND_ADD)
            elif self.invuln > 0 and (pygame.time.get_ticks() // 80) % 2 == 0:
                img = sprite.copy()
                img.fill((120, 120, 160), special_flags=pygame.BLEND_ADD)
            surface.blit(img, img.get_rect(center=(int(self.x), int(self.y))))
        else:
            pygame.draw.ellipse(surface, self.COLOR,
                                (int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h))
            pygame.draw.ellipse(surface, COLOR_WHITE,
                                (int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h), 4)

    def draw_bar(self, surface):
        if self.state == "entering":
            return
        w = int(settings.SCREEN_WIDTH * 0.56)
        x = (settings.SCREEN_WIDTH - w) // 2
        y = 26
        frac = self.hp / float(self.max_hp)
        col = lerp_color((255, 40, 40), (255, 200, 40), frac)
        draw_progress_bar(surface, x, y, w, 20, frac, col, (40, 12, 18), COLOR_WHITE, 2)
        for i in range(1, self.PHASE_COUNT):
            px = x + int(w * (i / float(self.PHASE_COUNT)))
            pygame.draw.line(surface, (10, 10, 15), (px, y), (px, y + 20), 3)
        draw_text(surface, self.NAME, 30, settings.SCREEN_WIDTH // 2, y - 4, COLOR_WHITE, shadow=True)
        if self.TITLE:
            draw_text(surface, self.TITLE, 18, settings.SCREEN_WIDTH // 2, y + 40, (190, 190, 210))


# ================================================================ 1. Военачальник
class BossWarlord(Boss):
    NAME = "ГЕНЕРАЛ КЛАК"
    TITLE = "Бронированный вожак стаи"
    SPRITE = "boss_warlord"
    BASE_HP = 460
    WIDTH = 520
    HEIGHT = 320
    COLOR = (255, 150, 60)
    SCORE = 12000

    def attacks_for_phase(self):
        pool = [(self.atk_gatling, 1500, 3), (self.atk_shotgun, 1400, 3), (self.atk_wall, 1800, 2)]
        if self.phase >= 2:
            pool.append((self.atk_summon, 2600, 2))
            pool.append((self.atk_strafe_run, 1600, 2))
        if self.phase >= 3:
            pool.append((self.atk_rotor, 2200, 3))
        return pool

    def atk_gatling(self):
        """Очереди попеременно из левой и правой турели."""
        for i in range(16):
            side = -1 if i % 2 == 0 else 1
            gx = self.x + side * self.w * 0.36
            gy = self.y + self.h * 0.05
            a = self.aim(gx, gy) + random.uniform(-0.07, 0.07)
            self.shoot(gx, gy, a, 9.5, "laser", (255, 210, 120), 7)
            self.game.audio.play("shoot", 0.25)
            yield self._w(70)

    def atk_shotgun(self):
        for _ in range(3):
            a = self.aim()
            self.fire_arc(9, 6.2, a, 1.15, "orb", self.COLOR, 11)
            self.game.audio.play("shoot_big", 0.4)
            yield self._w(420)

    def atk_wall(self):
        gap1 = random.randint(2, 5)
        gap2 = random.randint(8, 11)
        for row in range(2):
            for i in range(14):
                if i in (gap1, gap1 + 1, gap2, gap2 + 1):
                    continue
                x = 70 + i * (settings.SCREEN_WIDTH - 140) / 13.0
                self.game.enemy_bullets.append(
                    EnemyBullet(x, self.y - 20 - row * 60, 0, 5.4, "egg", COLOR_WHITE, 10))
            gap1 = (gap1 + 3) % 12
            yield self._w(650)

    def atk_summon(self):
        self.game.banner("ПОДКРЕПЛЕНИЕ!", self.COLOR, 900)
        for _ in range(3):
            self.summon("heavy", 1, "dive", 420)
            self.summon("scout", 2, "zigzag", 500)
            yield self._w(420)

    def atk_strafe_run(self):
        target = random.choice([settings.SCREEN_WIDTH * 0.22, settings.SCREEN_WIDTH * 0.78])
        self.move_to(target)
        for _ in range(18):
            self.fire_arc(3, 6.0, math.pi / 2, 0.5, "orb", self.COLOR, 9)
            yield self._w(120)
        self.move_to(settings.SCREEN_WIDTH / 2)

    def atk_rotor(self):
        off = 0.0
        for _ in range(56):
            self.shoot(self.x, self.y, off, 5.6, "orb", (255, 190, 90), 9)
            self.shoot(self.x, self.y, -off + math.pi, 5.6, "orb", (255, 120, 60), 9)
            off += 0.31
            yield self._w(45)


# ================================================================ 2. Матка
class BossBroodmother(Boss):
    NAME = "МАТЬ-НАСЕДКА"
    TITLE = "Она никогда не перестаёт нестись"
    SPRITE = "boss_broodmother"
    BASE_HP = 620
    WIDTH = 460
    HEIGHT = 360
    COLOR = COLOR_TOXIC
    SCORE = 18000

    def attacks_for_phase(self):
        pool = [(self.atk_mines, 2200, 3), (self.atk_slime_radial, 1500, 3), (self.atk_spray, 1700, 2)]
        if self.phase >= 2:
            pool.append((self.atk_swarm, 2800, 3))
        if self.phase >= 3:
            pool.append((self.atk_deluge, 2400, 3))
        return pool

    def atk_mines(self):
        for _ in range(5):
            x = clamp(self.x + random.uniform(-450, 450), 90, settings.SCREEN_WIDTH - 90)
            self.hazard(Mine(x, self.y + 40, random.choice(["normal", "scout", "kamikaze"])))
            self.game.audio.play("shoot_big", 0.3)
            yield self._w(280)

    def atk_slime_radial(self):
        for w in range(4):
            self.fire_radial(18 + w * 2, 4.6 + w * 0.35, offset=w * 0.17,
                             btype="orb", color=COLOR_TOXIC, radius=11, y_off=40)
            self.game.audio.play("shoot", 0.3)
            yield self._w(340)

    def atk_spray(self):
        a = math.pi / 2 - 0.9
        for _ in range(30):
            self.shoot(self.x, self.y + 50, a, 6.4, "orb", (190, 255, 120), 9)
            a += 0.06
            yield self._w(45)

    def atk_swarm(self):
        self.game.banner("ВЫВОДОК!", COLOR_TOXIC, 900)
        for _ in range(4):
            self.summon("scout", 3, random.choice(["zigzag", "swoop"]), 620)
            yield self._w(340)

    def atk_deluge(self):
        """Ливень яиц по всей ширине + добивающий радиальный залп."""
        for step in range(14):
            for i in range(9):
                x = random.uniform(60, settings.SCREEN_WIDTH - 60)
                self.game.enemy_bullets.append(
                    EnemyBullet(x, -20, random.uniform(-0.8, 0.8), random.uniform(5.0, 7.4),
                                "egg", COLOR_WHITE, 9))
            yield self._w(180)
        self.fire_radial(30, 5.2, 0.0, "orb", COLOR_TOXIC, 12, y_off=40)
        yield self._w(200)


# ================================================================ 3. Хромированный петух
class BossChrome(Boss):
    NAME = "ХРОМ-РУСТЕР MK-III"
    TITLE = "Боевая машина корпорации «Птицепром»"
    SPRITE = "boss_chrome"
    BASE_HP = 720
    WIDTH = 430
    HEIGHT = 400
    COLOR = COLOR_STEEL
    SCORE = 24000

    def attacks_for_phase(self):
        pool = [(self.atk_lasers, 2000, 3), (self.atk_missiles, 1700, 3), (self.atk_dash, 1900, 2)]
        if self.phase >= 2:
            pool.append((self.atk_escorts, 2800, 2))
            pool.append((self.atk_sweep, 2400, 3))
        if self.phase >= 3:
            pool.append((self.atk_grid, 2600, 3))
        return pool

    def atk_lasers(self):
        for _ in range(3):
            x = random.uniform(settings.SCREEN_WIDTH * 0.15, settings.SCREEN_WIDTH * 0.85)
            self.hazard(Beam(x, 80, 850, 750, COLOR_CYAN))
            self.game.audio.play("warning", 0.35)
            yield self._w(520)

    def atk_sweep(self):
        self.game.audio.play("laser", 0.5)
        d = random.choice((-1, 1))
        start = settings.SCREEN_WIDTH * (0.85 if d < 0 else 0.15)
        self.hazard(Beam(start, 90, 1000, 2600, (120, 240, 255), vx=d * 7.5))
        yield self._w(1200)

    def atk_missiles(self):
        for i in range(6):
            side = -1 if i % 2 == 0 else 1
            gx = self.x + side * self.w * 0.34
            a = self.aim(gx, self.y)
            self.game.enemy_bullets.append(
                EnemyBullet(gx, self.y, math.cos(a) * 4.2, math.sin(a) * 4.2,
                            "star", (255, 120, 80), 11, homing=0.035, accel=0.006))
            self.game.audio.play("shoot", 0.28)
            yield self._w(170)

    def atk_dash(self):
        for target in (settings.SCREEN_WIDTH * 0.2, settings.SCREEN_WIDTH * 0.8):
            self.move_to(target)
            for _ in range(10):
                self.fire_arc(2, 7.5, math.pi / 2, 0.35, "laser", COLOR_CYAN, 7)
                yield self._w(110)
        self.move_to(settings.SCREEN_WIDTH / 2)
        yield self._w(300)

    def atk_escorts(self):
        self.game.banner("ЗАПУСК ДРОНОВ", COLOR_CYAN, 900)
        for _ in range(2):
            self.summon("shielded", 2, "hold", 480)
            yield self._w(500)

    def atk_grid(self):
        """Сетка лучей: сначала вертикали, затем плотный веер."""
        xs = [settings.SCREEN_WIDTH * f for f in (0.18, 0.38, 0.62, 0.82)]
        random.shuffle(xs)
        for x in xs:
            self.hazard(Beam(x, 70, 800, 900, (150, 255, 255)))
            yield self._w(260)
        yield self._w(700)
        for k in range(3):
            self.fire_arc(15, 6.0, math.pi / 2, 2.2, "laser", COLOR_CYAN, 6)
            yield self._w(300)


# ================================================================ 4. Ледяная наседка
class BossFrost(Boss):
    NAME = "ЛЕДЯНАЯ НАСЕДКА"
    TITLE = "Дыхание абсолютного нуля"
    SPRITE = "boss_frost"
    BASE_HP = 860
    WIDTH = 800
    HEIGHT = 380
    COLOR = COLOR_ICE
    SCORE = 30000

    def attacks_for_phase(self):
        pool = [(self.atk_spiral, 2100, 3), (self.atk_hail, 1900, 3), (self.atk_zones, 2600, 2)]
        if self.phase >= 2:
            pool.append((self.atk_shatter, 2200, 3))
            pool.append((self.atk_flock, 2600, 2))
        if self.phase >= 3:
            pool.append((self.atk_blizzard, 2800, 4))
        return pool

    def atk_spiral(self):
        a = random.uniform(0, math.pi * 2)
        d = random.choice((-1, 1))
        for _ in range(60):
            for arm in range(3):
                self.shoot(self.x, self.y + 30, a + arm * math.pi * 2 / 3, 5.4, "shard", COLOR_ICE, 9)
            a += 0.19 * d
            yield self._w(48)

    def atk_hail(self):
        for _ in range(16):
            for _ in range(4):
                x = random.uniform(50, settings.SCREEN_WIDTH - 50)
                self.game.enemy_bullets.append(
                    EnemyBullet(x, -20, random.uniform(-1.2, 1.2), random.uniform(6.5, 9.0),
                                "shard", (190, 235, 255), 8))
            yield self._w(150)

    def atk_zones(self):
        self.game.banner("ЛЕДЯНОЕ ПОЛЕ", COLOR_ICE, 900)
        for _ in range(3):
            x = random.uniform(240, settings.SCREEN_WIDTH - 240)
            y = random.uniform(settings.SCREEN_HEIGHT * 0.45, settings.SCREEN_HEIGHT * 0.8)
            self.hazard(FrostZone(x, y, random.randint(160, 230)))
            yield self._w(420)

    def atk_shatter(self):
        for w in range(3):
            self.game.particles.shockwave(self.x, self.y, COLOR_ICE, 380, 18, 8)
            self.game.audio.play("explode", 0.4)
            self.fire_radial(26 + w * 6, 5.0 + w * 0.5, offset=w * 0.12, btype="shard",
                             color=(210, 245, 255), radius=9)
            yield self._w(620)

    def atk_flock(self):
        for _ in range(3):
            self.summon("scout", 3, "strafe", 700)
            yield self._w(420)

    def atk_blizzard(self):
        """Метель: медленная стена осколков с узкими проходами."""
        self.game.banner("МЕТЕЛЬ!", COLOR_ICE, 1100)
        for row in range(7):
            gap = random.randint(1, 12)
            for i in range(14):
                if abs(i - gap) <= 1:
                    continue
                x = 60 + i * (settings.SCREEN_WIDTH - 120) / 13.0
                self.game.enemy_bullets.append(
                    EnemyBullet(x, -20, 0, 4.2, "shard", (170, 225, 255), 9))
            yield self._w(560)


# ================================================================ 5. Омега
class BossOmega(Boss):
    NAME = "ОМЕГА-КЛЮВ"
    TITLE = "Пожиратель галактик. Последний бой"
    SPRITE = "boss_omega"
    BASE_HP = 1300
    WIDTH = 640
    HEIGHT = 380
    COLOR = COLOR_PURPLE
    SCORE = 60000
    PHASE_COUNT = 4

    def attacks_for_phase(self):
        pool = [(self.atk_bullet_hell, 2100, 3), (self.atk_eye_lasers, 2000, 3),
                (self.atk_halo, 1900, 3)]
        if self.phase >= 2:
            pool.append((self.atk_summon_all, 2800, 2))
            pool.append((self.atk_black_hole, 3000, 2))
        if self.phase >= 3:
            pool.append((self.atk_cross, 2400, 3))
        if self.phase >= 4:
            pool.append((self.atk_finale, 2600, 5))
        return pool

    def atk_bullet_hell(self):
        a = 0.0
        for _ in range(70):
            for arm in range(5):
                self.shoot(self.x, self.y + 20, a + arm * math.pi * 2 / 5, 4.8,
                           "orb", (200, 120, 255), 9)
                self.shoot(self.x, self.y + 20, -a + arm * math.pi * 2 / 5, 4.8,
                           "orb", (255, 200, 120), 9)
            a += 0.16
            yield self._w(52)

    def atk_eye_lasers(self):
        for _ in range(3):
            a = self.aim()
            for k in range(3):
                self.fire_arc(3, 11.0, a, 0.22, "laser", (255, 120, 255), 7)
                yield self._w(90)
            yield self._w(420)

    def atk_halo(self):
        for ring in range(5):
            n = 30
            hole = random.randint(0, n - 1)
            for i in range(n):
                if abs(i - hole) <= 1 or abs(i - hole) >= n - 1:
                    continue
                self.shoot(self.x, self.y, math.pi * 2 * i / n, 4.4 + ring * 0.25,
                           "star", COLOR_GOLD, 9)
            self.game.audio.play("shoot_big", 0.3)
            yield self._w(520)

    def atk_summon_all(self):
        self.game.banner("ЛЕГИОН!", COLOR_PURPLE, 1000)
        for etype, beh in (("kamikaze", "kamikaze"), ("shooter", "hold"),
                           ("scout", "swoop"), ("gunner", "hold")):
            self.summon(etype, 2, beh, 640)
            yield self._w(420)

    def atk_black_hole(self):
        self.game.banner("СИНГУЛЯРНОСТЬ", (200, 100, 255), 1200)
        bx = random.uniform(settings.SCREEN_WIDTH * 0.3, settings.SCREEN_WIDTH * 0.7)
        by = settings.SCREEN_HEIGHT * 0.62
        self.hazard(BlackHole(bx, by))
        for _ in range(16):
            self.fire_radial(12, 5.4, offset=random.uniform(0, 1), btype="orb",
                             color=(160, 90, 255), radius=8)
            yield self._w(280)

    def atk_cross(self):
        xs = [settings.SCREEN_WIDTH * f for f in (0.25, 0.5, 0.75)]
        for x in xs:
            self.hazard(Beam(x, 90, 750, 1000, (230, 130, 255)))
        yield self._w(900)
        for _ in range(10):
            self.fire_radial(16, 6.2, offset=random.uniform(0, 0.4), btype="orb",
                             color=COLOR_GOLD, radius=9)
            yield self._w(220)

    def atk_finale(self):
        """Всё сразу: спираль, лучи, подкрепления, стена."""
        self.game.banner("ОМЕГА-ПРОТОКОЛ", COLOR_GOLD, 1400)
        self.hazard(Beam(settings.SCREEN_WIDTH * 0.3, 80, 900, 2600, (255, 120, 255), vx=4.0))
        self.hazard(Beam(settings.SCREEN_WIDTH * 0.7, 80, 900, 2600, (255, 120, 255), vx=-4.0))
        a = 0.0
        for step in range(50):
            for arm in range(6):
                self.shoot(self.x, self.y, a + arm * math.pi / 3, 5.0, "orb",
                           (255, 160, 240), 9)
            a += 0.21
            if step % 14 == 0:
                self.summon("kamikaze", 2, "kamikaze", 600)
            yield self._w(60)



class BossSpider(Boss):
    NAME = "ПАУК-НАСЕДКА"; TITLE = "Восемь ног, один ужас"; SPRITE = "boss_spider"; BASE_HP = 980; WIDTH = 520; HEIGHT = 430; COLOR = (220,70,180); SCORE = 38000
    def attacks_for_phase(self):
        return [(self.atk_web,1800,3),(self.atk_eggs,2000,3),(self.atk_radial,1700,2)] + ([(self.atk_summon,2500,2)] if self.phase>=2 else [])
    def atk_web(self):
        for x in (settings.SCREEN_WIDTH*.25,settings.SCREEN_WIDTH*.5,settings.SCREEN_WIDTH*.75):
            self.hazard(Beam(x,55,700,900,self.COLOR)); yield self._w(340)
    def atk_eggs(self):
        for _ in range(18):
            a=self.aim()+random.uniform(-.35,.35); self.shoot(self.x,self.y,a,5.4,'orb',self.COLOR,10); yield self._w(90)
    def atk_radial(self):
        for _ in range(5): self.fire_radial(22,5.1,random.random(),'orb',self.COLOR,10); yield self._w(300)
    def atk_summon(self):
        self.summon('kamikaze',8,'kamikaze',600); yield self._w(500)

class BossVolcano(Boss):
    NAME = "ВУЛКАНИЧЕСКИЙ РОКЕР"; TITLE = "Сердце из лавы"; SPRITE = "boss_volcano"; BASE_HP = 1100; WIDTH = 650; HEIGHT = 360; COLOR = (255,100,30); SCORE = 46000
    def attacks_for_phase(self):
        return [(self.atk_magma,1800,3),(self.atk_ring,1900,3),(self.atk_beam,2200,2)] + ([(self.atk_eruption,2700,3)] if self.phase>=2 else [])
    def atk_magma(self):
        for _ in range(24):
            a=self.aim()+random.uniform(-.6,.6); self.shoot(self.x,self.y,a,6.4,'orb',self.COLOR,11); yield self._w(75)
    def atk_ring(self):
        for i in range(4): self.fire_radial(20+i*4,4.8+i*.3,i*.2,'orb',(255,190,50),10); yield self._w(350)
    def atk_beam(self):
        self.hazard(Beam(random.uniform(100,settings.SCREEN_WIDTH-100),100,800,1400,self.COLOR)); yield self._w(900)
    def atk_eruption(self):
        self.game.banner('ИЗВЕРЖЕНИЕ!',self.COLOR,1000); self.fire_radial(36,6.3,0,'orb',(255,220,70),11); yield self._w(600)

# ================================================================ реестр
BOSS_LIST = [BossWarlord, BossBroodmother, BossChrome, BossFrost, BossOmega, BossSpider, BossVolcano]
BOSSES = {
    "warlord": BossWarlord,
    "broodmother": BossBroodmother,
    "chrome": BossChrome,
    "frost": BossFrost,
    "omega": BossOmega,
    "spider": BossSpider,
    "volcano": BossVolcano,
}


def get_boss(key):
    return BOSSES.get(key, BossWarlord)
