"""Глобальные константы игры.

ВАЖНО: SCREEN_WIDTH / SCREEN_HEIGHT переопределяются в Game.__init__ под
реальное разрешение монитора. Поэтому в коде всегда обращайтесь к ним как
`settings.SCREEN_WIDTH`, а не через `from settings import *`.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SAVE_PATH = os.path.join(BASE_DIR, "savegame.json")

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
TITLE = "Chicken Invaders — Galactic Campaign"

# ---------------------------------------------------------------- цвета
COLOR_BG = (5, 5, 15)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_RED = (255, 60, 60)
COLOR_GREEN = (60, 255, 100)
COLOR_ORANGE = (255, 140, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_GRAY = (150, 150, 150)
COLOR_DARK = (22, 24, 38)
COLOR_PURPLE = (180, 50, 255)
COLOR_ICE = (100, 200, 255)
COLOR_ELECTRIC = (220, 120, 255)
COLOR_BOSS_HP = (255, 40, 40)
COLOR_GOLD = (255, 215, 0)
COLOR_PINK = (255, 100, 200)
COLOR_TOXIC = (150, 255, 60)
COLOR_STEEL = (200, 215, 230)

# ---------------------------------------------------------------- игрок
PLAYER_SPEED = 0.15          # коэффициент притяжения к курсору
PLAYER_KEY_SPEED = 11.0      # px/кадр в режиме клавиатуры
PLAYER_SIZE = 44
PLAYER_LIVES = 3
PLAYER_INVULNERABLE_TIME = 2000
PLAYER_FOCUS_FACTOR = 0.38   # замедление при удержании SHIFT
BOMB_START = 2
BOMB_MAX = 5
SHIELD_TIME = 8000

BULLET_SPEED = 14
BULLET_COOLDOWN = 160

ENEMY_SPAWN_MARGIN = 90
WAVE_COOLDOWN = 1400
WAVE_BANNER_TIME = 2200

POWERUP_SPEED = 3
POWERUP_LIFETIME = 9000
MAGNET_RADIUS = 260

DRONE_OFFSET = 80
DRONE_COOLDOWN_BASE = 400
BOSS_WARNING_TIME = 2600

# ---------------------------------------------------------------- эффекты
SCREEN_SHAKE_DECAY = 0.85
SCREEN_SHAKE_INTENSITY = 8
COMBO_TIMEOUT = 2000
COMBO_MULTIPLIERS = {5: 1.5, 10: 2.0, 15: 2.5, 20: 3.0, 30: 4.0, 50: 5.0}
TRAIL_LENGTH = 12
GLOW_RADIUS = 40

# ---------------------------------------------------------------- сложность
DIFFICULTIES = {
    "easy":   {"name": "ЛЁГКО",     "hp": 0.70, "speed": 0.85, "fire": 0.65, "lives": 5, "drop": 0.22, "score": 0.8},
    "normal": {"name": "НОРМАЛЬНО", "hp": 1.00, "speed": 1.00, "fire": 1.00, "lives": 3, "drop": 0.15, "score": 1.0},
    "hard":   {"name": "СЛОЖНО",    "hp": 1.35, "speed": 1.15, "fire": 1.35, "lives": 2, "drop": 0.11, "score": 1.4},
    "insane": {"name": "БЕЗУМИЕ",   "hp": 1.85, "speed": 1.30, "fire": 1.75, "lives": 1, "drop": 0.09, "score": 2.2},
}
DIFFICULTY_ORDER = ["easy", "normal", "hard", "insane"]
