# Menu jeda (scenes/level/pause_menu.tscn). Tetap berjalan saat game dijeda.
class_name PauseMenu
extends Control

signal restart_requested
signal quit_requested

@onready var controls_label: Label = %ControlsLabel


func _ready() -> void:
	visible = false
	var desktop = "Mouse: membidik\nKlik kiri: tembak (Magnet: tahan 1 detik)\nTombol 1, 2, 3, scroll, atau klik slot alat: ganti alat\nEsc, P, atau tombol jeda: jeda"
	var touch = "Ketuk layar: membidik dan menembak ke titik itu\nGeser jari: membidik (Magnet: tahan 1 detik)\nKetuk slot alat di kanan bawah: ganti alat\nTombol jeda di kanan atas: jeda"
	controls_label.text = Game.t(desktop, touch)


func open() -> void:
	visible = true
	controls_label.visible = false
	get_tree().paused = true


func resume() -> void:
	visible = false
	get_tree().paused = false


func _on_resume_pressed() -> void:
	resume()


func _on_controls_pressed() -> void:
	controls_label.visible = not controls_label.visible


func _on_restart_pressed() -> void:
	restart_requested.emit()


func _on_quit_pressed() -> void:
	quit_requested.emit()


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE or event.keycode == KEY_P:
			resume()
			get_viewport().set_input_as_handled()
