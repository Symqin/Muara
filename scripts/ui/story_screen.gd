# Adegan cerita (scenes/ui/story_screen.tscn): gambar + dialog satu baris per klik. Bisa dilewati.
# Isi cerita ada di scripts/data/story_data.gd.
extends Control

var main = null
var story: Dictionary = {}       # diisi Main: {"image": path, "lines": [[potret, nama, teks], ...]}
var on_done: Callable = Callable()
var _i: int = 0
var _done: bool = false

@onready var picture: TextureRect = %Picture
@onready var portrait: TextureRect = %Portrait
@onready var name_label: Label = %NameLabel
@onready var text_label: Label = %TextLabel
@onready var hint_label: Label = %HintLabel


func _ready() -> void:
	picture.texture = load(story["image"])
	hint_label.text = Game.t("Klik atau tekan Spasi untuk lanjut", "Ketuk untuk lanjut")
	_show_line(0)


func _show_line(i: int) -> void:
	_i = i
	var line = story["lines"][i]
	portrait.texture = load("res://art/portrait_%s.png" % line[0])
	name_label.text = line[1]
	text_label.text = line[2]


func _advance() -> void:
	if _done:
		return
	if _i + 1 < story["lines"].size():
		_show_line(_i + 1)
		Game.sfx("click")
	else:
		_finish()


func _finish() -> void:
	if _done:
		return
	_done = true
	if on_done.is_valid():
		on_done.call()


func _on_skip_pressed() -> void:
	_finish()


func go_back() -> void:
	_finish()


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_advance()
		accept_event()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_SPACE or event.keycode == KEY_ENTER or event.keycode == KEY_KP_ENTER:
			_advance()
		elif event.keycode == KEY_ESCAPE:
			_finish()
