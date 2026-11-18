# Harpun Tali: kait melesat lurus, lalu tali menarik tangkapan pulang.
# Menembus sampai 2 sampah ringan; berhenti di sampah sedang/berat, makhluk, rintangan, atau kraken.
extends LevelTool

@export var speed: float = 1600.0
@export var hit_radius: float = 12.0
## Lama tarikan untuk berat 0 (ringan), 1 (sedang), 2 (berat)
@export var pull_times: Array = [0.35, 0.7, 1.2]
@export var miss_pull: float = 0.5
@export var kraken_piece_pull: float = 0.5
@export var kraken_damage: float = 8.0
@export var hook_texture: Texture2D
## Tali harpun, diulang sepanjang jarak (art/fx_rope.png). Node ini memakai texture_repeat.
@export var rope_texture: Texture2D

var hook: Dictionary = {}


func _ready() -> void:
	super._ready()
	_reset()


func _reset() -> void:
	hook = {"state": "idle", "pos": Vector2.ZERO, "dir": Vector2.RIGHT, "items": [], "speed": 0.0}


func is_busy() -> bool:
	return hook["state"] != "idle"


func press() -> void:
	if is_busy():
		return
	hook = {"state": "out", "pos": level.raka.muzzle(), "dir": level.raka.aim_dir, "items": [], "speed": 0.0}
	Game.sfx("shoot")


func cancel() -> void:
	_reset()


func update_tool(delta: float) -> void:
	if hook["state"] == "out":
		var steps = 3
		for s in range(steps):
			hook["pos"] = hook["pos"] + hook["dir"] * speed * delta / float(steps)
			if _check_hit():
				_pull_back()
				break
			var p = hook["pos"]
			if p.x > 1940.0 or p.x < 0.0 or p.y < Arena.SURFACE_Y + 4.0 or p.y > Arena.BED_Y:
				_pull_back()
				break
	elif hook["state"] == "back":
		var m = level.raka.muzzle()
		var to = m - hook["pos"]
		var step = hook["speed"] * delta
		if to.length() <= step:
			_arrive()
			return
		hook["pos"] = hook["pos"] + to.normalized() * step
	for e in hook["items"]:
		if is_instance_valid(e):
			e.position = hook["pos"] + e.hook_offset


# true = kait berhenti dan ditarik pulang.
func _check_hit() -> bool:
	var p = hook["pos"]
	var kraken = level.kraken
	if kraken != null and kraken.remaining() > 0:
		var pi = kraken.piece_at(p, hit_radius + 8.0)
		if pi >= 0:
			var taken = kraken.take(pi)
			var piece = level.entities.spawn(taken[0], taken[1])
			piece.pull_override = kraken_piece_pull
			_attach(piece)
			Game.sfx("piece")
			return true
		if kraken.hit_body(p, 0.0):
			level.hurt_kraken(kraken_damage, p)
			return true
	for e in level.entities.items:
		if not e.is_free() or hook["items"].has(e):
			continue
		if not e.hit_test(p, hit_radius):
			continue
		if e.cat == "trash":
			_attach(e)
			if e.weight == 0 and hook["items"].size() < 2:
				continue
			return true
		elif e.cat == "pickup":
			_attach(e)
			return true
		elif e.cat == "creature":
			level.hit_creature(e)
			return true
		elif e.cat == "obstacle":
			Game.sfx("bounce")
			level.float_text(p, "Memantul", Color(0.9, 0.9, 0.9))
			return true
	return false


func _attach(e) -> void:
	e.state = "hooked"
	e.hook_offset = Vector2(randf_range(-10.0, 10.0), randf_range(-10.0, 10.0))
	hook["items"].append(e)


func _pull_back() -> void:
	var pull = miss_pull
	if hook["items"].size() > 0:
		pull = 0.0
		for e in hook["items"]:
			var pt = float(pull_times[clampi(e.weight, 0, 2)])
			if e.pull_override > 0.0:
				pt = e.pull_override
			pull = maxf(pull, pt)
		Game.sfx("pull")
	hook["state"] = "back"
	hook["speed"] = maxf(hook["pos"].distance_to(level.raka.muzzle()) / pull, 200.0)


func _arrive() -> void:
	var items = hook["items"]
	_reset()
	for e in items:
		if is_instance_valid(e):
			level.collect(e)


func _draw() -> void:
	if level == null or level.state == "ended":
		return
	var m = level.raka.muzzle()
	if aiming_now():
		draw_dots(m, m + level.raka.aim_dir * 620.0, Color(1, 1, 1, 0.75))
	if is_busy():
		if rope_texture != null:
			var v = hook["pos"] - m
			draw_set_transform(m, v.angle(), Vector2.ONE)
			var h = rope_texture.get_height()
			draw_texture_rect(rope_texture, Rect2(0, -h * 0.5, v.length(), h), true)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if hook_texture != null:
			draw_set_transform(hook["pos"], hook["dir"].angle(), Vector2.ONE)
			draw_texture(hook_texture, Vector2(-30, -12))
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		if Game.debug_hitbox:
			draw_arc(hook["pos"], hit_radius, 0.0, TAU, 16, Color(1, 1, 1, 0.95), 2.0)
