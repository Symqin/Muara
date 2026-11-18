# Satu titik segmen di Peta Perjalanan (scenes/ui/map_node.tscn).
# Taruh instance scene ini di world_map.tscn, isi segment_id, lalu geser ke posisi di peta.
class_name MapNode
extends Button

signal chosen(segment_id: String)

@export var segment_id: String = "1-1"

@onready var name_label: Label = $NameLabel
@onready var stars_label: Label = $StarsLabel


func _ready() -> void:
	focus_mode = Control.FOCUS_NONE
	var seg = LevelData.SEGMENTS[segment_id]
	var open = Game.is_unlocked(segment_id)
	text = segment_id
	theme_type_variation = &"MapNodeRiver" if int(seg["stage"]) == 1 else &"MapNodeSea"
	disabled = not open
	name_label.text = seg["name"]
	stars_label.text = stars_text(int(Game.stars.get(segment_id, 0))) if open else "terkunci"
	if not open:
		stars_label.add_theme_color_override("font_color", Color(0.9, 0.92, 0.94))
	pressed.connect(func(): chosen.emit(segment_id))


# Titik tengah lingkaran, dalam koordinat induknya.
func center() -> Vector2:
	return position + size * 0.5


static func stars_text(n: int) -> String:
	var s = ""
	for i in range(3):
		s += "★" if i < n else "☆"
	return s
