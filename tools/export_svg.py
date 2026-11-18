"""Ekspor semua gambar acuan Muara sebagai SVG vektor yang bisa di-import ke Figma.

Memakai fungsi gambar yang sama dengan gen_assets.py, tetapi setiap bentuk (kotak, elips, poligon,
garis, gradasi) ditulis sebagai elemen SVG bernama, bukan piksel. Efek buram (cahaya, awan) memakai
filter blur SVG; Figma mengubahnya menjadi Layer blur.

Pemakaian: python3 tools/export_svg.py <folder_keluaran>
Hasil: <folder>/svg/<nama>.svg (satu per aset) dan <folder>/Muara_Semua_Aset.svg (satu papan besar
berisi semua aset sebagai grup bernama, untuk di-drag ke Figma sekaligus).
"""
import base64, io, math, os, random, sys
import gen_assets as G
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "figma_export"
_uid = [0]


def uid(p):
    _uid[0] += 1
    return f"{p}{_uid[0]}"


def col(c):
    c = tuple(int(v) for v in c)
    a = c[3] / 255.0 if len(c) == 4 else 1.0
    return "#%02X%02X%02X" % c[:3], round(a, 3)


def fill_attr(c):
    if c is None:
        return 'fill="none"'
    h, a = col(c)
    return f'fill="{h}"' + (f' fill-opacity="{a}"' if a < 1 else "")


def stroke_attr(c, w):
    h, a = col(c)
    return f'stroke="{h}" stroke-width="{w:g}"' + (f' stroke-opacity="{a}"' if a < 1 else "")


