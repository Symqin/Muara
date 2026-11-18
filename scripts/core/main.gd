# Main (scenes/main.tscn): mengganti layar (menu, peta, cerita, level, ringkasan, dsb.).
# Setiap layar adalah scene sendiri di scenes/ui atau scenes/level; Main hanya memasang dan melepasnya.
extends Node

const MAIN_MENU = preload("res://scenes/ui/main_menu.tscn")
const WORLD_MAP = preload("res://scenes/ui/world_map.tscn")
const SETTINGS = preload("res://scenes/ui/settings_menu.tscn")
const CREDITS = preload("res://scenes/ui/credits_screen.tscn")
const STORY = preload("res://scenes/ui/story_screen.tscn")
const SUMMARY = preload("res://scenes/ui/summary_screen.tscn")
const LEVEL = preload("res://scenes/level/level.tscn")

var current: Node = null


func _ready() -> void:
	randomize()
	get_tree().quit_on_go_back = false
	show_menu()


# Tombol "kembali" Android (dan gestur kembali di HP): diteruskan ke layar yang sedang tampil.
func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if current != null and is_instance_valid(current) and current.has_method("go_back"):
			current.go_back()


func _open(scene: PackedScene) -> Node:
	get_tree().paused = false
	if current != null and is_instance_valid(current):
		current.queue_free()
	current = scene.instantiate()
	current.main = self
	return current


func _show(node: Node) -> void:
	add_child(node)


func show_menu() -> void:
	Game.play_music("music_menu")
	_show(_open(MAIN_MENU))


func show_map() -> void:
	_show(_open(WORLD_MAP))


func show_settings() -> void:
	_show(_open(SETTINGS))


func show_credits() -> void:
	Game.play_music("music_menu")
	_show(_open(CREDITS))


func show_story(key: String, on_done: Callable) -> void:
	var s = _open(STORY)
	s.story = StoryData.STORIES[key]
	s.on_done = on_done
	_show(s)


# Mulai segmen. with_story = putar adegan cerita yang mendahului segmen ini (jika ada).
func play(id: String, with_story: bool = true) -> void:
	if with_story and StoryData.STORY_BEFORE_SEGMENT.has(id):
		show_story(StoryData.STORY_BEFORE_SEGMENT[id], func(): play(id, false))
		return
	var lv = _open(LEVEL)
	lv.seg_id = id
	_show(lv)


func show_summary(result: Dictionary) -> void:
	Game.record(result)
	var s = _open(SUMMARY)
	s.result = result
	_show(s)


# Tombol "Lanjut" di ringkasan.
func after_summary(result: Dictionary) -> void:
	if result["id"] == "2-3":
		show_story("end", func(): show_credits())
		return
	var nid = Game.next_id(result["id"])
	if nid == "":
		show_menu()
	else:
		play(nid, true)
