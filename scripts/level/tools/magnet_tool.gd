# Magnet Pulsa: tahan 1 detik, lalu menarik semua sampah logam di kerucut arah bidik.
# Tidak pernah melukai makhluk atau kraken.
extends LevelTool

@export var max_range: float = 700.0
@export var boss_range: float = 1400.0
@export var half_angle_deg: float = 22.5
@export var charge_time: float = 1.0
@export var kraken_max_cans: int = 5
## Kerucut jangkauan (art/fx_magnet_cone.png): puncak di kiri tengah, jari-jari 512 px, sudut ±22,5°
@export var cone_texture: Texture2D

var cur_range: float = 700.0
var holding: bool = false
var charge: float = 0.0
var pulse: float = 0.0


func setup(is_boss: bool, is_unlocked: bool) -> void:
	super.setup(is_boss, is_unlocked)
	cur_range = boss_range if is_boss else max_range


func charge_fraction() -> float:
	return clampf(charge / charge_time, 0.0, 1.0)


func press() -> void:
	if ammo <= 0:
		Game.sfx("bounce")
		level.hints.request("noammo_mag", "Magnet habis. Tarik kotak bantuan untuk isi ulang", "", 2.5, false)
		return
	holding = true
	charge = 0.0


func release() -> void:
	if holding and charge < charge_time:
		cancel()


func cancel() -> void:
	holding = false
	charge = 0.0


func _process(delta: float) -> void:
	if pulse > 0.0:
		pulse -= delta
	queue_redraw()


func update_tool(delta: float) -> void:
	if not holding:
		return
	if not Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		cancel()
		return
	charge += delta
	if charge >= charge_time:
		_fire()


func _fire() -> void:
	cancel()
	ammo -= 1
	pulse = 0.4
	Game.sfx("magnet")
	level.hints.complete("magnet")
	var m = level.raka.muzzle()
	var aim = level.raka.aim_dir
	for e in level.entities.items.duplicate():
		if not e.is_free() or not e.metal:
			continue
		var v = e.position - m
		if v.length() > cur_range or absf(rad_to_deg(aim.angle_to(v))) > half_angle_deg:
			continue
		level.start_collect(e)
	var kraken = level.kraken
	if kraken != null and kraken.remaining() > 0:
		var vb = kraken.global_position - m
		var spread = rad_to_deg(atan2(kraken.reach_radius, vb.length()))
		if absf(rad_to_deg(aim.angle_to(vb))) <= half_angle_deg + spread:
			var got = kraken.remove_metal(kraken_max_cans)
			for item in got:
				level.start_collect(level.entities.spawn(item[0], item[1]))
			var where = kraken.bar_anchor() + Vector2(0, 80)
			if got.size() > 0:
				Game.sfx("piece")
				level.float_text(where, "Magnet: %d kaleng" % got.size(), Color(1, 0.85, 0.5))
			else:
				level.float_text(where, "Tidak ada kaleng lagi", Color(0.9, 0.9, 0.9))


func _draw() -> void:
	if level == null or level.state == "ended" or cone_texture == null:
		return
	var m = level.raka.muzzle()
	var a = level.raka.aim_dir.angle()
	if aiming_now():
		_cone(m, a, cur_range, Color(1, 1, 1, 0.8))
		if holding:
			_cone(m, a, 60.0 + (cur_range - 60.0) * charge_fraction(), Color(1, 0.6, 0.55, 0.9))
	if pulse > 0.0:
		_cone(m, a, maxf(cur_range * (1.0 - pulse / 0.4), 10.0), Color(1, 0.7, 0.65, pulse * 2.0))


# Tempel gambar kerucut, diputar ke arah bidik dan diskalakan sesuai jangkauan.
func _cone(origin: Vector2, angle: float, reach: float, tint: Color) -> void:
	var k = reach / 512.0
	var sz = cone_texture.get_size()
	draw_set_transform(origin, angle, Vector2(k, k * tan(deg_to_rad(half_angle_deg)) / tan(deg_to_rad(22.5))))
	draw_texture(cone_texture, Vector2(0, -sz.y * 0.5), tint)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
