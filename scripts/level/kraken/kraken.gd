# Kraken yang terlilit sampah (scenes/level/kraken/kraken.tscn).
# Pemain BUKAN melukai kraken, tetapi mengambil semua sampah yang menyangkut di kepala dan tentakelnya.
# Tembakan yang mengenai kulit kraken mengurangi nyawanya; kalau nyawa habis, pemain kalah.
# Semua bagian tubuh adalah gambar di scene: kepala, wajah, dan 6 tentakel. Tiap tentakel punya
# desain sendiri dan terdiri dari 3 potongan Line2D (Base, Mid, Tip) bertekstur
# art/kraken_tentacle_<n>_<base|mid|tip>.png. Script ini hanya menggerakkan titiknya supaya melambai.
class_name Kraken
extends Node2D

const PLASTIC = ["bag", "bottle", "sachet", "styro", "sandal", "ghostnet", "tire"]
const TEX = {
	"bag": "trash_bag", "bottle": "trash_bottle", "sachet": "trash_sachet_1", "styro": "trash_styro",
	"sandal": "trash_sandal", "ghostnet": "trash_ghostnet", "tire": "trash_tire", "can": "trash_can",
}
# Hitbox kepala = poligon HeadHitbox/Shape di scene (atur titiknya di editor).
# HEAD_C/HEAD_R hanya dipakai untuk menaruh sampah di kepala dan posisi teks.
const HEAD_C = Vector2(0, -70)        # pusat kepala (lokal)
const HEAD_R = 140.0                  # perkiraan jari-jari kepala
const SEGS = 16                       # jumlah ruas per tentakel
# titik (dari 0..SEGS) yang dipakai tiap potongan; saling tumpang satu ruas supaya sambungan tertutup
const PART_RANGE = {"Base": [0, 6], "Mid": [5, 11], "Tip": [10, 16]}
# arah dasar (radian), panjang, dan titik pangkal tiap tentakel
const TENT_ANGLE = [3.05, 2.75, 2.4, 2.0, 1.45, 0.95]
const TENT_LEN = [470.0, 450.0, 400.0, 340.0, 300.0, 260.0]
const TENT_BASE = [Vector2(-90, 40), Vector2(-60, 60), Vector2(-25, 72), Vector2(15, 72), Vector2(55, 60), Vector2(75, 45)]
const PIECE_R = 30.0

@export var hp_max: float = 100.0
@export var base_trash: int = 30
## Bagian sampah yang berupa kaleng (bisa ditarik Magnet)
@export_range(0.0, 1.0) var metal_ratio: float = 0.25
## Perkiraan jangkauan tubuh, dipakai Magnet untuk menentukan apakah kraken ada di kerucut
@export var reach_radius: float = 300.0
@export var face_worried: Texture2D
@export var face_hurt: Texture2D
@export var face_happy: Texture2D

var total: int = 30
var hp: float = 100.0
var size_scale: float = 1.0
var agitation: int = 1                # 1..3, mengikuti fase; tentakel makin cepat
var pieces: Array = []                # {"kind", "sprite", "anchor": -1 kepala / 0..5 tentakel, "u", "off"}
var tents: Array = []                 # titik lokal tiap tentakel (Array of Array of Vector2)
var base_pos: Vector2 = Vector2.ZERO
var t: float = 0.0
var hurt_t: float = 0.0
var happy: bool = false

@onready var head: Sprite2D = $Head
@onready var face: Sprite2D = $Face
@onready var piece_layer: Node2D = $Pieces
@onready var hp_bar: ProgressBar = $HpBar
@onready var tentacle_nodes: Array = $Tentacles.get_children()
@onready var head_shape: CollisionPolygon2D = $HeadHitbox/Shape

var _debug_layer: Node2D = null


func _ready() -> void:
	# Lapisan gambar hitbox (F3 saat bermain), di atas semua bagian kraken.
	_debug_layer = Node2D.new()
	_debug_layer.z_index = 10
	_debug_layer.visible = false
	_debug_layer.draw.connect(_draw_debug)
	add_child(_debug_layer)


