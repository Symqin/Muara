# Tombol yang sedikit membesar saat disorot dan berbunyi "klik" saat ditekan.
# Pasang skrip ini ke Button mana pun di scene.
class_name JuicyButton
extends Button

@export var hover_scale: float = 1.05


func _ready() -> void:
	focus_mode = Control.FOCUS_NONE
	mouse_entered.connect(_on_hover.bind(true))
	mouse_exited.connect(_on_hover.bind(false))
	pressed.connect(_on_pressed)


func _on_hover(on: bool) -> void:
	if disabled:
		return
	pivot_offset = size * 0.5
	var tw = create_tween()
	tw.tween_property(self, "scale", Vector2.ONE * (hover_scale if on else 1.0), 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _on_pressed() -> void:
	Game.sfx("click")
