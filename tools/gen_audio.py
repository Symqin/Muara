"""Synthesize reference SFX (WAV) and music loops (WAV -> OGG via ffmpeg).
REFERENCE ONLY: replace with team-made or properly licensed human-made audio."""
import os, sys, wave, subprocess
import numpy as np

ROOT = sys.argv[1]
SR = 22050
os.makedirs(os.path.join(ROOT, "audio"), exist_ok=True)
rng = np.random.default_rng(3)


def t_(d):
    return np.linspace(0, d, int(SR * d), endpoint=False)


def env(n, a=0.005, r=0.1):
    e = np.ones(n)
    na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def write(name, x, sr=SR):
    x = np.clip(x, -1, 1)
    data = (x * 32000).astype(np.int16)
    path = os.path.join(ROOT, "audio", name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(data.tobytes())
    return path


def sweep(f0, f1, d, kind="sine"):
    t = t_(d)
    f = np.linspace(f0, f1, len(t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) if kind == "sine" else np.sign(np.sin(ph)) * 0.6


def noise(d):
    return rng.uniform(-1, 1, int(SR * d))


def lowpass(x, k=8):
    return np.convolve(x, np.ones(k) / k, mode="same")


sfx = {
    "shoot.wav": lambda: (sweep(900, 300, 0.12) * 0.5 + lowpass(noise(0.12), 4) * 0.3) * env(int(SR * 0.12), 0.002, 0.08),
    "pull.wav": lambda: lowpass(noise(0.25), 16) * 0.5 * env(int(SR * 0.25), 0.01, 0.1),
    "catch.wav": lambda: sweep(500, 1100, 0.09) * 0.6 * env(int(SR * 0.09), 0.002, 0.05),
    "net.wav": lambda: (lowpass(noise(0.3), 30) * 0.6 + sweep(300, 150, 0.3) * 0.3) * env(int(SR * 0.3), 0.01, 0.2),
    "magnet.wav": lambda: (np.sin(2 * np.pi * 110 * t_(0.6)) * 0.4 + np.sin(2 * np.pi * 220 * t_(0.6)) * 0.2) * (0.6 + 0.4 * np.sin(2 * np.pi * 12 * t_(0.6))) * env(int(SR * 0.6), 0.05, 0.2),
    "startle.wav": lambda: sweep(1200, 600, 0.15, "square") * 0.35 * env(int(SR * 0.15), 0.002, 0.08),
    "bounce.wav": lambda: sweep(220, 160, 0.12, "square") * 0.4 * env(int(SR * 0.12), 0.002, 0.08),
    "bubble.wav": lambda: sweep(400, 1400, 0.18) * 0.5 * env(int(SR * 0.18), 0.005, 0.1),
    "leak.wav": lambda: (sweep(500, 380, 0.35) * 0.4) * env(int(SR * 0.35), 0.01, 0.2),
    "throw.wav": lambda: lowpass(noise(0.3), 6) * 0.35 * env(int(SR * 0.3), 0.05, 0.2),
    "piece.wav": lambda: (sweep(300, 700, 0.12) * 0.5 + lowpass(noise(0.12), 3) * 0.2) * env(int(SR * 0.12), 0.002, 0.06),
    "hurt.wav": lambda: sweep(300, 120, 0.25, "square") * 0.35 * env(int(SR * 0.25), 0.002, 0.15),
    "click.wav": lambda: sweep(1000, 1000, 0.04) * 0.4 * env(int(SR * 0.04), 0.001, 0.03),
    "o2_low.wav": lambda: np.concatenate([sweep(880, 880, 0.08) * env(int(SR * 0.08), 0.002, 0.03), np.zeros(int(SR * 0.06)), sweep(880, 880, 0.08) * env(int(SR * 0.08), 0.002, 0.03)]) * 0.35,
}


def chime(notes, d_each=0.12):
    out = []
    for n in notes:
        f = 440 * 2 ** ((n - 69) / 12)
        x = (np.sin(2 * np.pi * f * t_(d_each * 2)) * 0.5 + np.sin(4 * np.pi * f * t_(d_each * 2)) * 0.15)
        x *= np.exp(-t_(d_each * 2) * 6)
        out.append(x[: int(SR * d_each)])
    tail = np.zeros(int(SR * 0.3))
    return np.concatenate(out + [tail])


sfx["win.wav"] = lambda: chime([72, 76, 79, 84], 0.14)
sfx["lose.wav"] = lambda: chime([67, 63, 60], 0.2)
sfx["box.wav"] = lambda: chime([76, 81], 0.1)

for name, fn in sfx.items():
    write(name, fn())


def note_f(n):
    return 440 * 2 ** ((n - 69) / 12)


def pluck(f, d, vol=0.3):
    t = t_(d)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return x * np.exp(-t * 5) * vol


def pad(freqs, d, vol=0.08):
    t = t_(d)
    x = sum(np.sin(2 * np.pi * f * t) for f in freqs) / len(freqs)
    e = np.minimum(1, np.minimum(t / 0.4, (d - t) / 0.4))
    return x * e * vol


def song(bpm, chords, melody, bass=True, perc=True, bars_per_chord=1):
    beat = 60 / bpm
    bar = beat * 4
    total = bar * bars_per_chord * len(chords)
    out = np.zeros(int(SR * total) + SR)
    for i, ch in enumerate(chords):
        start = int(SR * i * bar * bars_per_chord)
        p = pad([note_f(n) for n in ch], bar * bars_per_chord)
        out[start:start + len(p)] += p
        if bass:
            for b in range(4 * bars_per_chord):
                s = start + int(SR * b * beat)
                x = pluck(note_f(ch[0] - 12), beat * 0.9, 0.22)
                out[s:s + len(x)] += x
    for k, n in enumerate(melody):
        if n is None:
            continue
        s = int(SR * k * beat / 2)
        x = pluck(note_f(n), beat, 0.18)
        out[s:s + len(x)] += x
    if perc:
        nb = int(total / beat)
        for b in range(nb):
            s = int(SR * b * beat)
            x = lowpass(noise(0.05), 2) * np.exp(-t_(0.05) * 60) * (0.12 if b % 2 else 0.2)
            out[s:s + len(x)] += x
    out = out[: int(SR * total)]
    return out / max(1e-6, np.max(np.abs(out))) * 0.7


river = song(96, [[60, 64, 67], [57, 60, 64], [65, 69, 72], [67, 71, 74]] * 2,
             [72, None, 74, 76, None, 74, 72, None, 69, None, 72, 74, None, 72, 69, None,
              77, None, 76, 74, None, 72, 74, None, 79, None, 77, 76, None, 74, 72, None] * 2)
sea = song(84, [[62, 66, 69], [59, 62, 66], [67, 71, 74], [69, 73, 76]] * 2,
           [74, None, None, 78, None, 76, 74, None, 71, None, None, 74, None, 73, 71, None,
            79, None, None, 78, None, 76, 74, None, 81, None, None, 78, None, 76, 73, None] * 2, perc=False)
boss = song(132, [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 56, 59]] * 2,
            [69, 72, 76, 72, 69, 72, 76, 79, 65, 69, 72, 69, 65, 69, 72, 77,
             67, 71, 74, 71, 67, 71, 74, 79, 64, 68, 71, 68, 76, 74, 71, 68] * 2)
menu = song(80, [[60, 64, 67], [65, 69, 72], [57, 60, 64], [67, 71, 74]],
            [76, None, None, None, 77, None, 76, None, 72, None, None, None, 74, None, None, None] * 2, bass=False, perc=False)

for name, x in [("music_river", river), ("music_sea", sea), ("music_boss", boss), ("music_menu", menu)]:
    wav = write(f"_{name}.wav", x)
    ogg = os.path.join(ROOT, "audio", f"{name}.ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "4", ogg], check=True)
    os.remove(wav)
print("audio ok")
