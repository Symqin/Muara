# Wadah semua WaterObject di arena: membuat, menghapus, dan menggerakkan objek.
class_name EntityLayer
extends Node2D

const WATER_OBJECT = preload("res://scenes/level/water_object.tscn")

var items: Array = []


func spawn(kind: String, pos: Vector2) -> WaterObject:
	var e: WaterObject = WATER_OBJECT.instantiate()
	add_child(e)
	e.setup(kind)
	e.position = pos
	e.base_x = pos.x
	e.base_y = pos.y
	items.append(e)
	return e


# Hiasan yang bergerak lurus lalu memudar (ikan berenang pergi, gelembung, penyu bebas).
func spawn_decor(tex_name: String, pos: Vector2, velocity: Vector2) -> WaterObject:
	var e = spawn("fish", pos)
	e.make_decor(tex_name, velocity)
	return e


func remove(e) -> void:
	items.erase(e)
	if is_instance_valid(e):
		e.queue_free()


# Gerakkan objek. frozen = tutorial sedang menahan arus (hanya hiasan yang bergerak).
# on_leak dipanggil untuk sampah yang melewati garis kiri.
func tick_all(delta: float, current: float, frozen: bool, on_leak: Callable) -> void:
	for e in items.duplicate():
		if not is_instance_valid(e):
			items.erase(e)
			continue
		if e.state == "hooked" or e.state == "collecting":
			continue
		if frozen and e.motion != "flee" and e.motion != "decor":
			continue
		var gone = e.tick(delta, current)
		if e.state == "free" and e.cat == "trash" and e.motion == "drift" and e.position.x < Arena.LEAK_X:
			on_leak.call(e)
			continue
		if gone:
			remove(e)


# Hanya hiasan (dipakai saat adegan pembuka dan setelah segmen selesai).
func tick_ambient(delta: float, current: float) -> void:
	for e in items.duplicate():
		if is_instance_valid(e) and e.is_ambient():
			if e.tick(delta, current):
				remove(e)


func has_hold(h: String) -> bool:
	for e in items:
		if e.hold == h:
			return true
	return false


func has_free_hold(h: String) -> bool:
	for e in items:
		if e.hold == h and e.state == "free":
			return true
	return false


# Jumlah sampah yang masih ada; wave < 0 berarti semua gelombang.
func trash_count(wave: int) -> int:
	var n = 0
	for e in items:
		if e.cat == "trash" and (wave < 0 or e.wave == wave):
			n += 1
	return n
