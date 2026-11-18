# Autoload "Game": progres, simpanan, pengaturan, dan audio.
extends Node

const SAVE_PATH = "user://muara_save.cfg"
const ORDER = ["1-1", "1-2", "1-3", "2-1", "2-2", "2-3"]
const STAGE1 = ["1-1", "1-2", "1-3"]

var unlocked = 1          # jumlah segmen yang sudah terbuka (1..6)
var stars = {}            # id segmen -> bintang terbaik (0..3)
var best = {}             # id segmen -> skor terbaik
var leaks = {}            # id segmen Stage 1 -> sampah lolos pada kelulusan terakhir
var seen_hints = {}       # kunci petunjuk tutorial yang sudah tampil
var music_vol = 0.7
var sfx_vol = 0.8
var fullscreen = false
var shake = true

var _music = null
var _sfx_players = []
var _sfx_cache = {}
var _music_track = ""


func _ready():
	process_mode = Node.PROCESS_MODE_ALWAYS
	_setup_buses()
	_music = AudioStreamPlayer.new()
	_music.bus = "Music"
	add_child(_music)
	_music.finished.connect(_on_music_finished)
	for i in range(10):
		var p = AudioStreamPlayer.new()
		p.bus = "SFX"
		add_child(p)
		_sfx_players.append(p)
	load_save()
	apply_audio()
	if not OS.has_feature("web") and fullscreen:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)


func _setup_buses():
	for bus_name in ["Music", "SFX"]:
		if AudioServer.get_bus_index(bus_name) == -1:
			AudioServer.add_bus()
			var idx = AudioServer.get_bus_count() - 1
			AudioServer.set_bus_name(idx, bus_name)
			AudioServer.set_bus_send(idx, "Master")


func apply_audio():
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("Music"), linear_to_db(maxf(music_vol, 0.0001)))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index("SFX"), linear_to_db(maxf(sfx_vol, 0.0001)))


func set_fullscreen(on):
	fullscreen = on
	if on:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	save_game()


# ------------------------------------------------------------------ audio
func play_music(track):
	if track == _music_track and _music.playing:
		return
	_music_track = track
	var st = load("res://audio/%s.ogg" % track)
	if st == null:
		return
	st.set("loop", true)
	_music.stream = st
	_music.play()


func _on_music_finished():
	if _music.stream != null:
		_music.play()


func sfx(key):
	var st = _sfx_cache.get(key, null)
	if st == null:
		st = load("res://audio/%s.wav" % key)
		if st == null:
			return
		_sfx_cache[key] = st
	for p in _sfx_players:
		if not p.playing:
			p.stream = st
			p.play()
			return
	_sfx_players[0].stream = st
	_sfx_players[0].play()


# ------------------------------------------------------------------ perangkat
# true di HP/tablet (Android, iOS, atau browser di HP). Dipakai untuk teks petunjuk.
func is_touch():
	return OS.has_feature("mobile") or OS.has_feature("web_android") or OS.has_feature("web_ios")


func t(desktop_text, touch_text):
	return touch_text if is_touch() else desktop_text


# ------------------------------------------------------------------ progres
func index_of(id):
	return ORDER.find(id)


func is_unlocked(id):
	return index_of(id) < unlocked


func next_id(id):
	var i = index_of(id)
	if i < 0 or i >= ORDER.size() - 1:
		return ""
	return ORDER[i + 1]


func continue_id():
	var i = clampi(unlocked, 1, ORDER.size()) - 1
	return ORDER[i]


func finished_game():
	return int(stars.get("2-3", 0)) > 0


func stage1_leaks():
	var total = 0
	for id in STAGE1:
		total += int(leaks.get(id, 0))
	return total


func boss_extra():
	return mini(20, floori(stage1_leaks() / 2.0))


func record(result):
	var id = result["id"]
	if result["passed"]:
		unlocked = maxi(unlocked, mini(index_of(id) + 2, ORDER.size()))
		stars[id] = maxi(int(stars.get(id, 0)), int(result["stars"]))
		best[id] = maxi(int(best.get(id, 0)), int(result["score"]))
		if STAGE1.has(id):
			leaks[id] = int(result["leaked"])
	save_game()


func mark_hint(key):
	seen_hints[key] = true


func reset_hints():
	seen_hints = {}
	save_game()


# ------------------------------------------------------------------ simpan
func save_game():
	var cf = ConfigFile.new()
	cf.set_value("progress", "unlocked", unlocked)
	cf.set_value("progress", "stars", stars)
	cf.set_value("progress", "best", best)
	cf.set_value("progress", "leaks", leaks)
	cf.set_value("progress", "seen_hints", seen_hints)
	cf.set_value("settings", "music_vol", music_vol)
	cf.set_value("settings", "sfx_vol", sfx_vol)
	cf.set_value("settings", "fullscreen", fullscreen)
	cf.set_value("settings", "shake", shake)
	cf.save(SAVE_PATH)


func load_save():
	var cf = ConfigFile.new()
	if cf.load(SAVE_PATH) != OK:
		return
	unlocked = clampi(int(cf.get_value("progress", "unlocked", 1)), 1, ORDER.size())
	stars = cf.get_value("progress", "stars", {})
	best = cf.get_value("progress", "best", {})
	leaks = cf.get_value("progress", "leaks", {})
	seen_hints = cf.get_value("progress", "seen_hints", {})
	music_vol = float(cf.get_value("settings", "music_vol", 0.7))
	sfx_vol = float(cf.get_value("settings", "sfx_vol", 0.8))
	fullscreen = bool(cf.get_value("settings", "fullscreen", false))
	shake = bool(cf.get_value("settings", "shake", true))


func reset_progress():
	unlocked = 1
	stars = {}
	best = {}
	leaks = {}
	seen_hints = {}
	save_game()
