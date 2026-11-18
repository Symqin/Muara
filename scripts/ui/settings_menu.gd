# Pengaturan (scenes/ui/settings_menu.tscn): volume, layar penuh, getar layar, tutorial, reset progres.
extends Control

var main = null
var _reset_armed: bool = false

@onready var music_slider: HSlider = %MusicSlider
@onready var sfx_slider: HSlider = %SfxSlider
@onready var fullscreen_toggle: CheckButton = %FullscreenToggle
@onready var shake_toggle: CheckButton = %ShakeToggle
@onready var reset_button: Button = %ResetButton
@onready var info_label: Label = %InfoLabel


func _ready() -> void:
	music_slider.set_value_no_signal(Game.music_vol)
	sfx_slider.set_value_no_signal(Game.sfx_vol)
	shake_toggle.set_pressed_no_signal(Game.shake)
	fullscreen_toggle.set_pressed_no_signal(Game.fullscreen)
	# Di HP dan web, layar penuh diatur oleh perangkat/itch.io.
	fullscreen_toggle.visible = not Game.is_touch() and not OS.has_feature("web")


func _on_music_changed(v: float) -> void:
	Game.music_vol = v
	Game.apply_audio()


func _on_sfx_changed(v: float) -> void:
	Game.sfx_vol = v
	Game.apply_audio()


func _on_fullscreen_toggled(on: bool) -> void:
	Game.set_fullscreen(on)


func _on_shake_toggled(on: bool) -> void:
	Game.shake = on


func _on_tutorial_pressed() -> void:
	Game.reset_hints()
	info_label.text = "Petunjuk tutorial akan tampil lagi."


# Perlu dua kali tekan supaya tidak terhapus tanpa sengaja.
func _on_reset_pressed() -> void:
	if not _reset_armed:
		_reset_armed = true
		reset_button.text = Game.t("Klik lagi untuk yakin menghapus", "Ketuk lagi untuk yakin menghapus")
		return
	Game.reset_progress()
	_reset_armed = false
	reset_button.text = "Hapus semua progres"
	info_label.text = "Progres sudah dihapus."


func _on_back_pressed() -> void:
	Game.save_game()
	main.show_menu()


func go_back() -> void:
	_on_back_pressed()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		_on_back_pressed()
