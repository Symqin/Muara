"""Generate REFERENCE art for Muara (Godot project).

Semua gambar di sini hanya ACUAN bentuk, ukuran, dan titik pivot. Aturan Gimersia melarang
aset buatan AI, jadi tim wajib menggambar ulang semuanya sebelum submit.

Pemakaian: python3 tools/gen_assets.py <folder_proyek>
Butuh: Pillow, numpy, scipy.
"""
import math, os, sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
K = 3
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK = (45, 52, 64, 255)
WHITE = (255, 255, 255, 255)
random.seed(7)
np.random.seed(7)


def rgba(c, a=255):
    return tuple(int(v) for v in c) if len(c) == 4 else (int(c[0]), int(c[1]), int(c[2]), a)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def lighten(c, t):
    return mix(c, (255, 255, 255), t)


def darken(c, t):
    return mix(c, (20, 26, 40), t)


# ============================================================== drawing canvas (supersampled)
class Img:
    def __init__(s, w, h, bg=(0, 0, 0, 0)):
        s.w, s.h = w, h
        s.im = Image.new("RGBA", (w * K, h * K), bg)
        s.d = ImageDraw.Draw(s.im)

    def _p(s, pts):
        return [(x * K, y * K) for x, y in pts]

    def rect(s, x0, y0, x1, y1, fill, r=0, outline=None, width=0):
        s.d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], radius=r * K,
                              fill=rgba(fill) if fill else None,
                              outline=rgba(outline) if outline else None, width=int(width * K))

    def ell(s, x0, y0, x1, y1, fill, outline=None, width=0):
        s.d.ellipse([x0 * K, y0 * K, x1 * K, y1 * K], fill=rgba(fill) if fill else None,
                    outline=rgba(outline) if outline else None, width=int(width * K))

    def circ(s, x, y, r, fill, outline=None, width=0):
        s.ell(x - r, y - r, x + r, y + r, fill, outline, width)

    def poly(s, pts, fill, outline=None):
        s.d.polygon(s._p(pts), fill=rgba(fill), outline=rgba(outline) if outline else None)

    def line(s, pts, fill, w=2):
        s.d.line(s._p(pts), fill=rgba(fill), width=max(1, int(w * K)), joint="curve")

    def arc(s, box, a0, a1, fill, w=2):
        s.d.arc([v * K for v in box], a0, a1, fill=rgba(fill), width=int(w * K))

    def pie(s, box, a0, a1, fill):
        s.d.pieslice([v * K for v in box], a0, a1, fill=rgba(fill))

    def text(s, x, y, t, size, fill=INK, bold=False, anchor="mm"):
        f = ImageFont.truetype(FB if bold else FR, int(size * K))
        s.d.text((x * K, y * K), t, font=f, fill=rgba(fill), anchor=anchor)

    # --- alpha-blended and gradient fills
    def _layer_draw(s, fn):
        layer = Image.new("RGBA", s.im.size, (0, 0, 0, 0))
        fn(ImageDraw.Draw(layer))
        s.im.alpha_composite(layer)

    def blend_poly(s, pts, fill):
        s._layer_draw(lambda d: d.polygon(s._p(pts), fill=rgba(fill)))

    def blend_ell(s, x0, y0, x1, y1, fill):
        s._layer_draw(lambda d: d.ellipse([x0 * K, y0 * K, x1 * K, y1 * K], fill=rgba(fill)))

    def blend_rect(s, x0, y0, x1, y1, fill, r=0):
        s._layer_draw(lambda d: d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], radius=r * K, fill=rgba(fill)))

    def blend_line(s, pts, fill, w=2):
        s._layer_draw(lambda d: d.line(s._p(pts), fill=rgba(fill), width=max(1, int(w * K)), joint="curve"))

    def _grad_paste(s, mask, y0, y1, c0, c1, horizontal=False, x0=0, x1=0):
        bb = mask.getbbox()
        if bb is None:
            return
        L, T, R, B = bb
        w, h = R - L, B - T
        if horizontal:
            t = np.clip((np.arange(L, R) - x0 * K) / max(1, (x1 - x0) * K), 0, 1)
            g = np.zeros((h, w, 4), np.float32)
            for i in range(3):
                g[:, :, i] = (c0[i] + (c1[i] - c0[i]) * t)[None, :]
        else:
            t = np.clip((np.arange(T, B) - y0 * K) / max(1, (y1 - y0) * K), 0, 1)
            g = np.zeros((h, w, 4), np.float32)
            for i in range(3):
                g[:, :, i] = (c0[i] + (c1[i] - c0[i]) * t)[:, None]
        a0 = c0[3] if len(c0) == 4 else 255
        mk = np.asarray(mask.crop(bb)).astype(np.float32) / 255.0
        g[:, :, 3] = a0 * mk
        tile = Image.fromarray(g.astype(np.uint8), "RGBA")
        s.im.alpha_composite(tile, (L, T))

    def _mask(s, fn):
        m = Image.new("L", s.im.size, 0)
        fn(ImageDraw.Draw(m))
        return m

    def grect(s, x0, y0, x1, y1, c0, c1, r=0, horizontal=False):
        m = s._mask(lambda d: d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], radius=r * K, fill=255))
        s._grad_paste(m, y0, y1, c0, c1, horizontal, x0, x1)

    def gell(s, x0, y0, x1, y1, c0, c1, horizontal=False):
        m = s._mask(lambda d: d.ellipse([x0 * K, y0 * K, x1 * K, y1 * K], fill=255))
        s._grad_paste(m, y0, y1, c0, c1, horizontal, x0, x1)

    def gcirc(s, x, y, r, c0, c1):
        s.gell(x - r, y - r, x + r, y + r, c0, c1)

    def gpoly(s, pts, c0, c1, horizontal=False):
        ys = [p[1] for p in pts]
        xs = [p[0] for p in pts]
        m = s._mask(lambda d: d.polygon(s._p(pts), fill=255))
        s._grad_paste(m, min(ys), max(ys), c0, c1, horizontal, min(xs), max(xs))

    def vgrad(s, y0, y1, c0, c1, x0=0, x1=None):
        x1 = s.w if x1 is None else x1
        s.grect(x0, y0, x1, y1, c0, c1)

    def result(s):
        return s.im.resize((s.w, s.h), Image.LANCZOS)

    def save(s, rel, shade=True, outline=2, light=0.26, grad=0.16):
        out = s.result()
        if shade:
            out = shade_sprite(out, outline, light, grad)
        save_img(out, rel)


def save_img(img, rel):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    img.save(path, optimize=True)


# ============================================================== volume pass for sprites
def shade_sprite(img, outline=2, light=0.26, grad=0.16):
    """Memberi volume: cahaya dari kiri atas, bayangan tepi, gradasi vertikal, dan garis tepi gelap."""
    arr = np.asarray(img).astype(np.float32)
    rgb = arr[:, :, :3]
    a = arr[:, :, 3] / 255.0
    if a.max() <= 0:
        return img
    size = max(img.size)
    ab = ndimage.gaussian_filter(a, sigma=max(1.5, size / 36.0))
    gy, gx = np.gradient(ab)
    n = gy * 0.85 + gx * 0.45
    n = n / (np.abs(n).max() + 1e-6)
    L = 1.0 + light * n
    rows = np.where(a.max(axis=1) > 0.05)[0]
    y0, y1 = rows[0], rows[-1]
    t = np.clip((np.arange(img.size[1]) - y0) / max(1, y1 - y0), 0, 1)
    L *= ((1.0 + grad * 0.5) - grad * t)[:, None]
    ab2 = ndimage.gaussian_filter(a, sigma=max(1.0, outline * 1.3))
    ao = np.clip((1.0 - ab2) * 2.2, 0, 1) * a
    L *= (1.0 - 0.2 * ao)
    rgb = np.clip(rgb * L[:, :, None], 0, 255)
    body = np.dstack([rgb, a * 255]).astype(np.uint8)
    body_img = Image.fromarray(body, "RGBA")
    if outline <= 0:
        return body_img
    # warna garis tepi: warna objek di sekitarnya yang digelapkan
    pa = ndimage.gaussian_filter(a, 3.0) + 1e-6
    col = np.dstack([ndimage.gaussian_filter(rgb[:, :, i] * a, 3.0) / pa for i in range(3)])
    col = col * 0.38 + np.array([22, 30, 48]) * 0.35
    yy, xx = np.mgrid[-outline:outline + 1, -outline:outline + 1]
    fp = (xx ** 2 + yy ** 2) <= outline ** 2 + 0.5
    dil = ndimage.grey_dilation(a, footprint=fp)
    dil = ndimage.gaussian_filter(dil, 0.6)
    ol = np.dstack([np.clip(col, 0, 255), np.clip(dil, 0, 1) * 255 * 0.95]).astype(np.uint8)
    base = Image.fromarray(ol, "RGBA")
    base.alpha_composite(body_img)
    return base


# ============================================================== post effects for big pictures (1x)
def fx_layer(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def blur_composite(base, draw_fn, radius):
    layer = fx_layer(base.size)
    draw_fn(ImageDraw.Draw(layer))
    if radius > 0:
        arr = np.asarray(layer).astype(np.float32)
        a = arr[:, :, 3:4] / 255.0
        pre = arr[:, :, :3] * a
        sig = radius / 2.0
        pre = np.dstack([ndimage.gaussian_filter(pre[:, :, i], sig) for i in range(3)])
        ab = ndimage.gaussian_filter(a[:, :, 0], sig)[:, :, None]
        rgb = np.where(ab > 1e-4, pre / np.maximum(ab, 1e-4), 0)
        layer = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(ab * 255, 0, 255)]).astype(np.uint8), "RGBA")
    base.alpha_composite(layer)


def god_rays(base, x_list, top, bottom, alpha, spread=260, blur=22):
    def d(dr):
        for x in x_list:
            w = random.randint(50, 110)
            dr.polygon([(x, top), (x + w, top), (x + w + spread, bottom), (x + spread * 0.55, bottom)], fill=(255, 255, 240, alpha))
    blur_composite(base, d, blur)


def caustics(base, top, bottom, alpha, count=90):
    def d(dr):
        for _ in range(count):
            x = random.uniform(0, base.size[0]); y = random.uniform(top, bottom)
            w = random.uniform(30, 90)
            pts = [(x + i * w / 6.0, y + math.sin(i * 1.3 + x) * 6) for i in range(7)]
            dr.line(pts, fill=(255, 255, 255, alpha), width=3)
    blur_composite(base, d, 2.5)


def particles(base, top, bottom, n, col, rmin=1.5, rmax=4.0, alpha=(40, 120)):
    def d(dr):
        for _ in range(n):
            x = random.uniform(0, base.size[0]); y = random.uniform(top, bottom)
            r = random.uniform(rmin, rmax)
            dr.ellipse([x - r, y - r, x + r, y + r], fill=col + (random.randint(*alpha),))
    blur_composite(base, d, 0.8)


def vignette(base, strength=0.35, top=0):
    w, h = base.size
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - w / 2) / (w / 2); dy = (yy - h / 2) / (h / 2)
    v = np.clip((dx ** 2 * 0.6 + dy ** 2 * 0.8) - 0.35, 0, 1) * strength
    v[:top, :] = 0
    layer = np.zeros((h, w, 4), np.uint8)
    layer[:, :, 0] = 8; layer[:, :, 1] = 20; layer[:, :, 2] = 34
    layer[:, :, 3] = (v * 255).astype(np.uint8)
    base.alpha_composite(Image.fromarray(layer, "RGBA"))


