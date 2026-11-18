# Satu objek di air: sampah, makhluk, rintangan, atau pickup (scenes/level/water_object.tscn).
# Objek hanya mengurus gerakannya sendiri. Tabrakan dan akibatnya diurus oleh alat dan Level.
class_name WaterObject
extends Node2D

var kind: String = ""
var cat: String = ""            # trash, creature, obstacle, pickup
var weight: int = 0             # 0 ringan, 1 sedang, 2 berat
var metal: bool = false
var pts: int = 0
var radius: float = 30.0
var amp: float = 8.0
var speed_mul: float = 1.0
var vel: Vector2 = Vector2.ZERO
var base_x: float = 0.0
var base_y: float = 0.0
var t: float = 0.0
var motion: String = "drift"    # drift, hold, swim, flee, fly, rise, fall, rest, proj, sink, toboss, decor
var state: String = "free"      # free, hooked, collecting, fleeing, decor
var hold: String = ""           # "", "tutorial", "clog", "clog_behind"
var wave: int = -1
var has_turtle: bool = false
var is_proj: bool = false
var is_boss_net: bool = false
var pull_override: float = -1.0
var dir: int = -1               # arah ikan: -1 ke kiri, 1 ke kanan
var rest_time: float = 0.0
var collect_from: Vector2 = Vector2.ZERO
var collect_t: float = 0.0
var hook_offset: Vector2 = Vector2.ZERO
var flash: float = 0.0

# lintasan lemparan kraken (kurva bezier) dan seretan jaring hantu
var p0: Vector2 = Vector2.ZERO
var p1: Vector2 = Vector2.ZERO
var p2: Vector2 = Vector2.ZERO
var dur: float = 1.0

@onready var sprite: Sprite2D = $Sprite
@onready var passenger: Sprite2D = $Passenger


func setup(k: String) -> void:
	kind = k
	var d = LevelData.KINDS[k]
	cat = d["cat"]
	weight = int(d["w"])
	metal = bool(d["metal"])
	pts = int(d["pts"])
	radius = float(d["r"])
	amp = float(d["amp"])
	speed_mul = float(d["speed"])
	t = randf() * 6.0
	var texs = d["tex"]
	sprite.texture = load("res://art/%s.png" % texs[randi() % texs.size()])
	if k == "turtlenet":
		set_passenger("turtle")


# Makhluk yang terjerat jaring (penyu atau ikan), digambar di belakang jaring.
func set_passenger(tex_name: String) -> void:
	has_turtle = tex_name == "turtle"
	passenger.texture = load("res://art/%s.png" % tex_name)
	passenger.visible = true


func passenger_texture_name() -> String:
	if passenger.texture == null:
		return "turtle"
	return passenger.texture.resource_path.get_file().get_basename()


# Hiasan saja (ikan lewat, gelembung): tidak bisa ditangkap.
func make_decor(tex_name: String, velocity: Vector2) -> void:
	sprite.texture = load("res://art/%s.png" % tex_name)
	sprite.flip_h = velocity.x > 0.0 and (tex_name.begins_with("fish") or tex_name == "turtle")
	state = "decor"
	motion = "decor"
	vel = velocity


func face(direction: int) -> void:
	# Tekstur ikan menghadap kiri; balik jika berenang ke kanan.
	dir = direction
	sprite.flip_h = direction > 0


func is_free() -> bool:
	return state == "free"


func is_ambient() -> bool:
	return motion == "flee" or motion == "decor" or motion == "sink"