func setup(extra: int) -> void:
	total = base_trash + extra
	hp = hp_max
	size_scale = 1.0 + 0.15 * float(extra) / 20.0
	scale = Vector2.ONE * size_scale
	base_pos = position
	face.texture = face_worried
	for i in range(TENT_ANGLE.size()):
		tents.append([])
	_update_tentacles()
	var kinds = []
	var metal_n = int(round(total * metal_ratio))
	for i in range(total):
		if i < metal_n:
			kinds.append("can")
		else:
			kinds.append(PLASTIC[randi() % PLASTIC.size()])
	kinds.shuffle()
	for i in range(total):
		_add_piece(kinds[i], i)
	_update_bar()


# Sebar sampah: sekitar 1/3 di kepala, sisanya di sepanjang tentakel (lebih banyak di tentakel kiri).
func _add_piece(k, i):
	var s = Sprite2D.new()
	s.texture = load("res://art/%s.png" % TEX[k])
	s.rotation = randf_range(-0.7, 0.7)
	s.scale = Vector2(0.6, 0.6)
	piece_layer.add_child(s)
	var p = {"kind": k, "sprite": s, "anchor": -1, "u": 0.0, "off": Vector2.ZERO}
	if i % 3 == 0:
		var ang = randf_range(-2.8, -0.35)
		var r = HEAD_R * randf_range(0.45, 0.85)
		p["off"] = HEAD_C + Vector2(cos(ang), sin(ang)) * r
	else:
		var weights = [3, 3, 2, 2, 1, 1]
		var pick = randi() % 12
		var acc = 0
		for ti in range(weights.size()):
			acc += weights[ti]
			if pick < acc:
				p["anchor"] = ti
				break
		p["u"] = randf_range(0.28, 0.9)
		p["off"] = Vector2(0, randf_range(-8.0, 8.0))
	pieces.append(p)
	_place(p)


func _place(p):
	if p["anchor"] < 0:
		p["sprite"].position = p["off"]
	else:
		var pts = tents[p["anchor"]]
		var k = clampi(int(p["u"] * SEGS), 1, SEGS)
		p["sprite"].position = pts[k] + p["off"]


func _update_tentacles():
	var spd = 0.9 + 0.45 * float(agitation - 1)
	var amp = 0.5 + 0.12 * float(agitation - 1)
	if hurt_t > 0.0:
		amp += 0.35
	for ti in range(TENT_ANGLE.size()):
		var pts = [TENT_BASE[ti]]
		var seg_len = TENT_LEN[ti] / float(SEGS)
		var p = TENT_BASE[ti]
		for k in range(1, SEGS + 1):
			var f = float(k) / float(SEGS)
			var a = TENT_ANGLE[ti] + sin(t * spd + float(ti) * 1.3 - float(k) * 0.42) * amp * f
			p = p + Vector2.from_angle(a) * seg_len
			pts.append(p)
		tents[ti] = pts
		if ti < tentacle_nodes.size():
			for part in tentacle_nodes[ti].get_children():
				var r = PART_RANGE.get(String(part.name), [0, SEGS])
				part.points = PackedVector2Array(pts.slice(r[0], r[1] + 1))


func _seg_r(k):
	return lerpf(34.0, 9.0, float(k) / float(SEGS))


func tick(delta):
	t += delta
	if hurt_t > 0.0:
		hurt_t -= delta
		if hurt_t <= 0.0 and not happy:
			face.texture = face_worried
			modulate = Color.WHITE
	if not happy:
		position.y = base_pos.y + sin(t * 0.8) * 24.0
	head.scale = Vector2(1.0, 1.0 + sin(t * 1.6) * 0.03)
	_update_tentacles()
	for p in pieces:
		_place(p)
	if Game.debug_hitbox or _debug_layer.visible:
		_debug_layer.visible = Game.debug_hitbox
		_debug_layer.queue_redraw()


# Gambar hitbox: kuning = kulit (melukai kraken), hijau = sampah yang bisa diambil.
func _draw_debug() -> void:
	if not Game.debug_hitbox:
		return
	var body_col = Color(1, 0.85, 0.1, 0.9)
	var pts = head_shape.polygon
	if pts.size() > 1:
		var closed = PackedVector2Array(pts)
		closed.append(pts[0])
		for i in range(closed.size()):
			closed[i] += head_shape.position
		_debug_layer.draw_polyline(closed, body_col, 2.0)
	for tp in tents:
		for k in range(tp.size()):
			_debug_layer.draw_arc(tp[k], _seg_r(k), 0.0, TAU, 20, body_col, 1.5)
	for p in pieces:
		_debug_layer.draw_arc(p["sprite"].position, PIECE_R, 0.0, TAU, 20, Color(0.3, 1, 0.4, 0.9), 2.0)