def haze(base, col, alpha, top=0, bottom=None):
    bottom = base.size[1] if bottom is None else bottom
    layer = fx_layer(base.size)
    ImageDraw.Draw(layer).rectangle([0, top, base.size[0], bottom], fill=col + (alpha,))
    base.alpha_composite(layer)


def soft_shapes(base, shapes, blur):
    """shapes: list of (kind, coords, rgba)."""
    def d(dr):
        for kind, c, col in shapes:
            if kind == "ell":
                dr.ellipse(c, fill=col)
            elif kind == "poly":
                dr.polygon(c, fill=col)
            elif kind == "rect":
                dr.rounded_rectangle(c, radius=12, fill=col)
    blur_composite(base, d, blur)


# ============================================================== characters
SKIN = (255, 210, 168)
SKIN_D = (232, 170, 128)
SUIT = (255, 150, 70)
SUIT_D = (220, 98, 46)
FLIP = (52, 176, 168)
TANK = (255, 212, 84)
METAL = (200, 210, 220)
HAIR = (70, 50, 40)


def helmet_head(m, cx, cy, r, look=1):
    """Kepala Raka dengan helm selam kaca."""
    m.gcirc(cx, cy, r + 9, (190, 205, 215), (120, 135, 150))           # rim logam
    m.gcirc(cx, cy, r, (215, 238, 248), (175, 210, 228))                # bagian dalam helm
    m.gcirc(cx + 2, cy + 4, r * 0.78, SKIN, SKIN_D)                     # wajah
    m.pie((cx - r * 0.82, cy - r * 0.86, cx + r * 0.86, cy + r * 0.5), 180, 360, HAIR)  # rambut
    m.poly([(cx - r * 0.5, cy - r * 0.2), (cx - r * 0.2, cy - r * 0.42), (cx + r * 0.1, cy - r * 0.2),
            (cx + r * 0.4, cy - r * 0.42), (cx + r * 0.7, cy - r * 0.18), (cx + r * 0.7, cy - r * 0.5),
            (cx - r * 0.6, cy - r * 0.5)], HAIR)
    ex = cx + 10 * look
    for dx in (-r * 0.28, r * 0.28):
        m.ell(ex + dx - 6, cy - 2, ex + dx + 6, cy + 14, INK)
        m.circ(ex + dx + 2, cy + 2, 2.6, WHITE)
    m.ell(ex - r * 0.55, cy + 14, ex - r * 0.3, cy + 22, (255, 160, 150))
    m.ell(ex + r * 0.3, cy + 14, ex + r * 0.55, cy + 22, (255, 160, 150))
    m.arc((ex - 12, cy + 8, ex + 12, cy + 28), 20, 160, INK, 3)
    # kilau kaca
    m.blend_ell(cx - r * 0.9, cy - r * 0.9, cx + r * 0.9, cy + r * 0.9, (190, 230, 255, 40))
    m.blend_line([(cx - r * 0.62, cy - r * 0.2), (cx - r * 0.5, cy - r * 0.5), (cx - r * 0.22, cy - r * 0.7)], (255, 255, 255, 210), 6)
    m.blend_ell(cx + r * 0.4, cy - r * 0.68, cx + r * 0.58, cy - r * 0.5, (255, 255, 255, 190))


def raka_body():
    # 240x300; anchor (pusat badan) di (110,180); bahu di (126,120)
    m = Img(240, 300)
    # kantong jaring di punggung (titik kumpul sampah)
    m.gell(12, 78, 70, 132, (130, 190, 150), (80, 140, 105))
    for i in range(5):
        m.line([(18 + i * 11, 84), (24 + i * 11, 128)], (60, 110, 80), 2)
        m.line([(14, 90 + i * 9), (68, 92 + i * 9)], (60, 110, 80), 2)
    # tabung oksigen
    m.grect(30, 98, 78, 204, lighten(TANK, 0.25), darken(TANK, 0.25), r=20, horizontal=True)
    m.rect(36, 112, 44, 190, (255, 255, 255, 120), r=4)
    m.grect(44, 86, 64, 102, METAL, darken(METAL, 0.3), r=4)
    m.rect(38, 150, 70, 160, (60, 70, 80), r=3)
    # selang ke helm
    m.line([(54, 88), (58, 70), (72, 62)], (60, 70, 85), 7)
    # kaki
    for x0 in (76, 116):
        m.grect(x0, 198, x0 + 30, 276, SUIT, SUIT_D, r=12)
        m.gell(x0 + 3, 228, x0 + 27, 248, (70, 80, 95), (40, 48, 60))
    # kaki katak
    for x0 in (60, 108):
        m.gpoly([(x0, 268), (x0 + 50, 264), (x0 + 62, 292), (x0 - 6, 296)], lighten(FLIP, 0.2), darken(FLIP, 0.25))
        m.line([(x0 + 14, 272), (x0 + 12, 292)], darken(FLIP, 0.35), 3)
        m.line([(x0 + 34, 270), (x0 + 36, 292)], darken(FLIP, 0.35), 3)
    # badan
    m.grect(64, 100, 158, 226, lighten(SUIT, 0.15), SUIT_D, r=34)
    m.grect(64, 120, 86, 220, SUIT_D, darken(SUIT_D, 0.15), r=12)          # sisi gelap
    m.line([(112, 112), (112, 196)], (255, 220, 190), 3)                   # ritsleting
    m.gcirc(134, 140, 12, (255, 255, 255), (220, 230, 235))                # lencana
    m.poly([(128, 144), (134, 132), (140, 144)], (80, 170, 120))
    # sabuk pemberat
    m.grect(62, 192, 160, 212, (70, 78, 92), (40, 46, 58), r=6)
    m.grect(102, 190, 124, 214, (230, 235, 240), (160, 170, 180), r=4)
    for x in (72, 136):
        m.grect(x, 194, x + 16, 210, (110, 120, 130), (70, 78, 88), r=3)
    # kerah helm
    m.grect(80, 98, 156, 116, METAL, darken(METAL, 0.35), r=8)
    helmet_head(m, 116, 62, 46)
    m.save("art/raka_body.png", outline=3)


def gun(name, col, extra):
    # 220x64; pivot (bahu) di (28,32); ujung laras di (188,32)
    m = Img(220, 64)
    m.grect(10, 16, 76, 48, lighten(SUIT, 0.15), SUIT_D, r=15)             # lengan baju
    m.grect(60, 22, 78, 44, (70, 80, 95), (40, 48, 60), r=5)               # manset
    extra_back = extra.get("back")
    if extra_back:
        extra_back(m)
    m.grect(64, 18, 182, 46, lighten(col, 0.3), darken(col, 0.3), r=12)    # badan alat
    m.grect(86, 40, 106, 62, lighten(col, 0.1), darken(col, 0.35), r=6)    # pegangan
    m.gcirc(78, 32, 13, SKIN, SKIN_D)                                       # tangan
    m.rect(70, 22, 172, 26, (255, 255, 255, 120), r=2)
    extra["front"](m)
    m.save(f"art/gun_{name}.png", outline=2)


def gun_all():
    def harpun(m):
        m.grect(150, 26, 200, 38, (230, 235, 240), (140, 150, 160), r=4)
        m.poly([(196, 24), (216, 32), (196, 40)], (230, 235, 240))
        m.ell(118, 26, 146, 42, (230, 210, 170)); m.ell(124, 30, 140, 38, (190, 160, 120))
    gun("harpun", (110, 125, 145), {"front": harpun})

    def jaring(m):
        m.gcirc(178, 32, 18, (170, 230, 190), (80, 160, 110))
        for i in range(-2, 3):
            m.line([(178 + i * 6, 16), (178 + i * 6, 48)], (40, 110, 70), 2)
            m.line([(162, 32 + i * 6), (194, 32 + i * 6)], (40, 110, 70), 2)
        m.grect(108, 22, 142, 42, (240, 220, 120), (200, 160, 60), r=6)
    gun("jaring", (70, 160, 110), {"front": jaring})

    def magnet(m):
        m.d.arc([164 * K, 12 * K, 204 * K, 52 * K], 270, 90, fill=rgba((215, 60, 60)), width=12 * K)
        m.grect(170, 10, 184, 22, (240, 245, 250), (170, 180, 190), r=2)
        m.grect(170, 42, 184, 54, (240, 245, 250), (170, 180, 190), r=2)
        for i in range(4):
            m.line([(116 + i * 8, 20), (116 + i * 8, 44)], (230, 180, 80), 3)
    gun("magnet", (200, 70, 70), {"front": magnet})


def portrait(name, draw):
    m = Img(220, 220)
    m.gcirc(110, 110, 106, (225, 245, 248), (160, 210, 220))
    m.blend_ell(20, 140, 200, 260, (255, 255, 255, 50))
    draw(m)
    out = shade_sprite(m.result(), 0, 0.18, 0.12)
    # bingkai cincin
    ring = Img(220, 220)
    ring.circ(110, 110, 106, None, outline=(255, 255, 255), width=8)
    ring.circ(110, 110, 109, None, outline=(60, 90, 110, 160), width=2)
    mask = Img(220, 220)
    mask.circ(110, 110, 104, (255, 255, 255))
    clip = Image.new("RGBA", out.size, (0, 0, 0, 0))
    clip.paste(out, (0, 0), mask.result().split()[3])
    clip.alpha_composite(ring.result())
    save_img(clip, f"art/portrait_{name}.png")


def kakek(m):
    m.grect(40, 150, 180, 240, (120, 150, 175), (80, 105, 130), r=44)      # baju
    m.poly([(92, 150), (110, 186), (128, 150)], (240, 240, 235))
    m.gcirc(110, 112, 50, (240, 205, 170), (210, 165, 130))                # wajah
    m.gell(66, 116, 154, 172, (250, 250, 250), (215, 215, 215))            # janggut
    m.ell(92, 128, 128, 142, (225, 160, 150))
    m.line([(84, 106), (100, 102)], INK, 4); m.line([(120, 102), (136, 106)], INK, 4)
    m.line([(80, 92), (98, 90)], (230, 230, 230), 5); m.line([(122, 90), (140, 92)], (230, 230, 230), 5)
    m.arc((86, 112, 104, 124), 200, 340, (180, 130, 100), 2)
    # caping (topi bambu)
    m.gpoly([(110, 24), (196, 82), (24, 82)], (240, 205, 130), (190, 145, 80))
    for i in range(-3, 4):
        m.line([(110, 28), (110 + i * 24, 80)], (170, 125, 70), 2)
    m.grect(24, 78, 196, 88, (190, 145, 80), (150, 110, 60), r=5)


def busari(m):
    m.grect(42, 150, 178, 240, (90, 170, 125), (55, 125, 90), r=44)
    m.grect(84, 162, 136, 240, (250, 250, 245), (220, 225, 220), r=10)     # celemek
    m.text(110, 196, "♻", 30, (60, 150, 100))
    m.gcirc(110, 108, 50, (232, 190, 150), (205, 155, 118))
    m.pie((56, 46, 164, 148), 180, 360, (60, 55, 70))                     # rambut
    m.gcirc(110, 48, 22, (75, 70, 88), (50, 45, 60))                      # sanggul
    m.rect(58, 90, 72, 140, (60, 55, 70), r=6); m.rect(148, 90, 162, 140, (60, 55, 70), r=6)
    for dx in (-18, 18):
        m.ell(110 + dx - 6, 100, 110 + dx + 6, 116, INK)
        m.circ(110 + dx + 2, 104, 2.4, WHITE)
    m.arc((94, 112, 126, 136), 20, 160, INK, 3)
    m.ell(72, 118, 88, 128, (240, 160, 150)); m.ell(132, 118, 148, 128, (240, 160, 150))