# Mengembalikan true jika objek harus dihapus (keluar layar, tenggelam, pudar).
func tick(delta: float, current: float) -> bool:
	t += delta
	if flash > 0.0:
		flash -= delta
		modulate = Color(1, 0.6, 0.6) if int(flash * 20.0) % 2 == 0 else Color(1, 1, 1)
		if flash <= 0.0:
			modulate = Color(1, 1, 1)
	match motion:
		"hold":
			position.y = base_y + sin(t * 1.6) * 5.0
		"drift":
			position.x -= current * speed_mul * delta
			position.y = base_y + sin(t * 1.3) * amp
			if kind == "sandal":
				rotation += delta * 0.8
			elif kind == "jelly":
				var s = 1.0 + sin(t * 3.0) * 0.06
				scale = Vector2(1.0 / s, s)
			if position.x < -radius - 20.0:
				return true
		"swim":
			position.x += vel.x * delta
			position.y = base_y + sin(t * 2.0) * amp
			if (dir < 0 and position.x < -140.0) or (dir > 0 and position.x > 2080.0):
				return true
		"flee":
			position += vel * delta
			modulate.a = maxf(0.0, modulate.a - delta * 0.9)
			if modulate.a <= 0.0 or position.x < -160.0 or position.x > 2100.0:
				return true
		"fly":
			position += vel * delta
			position.y += sin(t * 5.0) * 0.6
			rotation += delta * 3.0
			if position.x < -40.0:
				return true
		"rise":
			position.y -= 70.0 * delta
			position.x = base_x + sin(t * 2.0) * amp
			if position.y < Arena.SURFACE_Y + 24.0:
				return true
		"fall":
			position.y += 45.0 * delta
			rotation = sin(t * 2.0) * 0.08
			if position.y >= Arena.BED_Y - 40.0:
				position.y = Arena.BED_Y - 40.0
				motion = "rest"
				rest_time = 0.0
		"rest":
			rest_time += delta
			if rest_time > 2.0:
				modulate.a = maxf(0.0, 1.0 - (rest_time - 2.0))
			if rest_time > 3.0:
				return true
		"proj":
			var u = clampf(t / dur, 0.0, 1.0)
			position = p0.lerp(p1, u).lerp(p1.lerp(p2, u), u)
			rotation += delta * 4.0
		"sink":
			position.y += 140.0 * delta
			modulate.a = maxf(0.0, modulate.a - delta * 1.2)
			if modulate.a <= 0.0 or position.y > Arena.BED_Y + 40.0:
				return true
		"toboss":
			var u2 = clampf(t / dur, 0.0, 1.0)
			position = p0.lerp(p2, u2)
			position.y += sin(t * 2.0) * 6.0
		"decor":
			position += vel * delta
			modulate.a = maxf(0.0, modulate.a - delta * 0.35)
			if modulate.a <= 0.0:
				return true
	return false


func proj_done() -> bool:
	return motion == "proj" and t >= dur


func toboss_done() -> bool:
	return motion == "toboss" and t >= dur


func _ready() -> void:
	refresh_debug()


# Dipanggil saat F3 ditekan. Saat hitbox tampil, gambar objek dipindah ke belakang garis hitbox.
func refresh_debug() -> void:
	sprite.show_behind_parent = Game.debug_hitbox
	passenger.show_behind_parent = Game.debug_hitbox
	queue_redraw()


# Hitbox (F3): bentuk yang sama dengan hit_test di bawah. Hiasan tidak punya hitbox.
func _draw() -> void:
	if not Game.debug_hitbox or state == "decor":
		return
	var col = Color(0.3, 1, 0.4, 0.9)
	if cat == "creature":
		col = Color(1, 0.4, 0.4, 0.9)
	elif cat == "obstacle":
		col = Color(1, 0.85, 0.1, 0.9)
	elif cat == "pickup":
		col = Color(0.4, 0.8, 1, 0.9)
	# digambar di ruang lokal; batalkan rotasi/skala supaya sama dengan hit_test
	draw_set_transform(Vector2.ZERO, -rotation, Vector2.ONE / scale.abs().max(Vector2(0.01, 0.01)))
	if kind == "wood":
		draw_rect(Rect2(-84, -22, 168, 44), col, false, 2.0)
	else:
		draw_arc(Vector2.ZERO, radius, 0.0, TAU, 24, col, 2.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# Apakah titik p mengenai objek ini? Kayu memakai kotak, lainnya lingkaran.
func hit_test(p: Vector2, extra: float) -> bool:
	if kind == "wood":
		return absf(p.x - position.x) < 84.0 + extra and absf(p.y - position.y) < 22.0 + extra
	return position.distance_to(p) < radius + extra
