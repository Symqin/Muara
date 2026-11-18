# Raka: badan + alat di bahu (scenes/level/raka.tscn).
# Mengurus bidikan, ganti tampilan alat, adegan terjun dari kapal, dan naik ke permukaan.
class_name Raka
extends Node2D

signal dive_finished

# Tekstur alat sesuai urutan slot: Harpun, Jaring, Magnet.
@export var tool_textures: Array = []

var aim_deg: float = 20.0
var aim_dir: Vector2 = Vector2.RIGHT

var _dive_tween: Tween = null

@onready var body: Sprite2D = $Body
@onready var gun: Sprite2D = $Gun


# Titik putar alat (bahu) dalam koordinat arena.
func pivot() -> Vector2:
	return position + gun.position


func muzzle() -> Vector2:
	return pivot() + aim_dir * Arena.MUZZLE_LEN


func aim_at(p: Vector2) -> void:
	var v = p - pivot()
	if v.length() > 4.0:
		aim_deg = clampf(rad_to_deg(atan2(-v.y, v.x)), Arena.AIM_MIN_DEG, Arena.AIM_MAX_DEG)
	var r = deg_to_rad(aim_deg)
	aim_dir = Vector2(cos(r), -sin(r))
	gun.rotation = -r


func show_tool(i: int) -> void:
	if i >= 0 and i < tool_textures.size():
		gun.texture = tool_textures[i]


# Adegan pembuka: terjun dari kapal, cipratan, lalu turun pelan ke dasar.
func play_dive(on_splash: Callable) -> void:
	gun.visible = false
	position = Vector2(430, -170)
	rotation = 0.35
	_dive_tween = create_tween()
	_dive_tween.tween_interval(0.35)
	_dive_tween.tween_property(self, "position", Vector2(400, Arena.SURFACE_Y + 70.0), 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_dive_tween.tween_callback(on_splash)
	_dive_tween.tween_property(self, "position", Arena.RAKA_POS, 1.7).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_dive_tween.parallel().tween_property(self, "rotation", 0.0, 1.4)
	_dive_tween.tween_callback(finish_dive)


# Dipanggil di akhir animasi atau saat pemain melewati adegan.
func finish_dive() -> void:
	if _dive_tween != null and _dive_tween.is_valid():
		_dive_tween.kill()
	_dive_tween = null
	position = Arena.RAKA_POS
	rotation = 0.0
	gun.visible = true
	dive_finished.emit()


# Oksigen habis: naik ke permukaan.
func surface() -> void:
	gun.visible = false
	var tw = create_tween()
	tw.tween_property(self, "position", Vector2(300, Arena.SURFACE_Y + 60.0), 1.8).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)


# Posisi helm (untuk gelembung napas).
func helmet() -> Vector2:
	return position + Vector2(10, -150)