def raka_face(m):
    m.grect(40, 158, 180, 240, lighten(SUIT, 0.15), SUIT_D, r=44)
    m.grect(70, 150, 150, 170, METAL, darken(METAL, 0.3), r=8)
    helmet_head(m, 110, 100, 56, look=0)


# ============================================================== trash
def sachet(i, col):
    m = Img(64, 52)
    m.gpoly([(6, 10), (58, 4), (60, 42), (8, 48)], lighten(col, 0.2), darken(col, 0.2))
    for x in range(10, 58, 5):
        m.line([(x, 6 + (58 - x) * 0.1), (x + 1, 11)], darken(col, 0.3), 1)
    m.rect(22, 18, 46, 34, (255, 255, 255, 200), r=4)
    m.circ(34, 26, 5, darken(col, 0.1))
    m.line([(10, 16), (56, 10)], (255, 255, 255, 200), 2)
    m.save(f"art/trash_sachet_{i}.png", outline=2)


def bag():
    m = Img(96, 96)
    m.gpoly([(18, 34), (78, 34), (88, 86), (8, 86)], (250, 252, 255), (200, 212, 222))
    m.line([(26, 36), (34, 10), (44, 36)], (190, 205, 215), 6)
    m.line([(52, 36), (62, 10), (70, 36)], (190, 205, 215), 6)
    for (a, b) in [((30, 50), (40, 78)), ((56, 46), (66, 76)), ((44, 60), (48, 82))]:
        m.line([a, b], (205, 215, 225), 3)
    m.blend_poly([(22, 40), (34, 40), (26, 80), (16, 80)], (255, 255, 255, 140))
    m.save("art/trash_bag.png", outline=2)


def bottle():
    m = Img(104, 44)
    m.grect(4, 6, 80, 38, (215, 242, 252), (130, 190, 215), r=14)
    m.grect(66, 12, 82, 32, (200, 235, 248), (130, 190, 215), r=4)
    m.grect(80, 13, 98, 31, (255, 140, 110), (215, 85, 60), r=4)
    for x in (24, 40, 56):
        m.line([(x, 8), (x, 36)], (150, 200, 220), 2)
    m.blend_rect(12, 11, 62, 17, (255, 255, 255, 190), r=3)
    m.save("art/trash_bottle.png", outline=2)


def styro():
    m = Img(92, 64)
    m.grect(4, 8, 88, 58, (255, 255, 250), (215, 215, 205), r=10)
    m.line([(6, 30), (86, 30)], (205, 205, 195), 2)
    for x in range(14, 88, 12):
        for y in (18, 44):
            m.circ(x + (y % 7), y, 2, (220, 220, 210))
    m.poly([(70, 8), (88, 8), (88, 22)], (0, 0, 0, 0))
    m.save("art/trash_styro.png", outline=2)


def sandal():
    m = Img(96, 44)
    m.gell(4, 6, 92, 38, (100, 160, 235), (50, 100, 190))
    m.gell(10, 10, 86, 32, (140, 190, 245), (90, 145, 225))
    m.line([(54, 22), (36, 8)], (250, 250, 250), 5); m.line([(54, 22), (52, 6)], (250, 250, 250), 5)
    m.circ(54, 22, 4, (230, 230, 230))
    m.save("art/trash_sandal.png", outline=2)


def can():
    m = Img(48, 72)
    m.grect(4, 4, 44, 68, (235, 95, 95), (170, 50, 55), r=8, horizontal=True)
    m.grect(4, 4, 44, 12, (225, 230, 236), (150, 160, 170), r=4)
    m.grect(4, 60, 44, 68, (200, 205, 210), (140, 150, 160), r=4)
    m.rect(4, 28, 44, 42, (250, 250, 250))
    m.circ(24, 35, 4, (235, 95, 95))
    m.rect(10, 12, 16, 58, (255, 220, 220, 170), r=3)
    m.save("art/trash_can.png", outline=2)


def tire():
    m = Img(112, 112)
    m.gcirc(56, 56, 52, (85, 90, 100), (35, 38, 46))
    for a in range(0, 360, 18):
        x = 56 + 45 * math.cos(math.radians(a)); y = 56 + 45 * math.sin(math.radians(a))
        m.circ(x, y, 4, (70, 75, 85))
    m.circ(56, 56, 30, (60, 64, 72))
    m.circ(56, 56, 30, None, outline=(110, 115, 125), width=4)
    m.d.ellipse([(56 - 22) * K, (56 - 22) * K, (56 + 22) * K, (56 + 22) * K], fill=(0, 0, 0, 0))
    m.blend_line([(22, 40), (30, 24), (46, 14)], (255, 255, 255, 90), 5)
    m.save("art/trash_tire.png", outline=2)


def ghostnet():
    m = Img(140, 100)
    m.gell(4, 6, 136, 94, (190, 155, 110, 220), (140, 105, 70, 220))
    for i in range(-4, 5):
        m.line([(70 + i * 14, 10), (70 + i * 14 + 12, 90)], (100, 70, 45), 2)
        m.line([(10, 50 + i * 9), (130, 50 + i * 9 + 6)], (100, 70, 45), 2)
    m.ell(4, 6, 136, 94, None, outline=(100, 70, 45), width=3)
    for (x, y) in [(30, 30), (110, 70), (60, 80)]:
        m.gcirc(x, y, 7, (255, 210, 90), (220, 150, 40))
    m.save("art/trash_ghostnet.png", outline=2)


def flake(i):
    m = Img(28, 20)
    pts = [(2, 6), (14, 2), (26, 8), (22, 18), (6, 16)] if i == 1 else [(4, 4), (24, 2), (26, 14), (12, 18), (2, 12)]
    m.gpoly(pts, (250, 252, 255), (195, 205, 212))
    m.save(f"art/trash_flake_{i}.png", outline=1)


# ============================================================== creatures & props
def fish(i, col):
    m = Img(104, 64)  # menghadap kiri
    tail = darken(col, 0.15)
    m.gpoly([(74, 32), (100, 10), (94, 32), (100, 54)], lighten(tail, 0.1), darken(tail, 0.2))
    m.gpoly([(40, 14), (60, 2), (68, 16)], lighten(col, 0.1), darken(col, 0.2))
    m.gell(12, 10, 82, 54, lighten(col, 0.25), darken(col, 0.25))
    m.gell(18, 32, 74, 54, lighten(col, 0.55), lighten(col, 0.3))           # perut
    for x in (46, 58, 70):
        m.arc((x - 10, 14, x + 6, 50), 300, 60, darken(col, 0.2), 2)
    m.gpoly([(44, 34), (60, 40), (46, 48)], darken(col, 0.1), darken(col, 0.3))
    m.circ(32, 26, 8, WHITE); m.circ(30, 26, 5, INK); m.circ(28, 24, 1.8, WHITE)
    m.arc((14, 30, 26, 40), 300, 60, INK, 2)
    m.save(f"art/fish_{i}.png", outline=2)


def jelly():
    m = Img(84, 108)
    for i, x in enumerate((20, 31, 42, 53, 64)):
        pts = [(x + 5 * math.sin(t / 4 + i), 50 + t * 2.5) for t in range(0, 22)]
        m.line(pts, (240, 165, 230, 220), 4)
    m.gell(6, 6, 78, 92, (255, 200, 245, 240), (225, 130, 210, 240))
    m.d.rectangle([0, 50 * K, 84 * K, 108 * K], fill=(0, 0, 0, 0))
    for i, x in enumerate((20, 31, 42, 53, 64)):
        pts = [(x + 5 * math.sin(t / 4 + i), 50 + t * 2.5) for t in range(0, 22)]
        m.line(pts, (240, 165, 230, 230), 4)
    m.grect(6, 44, 78, 54, (235, 150, 220), (210, 120, 200), r=5)
    m.blend_ell(18, 14, 36, 30, (255, 255, 255, 200))
    m.circ(30, 34, 3, INK); m.circ(54, 34, 3, INK)
    m.save("art/jelly.png", outline=2, light=0.18)


def turtle():
    m = Img(124, 84)  # menghadap kiri
    flip = (120, 200, 130)
    for box in [(36, 56, 62, 82), (80, 56, 106, 82), (36, 6, 62, 26), (84, 8, 108, 26)]:
        m.gell(*box, lighten(flip, 0.1), darken(flip, 0.2))
    m.gell(6, 34, 36, 56, lighten(flip, 0.15), darken(flip, 0.15))
    m.circ(16, 42, 3.5, INK); m.circ(15, 41, 1.2, WHITE)
    m.gell(26, 12, 116, 72, (110, 175, 115), (55, 120, 75))
    for (x, y) in [(50, 30), (72, 26), (94, 32), (60, 52), (84, 52)]:
        m.gcirc(x, y, 10, (140, 195, 130), (90, 155, 100))
    m.blend_ell(40, 16, 70, 28, (255, 255, 255, 90))
    m.save("art/turtle.png", outline=2)


def wood():
    m = Img(184, 54)
    m.grect(4, 6, 168, 48, (175, 125, 80), (115, 75, 45), r=20)
    m.gell(150, 6, 182, 48, (230, 190, 135), (190, 145, 95))
    m.ell(158, 14, 174, 40, None, outline=(160, 115, 70), width=2)
    m.ell(163, 21, 169, 33, None, outline=(160, 115, 70), width=2)
    for x in (30, 66, 104, 136):
        m.line([(x, 14), (x + 20, 18)], (110, 70, 40), 3)
        m.line([(x + 6, 36), (x + 24, 40)], (110, 70, 40), 2)
    m.gell(70, 2, 92, 14, (120, 190, 90), (70, 140, 60))
    m.save("art/wood.png", outline=2)


def bubble():
    m = Img(60, 60)
    m.gcirc(30, 30, 26, (225, 248, 255, 150), (150, 210, 245, 150))
    m.circ(30, 30, 26, None, outline=(240, 252, 255), width=3)
    m.blend_ell(12, 10, 28, 24, (255, 255, 255, 230))
    m.blend_ell(36, 40, 44, 46, (255, 255, 255, 150))
    m.text(31, 33, "O2", 15, (30, 100, 150), True)
    m.save("art/bubble.png", shade=False)


def fx_bubble():
    m = Img(24, 24)
    m.gcirc(12, 12, 10, (230, 250, 255, 120), (170, 220, 245, 120))
    m.circ(12, 12, 10, None, outline=(245, 252, 255), width=2)
    m.blend_ell(6, 5, 12, 10, (255, 255, 255, 230))
    m.save("art/fx_bubble.png", shade=False)


def box():
    m = Img(88, 76)
    m.grect(6, 12, 82, 72, (215, 165, 100), (155, 110, 60), r=8)
    for y in (32, 52):
        m.line([(6, y), (82, y)], (130, 90, 50), 3)
    m.line([(8, 14), (80, 70)], (170, 125, 75), 4)
    m.grect(28, 24, 60, 60, (255, 255, 255), (225, 235, 230), r=8)
    m.rect(40, 30, 48, 54, (70, 160, 115)); m.rect(32, 38, 56, 46, (70, 160, 115))
    m.line([(44, 12), (44, 0)], (240, 240, 240), 3)
    m.save("art/box.png", outline=2)


def hook():
    m = Img(48, 24)
    m.gpoly([(2, 8), (30, 8), (30, 2), (46, 12), (30, 22), (30, 16), (2, 16)], (235, 240, 245), (120, 130, 145))
    m.save("art/hook.png", outline=1)


