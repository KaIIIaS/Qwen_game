"""Генератор волн: построения, состав, режиссура боя.

Раньше волна была одна и та же: N кур падают сверху синусоидой.
Теперь волна — это набор «отрядов» (squads), у каждого своё построение,
поведение, тип врага и задержка появления.
"""
import math
import random

import settings
from enemy import Enemy

FORMATIONS = ("line", "grid", "vee", "arc", "column", "sides", "scatter", "circle", "pincer", "wall")


def squad(etype="normal", count=6, formation="line", behavior="dive", delay=0, **params):
    return {"type": etype, "count": count, "formation": formation,
            "behavior": behavior, "delay": delay, "params": params}


# ---------------------------------------------------------------- построения
def _slots(formation, count, params):
    """Возвращает список (start_x, start_y, slot_x, slot_y, extra_params)."""
    W = settings.SCREEN_WIDTH
    H = settings.SCREEN_HEIGHT
    margin = settings.ENEMY_SPAWN_MARGIN
    top = params.get("top", H * params.get("topf", 0.20))
    out = []

    if formation == "line":
        for i in range(count):
            fx = margin + (W - margin * 2) * (i + 0.5) / count
            out.append((fx, -90 - i * 12, fx, top, {}))

    elif formation == "grid":
        cols = params.get("cols", min(8, max(3, int(math.ceil(math.sqrt(count * 1.8))))))
        rows = int(math.ceil(count / float(cols)))
        gw = min(W - margin * 2, cols * 150)
        for i in range(count):
            r, c = divmod(i, cols)
            fx = W / 2 - gw / 2 + gw * (c + 0.5) / cols
            fy = top + r * 110
            out.append((fx, -100 - r * 90, fx, fy, {}))

    elif formation == "vee":
        half = count // 2
        for i in range(count):
            k = i - half
            fx = W / 2 + k * 120
            fy = top + abs(k) * 55
            out.append((fx, -90 - abs(k) * 30, fx, fy, {}))

    elif formation == "arc":
        for i in range(count):
            t = (i + 0.5) / count
            a = math.pi * (0.15 + 0.7 * t)
            fx = W / 2 - math.cos(a) * (W * 0.34)
            fy = top + math.sin(a) * 130
            out.append((fx, -90, fx, fy, {}))

    elif formation == "column":
        if "x" in params:
            cx = params["x"]
        elif "xf" in params:
            cx = W * params["xf"]
        else:
            cx = random.uniform(W * 0.2, W * 0.8)
        for i in range(count):
            out.append((cx, -80 - i * 130, cx, top + i * 20, {}))

    elif formation == "sides":
        for i in range(count):
            left = i % 2 == 0
            y = top + (i // 2) * 95
            sx = -90 if left else W + 90
            out.append((sx, y, sx, y, {"dir": 1 if left else -1}))

    elif formation == "pincer":
        for i in range(count):
            left = i % 2 == 0
            fx = margin + 60 + (i // 2) * 70 if left else W - margin - 60 - (i // 2) * 70
            out.append((-80 if left else W + 80, -60, fx, top + (i // 2) * 60, {}))

    elif formation == "circle":
        cx = params.get("cx", W / 2)
        cy = params.get("cy", top + 90)
        r = params.get("orbit_r", 220)
        for i in range(count):
            a = math.pi * 2 * i / max(1, count)
            out.append((cx + math.cos(a) * r, -80, cx + math.cos(a) * r, cy + math.sin(a) * r * 0.5,
                        {"center": (cx, cy), "angle": a, "orbit_r": r}))

    elif formation == "wall":
        for i in range(count):
            fx = margin + (W - margin * 2) * (i + 0.5) / count
            out.append((fx, -80, fx, top, {}))

    else:  # scatter
        for i in range(count):
            fx = random.uniform(margin, W - margin)
            out.append((fx, random.uniform(-260, -60), fx, top + random.uniform(-60, 120), {}))

    return out


def build_squad(spec, hp_mult=1.0, speed_mult=1.0, fire_mult=1.0):
    etype = spec["type"]
    count = max(1, int(spec["count"]))
    behavior = spec["behavior"]
    params = dict(spec.get("params", {}))
    slots = _slots(spec["formation"], count, params)

    enemies = []
    needs_slot = behavior in ("hold", "orbit", "strafe")
    for i, (sx, sy, fx, fy, extra) in enumerate(slots):
        p = dict(params)
        p.update(extra)
        e = Enemy(sx, sy, etype, behavior,
                  slot=(fx, fy) if needs_slot else None,
                  hp_mult=hp_mult, speed_mult=speed_mult, fire_mult=fire_mult,
                  phase=i * 0.6, params=p)
        if not needs_slot:
            e.base_x = fx
            e.x = fx if behavior != "sides" else sx
        enemies.append(e)
    return enemies


# ---------------------------------------------------------------- режиссёр
class WaveDirector:
    def __init__(self, game):
        self.game = game
        self.spec = None
        self.pending = []
        self.timer = 0.0
        self.spawned_any = False

    def start(self, spec, hp_mult=1.0, speed_mult=1.0, fire_mult=1.0):
        self.spec = spec
        self.hp_mult = hp_mult
        self.speed_mult = speed_mult
        self.fire_mult = fire_mult
        self.timer = 0.0
        self.spawned_any = False
        self.pending = sorted(spec.get("squads", []), key=lambda s: s.get("delay", 0))

    @property
    def name(self):
        return self.spec.get("name", "") if self.spec else ""

    @property
    def done_spawning(self):
        return not self.pending

    def update(self, dt):
        if not self.pending:
            return
        self.timer += dt
        while self.pending and self.pending[0].get("delay", 0) <= self.timer:
            s = self.pending.pop(0)
            self.game.enemies.extend(build_squad(s, self.hp_mult, self.speed_mult, self.fire_mult))
            self.spawned_any = True


# ---------------------------------------------------------------- бесконечный режим
_POOLS = [
    ["normal"],
    ["normal", "scout"],
    ["normal", "scout", "heavy"],
    ["normal", "scout", "heavy", "shooter"],
    ["scout", "heavy", "shooter", "kamikaze"],
    ["heavy", "shooter", "kamikaze", "gunner", "shielded"],
    ["shooter", "kamikaze", "gunner", "shielded", "tank"],
]

_BEHAVIOR_BY_TYPE = {
    "normal": ["dive", "hold", "swoop", "zigzag"],
    "scout": ["zigzag", "swoop", "strafe", "dive"],
    "heavy": ["dive", "hold", "orbit"],
    "shooter": ["hold", "orbit", "dive"],
    "gunner": ["hold", "orbit"],
    "kamikaze": ["kamikaze", "kamikaze", "zigzag"],
    "shielded": ["hold", "dive"],
    "tank": ["hold", "dive"],
}

_FORM_BY_BEHAVIOR = {
    "dive": ["line", "vee", "scatter", "arc", "wall"],
    "hold": ["grid", "line", "arc", "vee"],
    "orbit": ["circle"],
    "strafe": ["sides"],
    "kamikaze": ["scatter", "line", "column"],
    "swoop": ["line", "scatter", "pincer"],
    "zigzag": ["line", "scatter", "column", "pincer"],
}

MODIFIERS = [
    ("", None),
    ("РОЙ", "swarm"),
    ("ЭЛИТА", "elite"),
    ("КАМИКАДЗЕ", "suicide"),
    ("ОСАДА", "siege"),
]


def endless_wave(n):
    """Процедурная волна для бесконечного режима. n начинается с 1."""
    tier = min(len(_POOLS) - 1, (n - 1) // 3)
    pool = _POOLS[tier]
    budget = 5 + n * 1.7 + tier * 2

    mod_name, mod = random.choice(MODIFIERS) if n >= 4 else ("", None)
    if mod == "swarm":
        budget *= 1.6
    elif mod == "elite":
        budget *= 0.6

    squads = []
    delay = 0
    guard = 0
    while budget > 0 and guard < 6:
        guard += 1
        if mod == "suicide" and guard <= 2:
            etype = "kamikaze"
        elif mod == "elite":
            etype = random.choice([t for t in pool if t in ("heavy", "gunner", "shielded", "tank")] or pool)
        elif mod == "siege" and guard == 1:
            etype = "gunner" if "gunner" in pool else pool[-1]
        else:
            etype = random.choice(pool)

        behavior = random.choice(_BEHAVIOR_BY_TYPE.get(etype, ["dive"]))
        formation = random.choice(_FORM_BY_BEHAVIOR.get(behavior, ["line"]))
        cost = {"normal": 1.0, "scout": 1.0, "heavy": 2.2, "shooter": 1.8,
                "gunner": 3.0, "kamikaze": 1.4, "shielded": 3.2, "tank": 6.0}[etype]
        count = int(max(2, min(14, budget / cost / random.uniform(1.4, 2.6))))
        if etype == "tank":
            count = min(count, 2)
        budget -= count * cost

        squads.append(squad(etype, count, formation, behavior, delay,
                            topf=random.uniform(0.14, 0.30)))
        delay += random.randint(900, 2200)

    name = "ВОЛНА %d" % n
    if mod_name:
        name += "  •  " + mod_name
    return {"name": name, "squads": squads, "modifier": mod}
