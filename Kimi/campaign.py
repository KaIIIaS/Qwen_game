"""Кампания: 5 секторов, в каждом ручные волны и свой босс."""
import settings
from wave import squad

S = settings


def _w(name, *squads):
    return {"name": name, "squads": list(squads)}


LEVELS = [
    # ------------------------------------------------------------ 1
    {
        "id": 1,
        "name": "СЕКТОР I — КУРЯТНИК",
        "subtitle": "Первое столкновение",
        "theme": (70, 110, 220),
        "briefing": [
            "Разведка нашла передовой отряд у пояса астероидов.",
            "Птицы ещё не ждут атаки. Прорвись через строй",
            "и уничтожь их вожака — Генерала Клака.",
        ],
        "boss": "warlord",
        "waves": [
            _w("РАЗВЕДКА",
               squad("normal", 7, "line", "dive", 0)),
            _w("СТРОЙ",
               squad("normal", 10, "grid", "hold", 0, topf=0.20),
               squad("scout", 4, "column", "zigzag", 3200)),
            _w("КЛИН",
               squad("normal", 9, "vee", "dive", 0),
               squad("scout", 6, "pincer", "swoop", 2400)),
            _w("ТЯЖЁЛАЯ ПОСТУПЬ",
               squad("heavy", 4, "line", "dive", 0),
               squad("normal", 8, "arc", "hold", 2600)),
            _w("КАРУСЕЛЬ",
               squad("scout", 8, "circle", "orbit", 0, orbit_r=230),
               squad("normal", 6, "scatter", "swoop", 3000)),
            _w("ПЕРЕД БУРЕЙ",
               squad("heavy", 3, "vee", "dive", 0),
               squad("scout", 8, "sides", "strafe", 1800),
               squad("normal", 10, "line", "dive", 4200)),
        ],
    },
    # ------------------------------------------------------------ 2
    {
        "id": 2,
        "name": "СЕКТОР II — ИНКУБАТОР",
        "subtitle": "Гнездо роя",
        "theme": (70, 190, 90),
        "briefing": [
            "Здесь они размножаются. Токсичная слизь, мины-яйца",
            "и бесконечный молодняк. Не дай себя окружить.",
            "Цель — Мать-Наседка.",
        ],
        "boss": "broodmother",
        "waves": [
            _w("МОЛОДНЯК",
               squad("scout", 10, "line", "zigzag", 0),
               squad("normal", 6, "scatter", "dive", 2400)),
            _w("СТРЕЛКИ",
               squad("shooter", 6, "grid", "hold", 0, topf=0.18),
               squad("scout", 6, "pincer", "swoop", 2800)),
            _w("ПЕРВЫЕ КАМИКАДЗЕ",
               squad("kamikaze", 6, "scatter", "kamikaze", 0),
               squad("normal", 8, "arc", "hold", 2600)),
            _w("ДВОЙНОЕ КОЛЬЦО",
               squad("scout", 9, "circle", "orbit", 0, orbit_r=260),
               squad("shooter", 5, "circle", "orbit", 2200, orbit_r=140),
               squad("kamikaze", 4, "column", "kamikaze", 4600)),
            _w("ОСАДА",
               squad("heavy", 5, "line", "hold", 0),
               squad("shooter", 4, "sides", "strafe", 2000),
               squad("scout", 10, "scatter", "swoop", 4200)),
            _w("ВЫВОДОК",
               squad("scout", 14, "grid", "dive", 0),
               squad("kamikaze", 6, "line", "kamikaze", 2600),
               squad("heavy", 4, "vee", "dive", 5200)),
        ],
    },
    # ------------------------------------------------------------ 3
    {
        "id": 3,
        "name": "СЕКТОР III — ВЕРФЬ",
        "subtitle": "Механизированная оборона",
        "theme": (150, 175, 200),
        "briefing": [
            "Куры научились строить машины. Плохие новости.",
            "Щиты, лазеры и дроны сопровождения.",
            "Разбери Хром-Растера на запчасти.",
        ],
        "boss": "chrome",
        "waves": [
            _w("ПАТРУЛЬ",
               squad("shielded", 4, "line", "hold", 0),
               squad("scout", 8, "sides", "strafe", 2200)),
            _w("ОГНЕВАЯ ТОЧКА",
               squad("gunner", 3, "arc", "hold", 0),
               squad("normal", 10, "grid", "dive", 2600)),
            _w("КОНВЕЙЕР",
               squad("heavy", 6, "column", "dive", 0, xf=0.3),
               squad("heavy", 6, "column", "dive", 900, xf=0.7),
               squad("kamikaze", 6, "scatter", "kamikaze", 3600)),
            _w("ЩИТОВОЙ СТРОЙ",
               squad("shielded", 6, "grid", "hold", 0),
               squad("shooter", 6, "circle", "orbit", 2600, orbit_r=250)),
            _w("ПЕРЕГРУЗКА",
               squad("gunner", 4, "line", "hold", 0),
               squad("scout", 12, "pincer", "swoop", 2000),
               squad("shielded", 4, "vee", "dive", 4400)),
            _w("ТАНКОВЫЙ КЛИН",
               squad("tank", 2, "line", "hold", 0),
               squad("heavy", 6, "arc", "dive", 2400),
               squad("kamikaze", 8, "scatter", "kamikaze", 5000)),
        ],
    },
    # ------------------------------------------------------------ 4
    {
        "id": 4,
        "name": "СЕКТОР IV — ЛЕДНИК",
        "subtitle": "Замёрзшая колония",
        "theme": (90, 175, 235),
        "briefing": [
            "Минус двести за бортом. Двигатели вязнут,",
            "а местные обитатели отлично видят в темноте.",
            "Растопи Ледяную Наседку.",
        ],
        "boss": "frost",
        "waves": [
            _w("ПОЗЁМКА",
               squad("scout", 12, "line", "zigzag", 0),
               squad("shooter", 5, "arc", "hold", 2400)),
            _w("ЛЕДЯНОЙ ВАЛ",
               squad("shielded", 6, "wall", "dive", 0),
               squad("gunner", 3, "line", "hold", 2600)),
            _w("ЗАСАДА",
               squad("kamikaze", 10, "pincer", "kamikaze", 0),
               squad("heavy", 6, "grid", "hold", 2800)),
            _w("ВИХРЬ",
               squad("scout", 10, "circle", "orbit", 0, orbit_r=290),
               squad("scout", 8, "circle", "orbit", 1600, orbit_r=170),
               squad("shooter", 6, "sides", "strafe", 4000)),
            _w("ТЯЖЁЛЫЙ ЛЁД",
               squad("tank", 2, "vee", "hold", 0),
               squad("shielded", 6, "arc", "dive", 2400),
               squad("scout", 12, "scatter", "swoop", 4800)),
            _w("БУРАН",
               squad("gunner", 5, "grid", "hold", 0),
               squad("kamikaze", 10, "line", "kamikaze", 2200),
               squad("heavy", 8, "wall", "dive", 4600),
               squad("shooter", 6, "circle", "orbit", 7000, orbit_r=220)),
        ],
    },
    # ------------------------------------------------------------ 5
    {
        "id": 5,
        "name": "СЕКТОР V — ЯДРО",
        "subtitle": "Финал",
        "theme": (170, 80, 235),
        "briefing": [
            "Дальше только Омега-Клюв. То, ради чего всё затевалось.",
            "Четыре фазы, никаких пауз, никаких вторых шансов.",
            "Удачи, пилот.",
        ],
        "boss": "omega",
        "waves": [
            _w("СТРАЖИ",
               squad("shielded", 6, "line", "hold", 0),
               squad("gunner", 4, "arc", "hold", 2200),
               squad("scout", 10, "pincer", "swoop", 4200)),
            _w("ОРБИТАЛЬНАЯ ОБОРОНА",
               squad("shooter", 10, "circle", "orbit", 0, orbit_r=300),
               squad("kamikaze", 8, "scatter", "kamikaze", 2600),
               squad("heavy", 6, "vee", "dive", 5000)),
            _w("БРОНЕКУЛАК",
               squad("tank", 3, "line", "hold", 0),
               squad("shielded", 8, "grid", "dive", 2600),
               squad("scout", 14, "sides", "strafe", 5200)),
            _w("ПОСЛЕДНИЙ РУБЕЖ",
               squad("gunner", 6, "grid", "hold", 0),
               squad("kamikaze", 12, "line", "kamikaze", 2200),
               squad("tank", 2, "vee", "dive", 4600),
               squad("shooter", 8, "circle", "orbit", 6800, orbit_r=240)),
        ],
    },
]



