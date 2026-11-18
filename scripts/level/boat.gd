# Kapal kakek: terapung di permukaan, lalu berlayar pergi setelah Raka terjun (scenes/level/boat.tscn).
class_name Boat
extends Sprite2D

@export var bob_height: float = 3.0

var _t: float = 0.0
var _rest_y: float = 0.0


func _ready() -> void:
	_rest_y = position.y


func _process(delta: float) -> void:
	_t += delta
	position.y = _rest_y + sin(_t * 2.0) * bob_height
	rotation = sin(_t * 1.6) * 0.02
	if position.x < -300.0:
		visible = false
		set_process(false)


func sail_away() -> void:
	var tw = create_tween()
	tw.tween_interval(0.6)
	tw.tween_property(self, "position:x", -320.0, 2.6).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