def net_open():
    m = Img(240, 240)
    m.circ(120, 120, 112, (120, 200, 150, 70), outline=(80, 160, 110), width=4)
    for i in range(-5, 6):
        x = 120 + i * 20
        h = math.sqrt(max(0, 112 ** 2 - (i * 20) ** 2))
        m.line([(x, 120 - h), (x, 120 + h)], (80, 160, 110, 200), 2)
        m.line([(120 - h, x), (120 + h, x)], (80, 160, 110, 200), 2)
    for a in range(0, 360, 30):
        m.gcirc(120 + 112 * math.cos(math.radians(a)), 120 + 112 * math.sin(math.radians(a)), 7, (240, 245, 250), (150, 160, 170))
    m.save("art/net_open.png", shade=False)


def boat():
    # 480x240. Garis air (permukaan) di y=200, pusat horizontal x=240.
    m = Img(480, 240)
    # kakek di kapal
    m.grect(272, 98, 330, 168, (120, 150, 175), (80, 105, 130), r=22)
    m.gcirc(300, 82, 24, (240, 205, 170), (210, 165, 130))
    m.gell(282, 86, 318, 108, (250, 250, 250), (215, 215, 215))
    m.gpoly([(300, 44), (342, 72), (258, 72)], (240, 205, 130), (190, 145, 80))
    m.line([(326, 120), (356, 84), (364, 64)], (120, 150, 175), 12)          # tangan melambai
    m.gcirc(366, 60, 9, (240, 205, 170), (210, 165, 130))
    # tiang & tali
    m.grect(140, 30, 150, 170, (170, 125, 80), (120, 85, 50), r=3)
    m.gpoly([(150, 36), (226, 150), (150, 150)], (255, 250, 240), (225, 220, 205))
    # lambung
    m.gpoly([(20, 150), (460, 150), (420, 214), (60, 214)], (255, 150, 110), (210, 90, 65))
    m.grect(20, 146, 460, 162, (255, 245, 230), (230, 215, 195), r=6)
    m.grect(40, 176, 440, 186, (70, 150, 200), (40, 110, 160), r=4)
    m.blend_poly([(60, 200), (420, 200), (420, 214), (60, 214)], (30, 80, 110, 90))
    # cadik (penyeimbang)
    m.line([(60, 170), (0, 196)], (140, 100, 60), 6); m.line([(420, 170), (480, 196)], (140, 100, 60), 6)
    m.save("art/boat.png", outline=3)


# ============================================================== backgrounds
SURF, BED = 200, 960
WATER = {
    "1-1": ((150, 170, 120), (80, 105, 78), (120, 196, 180), (50, 125, 128)),
    "1-2": ((150, 160, 110), (88, 98, 70), (115, 190, 178), (48, 120, 122)),
    "1-3": ((150, 140, 100), (88, 78, 60), (110, 184, 172), (45, 115, 120)),
    "2-1": ((110, 160, 150), (50, 100, 108), (110, 205, 222), (32, 115, 160)),
    "2-2": ((90, 150, 160), (32, 80, 102), (95, 200, 232), (24, 98, 158)),
    "2-3": ((60, 110, 130), (18, 40, 60), (70, 165, 210), (12, 62, 116)),
}


def tree(m, x, y, s, col=(90, 150, 90)):
    m.grect(x - 6 * s, y - 10 * s, x + 6 * s, y + 40 * s, (140, 100, 60), (100, 70, 40), r=3 * s)
    for dx, dy, r in [(-20, -10, 26), (18, -12, 24), (0, -34, 30)]:
        m.gcirc(x + dx * s, y + dy * s, r * s, lighten(col, 0.25), darken(col, 0.25))


def bed_plants(m, clean, rows):
    for (x, h, col) in rows:
        c = col if clean else mix(col, (130, 130, 110), 0.55)
        for j in range(4):
            hh = h - j * 12
            pts = [(x + j * 16, BED + 6)]
            for k in range(8):
                t = k / 7.0
                pts.append((x + j * 16 + math.sin(t * 3 + j) * 8 + 5, BED - hh * t))
            for k in range(7, -1, -1):
                t = k / 7.0
                pts.append((x + j * 16 + math.sin(t * 3 + j) * 8 + 22 - t * 14, BED - hh * t))
            m.gpoly(pts, lighten(c, 0.2), darken(c, 0.25))


def corals(m, clean, spots, scale=1.0):
    pal = [(255, 140, 120), (255, 200, 90), (200, 120, 220), (120, 200, 150)]
    for i, (x, s) in enumerate(spots):
        col = pal[i % 4] if clean else (200, 198, 194)
        s = s * scale
        for dx, h in [(-24, 64), (0, 96), (24, 58)]:
            m.grect(x + dx * s - 10 * s, BED - h * s, x + dx * s + 10 * s, BED + 6, lighten(col, 0.2), darken(col, 0.25), r=10 * s)
            m.gcirc(x + dx * s, BED - h * s, 13 * s, lighten(col, 0.3), col)
            m.gcirc(x + dx * s - 14 * s, BED - h * s * 0.6, 9 * s, lighten(col, 0.3), col)


def rocks(m, items, col):
    for (x, w, h) in items:
        m.gell(x, BED - h, x + w, BED + h * 0.4, lighten(col, 0.18), darken(col, 0.3))
        m.blend_ell(x + w * 0.2, BED - h * 0.85, x + w * 0.5, BED - h * 0.55, (255, 255, 255, 50))


def scenery(m, seg):
    if seg == "1-1":
        m.gpoly([(0, 150), (520, 130), (900, 160), (1920, 140), (1920, SURF), (0, SURF)], (160, 200, 140), (120, 165, 110))
        for x in (40, 160, 1660, 1780, 1880):
            tree(m, x, 150, 1.2, (70, 140, 80))
        for x in (60, 1700):
            for k in range(5):
                m.line([(x + 10 + k * 40, SURF - 8), (x + 22 + k * 40, SURF + 46)], (120, 90, 60), 5)
        m.grect(470, 104, 620, 150, (252, 244, 226), (225, 210, 185), r=8)
        m.gpoly([(456, 110), (634, 110), (545, 62)], (255, 140, 100), (210, 95, 70))
        for px in (480, 600):
            m.rect(px, 150, px + 10, SURF + 30, (130, 95, 60))
    elif seg == "1-2":
        m.gpoly([(0, 140), (1920, 120), (1920, SURF), (0, SURF)], (165, 205, 135), (125, 165, 105))
        for i, x in enumerate(range(120, 1800, 300)):
            m.grect(x, 70, x + 120, 140, (252, 244, 226), (222, 205, 180), r=8)
            roof = (255, 140, 100) if i % 2 == 0 else (110, 150, 205)
            m.gpoly([(x - 14, 76), (x + 134, 76), (x + 60, 28)], lighten(roof, 0.15), darken(roof, 0.25))
            m.grect(x + 46, 98, x + 74, 140, (150, 110, 70), (110, 75, 45), r=3)
            m.grect(x + 14, 88, x + 36, 108, (170, 215, 235), (120, 175, 205), r=3)
            for px in (x + 10, x + 100):
                m.grect(px, 140, px + 9, SURF + 40, (150, 110, 70), (110, 75, 45))
        m.line([(300, 90), (520, 90)], (120, 120, 120), 2)
        for k, col in enumerate([(240, 120, 120), (120, 180, 240), (250, 220, 120)]):
            m.grect(330 + k * 60, 90, 370 + k * 60, 126, col, darken(col, 0.25), r=4)
    elif seg == "1-3":
        for k, (bx, bh) in enumerate([(1060, 130), (1140, 170), (1230, 110), (1300, 150), (1390, 120), (1470, 180), (1560, 140), (1640, 160), (1730, 120)]):
            m.grect(bx, SURF - bh - 20, bx + 70, SURF - 20, (190, 198, 214), (150, 158, 176), r=4)
            for wy in range(int(SURF - bh), int(SURF - 30), 22):
                for wx in (bx + 12, bx + 40):
                    m.rect(wx, wy, wx + 14, wy + 10, (235, 240, 200))
        m.grect(0, 146, 1920, 174, (185, 185, 185), (135, 135, 135))
        for px in range(60, 1920, 160):
            m.grect(px, 174, px + 20, SURF, (165, 165, 165), (120, 120, 120))
        m.grect(1560, 120, 1760, SURF + 2, (150, 150, 155), (105, 105, 112), r=4)
    elif seg == "2-1":
        m.gpoly([(0, 110), (520, 150), (700, SURF), (0, SURF)], (250, 232, 185), (220, 195, 145))
        for x in (60, 220, 380):
            m.line([(x, 150), (x + 14, 60)], (140, 100, 60), 7)
            for a in range(5):
                ang = math.radians(200 + a * 35)
                m.line([(x + 14, 60), (x + 14 + 60 * math.cos(ang), 60 + 34 * math.sin(ang) + 30)], (80, 160, 90), 8)
        m.grect(1200, 116, 1500, 134, (170, 125, 80), (120, 85, 50))
        for px in (1210, 1290, 1370, 1450, 1490):
            m.line([(px, 134), (px - 20, SURF + 140)], (150, 110, 70), 7)
        m.gpoly([(1250, 118), (1450, 118), (1350, 64)], (230, 200, 140), (185, 150, 95))
    elif seg == "2-2":
        m.gpoly([(1300, SURF), (1500, 150), (1700, 170), (1920, 140), (1920, SURF)], (110, 170, 150), (70, 130, 120))
    elif seg == "2-3":
        for x in (200, 900, 1500):
            m.gell(x, 60, x + 300, 160, (70, 105, 132), (45, 75, 100))


def sky(m, seg):
    if seg == "2-3":
        m.vgrad(0, SURF, (30, 55, 80), (70, 110, 130))
    else:
        m.vgrad(0, SURF, (150, 205, 235), (230, 245, 245))


def far_layer(seg, clean, size, top_col):
    """Siluet jauh di bawah air (diburamkan)."""
    shapes = []
    c = mix(top_col, (20, 40, 50), 0.35) + (150,)
    if seg.startswith("1"):
        for x in range(-100, 2000, 260):
            h = random.randint(120, 260)
            shapes.append(("ell", [x, BED - h, x + 340, BED + 120], c))
    else:
        for x in range(-100, 2000, 300):
            h = random.randint(160, 320)
            shapes.append(("poly", [(x, BED + 40), (x + 80, BED - h), (x + 160, BED - h * 0.7), (x + 260, BED - h * 0.9), (x + 340, BED + 40)], c))
    return shapes


