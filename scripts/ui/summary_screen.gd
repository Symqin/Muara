# Ringkasan segmen (scenes/ui/summary_screen.tscn).
extends Control

var main = null
var result: Dictionary = {}      # diisi Main, dibuat oleh Level.finish_normal/finish_boss

@onready var background: TextureRect = %Background
@onready var title_label: Label = %TitleLabel
@onready var verdict_label: Label = %VerdictLabel
@onready var stars_label: Label = %StarsLabel
@onready var stats: GridContainer = %Stats
@onready var note_label: Label = %NoteLabel
@onready var next_button: Button = %NextButton


func _ready() -> void:
	var id = result["id"]
	var passed = result["passed"]
	var is_boss = result["is_boss"]
	var seg = LevelData.SEGMENTS[id]
	background.texture = load("res://art/bg_%s_%s.png" % [id.replace("-", "_"), "clean" if passed else "murky"])
	Game.sfx("win" if passed else "lose")

	title_label.text = "Segmen %s %s" % [id, seg["name"]]
	verdict_label.text = _verdict()
	verdict_label.add_theme_color_override("font_color", Color(1.0, 0.44, 0.35) if passed else Color(0.176, 0.204, 0.251))
	stars_label.text = MapNode.stars_text(int(result["stars"]))
	next_button.visible = passed

	if is_boss:
		_add_row("Sampah diambil", "%d / %d" % [result["caught"], result["total"]])
		_add_row("Nyawa kraken", "%d / 100" % int(result.get("kraken_hp", 100)))
		_add_row("Tembakan kena makhluk", str(result["creature_hits"]))
	else:
		_add_row("Sampah tertangkap", "%d / %d (%d%%)" % [result["caught"], result["total"], int(round(result["meter"] * 100.0))])
		_add_row("Target lulus", "%d%%" % int(round(float(seg["target"]) * 100.0)))
		_add_row("Sampah lolos", str(result["leaked"]))
		_add_row("Makhluk terkena", str(result["creature_hits"]))
	_add_row("Penyu diselamatkan", str(result["turtles"]))
	_add_row("Sisa oksigen", str(int(result["oxygen_left"])))
	_add_row("Bonus", str(result["bonus"]))
	_add_row("Skor", str(result["score"]))
	note_label.text = _note()


func _verdict() -> String:
	if result["is_boss"]:
		if result["passed"]:
			return "Kraken bebas!"
		if result.get("kraken_down", false):
			return "Kraken terluka parah"
	return "Lulus!" if result["passed"] else "Belum lulus"


func _note() -> String:
	if result["id"] == "1-3" and result["passed"]:
		return "Sampah lolos ke laut selama Stage 1: %d. Kraken di laut dalam terlilit %d sampah tambahan." % [Game.stage1_leaks(), Game.boss_extra()]
	if result["passed"]:
		return ""
	if not result["is_boss"]:
		return "Tips: tangkap gelembung udara dan pakai Jaring untuk gerombolan."
	if result.get("kraken_down", false):
		return "Tips: bidik sampahnya, bukan kulit kraken. Magnet tidak pernah melukai kraken."
	return "Tips: tangkap lemparan kraken dan tarik jaring hantu sebelum melilitnya lagi."


func _add_row(name_text: String, value_text: String) -> void:
	var name_cell = Label.new()
	name_cell.text = name_text
	name_cell.add_theme_font_size_override("font_size", 28)
	stats.add_child(name_cell)
	var value_cell = Label.new()
	value_cell.text = value_text
	value_cell.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value_cell.add_theme_font_size_override("font_size", 28)
	stats.add_child(value_cell)


func _on_next_pressed() -> void:
	main.after_summary(result)


func _on_retry_pressed() -> void:
	main.play(result["id"], false)


func _on_menu_pressed() -> void:
	main.show_menu()


func go_back() -> void:
	main.show_menu()
