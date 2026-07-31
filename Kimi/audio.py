"""Процедурный звук: синтезируем эффекты на лету, файлы не нужны.

Если numpy или микшер недоступны — всё молча выключается.
"""
import math
import random

import pygame
import settings

try:
    import numpy as np
except Exception:
    np = None

SAMPLE_RATE = 44100


def _envelope(n, attack=0.01, release=0.6):
    a = max(1, int(n * attack))
    r = max(1, int(n * release))
    env = np.ones(n, dtype=np.float32)
    env[:a] = np.linspace(0.0, 1.0, a)
    env[n - r:] = np.linspace(1.0, 0.0, r)
    return env


class Audio:
    def __init__(self, config):
        self.config = config
        self.ok = False
        self.sounds = {}
        if np is None:
            return
        try:
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.set_num_channels(32)
            self.ok = True
        except Exception:
            self.ok = False
            return
        self._build()
        self._load_assets()

    # ------------------------------------------------------------ синтез
    def _make(self, samples):
        samples = np.clip(samples, -1.0, 1.0)
        data = (samples * 32767).astype(np.int16)
        stereo = np.column_stack([data, data])
        return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))

    def _tone(self, f0, f1, dur, kind="sine", noise=0.0, attack=0.01, release=0.7):
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        freq = np.linspace(f0, f1, n)
        phase = np.cumsum(2 * math.pi * freq / SAMPLE_RATE)
        if kind == "sine":
            wave = np.sin(phase)
        elif kind == "square":
            wave = np.sign(np.sin(phase))
        elif kind == "saw":
            wave = 2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0
        else:
            wave = np.sin(phase)
        if noise > 0:
            wave = wave * (1 - noise) + np.random.uniform(-1, 1, n) * noise
        return self._make(wave * _envelope(n, attack, release) * 0.6)

    def _build(self):
        s = self.sounds
        s["shoot"] = self._tone(900, 380, 0.09, "square", 0.05, 0.005, 0.8)
        s["shoot_big"] = self._tone(420, 140, 0.16, "saw", 0.12, 0.005, 0.8)
        s["hit"] = self._tone(1400, 700, 0.05, "square", 0.35, 0.002, 0.9)
        s["explode"] = self._tone(300, 40, 0.42, "saw", 0.85, 0.004, 0.9)
        s["boss_explode"] = self._tone(180, 25, 1.1, "saw", 0.9, 0.01, 0.85)
        s["powerup"] = self._tone(500, 1500, 0.24, "sine", 0.0, 0.01, 0.6)
        s["life"] = self._tone(700, 1900, 0.35, "sine", 0.0, 0.01, 0.6)
        s["hurt"] = self._tone(260, 60, 0.35, "square", 0.4, 0.004, 0.85)
        s["warning"] = self._tone(680, 680, 0.35, "square", 0.0, 0.05, 0.4)
        s["click"] = self._tone(1200, 900, 0.05, "square", 0.0, 0.005, 0.8)
        s["select"] = self._tone(640, 1280, 0.14, "square", 0.0, 0.01, 0.7)
        s["bomb"] = self._tone(120, 900, 0.6, "saw", 0.5, 0.02, 0.7)
        s["wave"] = self._tone(420, 900, 0.3, "sine", 0.0, 0.02, 0.6)
        s["laser"] = self._tone(1700, 500, 0.3, "saw", 0.15, 0.01, 0.7)


    def _load_assets(self):
        import os
        for name in ("shoot","shoot_big","hit","explode","boss_explode","powerup","life","hurt","warning","click","select","bomb","wave","laser","coin"):
            path=os.path.join(settings.ASSETS_DIR,"sfx",name+".wav")
            if os.path.exists(path):
                try: self.sounds[name]=pygame.mixer.Sound(path)
                except Exception: pass

    # ------------------------------------------------------------ api
    def play(self, name, volume=1.0, pitch_jitter=True):
        if not self.ok:
            return
        snd = self.sounds.get(name)
        if snd is None:
            return
        vol = volume * float(self.config.get("master_volume", 0.7)) * float(self.config.get("sfx_volume", 0.8))
        if vol <= 0.005:
            return
        try:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(min(1.0, vol * (random.uniform(0.9, 1.1) if pitch_jitter else 1.0)))
                ch.play(snd)
        except Exception:
            pass