def background(seg, clean):
    w0, w1, c0, c1 = WATER[seg]
    top, bot = (c0, c1) if clean else (w0, w1)
    stage1 = seg.startswith("1")
    m = Img(1920, 1080)
    sky(m, seg)
    m.vgrad(SURF, BED + 40, top, bot)
    base = m.result()
    random.seed(hash(seg) % 1000 + (1 if clean else 0))
    # awan
    if seg != "2-3":
        soft_shapes(base, [("ell", [x, y, x + w, y + 46], (255, 255, 255, 170)) for x, y, w in
                           [(200, 30, 260), (330, 50, 200), (900, 20, 300), (1500, 40, 240), (1620, 26, 180)]], 10)
    # lapisan jauh di air
    soft_shapes(base, far_layer(seg, clean, base.size, top), 14)
    # pemandangan atas dan dasar (tajam)
    m2 = Img(1920, 1080)
    scenery(m2, seg)
    sand = (150, 125, 90) if stage1 else (215, 198, 160)
    if not clean and stage1:
        sand = (120, 102, 76)
    m2.gpoly([(0, BED), (480, BED - 14), (960, BED + 6), (1440, BED - 12), (1920, BED), (1920, 1080), (0, 1080)], lighten(sand, 0.1), darken(sand, 0.35))
    if stage1:
        rocks(m2, [(150, 90, 40), (700, 120, 46), (1100, 80, 30), (1600, 130, 50)], (120, 115, 105) if clean else (100, 95, 85))
        bed_plants(m2, clean, [(330, 90, (100, 170, 80)), (900, 70, (100, 170, 80)), (1250, 100, (100, 170, 80)), (1760, 90, (100, 170, 80))])
    else:
        rocks(m2, [(120, 100, 44), (980, 120, 40), (1660, 110, 46)], (140, 135, 125))
        corals(m2, clean, [(420, 1.0), (760, 0.9), (1080, 1.2), (1420, 1.0), (1800, 0.9)] if seg != "2-1" else [(700, 0.8), (1500, 0.8)])
    if seg == "1-3":
        m2.grect(1580, SURF, 1612, BED, (150, 150, 155), (90, 90, 96))
        m2.grect(1700, SURF, 1732, BED, (150, 150, 155), (90, 90, 96))
    if seg == "2-1":
        for px in (1210, 1290, 1370, 1450, 1490):
            m2.blend_line([(px - 20, SURF + 140), (px - 30, BED)], (110, 80, 50, 90), 6)
    base.alpha_composite(m2.result())
    # garis permukaan berkilau
    def surf(dr):
        for x in range(-40, 1960, 70):
            dr.ellipse([x, SURF - 8, x + 90, SURF + 10], fill=lighten(top, 0.35) + (230,))
        dr.line([(0, SURF + 2), (1920, SURF + 2)], fill=(255, 255, 255, 180), width=3)
    blur_composite(base, surf, 1.2)
    # cahaya dan partikel
    ray_alpha = 46 if clean else 22
    if seg == "2-3":
        ray_alpha = 26 if clean else 12
    god_rays(base, [random.randint(-100, 1900) for _ in range(6)], SURF, BED - 60, ray_alpha)
    caustics(base, SURF + 10, SURF + 160, 38 if clean else 18)
    if clean:
        particles(base, SURF + 20, BED, 120, (255, 255, 255), 1.2, 3.0, (40, 110))
    else:
        haze(base, (120, 110, 70) if stage1 else (70, 90, 80), 40, SURF, BED + 40)
        particles(base, SURF + 20, BED, 420, (150, 130, 90) if stage1 else (170, 175, 160), 1.5, 4.5, (50, 140))
    vignette(base, 0.32 if clean else 0.45, top=0)
    save_img(base.convert("RGB"), f"art/bg_{seg.replace('-', '_')}_{'clean' if clean else 'murky'}.png")


# ============================================================== story pictures (1280x720)
def story_base(sky_cols, water_cols, horizon):
    m = Img(1280, 720)
    m.vgrad(0, horizon, *sky_cols)
    m.vgrad(horizon, 720, *water_cols)
    return m


def story_finish(m, horizon, rays=True):
    base = m.result()
    soft_shapes(base, [("ell", [x, y, x + w, y + 40], (255, 255, 255, 160)) for x, y, w in [(100, 40, 220), (700, 60, 260), (1000, 30, 200)]], 10)
    return base


def story_intro():
    m = story_base(((150, 205, 235), (230, 245, 245)), ((150, 170, 120), (80, 105, 78)), 300)
    m.gpoly([(0, 250), (300, 230), (520, 260), (0, 300)], (140, 190, 120), (100, 150, 90))
    for x in (40, 150, 260):
        tree(m, x, 230, 1.1, (70, 140, 80))
    m.gpoly([(380, 250), (900, 250), (840, 330), (440, 330)], (255, 150, 110), (210, 90, 65))
    m.grect(380, 246, 900, 262, (255, 245, 230), (230, 215, 195), r=6)
    m.grect(430, 150, 560, 248, (252, 244, 226), (225, 210, 185), r=14)
    m.grect(660, 170, 740, 250, (120, 150, 175), (80, 105, 130), r=26)
    m.gcirc(700, 140, 36, (240, 205, 170), (210, 165, 130)); m.gell(670, 146, 730, 184, (250, 250, 250), (215, 215, 215))
    m.gpoly([(700, 92), (760, 128), (640, 128)], (240, 205, 130), (190, 145, 80))
    m.line([(740, 200), (900, 300)], (120, 90, 60), 4)
    m.gell(860, 300, 1080, 470, (190, 155, 110, 200), (140, 105, 70, 200))
    for i in range(-5, 6):
        m.line([(970 + i * 18, 304), (970 + i * 18 + 10, 466)], (110, 80, 50), 2)
    for (x, y, c) in [(910, 360, (240, 180, 60)), (980, 330, (240, 244, 247)), (1010, 410, (190, 228, 245)), (930, 420, (120, 200, 120))]:
        m.grect(x - 26, y - 18, x + 26, y + 18, lighten(c, 0.2), darken(c, 0.2), r=6)
    base = story_finish(m, 300)
    god_rays(base, [300, 700, 1000], 300, 720, 30)
    particles(base, 310, 720, 160, (150, 130, 90), 1.5, 4, (60, 140))
    vignette(base, 0.35)
    save_img(base.convert("RGB"), "art/story_intro.png")


def story_sea():
    m = story_base(((150, 205, 235), (230, 245, 245)), ((110, 205, 222), (32, 115, 160)), 330)
    m.gpoly([(0, 260), (300, 300), (420, 330), (0, 330)], (250, 232, 185), (220, 195, 145))
    m.gpoly([(560, 280), (900, 280), (860, 340), (600, 340)], (255, 150, 110), (210, 90, 65))
    m.grect(560, 276, 900, 290, (255, 245, 230), (230, 215, 195), r=6)
    m.grect(600, 190, 700, 278, (252, 244, 226), (225, 210, 185), r=12)
    m.grect(756, 230, 804, 280, lighten(SUIT, 0.15), SUIT_D, r=14)
    helmet_head(m, 780, 214, 22)
    m.grect(812, 200, 856, 278, (120, 150, 175), (80, 105, 130), r=18)
    m.gcirc(834, 184, 18, (240, 205, 170), (210, 165, 130))
    m.gpoly([(834, 150), (866, 172), (802, 172)], (240, 205, 130), (190, 145, 80))
    base = m.result()
    def wake(dr):
        for k in range(5):
            dr.line([(920 + k * 50, 330 + k * 3), (990 + k * 50, 330 + k * 3)], fill=(255, 255, 255, 200), width=4)
    blur_composite(base, wake, 1.5)
    base = story_finish_img(base)
    god_rays(base, [200, 600, 1000], 330, 720, 36)
    vignette(base, 0.3)
    save_img(base.convert("RGB"), "art/story_sea.png")


def story_finish_img(base):
    soft_shapes(base, [("ell", [x, y, x + w, y + 40], (255, 255, 255, 160)) for x, y, w in [(100, 40, 220), (700, 60, 260), (1000, 30, 200)]], 10)
    return base


def story_end():
    m = story_base(((160, 215, 245), (236, 248, 250)), ((95, 200, 232), (24, 98, 158)), 300)
    for x, col in [(200, (255, 140, 120)), (420, (255, 200, 90)), (900, (200, 120, 220)), (1120, (120, 200, 150))]:
        for dx, h in [(-22, 74), (0, 104), (22, 62)]:
            m.grect(x + dx - 10, 720 - h, x + dx + 10, 720, lighten(col, 0.2), darken(col, 0.25), r=10)
            m.gcirc(x + dx, 720 - h, 13, lighten(col, 0.3), col)
    m.gpoly([(460, 250), (820, 250), (780, 310), (500, 310)], (255, 150, 110), (210, 90, 65))
    m.grect(460, 246, 820, 260, (255, 245, 230), (230, 215, 195), r=6)
    m.grect(500, 170, 600, 248, (252, 244, 226), (225, 210, 185), r=12)
    m.gcirc(700, 210, 28, (240, 205, 170), (210, 165, 130)); m.gell(676, 214, 724, 244, (250, 250, 250), (215, 215, 215))
    m.gpoly([(700, 170), (742, 196), (658, 196)], (240, 205, 130), (190, 145, 80))
    m.line([(730, 200), (860, 140)], (120, 90, 60), 4); m.line([(860, 140), (860, 360)], (230, 230, 230), 2)
    for (x, y, c) in [(860, 380, (255, 170, 90)), (600, 500, (120, 200, 230)), (980, 560, (250, 210, 90)), (300, 450, (255, 170, 90))]:
        m.gell(x - 30, y - 18, x + 30, y + 18, lighten(c, 0.2), darken(c, 0.2))
        m.poly([(x + 28, y), (x + 50, y - 14), (x + 50, y + 14)], c)
        m.circ(x - 16, y - 4, 4, INK)
    m.gpoly([(0, 220), (300, 250), (380, 300), (0, 300)], (250, 232, 185), (220, 195, 145))
    for i, x in enumerate((60, 130, 200)):
        c = [(90, 170, 125), (110, 150, 205), (255, 150, 70)][i]
        m.grect(x - 16, 220, x + 16, 270, lighten(c, 0.15), darken(c, 0.2), r=10)
        m.gcirc(x, 205, 16, (232, 190, 150), (205, 155, 118))
    m.grect(90, 248, 170, 280, (215, 165, 100), (155, 110, 60), r=6)
    base = story_finish(m, 300)
    god_rays(base, [100, 500, 900, 1150], 300, 720, 48)
    caustics(base, 310, 430, 40, 50)
    particles(base, 310, 720, 90, (255, 255, 255), 1.2, 3, (50, 120))
    vignette(base, 0.25)
    save_img(base.convert("RGB"), "art/story_end.png")


# ============================================================== world map (1920x1080)
MAP_NODES = {
    "1-1": (980, 712), "1-2": (560, 520), "1-3": (290, 400),
    "2-1": (1300, 590), "2-2": (1530, 300), "2-3": (1770, 640),
}