def arc_pts(box, a0, a1, steps=24):
    x0, y0, x1, y1 = box
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    if a1 < a0:
        a1 += 360
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def pts_str(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


class Drawer:
    """Pengganti ImageDraw: menulis bentuk ke SvgImg. scale = pembagi koordinat (K untuk m.d)."""

    def __init__(s, svg, scale=1.0, target=None):
        s.svg, s.k, s.t = svg, scale, target

    def _b(s, box):
        return [v / s.k for v in box]

    def _add(s, el):
        (s.t if s.t is not None else s.svg.els).append(el)

    def polygon(s, pts, fill=None, outline=None):
        pts = [(x / s.k, y / s.k) for x, y in pts]
        if fill is not None and len(fill) == 4 and fill[3] == 0:
            s.svg.erase(f'<polygon points="{pts_str(pts)}" fill="black"/>')
            return
        s._add(f'<polygon points="{pts_str(pts)}" {fill_attr(fill)}/>')

    def line(s, pts, fill=None, width=1, joint=None):
        pts = [(x / s.k, y / s.k) for x, y in pts]
        s._add(f'<polyline points="{pts_str(pts)}" fill="none" {stroke_attr(fill, width / s.k)} stroke-linecap="round" stroke-linejoin="round"/>')

    def ellipse(s, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = s._b(box)
        shape = f'<ellipse cx="{(x0 + x1) / 2:.1f}" cy="{(y0 + y1) / 2:.1f}" rx="{(x1 - x0) / 2:.1f}" ry="{(y1 - y0) / 2:.1f}"'
        if fill is not None and len(fill) == 4 and fill[3] == 0:
            s.svg.erase(shape + ' fill="black"/>')
            return
        st = f" {stroke_attr(outline, width / s.k)}" if outline else ""
        s._add(shape + f" {fill_attr(fill)}{st}/>")

    def rectangle(s, box, fill=None, outline=None, width=1):
        s.rounded_rectangle(box, 0, fill, outline, width)

    def rounded_rectangle(s, box, radius=0, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = s._b(box)
        r = radius / s.k
        shape = f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" rx="{r:.1f}"'
        if fill is not None and len(fill) == 4 and fill[3] == 0:
            s.svg.erase(shape + ' fill="black"/>')
            return
        st = f" {stroke_attr(outline, width / s.k)}" if outline else ""
        s._add(shape + f" {fill_attr(fill)}{st}/>")

    def arc(s, box, a0, a1, fill=None, width=1):
        pts = arc_pts(s._b(box), a0, a1)
        s._add(f'<polyline points="{pts_str(pts)}" fill="none" {stroke_attr(fill, width / s.k)} stroke-linecap="round"/>')

    def pieslice(s, box, a0, a1, fill=None):
        b = s._b(box)
        pts = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)] + arc_pts(b, a0, a1)
        s._add(f'<polygon points="{pts_str(pts)}" {fill_attr(fill)}/>')


class SvgImg:
    def __init__(s, w, h, bg=(0, 0, 0, 0)):
        s.w, s.h = w, h
        s.els, s.defs = [], []
        s.d = Drawer(s, G.K)
        if bg and len(bg) == 4 and bg[3] > 0:
            s.els.append(f'<rect width="{w}" height="{h}" {fill_attr(bg)}/>')

    size = property(lambda s: (s.w, s.h))

    # --- bentuk dasar (koordinat logis)
    def rect(s, x0, y0, x1, y1, fill, r=0, outline=None, width=0):
        Drawer(s).rounded_rectangle([x0, y0, x1, y1], r, G.rgba(fill) if fill else None, G.rgba(outline) if outline else None, width)

    def ell(s, x0, y0, x1, y1, fill, outline=None, width=0):
        Drawer(s).ellipse([x0, y0, x1, y1], G.rgba(fill) if fill else None, G.rgba(outline) if outline else None, width)

    def circ(s, x, y, r, fill, outline=None, width=0):
        s.ell(x - r, y - r, x + r, y + r, fill, outline, width)

    def poly(s, pts, fill, outline=None):
        Drawer(s).polygon(pts, G.rgba(fill))

    def line(s, pts, fill, w=2):
        Drawer(s).line(pts, G.rgba(fill), w)

    def arc(s, box, a0, a1, fill, w=2):
        Drawer(s).arc(box, a0, a1, G.rgba(fill), w)

    def pie(s, box, a0, a1, fill):
        Drawer(s).pieslice(box, a0, a1, G.rgba(fill))

    def text(s, x, y, t, size, fill=G.INK, bold=False, anchor="mm"):
        t = t.replace("&", "&amp;").replace("<", "&lt;")
        s.els.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans, Arial, sans-serif" font-size="{size}" '
                     f'font-weight="{"bold" if bold else "normal"}" text-anchor="middle" dominant-baseline="central" {fill_attr(G.rgba(fill))}>{t}</text>')

    blend_poly = poly
    blend_ell = ell
    blend_line = line

    def blend_rect(s, x0, y0, x1, y1, fill, r=0):
        s.rect(x0, y0, x1, y1, fill, r)

    # --- gradasi
    def _grad(s, c0, c1, horizontal, x0, y0, x1, y1):
        gid = uid("g")
        h0, a0 = col(G.rgba(c0))
        h1, a1 = col(G.rgba(c1))
        a1 = a0 if len(c0) == 4 else a1
        if horizontal:
            xy = f'x1="{x0:.1f}" y1="0" x2="{x1:.1f}" y2="0"'
        else:
            xy = f'x1="0" y1="{y0:.1f}" x2="0" y2="{y1:.1f}"'
        s.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" {xy}>'
                      f'<stop offset="0" stop-color="{h0}" stop-opacity="{a0}"/><stop offset="1" stop-color="{h1}" stop-opacity="{a1}"/></linearGradient>')
        return f'fill="url(#{gid})"'

    def grect(s, x0, y0, x1, y1, c0, c1, r=0, horizontal=False):
        s.els.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" rx="{r:.1f}" {s._grad(c0, c1, horizontal, x0, y0, x1, y1)}/>')

    def gell(s, x0, y0, x1, y1, c0, c1, horizontal=False):
        s.els.append(f'<ellipse cx="{(x0 + x1) / 2:.1f}" cy="{(y0 + y1) / 2:.1f}" rx="{(x1 - x0) / 2:.1f}" ry="{(y1 - y0) / 2:.1f}" {s._grad(c0, c1, horizontal, x0, y0, x1, y1)}/>')

    def gcirc(s, x, y, r, c0, c1):
        s.gell(x - r, y - r, x + r, y + r, c0, c1)

    def gpoly(s, pts, c0, c1, horizontal=False):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        s.els.append(f'<polygon points="{pts_str(pts)}" {s._grad(c0, c1, horizontal, min(xs), min(ys), max(xs), max(ys))}/>')

    def vgrad(s, y0, y1, c0, c1, x0=0, x1=None):
        s.grect(x0, y0, s.w if x1 is None else x1, y1, c0, c1)

    # --- penghapusan (piksel transparan di versi PNG) = mask
    def erase(s, shape_black):
        mid = uid("m")
        s.defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{s.w}" height="{s.h}">'
                      f'<rect width="{s.w}" height="{s.h}" fill="white"/>{shape_black}</mask>')
        s.els = [f'<g mask="url(#{mid})">'] + s.els + ["</g>"]

    # --- kompatibel dengan PIL Image
    def result(s):
        return s

    def convert(s, mode):
        return s

    def filter(s, f):
        return s

    def alpha_composite(s, other, dest=(0, 0)):
        if isinstance(other, SvgImg):
            s.defs += other.defs
            s.els += other.els
        else:
            buf = io.BytesIO(); other.save(buf, "PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            s.els.append(f'<image x="{dest[0]}" y="{dest[1]}" width="{other.size[0]}" height="{other.size[1]}" href="data:image/png;base64,{b64}"/>')

    def save(s, rel, shade=True, outline=2, light=0.26, grad=0.16):
        save_img(s, rel)

    def body(s):
        return "".join(s.els)

    def svg(s):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{s.w}" height="{s.h}" viewBox="0 0 {s.w} {s.h}" overflow="hidden">'
                f'<defs>{"".join(s.defs)}</defs>{s.body()}</svg>')


