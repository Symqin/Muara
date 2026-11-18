# HUD permainan (scenes/level/hud.tscn): meter, oksigen, nyawa kraken, skor, slot alat,
# tombol jeda, banner, petunjuk, dan kotak dialog awal segmen.
# Tata letak diatur di scene; skrip ini hanya mengisi angka dan teks setiap frame.
class_name Hud
extends Control

const UI_INK = Color(0.176, 0.204, 0.251)
const UI_ACCENT = Color(1.0, 0.44, 0.35)

var level = null
var _low_oxygen: bool = false
var _low_kraken: bool = false

@onready var meter_row: Control = %MeterRow
@onready var meter_name: Label = %MeterName
@onready var meter_bar: ProgressBar = %MeterBar
@onready var meter_value: Label = %MeterValue
@onready var target_mark: Control = %TargetMark
@onready var oxygen_name: Label = %OxygenName
@onready var oxygen_bar: ProgressBar = %OxygenBar
@onready var oxygen_value: Label = %OxygenValue
@onready var kraken_row: Control = %KrakenRow
@onready var kraken_name: Label = %KrakenName
@onready var kraken_bar: ProgressBar = %KrakenBar
@onready var kraken_value: Label = %KrakenValue
@onready var info_label: Label = %InfoLabel
@onready var segment_label: Label = %SegmentLabel
@onready var score_label: Label = %ScoreLabel
@onready var pause_button: Button = %PauseButton
@onready var slots: Array = [%Slot1, %Slot2, %Slot3]
@onready var leak_flash: TextureRect = %LeakFlash
@onready var banner: Label = %Banner
@onready var hint_panel: Control = %HintPanel
@onready var hint_label: Label = %HintLabel
@onready var dialog_box: Control = %DialogBox
@onready var dialog_portrait: TextureRect = %DialogPortrait
@onready var dialog_name: Label = %DialogName
@onready var dialog_text: Label = %DialogText
@onready var dialog_prompt: Label = %DialogPrompt


func setup(lv) -> void:
	level = lv
	meter_row.visible = not lv.is_boss
	kraken_row.visible = lv.is_boss
	meter_name.text = lv.meter_label
	target_mark.anchor_left = lv.target
	target_mark.anchor_right = lv.target
	for s in slots:
		s.chosen.connect(lv.select_tool)
	pause_button.pressed.connect(lv.open_pause)
	var d = lv.dialog
	dialog_portrait.texture = load("res://art/portrait_%s.png" % d[0])
	dialog_name.text = d[1]
	dialog_text.text = d[2]
	dialog_prompt.text = Game.t("Klik untuk mulai", "Ketuk untuk mulai")


func _process(_delta: float) -> void:
	if level == null:
		return
	visible = level.state != "intro"
	if not visible:
		return
	_update_status()
	_update_score()
	for i in range(slots.size()):
		slots[i].refresh(level.tools[i], level.cur_tool == i)
	leak_flash.modulate.a = clampf(level.leak_flash, 0.0, 1.0)
	banner.visible = level.banner_t > 0.0 and level.banner_text != ""
	if banner.visible:
		banner.text = level.banner_text
		banner.modulate.a = clampf(level.banner_t / 0.4, 0.0, 1.0)
	var hint = level.hints.current_text()
	hint_panel.visible = hint != ""
	hint_label.text = hint
	dialog_box.visible = level.state == "dialog"


func _update_status() -> void:
	var blink = int(level.clock * 4.0) % 2 == 0
	if not level.is_boss:
		var frac = float(level.caught) / float(maxi(level.total_trash, 1))
		meter_bar.value = frac * 100.0
		meter_value.text = "%d%%" % int(round(frac * 100.0))
		info_label.text = "Keranjang %d  ·  Lolos %d" % [level.caught, level.leaked]
	else:
		var k = level.kraken
		var hpf = k.hp_fraction()
		kraken_bar.value = hpf * 100.0
		kraken_value.text = "%d" % int(ceil(hpf * 100.0))
		var low_k = hpf < 0.3 and blink
		if low_k != _low_kraken:
			_low_kraken = low_k
			kraken_bar.theme_type_variation = &"HudBarRed" if low_k else &"HudBarGreen"
			kraken_name.add_theme_color_override("font_color", UI_ACCENT if low_k else UI_INK)
		info_label.text = "Sampah di kraken %d / %d" % [k.remaining(), k.total]
	var o2f = level.oxygen / level.oxygen_max
	oxygen_bar.value = o2f * 100.0
	oxygen_value.text = "%d" % int(ceil(level.oxygen))
	var low = o2f < 0.2 and blink
	if low != _low_oxygen:
		_low_oxygen = low
		oxygen_bar.theme_type_variation = &"HudBarRed" if low else &"HudBarBlue"
		oxygen_name.add_theme_color_override("font_color", UI_ACCENT if low else UI_INK)


func _update_score() -> void:
	var top = "Segmen %s" % level.seg_id
	if level.is_boss:
		top += "  ·  Kraken fase %d" % level.fight.phase
	else:
		var n = level.waves.wave_count()
		top += "  ·  Gelombang %d/%d" % [clampi(level.waves.wave_i + 1, 1, n), n]
	segment_label.text = top
	score_label.text = "Skor %d  ·  Combo x%d" % [level.score, level.mult()]