def world_map():
    m = Img(1920, 1080)
    # laut: tiga pita makin dalam
    m.grect(0, 0, 1920, 1080, (120, 200, 230), (90, 175, 215))
    m.gpoly([(1380, 0), (1920, 0), (1920, 1080), (1240, 1080)], (70, 160, 215), (50, 135, 195))
    m.gpoly([(1640, 0), (1920, 0), (1920, 1080), (1560, 1080)], (45, 115, 180), (30, 90, 155))
    # daratan
    land = [(0, 0), (1230, 0), (1190, 220), (1120, 460), (1060, 700), (980, 900), (900, 1080), (0, 1080)]
    m.gpoly([(x + 40 if x > 0 else x, y) for x, y in land], (250, 232, 185), (225, 205, 155))  # pantai pasir
    m.gpoly(land, (190, 220, 150), (150, 195, 120))
    # bukit lembut
    for (x, y, w, h) in [(120, 520, 420, 200), (520, 760, 360, 180), (700, 120, 360, 170), (40, 860, 420, 220)]:
        m.gell(x, y, x + w, y + h, (175, 210, 140), (150, 190, 120))
    # sungai dari kota ke muara
    river = [(240, 250), (300, 340), (380, 420), (470, 480), (560, 530), (660, 610), (760, 680), (880, 720), (1000, 720), (1100, 690)]
    for wdt, col in [(78, (150, 140, 90)), (60, (160, 165, 110)), (44, (175, 185, 125))]:
        m.line(river, col, wdt)
    m.blend_line([(p[0], p[1] - 10) for p in river], (255, 255, 255, 60), 6)
    # kota
    for (bx, bw, bh) in [(70, 70, 150), (150, 60, 200), (220, 80, 130), (310, 60, 170), (380, 70, 120)]:
        m.grect(bx, 260 - bh, bx + bw, 260, (190, 196, 214), (150, 156, 176), r=4)
        for wy in range(260 - bh + 14, 250, 24):
            for wx in range(bx + 10, bx + bw - 14, 20):
                m.rect(wx, wy, wx + 10, wy + 10, (235, 240, 205))
    m.grect(200, 272, 340, 290, (120, 120, 125), (90, 90, 96), r=4)       # pintu air
    # rumah kampung
    def house(x, y, roof):
        m.grect(x, y, x + 54, y + 40, (252, 244, 226), (222, 205, 180), r=4)
        m.gpoly([(x - 8, y + 4), (x + 62, y + 4), (x + 27, y - 26)], lighten(roof, 0.15), darken(roof, 0.25))
        m.rect(x + 20, y + 18, x + 34, y + 40, (150, 110, 70))
    for (x, y, r) in [(600, 420, (255, 130, 100)), (680, 440, (255, 130, 100)), (470, 600, (110, 150, 205)),
                      (780, 780, (255, 130, 100)), (860, 800, (255, 130, 100))]:
        house(x, y, r)
    # pohon
    for (x, y) in [(120, 420), (180, 470), (420, 300), (480, 700), (700, 300), (760, 340), (300, 820), (380, 900), (620, 900), (840, 560)]:
        tree(m, x, y, 0.9, (80, 150, 85))
    # bakau di muara
    for x in range(930, 1100, 34):
        m.gcirc(x, 770, 20, (90, 160, 90), (55, 115, 65))
    # bagan
    bx, by = MAP_NODES["2-1"]
    m.grect(bx - 70, by + 50, bx + 70, by + 60, (170, 125, 80), (120, 85, 50))
    for px in (bx - 60, bx - 20, bx + 20, bx + 60):
        m.line([(px, by + 60), (px, by + 110)], (150, 110, 70), 5)
    m.gpoly([(bx - 50, by + 50), (bx + 50, by + 50), (bx, by + 20)], (230, 200, 140), (185, 150, 95))
    # terumbu
    rx, ry = MAP_NODES["2-2"]
    for (dx, dy, r) in [(-90, 50, 30), (70, 40, 34), (-20, 110, 26), (100, 120, 22)]:
        m.gell(rx + dx - r, ry + dy - r * 0.7, rx + dx + r, ry + dy + r * 0.7, (235, 235, 230), (190, 195, 195))
    # sarang kraken
    gx, gy = MAP_NODES["2-3"]
    m.gcirc(gx, gy + 20, 130, (40, 80, 120), (25, 55, 90))
    m.gcirc(gx, gy + 20, 70, (140, 150, 140), (90, 98, 94))
    base = m.result()
    # ombak dan tekstur laut
    def waves(dr):
        rnd = random.Random(5)
        for _ in range(140):
            x = rnd.uniform(1180, 1920); y = rnd.uniform(0, 1080)
            dr.arc([x, y, x + 40, y + 14], 200, 340, fill=(255, 255, 255, 110), width=3)
    blur_composite(base, waves, 0.6)
    # garis pantai berbuih
    def foam(dr):
        pts = [(1230 + 44, 0), (1190 + 44, 220), (1120 + 44, 460), (1060 + 44, 700), (980 + 44, 900), (900 + 44, 1080)]
        dr.line(pts, fill=(255, 255, 255, 200), width=8, joint="curve")
    blur_composite(base, foam, 2)
    # label tempat (tetap; nama segmen digambar oleh Godot)
    lab = Img(1920, 1080)
    lab.text(240, 54, "Kota", 34, (60, 70, 85), True)
    base.alpha_composite(lab.result())
    vignette(base, 0.3)
    save_img(base.convert("RGB"), "art/map_world.png")


# ============================================================== UI textures (9-slice)
def ui_button(name, top, bot, lip, pressed=False, alpha=255):
    S = 120
    m = Img(S, S)
    off = 4 if pressed else 0
    m.blend_rect(8, 14, 112, 112, (20, 40, 60, 70 if not pressed else 30), r=28)  # bayangan
    if not pressed:
        m.grect(8, 12, 112, 106, lip + (alpha,), darken(lip, 0.15) + (alpha,), r=28)  # bibir bawah (3D)
    m.grect(8, 6 + off, 112, 98 + off, top + (alpha,), bot + (alpha,), r=28)
    m.blend_rect(18, 12 + off, 102, 40 + off, (255, 255, 255, 110 if alpha == 255 else 50), r=14)  # kilau
    out = m.result()
    out = out.filter(ImageFilter.SMOOTH)
    save_img(out, f"art/{name}.png")


def ui_panel():
    S = 160
    m = Img(S, S)
    m.blend_rect(8, 14, 152, 156, (10, 30, 45, 70), r=44)
    m.grect(8, 6, 152, 148, (255, 255, 255, 245), (235, 245, 248, 245), r=40)
    m.rect(8, 6, 152, 148, None, r=40, outline=(255, 255, 255), width=3)
    m.blend_rect(14, 10, 146, 30, (255, 255, 255, 140), r=16)
    base = m.result()
    save_img(base, "art/ui_panel.png")


def ui_all():
    ui_button("ui_btn", (255, 255, 255), (226, 238, 242), (170, 196, 208))
    ui_button("ui_btn_hover", (255, 238, 228), (255, 205, 188), (225, 140, 115))
    ui_button("ui_btn_pressed", (255, 205, 188), (250, 180, 160), (225, 140, 115), pressed=True)
    ui_button("ui_btn_disabled", (235, 238, 240), (210, 216, 220), (180, 186, 192), alpha=150)
    ui_panel()


def title_logo():
    W, H = 1200, 320
    m = Img(W, H)
    f = ImageFont.truetype(FB, 190 * K)
    mask = Image.new("L", m.im.size, 0)
    ImageDraw.Draw(mask).text((W * K / 2, 150 * K), "MUARA", font=f, anchor="mm", fill=255)
    # bayangan
    sh = Image.new("RGBA", m.im.size, (0, 0, 0, 0))
    sh.paste((10, 40, 60, 140), (0, 0), mask.filter(ImageFilter.GaussianBlur(10 * K)).transform(mask.size, Image.AFFINE, (1, 0, 0, 0, 1, -10 * K)))
    m.im.alpha_composite(sh)
    # garis tepi tebal
    edge = mask.filter(ImageFilter.MaxFilter(25)).filter(ImageFilter.MaxFilter(25))
    m.im.paste((20, 70, 100, 255), (0, 0), edge)
    # isi gradasi
    m._grad_paste(mask, 70, 240, (255, 236, 150), (255, 140, 90))
    # kilau atas
    hl = Image.new("L", m.im.size, 0)
    ImageDraw.Draw(hl).rectangle([0, 0, W * K, 120 * K], fill=110)
    hl = Image.fromarray(np.minimum(np.asarray(hl), np.asarray(mask)).astype(np.uint8))
    m.im.paste((255, 255, 255, 255), (0, 0), hl)
    # gelembung hiasan
    for (x, y, r) in [(1080, 70, 18), (1120, 30, 10), (1050, 20, 8), (110, 250, 14), (80, 210, 8)]:
        m.circ(x, y, r, (230, 250, 255, 200), outline=(255, 255, 255), width=3)
    save_img(m.result(), "art/title_logo.png")


def icon():
    m = Img(128, 128)
    m.gcirc(64, 64, 62, (120, 210, 230), (50, 140, 180))
    helmet_head(m, 64, 60, 34, look=0)
    m.grect(34, 98, 94, 116, lighten(SUIT, 0.15), SUIT_D, r=10)
    save_img(shade_sprite(m.result(), 2, 0.2, 0.12), "icon.png")


# ============================================================== main menu & UI kit
def menu_bg():
    W, H, SW = 1920, 1080, 340
    m = Img(W, H)
    m.vgrad(0, SW, (110, 190, 235), (225, 244, 248))
    m.vgrad(SW, H, (90, 205, 230), (16, 70, 130))
    base = m.result()
    random.seed(21)
    # matahari dan awan
    soft_shapes(base, [("ell", [1460, -120, 1860, 260], (255, 250, 220, 150))], 60)
    soft_shapes(base, [("ell", [1560, 20, 1740, 190], (255, 252, 235, 255))], 6)
    soft_shapes(base, [("ell", [x, y, x + w, y + 54], (255, 255, 255, 210)) for x, y, w in
                       [(120, 60, 300), (260, 90, 220), (820, 40, 340), (980, 70, 240), (1300, 150, 260)]], 12)
    soft_shapes(base, [("poly", [(x, 1000), (x + 120, 760 - random.randint(0, 120)), (x + 260, 1000)], (20, 70, 110, 120)) for x in range(-60, 1960, 220)], 18)
    m2 = Img(W, H)
    # pulau jauh dengan pohon kelapa
    m2.gpoly([(-40, SW + 4), (120, SW - 60), (360, SW - 80), (560, SW - 30), (660, SW + 4)], (150, 200, 150), (110, 165, 120))
    m2.gpoly([(1180, SW + 4), (1330, SW - 34), (1480, SW - 20), (1560, SW + 4)], (170, 205, 175), (140, 180, 150))
    for x in (200, 300, 420):
        m2.line([(x, SW - 60), (x + 18, SW - 170)], (140, 100, 60), 8)
        for a in range(5):
            ang = math.radians(195 + a * 37)
            m2.line([(x + 18, SW - 170), (x + 18 + 70 * math.cos(ang), SW - 170 + 40 * math.sin(ang) + 30)], (70, 150, 85), 10)
    # dasar laut
    m2.gpoly([(0, 980), (400, 950), (900, 990), (1400, 955), (1920, 975), (1920, 1080), (0, 1080)], (235, 215, 170), (180, 155, 110))
    pal = [(255, 140, 120), (255, 200, 90), (200, 120, 220), (120, 200, 150), (255, 160, 190)]
    for i, (x, sc) in enumerate([(120, 1.3), (330, 1.0), (980, 1.1), (1180, 1.4), (1450, 0.9), (1700, 1.3), (1860, 1.0)]):
        col = pal[i % len(pal)]
        for dx, h in [(-26, 70), (0, 110), (26, 64)]:
            m2.grect(x + dx * sc - 11 * sc, 980 - h * sc, x + dx * sc + 11 * sc, 1000, lighten(col, 0.2), darken(col, 0.25), r=11 * sc)
            m2.gcirc(x + dx * sc, 980 - h * sc, 14 * sc, lighten(col, 0.3), col)
    for (x, w, h) in [(520, 160, 60), (760, 120, 44), (1560, 150, 56)]:
        m2.gell(x, 975 - h, x + w, 975 + h * 0.4, (160, 165, 160), (95, 100, 100))
    for x in (600, 880, 1300, 1620):
        for j in range(4):
            pts = [(x + j * 18, 1000)]
            for k in range(9):
                t = k / 8.0
                pts.append((x + j * 18 + math.sin(t * 3 + j) * 10 + 5, 1000 - (130 - j * 16) * t))
            for k in range(8, -1, -1):
                t = k / 8.0
                pts.append((x + j * 18 + math.sin(t * 3 + j) * 10 + 22 - t * 14, 1000 - (130 - j * 16) * t))
            m2.gpoly(pts, (120, 210, 130), (40, 120, 80))
    base.alpha_composite(m2.result())
    def surf(dr):
        for x in range(-40, 1960, 80):
            dr.ellipse([x, SW - 9, x + 100, SW + 11], fill=(190, 240, 250, 230))
        dr.line([(0, SW + 2), (1920, SW + 2)], fill=(255, 255, 255, 200), width=3)
    blur_composite(base, surf, 1.2)
    caustics(base, SW + 10, SW + 200, 40, 120)
    particles(base, SW + 30, 1000, 160, (255, 255, 255), 1.2, 3.2, (40, 120))
    # sisi kiri sedikit lebih gelap supaya tombol mudah dibaca
    w, h = base.size
    xs = np.clip(1.0 - np.arange(w) / 1000.0, 0, 1) ** 1.6
    ov = np.zeros((h, w, 4), np.uint8)
    ov[:, :, 0] = 8; ov[:, :, 1] = 30; ov[:, :, 2] = 50
    ov[:, :, 3] = (xs[None, :] * 120).astype(np.uint8)
    ov[:SW, :, 3] = (ov[:SW, :, 3] * 0.35).astype(np.uint8)
    base.alpha_composite(Image.fromarray(ov, "RGBA"))
    vignette(base, 0.3)
    save_img(base.convert("RGB"), "art/menu_bg.png")


