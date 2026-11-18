# Jaring Lontar: terbang ke titik bidik lalu terbuka, menangkap sampah ringan dan sedang di area.
# Ikan di area ikut terjerat (dihitung kena makhluk).
extends LevelTool

@export var max_range: float = 900.0
## Jangkauan khusus segmen kraken (kepalanya jauh di kanan)
@export var boss_range: float = 1350.0
@export var radius: float = 110.0
@export var speed: float = 1400.0
@export var cooldown: float = 1.0
@export var kraken_max_pieces: int = 4
@export var kraken_damage: float = 5.0
@export var net_texture: Texture2D
## Cincin area jaring saat membidik (art/fx_net_ring.png, cincin berjari-jari 110 px)
@export var ring_texture: Texture2D

var cur_range: float = 900.0
var shot: Dictionary = {}
var cd: float = 0.0


func setup(is_boss: bool, is_unlocked: bool) -> void:
	super.setup(is_boss, is_unlocked)
	cur_range = boss_range if is_boss else max_range


func target_point() -> Vector2:
	var m = level.raka.muzzle()
	var d = clampf((get_global_mouse_position() - m).length(), 120.0, cur_range)
	return m + level.raka.aim_dir * d


func press() -> void:
	if not shot.is_empty() or cd > 0.0:
		return
	if ammo <= 0:
		Game.sfx("bounce")
		level.hints.request("noammo_net", "Jaring habis. Tarik kotak bantuan untuk isi ulang", "", 2.5, false)
		return
	ammo -= 1
	cd = cooldown
	shot = {"state": "fly", "pos": level.raka.muzzle(), "target": target_point(), "time": 0.0}
	Game.sfx("shoot")
	level.hints.complete("net")


func cancel() -> void:
	shot = {}


func update_tool(delta: float) -> void:
	if cd > 0.0:
		cd -= delta
	if shot.is_empty():
		return
	if shot["state"] == "fly":
		var to = shot["target"] - shot["pos"]
		var step = speed * delta
		if to.length() <= step:
			shot["pos"] = shot["target"]
			_open()
		else:
			shot["pos"] = shot["pos"] + to.normalized() * step
	else:
		shot["time"] = shot["time"] - delta
		if shot["time"] <= 0.0:
			shot = {}


func _open() -> void:
	shot["state"] = "open"
	shot["time"] = 0.4
	Game.sfx("net")
	var c = shot["pos"]
	for e in level.entities.items.duplicate():
		if not e.is_free():
			continue
		if e.position.distance_to(c) > radius + e.radius * 0.5:
			continue
		if e.cat == "trash" and e.weight <= 1:
			level.start_collect(e)
		elif e.cat == "creature":
			level.hit_creature(e)
	var kraken = level.kraken
	if kraken != null and kraken.remaining() > 0:
		var got = kraken.take_in_radius(c, radius, kraken_max_pieces)
		for item in got:
			level.start_collect(level.entities.spawn(item[0], item[1]))
		if got.size() > 0:
			Game.sfx("piece")
			level.float_text(c, "Jaring: %d sampah" % got.size(), Color(1, 0.85, 0.5))
		elif kraken.hit_body(c, 0.0):
			level.hurt_kraken(kraken_damage, c)


func _draw() -> void:
	if level == null or level.state == "ended":
		return
	if aiming_now():
		var col = Color(0.75, 1, 0.85, 0.8)
		var tgt = target_point()
		draw_dots(level.raka.muzzle(), tgt, col)
		if ring_texture != null:
			var sz = ring_texture.get_size() * (radius / 110.0)
			draw_texture_rect(ring_texture, Rect2(tgt - sz * 0.5, sz), false, col)
	if not shot.is_empty() and net_texture != null:
		var s = 0.35 if shot["state"] == "fly" else 1.0
		var a = 1.0 if shot["state"] == "fly" else clampf(shot["time"] / 0.4, 0.0, 1.0)
		draw_set_transform(shot["pos"], 0.0, Vector2.ONE * s * (radius / 112.0))
		draw_texture(net_texture, Vector2(-120, -120), Color(1, 1, 1, a))
		draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