# ---------------------------------------------------------------- efek dalam SVG
def blur_composite(base, draw_fn, radius):
    group = []
    draw_fn(Drawer(base, 1.0, group))
    if radius > 0:
        fid = uid("f")
        base.defs.append(f'<filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{radius / 2:.1f}"/></filter>')
        base.els.append(f'<g filter="url(#{fid})">' + "".join(group) + "</g>")
    else:
        base.els.append("<g>" + "".join(group) + "</g>")


def vignette(base, strength=0.35, top=0):
    gid = uid("v")
    base.defs.append(f'<radialGradient id="{gid}" cx="50%" cy="50%" r="75%"><stop offset="0.55" stop-color="#081422" stop-opacity="0"/>'
                     f'<stop offset="1" stop-color="#081422" stop-opacity="{strength}"/></radialGradient>')
    base.els.append(f'<rect width="{base.w}" height="{base.h}" fill="url(#{gid})"/>')


def haze(base, c, alpha, top=0, bottom=None):
    bottom = base.h if bottom is None else bottom
    base.els.append(f'<rect x="0" y="{top}" width="{base.w}" height="{bottom - top}" {fill_attr(tuple(c) + (alpha,))}/>')


def fx_layer(size):
    return SvgImg(*size)


SAVED = {}


def save_img(img, rel):
    name = os.path.splitext(os.path.basename(rel))[0]
    path = os.path.join(OUT, "svg", name + ".svg")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(img.svg())
    SAVED[name] = img


# ---------------------------------------------------------------- versi SVG untuk fungsi khusus
def portrait(name, draw):
    m = SvgImg(220, 220)
    m.gcirc(110, 110, 106, (225, 245, 248), (160, 210, 220))
    m.blend_ell(20, 140, 200, 260, (255, 255, 255, 50))
    draw(m)
    cid = uid("c")
    m.defs.append(f'<clipPath id="{cid}"><circle cx="110" cy="110" r="104"/></clipPath>')
    m.els = [f'<g clip-path="url(#{cid})">'] + m.els + ["</g>"]
    m.circ(110, 110, 106, None, outline=(255, 255, 255), width=8)
    m.circ(110, 110, 109, None, outline=(60, 90, 110, 160), width=2)
    save_img(m, f"art/portrait_{name}.png")


def title_logo():
    m = SvgImg(1200, 320)
    gid, fid = uid("g"), uid("f")
    m.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFEC96"/><stop offset="1" stop-color="#FF8C5A"/></linearGradient>'
                  f'<filter id="{fid}"><feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#0A283C" flood-opacity="0.55"/></filter>')
    style = 'font-family="DejaVu Sans, Arial, sans-serif" font-weight="bold" font-size="190" text-anchor="middle" dominant-baseline="central"'
    m.els.append(f'<text x="600" y="150" {style} fill="#14465F" stroke="#14465F" stroke-width="26" stroke-linejoin="round" filter="url(#{fid})">MUARA</text>')
    m.els.append(f'<text x="600" y="150" {style} fill="url(#{gid})">MUARA</text>')
    for (x, y, r) in [(1080, 70, 18), (1120, 30, 10), (1050, 20, 8), (110, 250, 14), (80, 210, 8)]:
        m.circ(x, y, r, (230, 250, 255, 200), outline=(255, 255, 255), width=3)
    save_img(m, "art/title_logo.png")


def menu_bg():
    # versi SVG: sama seperti gen_assets.menu_bg tanpa lapisan gelap piksel di kiri (diganti gradasi vektor)
    orig_alpha = SvgImg.alpha_composite

    def ac(s, other, dest=(0, 0)):
        if isinstance(other, SvgImg):
            return orig_alpha(s, other, dest)
        gid = uid("l")
        s.defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#081E32" stop-opacity="0.47"/>'
                      f'<stop offset="0.52" stop-color="#081E32" stop-opacity="0"/></linearGradient>')
        s.els.append(f'<rect width="{s.w}" height="{s.h}" fill="url(#{gid})"/>')
    SvgImg.alpha_composite = ac
    try:
        _orig_menu_bg()
    finally:
        SvgImg.alpha_composite = orig_alpha


# ---------------------------------------------------------------- pasang dan jalankan
G.Img = SvgImg
G.save_img = save_img
G.shade_sprite = lambda img, *a, **k: img
G.blur_composite = blur_composite
G.vignette = vignette
G.haze = haze
G.fx_layer = fx_layer
G.portrait = portrait
G.title_logo = title_logo
_orig_menu_bg = G.menu_bg
G.menu_bg = menu_bg
G.ROOT = OUT

