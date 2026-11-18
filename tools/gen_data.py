"""Generate scripts/data.gd (wave data) from the GDD level design and verify counts/timing."""
import sys, random, json

OUT = sys.argv[1]
rng = random.Random(2026)
LANES = [300.0, 440.0, 580.0, 720.0, 860.0]
SPAWN_X = 1980.0
TRASH = {"sachet", "bag", "bottle", "styro", "sandal", "can", "tire", "ghostnet", "turtlenet", "flake"}


def ev(t, k, lane=None, **kw):
    e = {"t": round(float(t), 2), "k": k}
    if lane is not None:
        e["lane"] = lane
        e["y"] = LANES[lane]
    e.update(kw)
    if "x" not in e:
        e["x"] = SPAWN_X
    return e


def cluster(t, k, lane, n, gap=46):
    out = []
    for i in range(n):
        dy = [0, -34, 30, -14, 40, -40][i % 6]
        out.append(ev(t, k, lane, x=SPAWN_X + i * gap, y=LANES[lane] + dy))
    return out


def fish(t, lane, d=None):
    d = d if d is not None else rng.choice([-1, 1])
    return ev(t, "fish", lane, dir=d, x=SPAWN_X if d < 0 else -80.0)


def bubble(t):
    return ev(t, "bubble", None, x=float(rng.randint(760, 1560)), y=950.0)


def box(t):
    return ev(t, "box", None, x=float(rng.randint(820, 1500)), y=215.0)


def seq(t0, step, kinds, lanes):
    return [ev(t0 + i * step, k, lanes[i % len(lanes)]) for i, k in enumerate(kinds)]


def mixed(n, pool):
    return [pool[i % len(pool)] for i in range(n)]


SEGMENTS = {
    "1-1": {"name": "Muara", "stage": 1, "current": 60.0, "target": 0.60, "oxygen": 100.0, "total": 22},
    "1-2": {"name": "Kampung Tepi Sungai", "stage": 1, "current": 80.0, "target": 0.70, "oxygen": 100.0, "total": 37},
    "1-3": {"name": "Pintu Air Kota", "stage": 1, "current": 100.0, "target": 0.70, "oxygen": 100.0, "total": 44},
    "2-1": {"name": "Pesisir dan Bagan", "stage": 2, "current": 70.0, "target": 0.70, "oxygen": 100.0, "total": 40},
    "2-2": {"name": "Terumbu Pucat", "stage": 2, "current": 80.0, "target": 0.75, "oxygen": 100.0, "total": 38},
    "2-3": {"name": "Sarang Kraken", "stage": 2, "current": 60.0, "target": 1.0, "oxygen": 170.0, "total": 0},
}