def menu_rays():
    base = fx_layer((1920, 1080))
    random.seed(4)
    god_rays(base, [300, 640, 980, 1280, 1560], 340, 1040, 60, spread=320, blur=26)
    save_img(base, "art/menu_rays.png")


def ui_primary():
    ui_button("ui_btn_primary", (255, 178, 110), (245, 110, 70), (190, 70, 45))
    ui_button("ui_btn_primary_hover", (255, 200, 135), (255, 130, 85), (200, 80, 50))
    ui_button("ui_btn_primary_pressed", (245, 130, 85), (225, 95, 60), (190, 70, 45), pressed=True)


def badge(name, glyph, col=(60, 175, 190)):
    S = 56
    m = Img(S, S)
    m.blend_ell(4, 7, 54, 57, (10, 40, 60, 80))
    m.gcirc(28, 26, 24, lighten(col, 0.25), darken(col, 0.2))
    m.circ(28, 26, 24, None, outline=(255, 255, 255), width=3)
    m.blend_ell(14, 8, 36, 20, (255, 255, 255, 110))
    glyph(m)
    save_img(m.result(), f"art/{name}.png")


def icons():
    W = (255, 255, 255)
    badge("icon_play", lambda m: m.poly([(22, 15), (40, 26), (22, 37)], (245, 120, 75)), (255, 255, 255))
    def mapg(m):
        m.poly([(15, 17), (23, 14), (33, 18), (41, 15), (41, 35), (33, 38), (23, 34), (15, 37)], W)
        m.line([(23, 14), (23, 34)], (60, 175, 190), 2); m.line([(33, 18), (33, 38)], (60, 175, 190), 2)
    badge("icon_map", mapg)
    def gear(m):
        for a in range(0, 360, 45):
            x = 28 + 12 * math.cos(math.radians(a)); y = 26 + 12 * math.sin(math.radians(a))
            m.circ(x, y, 4.5, W)
        m.circ(28, 26, 11, W); m.circ(28, 26, 4.5, (60, 175, 190))
    badge("icon_settings", gear)
    def heart(m):
        m.circ(22, 22, 7, W); m.circ(34, 22, 7, W); m.poly([(15.5, 24), (40.5, 24), (28, 38)], W)
    badge("icon_credits", heart, (240, 120, 150))
    def door(m):
        m.rect(16, 13, 32, 39, None, outline=W, width=3, r=2)
        m.line([(26, 26), (42, 26)], W, 4); m.poly([(38, 20), (45, 26), (38, 32)], W)
    badge("icon_exit", door, (150, 160, 175))
    def back(m):
        m.line([(18, 26), (38, 26)], W, 5); m.poly([(14, 26), (24, 17), (24, 35)], W)
    badge("icon_back", back, (150, 160, 175))
    def retry(m):
        m.arc((16, 14, 40, 38), 40, 330, W, 4); m.poly([(36, 12), (42, 20), (33, 22)], W)
    badge("icon_retry", retry, (60, 175, 190))
    def nxt(m):
        m.poly([(18, 15), (30, 26), (18, 37)], W); m.poly([(28, 15), (40, 26), (28, 37)], W)
    badge("icon_next", nxt, (245, 120, 75))


def ribbon():
    m = Img(640, 120)
    for side in (0, 1):
        x = 0 if side == 0 else 640
        sgn = 1 if side == 0 else -1
        m.gpoly([(x, 30), (x + sgn * 90, 30), (x + sgn * 90, 104), (x, 104), (x + sgn * 26, 67)], (225, 95, 60), (180, 70, 45))
        m.poly([(x + sgn * 70, 92), (x + sgn * 90, 104), (x + sgn * 90, 92)], (140, 50, 35))
    m.grect(60, 16, 580, 92, (255, 170, 105), (240, 110, 70), r=10)
    m.blend_rect(70, 20, 570, 40, (255, 255, 255, 90), r=8)
    m.rect(60, 16, 580, 92, None, r=10, outline=(255, 235, 215), width=3)
    save_img(m.result(), "art/ui_ribbon.png")


def knobs():
    m = Img(44, 44)
    m.blend_ell(3, 6, 41, 44, (10, 40, 60, 90))
    m.gcirc(22, 20, 18, (255, 190, 130), (240, 105, 65))
    m.circ(22, 20, 18, None, outline=(255, 255, 255), width=4)
    save_img(m.result(), "art/ui_knob.png")
    for on in (True, False):
        t = Img(96, 52)
        t.blend_rect(4, 8, 92, 52, (10, 40, 60, 70), r=22)
        t.grect(4, 4, 92, 46, (110, 210, 170) if on else (205, 212, 218), (60, 160, 125) if on else (170, 178, 186), r=21)
        cx = 70 if on else 26
        t.gcirc(cx, 25, 17, (255, 255, 255), (225, 232, 236))
        save_img(t.result(), f"art/ui_toggle_{'on' if on else 'off'}.png")


# ============================================================== bos: kraken terlilit sampah
KRAKEN = (205, 110, 165)


def kraken():
    # kepala (mantel) 360x380; pusat kepala ada di tengah gambar. Tentakel digambar oleh Godot.
    m = Img(360, 380)
    m.gell(30, 10, 330, 300, lighten(KRAKEN, 0.2), darken(KRAKEN, 0.25))
    m.gell(70, 200, 290, 370, KRAKEN, darken(KRAKEN, 0.35))
    m.gell(40, 30, 320, 290, lighten(KRAKEN, 0.15), darken(KRAKEN, 0.15))
    rnd = random.Random(11)
    for _ in range(16):
        x = rnd.randint(70, 290); y = rnd.randint(40, 200)
        r = rnd.randint(8, 18)
        m.gcirc(x, y, r, darken(KRAKEN, 0.1), darken(KRAKEN, 0.3))
    m.blend_ell(80, 40, 170, 110, (255, 255, 255, 90))
    m.blend_ell(100, 54, 130, 74, (255, 255, 255, 160))
    m.save("art/kraken_head.png", outline=4, light=0.3, grad=0.2)

    def face(name, kind):
        f = Img(260, 150)
        for cx in (70, 190):
            if kind == "hurt":
                f.line([(cx - 32, 46), (cx + 26, 70), (cx - 32, 94)], INK, 10)
            elif kind == "happy":
                f.arc((cx - 34, 42, cx + 34, 106), 200, 340, INK, 10)
            else:
                f.gell(cx - 36, 34, cx + 36, 112, WHITE, (225, 230, 235))
                f.gcirc(cx + 4, 80, 20, (60, 70, 90), INK)
                f.circ(cx - 4, 70, 7, WHITE)
        if kind == "worried":
            f.line([(36, 26), (100, 14)], INK, 7); f.line([(224, 26), (160, 14)], INK, 7)
            f.arc((100, 112, 160, 146), 200, 340, INK, 6)
        elif kind == "hurt":
            f.gell(104, 104, 156, 146, (120, 40, 60), (80, 25, 40))
            f.blend_ell(20, 96, 60, 118, (255, 120, 140, 160)); f.blend_ell(200, 96, 240, 118, (255, 120, 140, 160))
            f.gell(232, 30, 248, 56, (170, 220, 255), (110, 170, 230))
        else:
            f.arc((96, 96, 164, 144), 20, 160, INK, 7)
            f.blend_ell(20, 96, 60, 118, (255, 140, 160, 170)); f.blend_ell(200, 96, 240, 118, (255, 140, 160, 170))
        f.save(f"art/{name}.png", outline=2, light=0.15)
    face("kraken_face", "worried")
    face("kraken_face_hurt", "hurt")
    face("kraken_face_happy", "happy")


# ============================================================== tentakel kraken (6 desain x 3 potongan)
# Setiap tentakel dipotong jadi pangkal (base), tengah (mid), dan ujung (tip). Godot menyambung dan
# menekuk ketiganya. Ketiga potongan sama tinggi (96 px) supaya sambungannya pas; bentuk menyempit
# terus dari pangkal ke ujung. Ujung kiri dan kanan potongan base/mid dibiarkan terpotong rata.
TENT_PARTS = {"base": (0.0, 6 / 16), "mid": (5 / 16, 11 / 16), "tip": (10 / 16, 1.0)}
TENT_DESIGNS = [
    # warna kulit, tebal pangkal, kelengkungan sempit, pola isap, ujung, hiasan
    dict(col=KRAKEN, base=42, p=0.85, suck="double", tip="point", deco=None),
    dict(col=mix(KRAKEN, (230, 120, 150), 0.4), base=40, p=0.75, suck="single", tip="curl", deco=None),
    dict(col=mix(KRAKEN, (180, 100, 190), 0.35), base=42, p=0.9, suck="double", tip="point", deco="stripes"),
    dict(col=mix(KRAKEN, (215, 120, 140), 0.3), base=38, p=0.7, suck="single", tip="club", deco="spots"),
    dict(col=mix(KRAKEN, (240, 150, 185), 0.45), base=34, p=0.8, suck="zigzag", tip="curl", deco=None),
    dict(col=mix(KRAKEN, (190, 95, 150), 0.4), base=44, p=1.0, suck="double", tip="point", deco="scar"),
]


def _tent_half(d, u):
    h = d["base"] * (1 - u) ** d["p"] + 4
    if d["tip"] == "club" and u > 0.86:
        h += 7 * math.sin((u - 0.86) / 0.14 * math.pi)
    return h