# ------------------------------------------------------------------ API untuk Level, alat, dan KrakenFight
func remaining():
	return pieces.size()


func fraction():
	if total <= 0:
		return 0.0
	return float(pieces.size()) / float(total)


func hp_fraction():
	return clampf(hp / hp_max, 0.0, 1.0)


# Titik global p berada di kulit kraken (kepala atau tentakel)?
func hit_body(p, extra):
	var lp = to_local(p)
	var e = extra / size_scale
	if _in_head(lp, e):
		return true
	for pts in tents:
		for k in range(pts.size()):
			if lp.distance_to(pts[k]) < _seg_r(k) + e:
				return true
	return false


# Titik lokal lp di dalam poligon kepala, atau dalam jarak e dari tepinya?
func _in_head(lp: Vector2, e: float) -> bool:
	var poly = head_shape.polygon
	var q = lp - head_shape.position
	if Geometry2D.is_point_in_polygon(q, poly):
		return true
	if e <= 0.0:
		return false
	for i in range(poly.size()):
		var c = Geometry2D.get_closest_point_to_segment(q, poly[i], poly[(i + 1) % poly.size()])
		if q.distance_to(c) < e:
			return true
	return false


# Perkiraan: apakah titik dekat tubuh kraken (dipakai untuk jaring).
func contains(p, extra):
	return hit_body(p, extra)


# Indeks sampah terdekat dalam jarak PIECE_R + extra dari titik global p, atau -1.
func piece_at(p, extra):
	var best = -1
	var best_d = PIECE_R * size_scale + extra
	for i in range(pieces.size()):
		var d = pieces[i]["sprite"].global_position.distance_to(p)
		if d < best_d:
			best_d = d
			best = i
	return best


func take(i):
	var p = pieces[i]
	var gp = p["sprite"].global_position
	p["sprite"].queue_free()
	pieces.remove_at(i)
	return [p["kind"], gp]


# Ambil sampai maxn sampah dalam jarak r dari titik global p (untuk jaring).
func take_in_radius(p, r, maxn):
	var out = []
	var i = 0
	while i < pieces.size() and out.size() < maxn:
		if pieces[i]["sprite"].global_position.distance_to(p) <= r:
			out.append(take(i))
		else:
			i += 1
	return out


func remove_metal(maxn):
	var out = []
	var i = 0
	while i < pieces.size() and out.size() < maxn:
		if pieces[i]["kind"] == "can":
			out.append(take(i))
		else:
			i += 1
	return out


func has_metal():
	for p in pieces:
		if p["kind"] == "can":
			return true
	return false


# Kraken terlilit lagi oleh jaring hantu: tambah n sampah, tidak melebihi jumlah awal.
func heal(n):
	for i in range(n):
		if pieces.size() >= total:
			return
		_add_piece(PLASTIC[randi() % 3], 1)


# Kulit kraken terkena alat.
func hurt(amount):
	hp = maxf(0.0, hp - amount)
	hurt_t = 0.6
	face.texture = face_hurt
	modulate = Color(1.0, 0.7, 0.7)
	_update_bar()


func set_happy():
	happy = true
	face.texture = face_happy
	modulate = Color.WHITE


# Titik global ujung tentakel kiri (asal lemparan sampah).
func throw_point():
	var ti = randi() % 2
	var pts = tents[ti]
	return to_global(pts[SEGS - 3])


# Titik global paling kiri dari tubuh kraken.
func left_edge():
	var m = INF
	for pts in tents:
		for q in pts:
			m = minf(m, to_global(q).x)
	return m


# Titik di atas kepala (untuk teks melayang).
func bar_anchor():
	return to_global(HEAD_C + Vector2(0, -HEAD_R - 60.0))


func _update_bar() -> void:
	hp_bar.value = hp_fraction() * 100.0