GROUPS = [
    ("Karakter", ["raka_body", "gun_harpun", "gun_jaring", "gun_magnet", "portrait_raka", "portrait_kakek", "portrait_busari", "boat"]),
    ("Sampah", ["trash_sachet_1", "trash_sachet_2", "trash_sachet_3", "trash_bag", "trash_bottle", "trash_styro", "trash_sandal", "trash_can", "trash_tire", "trash_ghostnet", "trash_flake_1", "trash_flake_2"]),
    ("Makhluk dan objek", ["fish_1", "fish_2", "fish_3", "jelly", "turtle", "wood", "bubble", "fx_bubble", "box", "hook", "net_open"]),
    ("Kraken", ["kraken_head", "kraken_face", "kraken_face_hurt", "kraken_face_happy"]),
    ("UI", ["title_logo", "ui_btn", "ui_btn_hover", "ui_btn_pressed", "ui_btn_disabled", "ui_btn_primary", "ui_btn_primary_hover", "ui_btn_primary_pressed", "ui_panel", "ui_ribbon", "ui_knob", "ui_toggle_on", "ui_toggle_off", "icon_play", "icon_map", "icon_settings", "icon_credits", "icon_exit", "icon_back", "icon_retry", "icon_next", "icon"]),
    ("Latar", [f"bg_{s}_{v}" for s in ["1_1", "1_2", "1_3", "2_1", "2_2", "2_3"] for v in ["murky", "clean"]] + ["menu_bg", "menu_rays", "map_world"]),
    ("Cerita", ["story_intro", "story_sea", "story_end"]),
]


def board():
    """Satu SVG besar: setiap kelompok satu baris, setiap aset satu grup bernama (nama layer di Figma)."""
    defs, body = [], []
    y = 0
    width = 0
    for title, names in GROUPS:
        body.append(f'<text x="0" y="{y + 40}" font-family="DejaVu Sans, Arial" font-weight="bold" font-size="40" fill="#14213D">{title}</text>')
        y += 70
        x, row_h = 0, 0
        big = title in ("Latar", "Cerita")
        for n in names:
            img = SAVED[n]
            sc = 0.5 if big else 1.0
            w, h = img.w * sc, img.h * sc
            if x + w > 4000:
                x = 0; y += row_h + 60; row_h = 0
            defs += img.defs
            body.append(f'<g id="{n}" transform="translate({x:.0f},{y:.0f}) scale({sc})">'
                        f'<rect width="{img.w}" height="{img.h}" fill="none" stroke="#9BB5C4" stroke-dasharray="6 6"/>{img.body()}</g>')
            body.append(f'<text x="{x:.0f}" y="{y + h + 28:.0f}" font-family="DejaVu Sans, Arial" font-size="20" fill="#3E4A5C">{n}.png · {img.w}×{img.h}</text>')
            x += w + 50
            row_h = max(row_h, h + 40)
            width = max(width, x)
        y += row_h + 120
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{y:.0f}" viewBox="0 0 {width:.0f} {y:.0f}">'
           f'<rect width="{width:.0f}" height="{y:.0f}" fill="#F4F8F6"/><defs>{"".join(defs)}</defs>{"".join(body)}</svg>')
    open(os.path.join(OUT, "Muara_Semua_Aset.svg"), "w", encoding="utf-8").write(svg)


if __name__ == "__main__":
    random.seed(7)
    G.random.seed(7)
    G.raka_body(); G.gun_all()
    G.portrait("kakek", G.kakek); G.portrait("busari", G.busari); G.portrait("raka", G.raka_face)
    for i, c in enumerate([(240, 180, 60), (120, 200, 120), (230, 120, 160)], 1):
        G.sachet(i, c)
    G.bag(); G.bottle(); G.styro(); G.sandal(); G.can(); G.tire(); G.ghostnet(); G.flake(1); G.flake(2)
    for i, c in enumerate([(255, 170, 90), (120, 200, 230), (250, 210, 90)], 1):
        G.fish(i, c)
    G.jelly(); G.turtle(); G.wood(); G.bubble(); G.fx_bubble(); G.box(); G.hook(); G.net_open(); G.kraken(); G.boat()
    for seg in G.WATER:
        G.background(seg, False); G.background(seg, True)
    G.story_intro(); G.story_sea(); G.story_end()
    G.world_map(); G.ui_all(); G.title_logo(); G.icon()
    G.menu_bg(); G.menu_rays(); G.ui_primary(); G.icons(); G.ribbon(); G.knobs()
    G.kraken_tentacles(); G.aim_fx(); G.map_marks(); G.hud_parts()
    board()
    print(len(SAVED), "SVG")
