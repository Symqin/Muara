# Dasar semua alat Raka. Setiap alat menembak, memperbarui, dan menggambar bidikannya sendiri.
# Alat adalah anak dari node World di scenes/level/level.tscn; `owner` = Level.
class_name LevelTool
extends Node2D

@export var slot: int = 0
@export var tool_name: String = ""
## -1 = amunisi tak terbatas
@export var start_ammo: int = -1
@export var boss_start_ammo: int = -1
@export var max_ammo: int = -1
## Gambar titik garis bidik (art/fx_aim_dot.png)
@export var aim_dot_texture: Texture2D

var level = null
var unlocked: bool = false
var ammo: int = -1


func _ready() -> void:
	level = owner


func setup(is_boss: bool, is_unlocked: bool) -> void:
	unlocked = is_unlocked
	if max_ammo < 0:
		ammo = -1
	elif not unlocked:
		ammo = 0
	else:
		ammo = boss_start_ammo if is_boss else start_ammo


func infinite_ammo() -> bool:
	return max_ammo < 0


# Kotak bantuan: tambah 1 amunisi. Mengembalikan true kalau berhasil.
func refill() -> bool:
	if not unlocked or infinite_ammo() or ammo >= max_ammo:
		return false
	ammo += 1
	return true


func is_selected() -> bool:
	return level != null and level.cur_tool == slot


func aiming_now() -> bool:
	return is_selected() and level.state == "play"


func _process(_delta: float) -> void:
	queue_redraw()


# --- diisi oleh tiap alat ---
func press() -> void:
	pass


func release() -> void:
	pass


func update_tool(_delta: float) -> void:
	pass


# Batalkan semua yang sedang berjalan (ganti alat, jeda, segmen selesai).
func cancel() -> void:
	pass


# Tempel gambar titik bidik berjajar dari a ke b. r = jari-jari tampilan (gambar aslinya 16 px).
func draw_dots(a: Vector2, b: Vector2, color: Color, step: float = 22.0, r: float = 4.0) -> void:
	var d = a.distance_to(b)
	if d < 1.0 or aim_dot_texture == null:
		return
	var n = int(d / step)
	var size = Vector2.ONE * r * 2.4
	for i in range(n + 1):
		var p = a.lerp(b, float(i) / float(maxi(n, 1)))
		draw_texture_rect(aim_dot_texture, Rect2(p - size * 0.5, size), false, color)
