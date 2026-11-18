# Peta Perjalanan (scenes/ui/world_map.tscn): pilih segmen dari peta.
# Titik segmen adalah instance map_node.tscn di node Nodes; geser di editor untuk memindahkan.
# Klik titik untuk melihat info, klik lagi (atau tombol Main) untuk bermain.
extends Control

## Titik kendali kurva jalur kapal dari 1-3 ke 2-1
@export var boat_route_control: Vector2 = Vector2(820, 120)
## Wajah di penanda posisi pemain
@export var marker_texture: Texture2D
## Titik jalur antar segmen (art/ui_map_dot.png)
@export var dot_texture: Texture2D
## Cincin segmen terpilih (art/ui_map_ring.png)
@export var ring_texture: Texture2D
## Bingkai penanda posisi pemain (art/ui_map_pin.png)
@export var pin_texture: Texture2D

var main = null
var selected: String = ""
var _t: float = 0.0
var _nodes: Dictionary = {}

@onready var paths: Control = %Paths
@onready var node_layer: Control = %Nodes
@onready var info_title: Label = %InfoTitle
@onready var info_desc: Label = %InfoDesc
@onready var info_stats: Label = %InfoStats
@onready var play_button: Button = %PlayButton


func _ready() -> void:
	for n in node_layer.get_children():
		if n is MapNode:
			_nodes[n.segment_id] = n
			n.chosen.connect(_on_node_chosen)
	paths.draw.connect(_draw_paths)
	_select(Game.continue_id())


func _process(delta: float) -> void:
	_t += delta
	paths.queue_redraw()


func _on_node_chosen(id: String) -> void:
	if id == selected:
		_on_play_pressed()
	else:
		Game.sfx("click")
		_select(id)


func _select(id: String) -> void:
	selected = id
	var seg = LevelData.SEGMENTS[id]
	var stage = "Stage 1 · Sungai" if int(seg["stage"]) == 1 else "Stage 2 · Laut"
	info_title.text = "%s  %s" % [id, seg["name"]]
	info_desc.text = stage + ". " + StoryData.SEGMENT_DESC[id]
	var open = Game.is_unlocked(id)
	var stars = MapNode.stars_text(int(Game.stars.get(id, 0)))
	if not open:
		info_stats.text = "Terkunci. Selesaikan segmen sebelumnya dulu."
	elif id == "2-3":
		info_stats.text = "Sampah di kraken: %d   ·   Bintang %s" % [30 + Game.boss_extra(), stars]
	else:
		info_stats.text = "Target %d%%   ·   Skor terbaik %d   ·   %s" % [int(round(float(seg["target"]) * 100.0)), int(Game.best.get(id, 0)), stars]
	play_button.disabled = not open


func _on_play_pressed() -> void:
	if selected != "" and Game.is_unlocked(selected):
		main.play(selected, true)


func _on_back_pressed() -> void:
	main.show_menu()


func go_back() -> void:
	main.show_menu()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			main.show_menu()
		elif event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			_on_play_pressed()


# ------------------------------------------------------------------ gambar jalur, cincin, penanda Raka
func _route_points(a_id: String, b_id: String) -> Array:
	var a = _nodes[a_id].center()
	var b = _nodes[b_id].center()
	var pts = []
	for k in range(41):
		var u = float(k) / 40.0
		if a_id == "1-3":
			pts.append(a.lerp(boat_route_control, u).lerp(boat_route_control.lerp(b, u), u))
		else:
			pts.append(a.lerp(b, u))
	return pts


func _draw_paths() -> void:
	var order = Game.ORDER
	for i in range(order.size() - 1):
		if not _nodes.has(order[i]) or not _nodes.has(order[i + 1]):
			continue
		var open = Game.is_unlocked(order[i + 1])
		var pts = _route_points(order[i], order[i + 1])
		_draw_dotted(pts, Color(1, 1, 1, 0.95 if open else 0.45))
		if order[i] == "1-3":
			var font = get_theme_default_font()
			var mid = pts[20] + Vector2(-220, -24)
			var txt = "naik kapal kakek kembali ke laut"
			paths.draw_string_outline(font, mid, txt, HORIZONTAL_ALIGNMENT_CENTER, 440, 20, 6, Color(0.1, 0.2, 0.28))
			paths.draw_string(font, mid, txt, HORIZONTAL_ALIGNMENT_CENTER, 440, 20, Color.WHITE)
	if _nodes.has(selected) and ring_texture != null:
		var rs = ring_texture.get_size() * (1.0 + sin(_t * 4.0) * 0.06)
		paths.draw_texture_rect(ring_texture, Rect2(_nodes[selected].center() - rs * 0.5, rs), false)
	var cur = Game.continue_id()
	if _nodes.has(cur) and pin_texture != null:
		var top = _nodes[cur].center() + Vector2(0, -132 + sin(_t * 3.0) * 6.0)
		paths.draw_texture(pin_texture, top - Vector2(52, 50))
		if marker_texture != null:
			paths.draw_texture_rect(marker_texture, Rect2(top - Vector2(38, 38), Vector2(76, 76)), false)


# Tempel gambar titik sepanjang jalur, berhenti sebelum menyentuh lingkaran segmen.
func _draw_dotted(pts: Array, color: Color) -> void:
	var total = 0.0
	for k in range(1, pts.size()):
		total += pts[k - 1].distance_to(pts[k])
	var dist = 0.0
	var next_dot = 60.0
	for k in range(1, pts.size()):
		var seg_len = pts[k - 1].distance_to(pts[k])
		while next_dot <= dist + seg_len:
			var p = pts[k - 1].lerp(pts[k], (next_dot - dist) / maxf(seg_len, 0.001))
			if next_dot < total - 55.0 and dot_texture != null:
				paths.draw_texture(dot_texture, p - Vector2(11, 11), color)
			next_dot += 28.0
		dist += seg_len