def kraken_tentacles():
    W, H = 176, 96
    for ti, d in enumerate(TENT_DESIGNS, 1):
        col = d["col"]
        edge = darken(col, 0.45)
        for part, (u0, u1) in TENT_PARTS.items():
            m = Img(W, H)
            last = 1.0 if part == "tip" else u1
            end_x = W - (14 if part == "tip" and d["tip"] == "curl" else 4) if part == "tip" else W + 2
            x_of = lambda u: -2 + (u - u0) / (u1 - u0) * (end_x + 2)
            top, bot = [], []
            for i in range(41):
                u = u0 + (last - u0) * i / 40
                x = x_of(u)
                h = _tent_half(d, u)
                top.append((x, H / 2 - h))
                bot.append((x, H / 2 + h))
            outline_pts = top + bot[::-1]
            if part == "tip":
                if d["tip"] == "curl":
                    cx, cy = end_x - 2, H / 2 - 10
                    curl = [(cx + 10 * math.cos(t), cy + 10 * math.sin(t)) for t in np.linspace(math.pi * 0.5, math.pi * 2.3, 14)]
                    outline_pts = top + [(end_x + 2, H / 2 - 2)] + bot[::-1]
                    m.blend_line(curl, col + (255,), 6)
                elif d["tip"] == "point":
                    outline_pts = top + [(W - 1, H / 2 + 1)] + bot[::-1]
            m.gpoly(outline_pts, lighten(col, 0.2), darken(col, 0.28))
            # perut lebih terang di bawah
            belly = [(x, y - (y - H / 2) * 0.45) for x, y in bot]
            m.blend_poly(bot + belly[::-1], lighten(col, 0.3) + (70,))
            # hiasan per desain
            if d["deco"] == "stripes":
                for i in range(2, 40, 5):
                    u = u0 + (last - u0) * i / 40
                    x = x_of(u); h = _tent_half(d, u)
                    m.blend_line([(x - 4, H / 2 - h + 2), (x + 3, H / 2 + h * 0.2)], darken(col, 0.3) + (110,), max(2, h * 0.18))
            elif d["deco"] == "spots":
                rnd = random.Random(ti * 10 + len(part))
                for _ in range(7):
                    u = u0 + (last - u0) * rnd.uniform(0.05, 0.95)
                    x = x_of(u); h = _tent_half(d, u)
                    m.blend_ell(x - h * 0.22, H / 2 - h * 0.6, x + h * 0.22, H / 2 - h * 0.6 + h * 0.36, darken(col, 0.25) + (120,))
            elif d["deco"] == "scar" and part == "mid":
                xm = W * 0.5
                h = _tent_half(d, (u0 + u1) / 2)
                for k in (-6, 0, 6):
                    m.blend_line([(xm + k - 3, H / 2 - h + 3), (xm + k + 3, H / 2 + h - 3)], (245, 205, 215, 150), 3)
            # kilau punggung
            m.blend_line([(x, y + 7) for x, y in top[1:-3]], (255, 255, 255, 75), 4)
            # alat isap
            n = 12
            for i in range(n):
                f = (i + 0.5) / n
                u = u0 + (last - u0) * f
                if part == "tip" and f > 0.85:
                    continue
                x = x_of(u); h = _tent_half(d, u)
                r = max(2.2, h * 0.27)
                rows = {"double": [0.5, 0.82], "single": [0.68], "zigzag": [0.55 if i % 2 else 0.8]}[d["suck"]]
                for rr in rows:
                    cy = H / 2 + h * rr
                    rs = r * (0.75 if len(rows) == 2 else 1.0)
                    m.gell(x - rs * 1.1, cy - rs * 0.8, x + rs * 1.1, cy + rs * 0.8, (255, 228, 236), (232, 168, 194))
                    m.ell(x - rs * 0.45, cy - rs * 0.3, x + rs * 0.45, cy + rs * 0.3, darken((232, 168, 194), 0.18))
            # garis tepi hanya di atas dan bawah (ujung potongan tetap rata agar sambungan tak terlihat)
            if part == "tip":
                m.line(outline_pts[1:-1], edge, 3)
                if d["tip"] == "curl":
                    m.line(curl, edge, 1.5)
            else:
                m.line(top, edge, 3); m.line(bot, edge, 3)
            m.save(f"art/kraken_tentacle_{ti}_{part}.png", outline=0, light=0.2, grad=0.1)


# ============================================================== efek bidik alat
def aim_fx():
    d = Img(16, 16)
    d.blend_ell(2, 3, 15, 16, (0, 0, 0, 60))
    d.circ(8, 7, 5.5, WHITE)
    save_img(d.result(), "art/fx_aim_dot.png")

    # tali harpun, bisa diulang (tile) mendatar
    r = Img(32, 8)
    r.rect(0, 1, 32, 7, (225, 214, 186))
    for x in range(-8, 40, 8):
        r.line([(x, 7), (x + 6, 1)], (170, 150, 110), 2)
    save_img(r.result(), "art/fx_rope.png")

    # kerucut magnet: puncak di kiri tengah, jari-jari 512, sudut ±22.5°
    W, H = 512, 400
    c = Img(W, H)
    a = math.radians(22.5)
    pts = [(0, H / 2)] + [(512 * math.cos(t), H / 2 + 512 * math.sin(t)) for t in np.linspace(-a, a, 30)]
    c.blend_poly(pts, (255, 190, 175, 60))
    for k in range(10, 512, 26):
        for sgn in (-1, 1):
            c.circ(k * math.cos(a), H / 2 + sgn * k * math.sin(a), 3.2, (255, 160, 150))
    arc_pts = [(505 * math.cos(t), H / 2 + 505 * math.sin(t)) for t in np.linspace(-a, a, 30)]
    c.line(arc_pts, (255, 140, 125), 5)
    save_img(c.result(), "art/fx_magnet_cone.png")

    # cincin target jaring, jari-jari 110 di gambar 240
    n = Img(240, 240)
    for i in range(36):
        t0 = i * 10
        n.arc((10, 10, 230, 230), t0, t0 + 6, (190, 255, 215), 5)
    n.circ(120, 120, 6, (190, 255, 215))
    save_img(n.result(), "art/fx_net_ring.png")


# ============================================================== peta, HUD, dan bar (pengganti bentuk buatan kode)
def map_marks():
    d = Img(24, 24)
    d.blend_ell(4, 6, 22, 24, (0, 0, 0, 55))
    d.circ(11, 11, 7.5, WHITE)
    save_img(d.result(), "art/ui_map_dot.png")

    r = Img(160, 160)
    r.circ(80, 80, 66, None, outline=(255, 215, 80), width=8)
    r.blend_ell(8, 8, 152, 152, (255, 230, 120, 0))
    for i in range(8):
        t = math.radians(i * 45)
        r.circ(80 + 66 * math.cos(t), 80 + 66 * math.sin(t), 5, (255, 240, 170))
    save_img(r.result(), "art/ui_map_ring.png")

    p = Img(104, 136)
    p.blend_ell(22, 118, 82, 134, (0, 0, 0, 60))
    p.poly([(38, 92), (66, 92), (52, 124)], WHITE)
    p.circ(52, 50, 46, WHITE)
    p.circ(52, 50, 40, (226, 238, 242))
    save_img(p.result(), "art/ui_map_pin.png")


def hud_parts():
    # garis batas bocor (kiri layar), diulang tegak
    L = Img(24, 96)
    L.rect(8, 0, 16, 96, (255, 110, 95, 150))
    L.gcirc(12, 48, 10, (255, 150, 120), (230, 80, 60))
    L.circ(12, 48, 10, None, outline=WHITE, width=2)
    save_img(L.result(), "art/ui_leak_line.png")

    f = Img(64, 64)
    for i in range(16):
        f.blend_rect(i * 4, 0, i * 4 + 4, 64, (255, 80, 60, int(210 * (1 - i / 16) ** 1.6)))
    save_img(f.result(), "art/fx_leak_flash.png")

    t = Img(16, 44)
    t.poly([(2, 0), (14, 0), (8, 10)], (255, 112, 90))
    t.rect(6, 6, 10, 44, (255, 112, 90), r=2)
    save_img(t.result(), "art/ui_target_mark.png")

    def panel(name, S, rad, fill0, fill1, lip, shadow=True, alpha=240, border=None):
        m = Img(S, S)
        if shadow:
            m.blend_rect(6, 12, S - 6, S - 2, (10, 30, 45, 60), r=rad)
        if lip:
            m.grect(6, 8, S - 6, S - 8, lip + (alpha,), darken(lip, 0.1) + (alpha,), r=rad)
        m.grect(6, 4, S - 6, S - 13, fill0 + (alpha,), fill1 + (alpha,), r=rad)
        if border:
            m.rect(8, 6, S - 8, S - 15, None, r=rad - 2, outline=border, width=5)
        m.blend_rect(14, 8, S - 14, 22, (255, 255, 255, 90), r=8)
        save_img(m.result(), f"art/{name}.png")

    panel("ui_hud_panel", 120, 28, (255, 255, 255), (238, 246, 248), (184, 204, 214))
    panel("ui_slot", 104, 22, (255, 255, 255), (238, 246, 248), (184, 204, 214))
    panel("ui_slot_selected", 104, 22, (255, 255, 255), (255, 244, 238), (225, 140, 115), border=(255, 112, 90))
    panel("ui_slot_locked", 104, 22, (222, 226, 228), (205, 210, 214), None, shadow=False, alpha=215)

    h = Img(96, 64)
    h.grect(2, 2, 94, 62, (52, 58, 70, 230), (38, 44, 56, 230), r=30)
    h.blend_rect(14, 6, 82, 16, (255, 255, 255, 40), r=5)
    save_img(h.result(), "art/ui_hint_panel.png")

    rb = Img(96, 96)
    rb.blend_ell(6, 12, 90, 94, (10, 30, 45, 60))
    rb.gell(4, 8, 92, 90, (184, 204, 214), (160, 182, 194))
    rb.gell(4, 4, 92, 84, (255, 255, 255), (232, 242, 246))
    rb.blend_ell(18, 10, 78, 30, (255, 255, 255, 120))
    save_img(rb.result(), "art/ui_round_btn.png")

    def bar(name, top, bot, lip=None, H=28):
        b = Img(64, H)
        if lip:
            b.grect(0, 0, 64, H, lip, darken(lip, 0.1), r=H / 2)
            b.grect(0, 0, 64, H - 4, top, bot, r=H / 2)
            b.blend_rect(8, 3, 56, 9, (255, 255, 255, 90), r=3)
        else:
            b.grect(0, 0, 64, H, top, bot, r=H / 2)
            b.blend_rect(6, H - 7, 58, H - 2, (255, 255, 255, 60), r=3)
        save_img(b.result(), f"art/{name}.png")

    bar("ui_bar_bg", (176, 196, 206), (206, 220, 226))
    bar("ui_bar_green", (110, 210, 175), (70, 185, 150), (50, 148, 122))
    bar("ui_bar_blue", (120, 190, 240), (80, 160, 225), (56, 128, 184))
    bar("ui_bar_red", (255, 140, 115), (250, 105, 85), (204, 76, 60))
    bar("ui_slider_track", (190, 206, 214), (214, 226, 232), H=20)
    bar("ui_slider_fill", (255, 175, 120), (255, 130, 90), H=20)

    def node(name, c0, c1):
        n = Img(120, 120)
        n.blend_ell(14, 22, 106, 116, (5, 25, 40, 90))
        n.circ(60, 58, 48, WHITE)
        n.gcirc(60, 58, 42, c0, c1)
        n.blend_ell(32, 24, 88, 46, (255, 255, 255, 80))
        save_img(n.result(), f"art/{name}.png")

    node("ui_node_river", (255, 140, 115), (235, 95, 75))
    node("ui_node_river_hover", (255, 170, 145), (250, 120, 95))
    node("ui_node_sea", (80, 175, 190), (40, 135, 155))
    node("ui_node_sea_hover", (115, 200, 215), (70, 165, 185))
    node("ui_node_locked", (160, 168, 175), (125, 134, 142))


if __name__ == "__main__":
    raka_body(); gun_all()
    portrait("kakek", kakek); portrait("busari", busari); portrait("raka", raka_face)
    for i, c in enumerate([(240, 180, 60), (120, 200, 120), (230, 120, 160)], 1):
        sachet(i, c)
    bag(); bottle(); styro(); sandal(); can(); tire(); ghostnet(); flake(1); flake(2)
    for i, c in enumerate([(255, 170, 90), (120, 200, 230), (250, 210, 90)], 1):
        fish(i, c)
    jelly(); turtle(); wood(); bubble(); fx_bubble(); box(); hook(); net_open(); kraken(); boat()
    for seg in WATER:
        background(seg, False); background(seg, True)
    story_intro(); story_sea(); story_end()
    world_map(); ui_all(); title_logo(); icon()
    menu_bg(); menu_rays(); ui_primary(); icons(); ribbon(); knobs()
    kraken_tentacles(); aim_fx(); map_marks(); hud_parts()
    print("assets ok")
