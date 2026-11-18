# Latar laut hidup untuk layar menu (scenes/ui/components/ocean_backdrop.tscn):
# cahaya berdenyut, kapal kakek bergoyang, ikan berenang, gelembung naik, dan Raka melayang.
# Tambah ikan cukup dengan menambah Sprite2D di node Fishes (ikan yang flip_h berenang ke kanan).
class_name OceanBackdrop
extends Control

const SURFACE_Y = 340.0
const BUBBLE_TEX = preload("res://art/fx_bubble.png")

@export var show_raka: bool = true
@export_range(0.0, 1.0) var dim: float = 0.0
@export var bubbles_per_second: float = 5.0

var _t: float = 0.0
var _fish: Array = []
var _bubbles: Array = []

@onready var rays: TextureRect = %Rays
@onready var boat: Sprite2D = %Boat
@onready var raka: Sprite2D = %Raka
@onready var fishes: Node2D = %Fishes
@onready var bubble_layer: Node2D = %Bubbles
@onready var shade: ColorRect = %Shade


func _ready() -> void:
	raka.visible = show_raka
	shade.color.a = dim
	for f in fishes.get_children():
		var d = {"node": f, "dir": 1 if f.flip_h else -1, "speed": randf_range(60.0, 130.0), "y": f.position.y, "phase": randf() * 6.0}
		_fish.append(d)


func _process(delta: float) -> void:
	_t += delta
	rays.modulate.a = 0.55 + 0.35 * sin(_t * 0.7)
	boat.position.y = SURFACE_Y + 2.0 + sin(_t * 1.8) * 4.0
	boat.rotation = sin(_t * 1.3) * 0.025
	if show_raka:
		raka.position = Vector2(1320.0 + sin(_t * 0.6) * 18.0, 640.0 + sin(_t * 1.2) * 14.0)
		raka.rotation = sin(_t * 0.9) * 0.05
	_move_fish(delta)
	_move_bubbles(delta)


func _move_fish(delta: float) -> void:
	for d in _fish:
		var f = d["node"]
		f.position.x += d["dir"] * d["speed"] * delta
		f.position.y = d["y"] + sin(_t * 2.0 + d["phase"]) * 10.0
		if d["dir"] < 0 and f.position.x < -120.0:
			_respawn_fish(d, 2020.0)
		elif d["dir"] > 0 and f.position.x > 2040.0:
			_respawn_fish(d, -100.0)


func _respawn_fish(d: Dictionary, x: float) -> void:
	d["y"] = randf_range(470.0, 900.0)
	d["speed"] = randf_range(60.0, 130.0)
	d["node"].position = Vector2(x, d["y"])


func _move_bubbles(delta: float) -> void:
	if randf() < delta * bubbles_per_second:
		var b = Sprite2D.new()
		b.texture = BUBBLE_TEX
		if show_raka and randf() < 0.5:
			b.position = raka.position + Vector2(10, -150)
		else:
			b.position = Vector2(randf_range(0.0, 1920.0), 1060.0)
		b.scale = Vector2.ONE * randf_range(0.5, 1.2)
		bubble_layer.add_child(b)
		_bubbles.append({"node": b, "speed": randf_range(70.0, 140.0), "phase": randf() * 6.0, "x": b.position.x})
	for bd in _bubbles.duplicate():
		var n = bd["node"]
		n.position.y -= bd["speed"] * delta
		n.position.x = bd["x"] + sin(_t * 3.0 + bd["phase"]) * 6.0
		if n.position.y < SURFACE_Y + 10.0:
			_bubbles.erase(bd)
			n.queue_free()
