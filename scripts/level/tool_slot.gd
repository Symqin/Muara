# Satu slot alat di HUD (scenes/level/tool_slot.tscn). Bisa diklik atau disentuh untuk ganti alat.
class_name ToolSlot
extends Button

signal chosen(slot: int)

@export var slot: int = 0
@export var tool_name: String = ""
@export var tool_icon: Texture2D

var _selected: bool = false

@onready var number_label: Label = $Number
@onready var icon_rect: TextureRect = $Icon
@onready var name_label: Label = $ToolName
@onready var ammo_label: Label = $Ammo
@onready var charge_bar: ProgressBar = $Charge
@onready var locked_label: Label = $Locked


func _ready() -> void:
	focus_mode = Control.FOCUS_NONE
	number_label.text = str(slot + 1)
	name_label.text = tool_name
	icon_rect.texture = tool_icon
	pressed.connect(func(): chosen.emit(slot))


# Perbarui tampilan dari alat (LevelTool) yang diwakili slot ini.
func refresh(lt, selected: bool) -> void:
	var open = lt.unlocked
	disabled = not open
	icon_rect.visible = open
	name_label.visible = open
	ammo_label.visible = open
	locked_label.visible = not open
	ammo_label.text = "∞" if lt.infinite_ammo() else "×%d" % lt.ammo
	var charging = open and lt.has_method("charge_fraction") and lt.holding
	charge_bar.visible = charging
	if charging:
		charge_bar.value = lt.charge_fraction() * 100.0
	var want = selected and open
	if want != _selected:
		_selected = want
		theme_type_variation = &"ToolSlotSelected" if want else &"ToolSlot"