W = {}
# ---- 1-1 Muara
W["1-1"] = [
    [ev(0, "bag", 3, x=1500.0, hold="tutorial"), ev(4, "bag", 4), ev(8, "bag", 3)],
    seq(0, 2.5, mixed(6, ["bag", "bottle"]), [1, 3, 0, 4, 2, 1]) + [fish(3.5, 2), bubble(5)],
    seq(0, 1.5, mixed(13, ["bag", "bottle", "sachet"]), [0, 2, 4, 1, 3]) + [fish(2.2, 3), fish(9.8, 0), bubble(7)],
]
# ---- 1-2 Kampung
W["1-2"] = [
    cluster(0, "sachet", 1, 5) + cluster(6, "sachet", 2, 5) + cluster(12, "sachet", 3, 5),
    [box(0)] + seq(0, 1.5, mixed(10, ["bag", "bottle", "styro", "sandal"]), [0, 2, 4, 1, 3]) +
    [ev(3, "wood", 1), ev(9, "wood", 3), fish(4.5, 4), fish(11, 0), bubble(6)],
    [box(0)] + cluster(0, "sachet", 1, 5) + cluster(7, "sachet", 3, 5) +
    [ev(3, "bottle", 0), ev(10, "bottle", 4), fish(0.6, 2, -1), fish(7.6, 4, -1), ev(5, "wood", 2), bubble(4)],
]
# ---- 1-3 Pintu Air Kota
W["1-3"] = [
    seq(0, 1.0, mixed(14, ["bag", "sachet", "bottle", "styro", "sandal", "bag", "sachet"]), [0, 3, 1, 4, 2]) +
    [fish(2.5, 3), fish(9.5, 1), bubble(6)],
    [box(0)] + seq(0, 1.0, mixed(14, ["bottle", "bag", "sandal", "sachet", "styro", "bag", "sachet"]), [2, 0, 3, 1, 4]) +
    [ev(1.5, "wood", 1), ev(5.5, "wood", 3), ev(9.5, "wood", 2), fish(3.5, 2), fish(11.5, 4), bubble(7)],
    [box(0), bubble(5)] + [ev(0, "tire", l, x=1500.0, hold="clog") for l in (1, 2, 3, 4)] +
    [ev(0, mixed(12, ["bag", "sachet", "bottle"])[i], 1 + i % 4, x=1640.0 + (i // 4) * 110.0,
        y=LANES[1 + i % 4] + [-30, 10, 34][i // 4], hold="clog_behind") for i in range(12)],
]
# ---- 2-1 Pesisir dan Bagan
W["2-1"] = [
    cluster(0, "can", 1, 4) + cluster(6, "can", 3, 4) + cluster(12, "can", 2, 4),
    [box(0)] + seq(0, 1.2, mixed(14, ["can", "bottle", "bag", "sachet"]), [0, 2, 4, 1, 3]) + [fish(3.0, 4), fish(10.2, 1), bubble(6)],
    [box(0)] + seq(0, 1.1, mixed(12, ["bag", "can", "sachet", "bottle"]), [3, 1, 4, 0, 2]) +
    [ev(5.0, "tire", 4), ev(10.5, "tire", 0), fish(1.65, 4), fish(6.6, 2), fish(12.6, 1), bubble(8)],
]
# ---- 2-2 Terumbu Pucat
w1 = []
pattern = ["bag", "bag", "jelly"] * 4
lanes = [1, 3, 2, 4, 0, 2, 1, 3, 4, 0, 2, 1]
for i, k in enumerate(pattern):
    w1.append(ev(i * 1.5, k, lanes[i]))
W["2-2"] = [
    w1,
    [box(0), ev(0, "turtlenet", 2, x=1800.0)] + seq(1.0, 1.2, mixed(13, ["bag", "bottle", "sachet", "can"]), [0, 4, 1, 3]) +
    [fish(3.0, 2), fish(11.0, 2), bubble(7)],
    [box(0)] + seq(0, 1.0, mixed(14, ["bag", "sachet", "bottle", "can"]), [1, 3, 0, 4, 2]) +
    [ev(4.5, "ghostnet", 2), ev(11.5, "ghostnet", 0), ev(2.5, "jelly", 0), ev(7.5, "jelly", 4), ev(13.5, "jelly", 3),
     fish(5.5, 1), fish(9.6, 4), bubble(8)],
]

# ---------------------------------------------------------------- fairness fix-up
def conflicts(wv, a, lane):
    return any(b["k"] in TRASH and b.get("lane") == lane and abs(b["t"] - a["t"]) < 1.0 for b in wv)


for sid, waves in W.items():
    for wv in waves:
        for a in wv:
            if a["k"] in ("fish", "jelly") and conflicts(wv, a, a["lane"]):
                for cand in [2, 1, 3, 0, 4]:
                    if not conflicts(wv, a, cand):
                        a["lane"] = cand; a["y"] = LANES[cand]
                        break
                else:
                    raise SystemExit(f"no safe lane {sid} {a}")
    # remove exact overlaps between a big item and another item spawned in the same lane at the same time
    for wv in waves:
        for i, a in enumerate(wv):
            for b in wv[i + 1:]:
                if a.get("lane") is not None and a.get("lane") == b.get("lane") and a["t"] == b["t"] and a["x"] == b["x"] and a.get("y") == b.get("y"):
                    b["t"] = round(b["t"] + 0.6, 2)

# ---------------------------------------------------------------- checks
for sid, waves in W.items():
    total = sum(1 for wv in waves for e in wv if e["k"] in TRASH)
    assert total == SEGMENTS[sid]["total"], (sid, total)
    spans = []
    for wi, wv in enumerate(waves):
        wv.sort(key=lambda e: e["t"])
        spans.append(max(e["t"] for e in wv))
        # fairness: creature and trash never in the same lane within 1 s
        for a in wv:
            if a["k"] in ("fish", "jelly"):
                for b in wv:
                    if b["k"] in TRASH and b.get("lane") == a.get("lane") and abs(b["t"] - a["t"]) < 1.0:
                        raise SystemExit(f"fairness {sid} w{wi} {a} {b}")
    worst = sum(spans) + 2 * (8 + 3)
    assert worst <= 75, (sid, spans, worst)
    print(sid, "trash", total, "spans", spans, "worst last spawn", worst)


def gd(v, ind=0):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(float(v)) if isinstance(v, float) else str(v)
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, dict):
        return "{" + ", ".join(f"{json.dumps(k)}: {gd(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(gd(x) for x in v) + "]"
    raise TypeError(v)


KINDS = {
    "sachet": {"cat": "trash", "w": 0, "metal": False, "pts": 10, "r": 26.0, "tex": ["trash_sachet_1", "trash_sachet_2", "trash_sachet_3"], "speed": 1.0, "amp": 8.0},
    "bag": {"cat": "trash", "w": 0, "metal": False, "pts": 10, "r": 40.0, "tex": ["trash_bag"], "speed": 1.0, "amp": 22.0},
    "bottle": {"cat": "trash", "w": 0, "metal": False, "pts": 15, "r": 34.0, "tex": ["trash_bottle"], "speed": 1.2, "amp": 8.0},
    "styro": {"cat": "trash", "w": 1, "metal": False, "pts": 20, "r": 40.0, "tex": ["trash_styro"], "speed": 1.0, "amp": 6.0},
    "sandal": {"cat": "trash", "w": 1, "metal": False, "pts": 20, "r": 38.0, "tex": ["trash_sandal"], "speed": 1.0, "amp": 8.0},
    "can": {"cat": "trash", "w": 1, "metal": True, "pts": 20, "r": 30.0, "tex": ["trash_can"], "speed": 1.0, "amp": 8.0},
    "tire": {"cat": "trash", "w": 2, "metal": False, "pts": 40, "r": 52.0, "tex": ["trash_tire"], "speed": 0.9, "amp": 4.0},
    "ghostnet": {"cat": "trash", "w": 2, "metal": False, "pts": 50, "r": 56.0, "tex": ["trash_ghostnet"], "speed": 0.9, "amp": 6.0},
    "turtlenet": {"cat": "trash", "w": 2, "metal": False, "pts": 50, "r": 56.0, "tex": ["trash_ghostnet"], "speed": 0.8, "amp": 6.0},
    "flake": {"cat": "trash", "w": 0, "metal": False, "pts": 5, "r": 16.0, "tex": ["trash_flake_1", "trash_flake_2"], "speed": 1.0, "amp": 3.0},
    "fish": {"cat": "creature", "w": 0, "metal": False, "pts": 0, "r": 34.0, "tex": ["fish_1", "fish_2", "fish_3"], "speed": 1.0, "amp": 10.0},
    "jelly": {"cat": "creature", "w": 0, "metal": False, "pts": 0, "r": 36.0, "tex": ["jelly"], "speed": 0.7, "amp": 24.0},
    "wood": {"cat": "obstacle", "w": 2, "metal": False, "pts": 0, "r": 80.0, "tex": ["wood"], "speed": 1.0, "amp": 4.0},
    "bubble": {"cat": "pickup", "w": 0, "metal": False, "pts": 0, "r": 30.0, "tex": ["bubble"], "speed": 1.0, "amp": 10.0},
    "box": {"cat": "pickup", "w": 1, "metal": False, "pts": 0, "r": 42.0, "tex": ["box"], "speed": 1.0, "amp": 0.0},
}

with open(OUT, "w") as f:
    f.write("# Data gelombang dan jenis objek Muara.\n")
    f.write("# File ini dibuat oleh tools/gen_data.py dari GDD bagian 7, 8, dan 10. Ubah angka di sini setelah playtest.\n")
    f.write("class_name LevelData\nextends RefCounted\n\n")
    f.write("const ORDER = [\"1-1\", \"1-2\", \"1-3\", \"2-1\", \"2-2\", \"2-3\"]\n\n")
    f.write("const LANES = [300.0, 440.0, 580.0, 720.0, 860.0]\n\n")
    f.write("# w: 0 ringan, 1 sedang, 2 berat. r: radius tabrakan (px). speed: pengali kecepatan arus. amp: goyangan naik-turun (px).\n")
    f.write("const KINDS = {\n")
    for k, v in KINDS.items():
        f.write(f"\t{json.dumps(k)}: {gd(v)},\n")
    f.write("}\n\n")
    f.write("const SEGMENTS = {\n")
    for k, v in SEGMENTS.items():
        f.write(f"\t{json.dumps(k)}: {gd(v)},\n")
    f.write("}\n\n")
    f.write("# Setiap segmen: array 3 gelombang. Setiap event: t (detik sejak gelombang mulai), k (jenis), x, y,\n")
    f.write("# lane (opsional), dir (ikan: -1 ke kiri, 1 ke kanan), hold (\"tutorial\", \"clog\", \"clog_behind\").\n")
    f.write("const WAVES = {\n")
    for sid, waves in W.items():
        f.write(f"\t{json.dumps(sid)}: [\n")
        for wv in waves:
            f.write("\t\t[\n")
            for e in wv:
                f.write(f"\t\t\t{gd(e)},\n")
            f.write("\t\t],\n")
        f.write("\t],\n")
    f.write("}\n")
print("data ok")