LEVELS.extend([
 {"id":6,"name":"СЕКТОР VI — ПАУТИНА","subtitle":"Гнездо в пустоте","theme":(190,60,160),"briefing":["Сигнал идёт из мёртвого кармана космоса.","Там что-то плетёт ловушку.","Разорви сеть и уничтожь Паук-Наседку."],"boss":"spider","waves":LEVELS[1]["waves"]},
 {"id":7,"name":"СЕКТОР VII — ВУЛКАН","subtitle":"Последний жар","theme":(220,70,30),"briefing":["Ядро звезды стало оружием.","Больше никаких отступлений.","Погаси Вулканического Рокера."],"boss":"volcano","waves":LEVELS[2]["waves"]},
])

LEVELS.extend([
 {"id":8,"name":"СЕКТОР VIII — ШТОРМ","subtitle":"Электрический рой","theme":(40,150,220),"briefing":["Пространство разорвано молниями.","Стая научилась управлять бурей.","Уничтожь Штормовую Мат​​ку."],"boss":"storm","waves":LEVELS[0]["waves"]},
 {"id":9,"name":"СЕКТОР IX — ОСАДА","subtitle":"Последняя крепость","theme":(220,90,45),"briefing":["Флот собрал всё тяжёлое оружие.","Пройди через огневой коридор.","Сломай Осадного Колосса."],"boss":"siege","waves":LEVELS[2]["waves"]},
 {"id":10,"name":"СЕКТОР X — ЛУНА","subtitle":"Тёмная сторона","theme":(100,70,190),"briefing":["Сигнал идёт с обратной стороны луны.","Там ждёт последний командир.","Заверши войну с Лунным Клаком."],"boss":"moon","waves":LEVELS[4]["waves"]},
])

BY_ID = {lv["id"]: lv for lv in LEVELS}


def get_level(level_id):
    return BY_ID.get(level_id, LEVELS[0])


def count():
    return len(LEVELS)


def stars_for(deaths, waves_total):
    """3 звезды — без потерь, 2 — одна потеря, 1 — прошёл."""
    if deaths <= 0:
        return 3
    if deaths <= 2:
        return 2
    return 1
