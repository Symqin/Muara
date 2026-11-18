# Credits (scenes/ui/credits_screen.tscn). Teks credits ditulis langsung di scene (node Body).
extends Control

var main = null


func _on_back_pressed() -> void:
	main.show_menu()


func go_back() -> void:
	main.show_menu()


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		main.show_menu()
