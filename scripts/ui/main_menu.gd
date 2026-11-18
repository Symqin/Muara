# Menu utama (scenes/ui/main_menu.tscn).
extends Control

var main = null
var _t: float = 0.0

@onready var logo: TextureRect = %Logo
@onready var tagline: Control = %Tagline
@onready var buttons: VBoxContainer = %Buttons
@onready var play_button: Button = %PlayButton
@onready var quit_button: Button = %QuitButton
@onready var stars_label: Label = %StarsLabel
@onready var segments_label: Label = %SegmentsLabel


func _ready() -> void:
	var fresh = Game.unlocked <= 1 and Game.stars.is_empty()
	play_button.text = "Mulai" if fresh else "Lanjutkan"
	quit_button.visible = not OS.has_feature("web")
	_fill_progress()
	_play_entrance()


func _fill_progress() -> void:
	var total = 0
	for id in Game.ORDER:
		total += int(Game.stars.get(id, 0))
	stars_label.text = "★ %d / %d" % [total, Game.ORDER.size() * 3]
	segments_label.text = "Segmen %d / %d" % [Game.unlocked, Game.ORDER.size()]


# Logo jatuh dengan memantul, pita dan tombol muncul satu per satu.
func _play_entrance() -> void:
	var logo_y = logo.position.y
	logo.position.y = -260.0
	logo.pivot_offset = logo.size * 0.5
	create_tween().tween_property(logo, "position:y", logo_y, 0.7).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tagline.modulate.a = 0.0
	var tw = create_tween()
	tw.tween_interval(0.5)
	tw.tween_property(tagline, "modulate:a", 1.0, 0.4)
	for b in buttons.get_children():
		b.modulate.a = 0.0
		tw.tween_property(b, "modulate:a", 1.0, 0.18)


func _process(delta: float) -> void:
	_t += delta
	logo.rotation = sin(_t * 1.1) * 0.015
	logo.scale = Vector2.ONE * (1.0 + sin(_t * 1.7) * 0.012)


func _on_play_pressed() -> void:
	if Game.finished_game():
		main.show_map()
	else:
		main.play(Game.continue_id(), true)


func _on_map_pressed() -> void:
	main.show_map()


func _on_settings_pressed() -> void:
	main.show_settings()


func _on_credits_pressed() -> void:
	main.show_credits()


func _on_quit_pressed() -> void:
	get_tree().quit()


func go_back() -> void:
	if not OS.has_feature("web"):
		get_tree().quit()
