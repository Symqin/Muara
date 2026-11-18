# Teks yang melayang naik lalu memudar (skor, "+8 Oksigen", "Aduh!"). Scene: floating_text.tscn
class_name FloatingText
extends Label


func popup(at: Vector2, msg: String, color: Color) -> void:
	text = msg
	add_theme_color_override("font_color", color)
	position = at + Vector2(-40, -40)
	var tw = create_tween()
	tw.set_parallel(true)
	tw.tween_property(self, "position:y", position.y - 70.0, 0.9)
	tw.tween_property(self, "modulate:a", 0.0, 0.9)
	tw.chain().tween_callback(queue_free)
