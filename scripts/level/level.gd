# Satu segmen permainan (scenes/level/level.tscn).
#
# Level adalah "koordinator": menyimpan status (oksigen, skor, combo), menjalankan alur
# intro -> dialog -> play -> ended, dan menghubungkan komponen di scene:
#   Raka (bidikan), HookTool/NetTool/MagnetTool (alat), EntityLayer (objek di air),
#   WaveDirector (gelombang segmen biasa), KrakenFight (bos 2-3), HintSystem, Hud, PauseMenu.
# Komponen memanggil fungsi publik di bawah ("API untuk komponen") untuk memberi skor, melukai, dll.
class_name Level
extends Node2D

const KRAKEN_SCENE = preload("res://scenes/level/kraken/kraken.tscn")
const FLOATING_TEXT = preload("res://scenes/level/floating_text.tscn")

@export var oxygen_drain: float = 1.0
@export var bubble_oxygen: float = 8.0
@export var rescue_oxygen: float = 10.0
@export var rescue_points: int = 100
@export var creature_penalty: int = 30
@export var creature_oxygen_penalty: float = 5.0
## Dialog awal mulai otomatis setelah sekian detik
@export var dialog_auto_start: float = 8.0
@export var collect_time: float = 0.35
@export var banner_time: float = 1.5

var main = null                  # diisi oleh Main sebelum add_child
var seg_id: String = "1-1"       # diisi oleh Main sebelum add_child
var seg: Dictionary = {}
var is_boss: bool = false
var meter_label: String = "Sungai bersih"
var target: float = 0.6
var current: float = 60.0
var total_trash: int = 0
var dialog: Array = []

var state: String = "intro"      # intro, dialog, play, ended
var clock: float = 0.0
var oxygen: float = 100.0
var oxygen_max: float = 100.0
var score: int = 0
var streak: int = 0
var caught: int = 0
var leaked: int = 0
var creature_hits: int = 0
var turtles: int = 0
var cur_tool: int = 0
var tutorial_hold: bool = false

var banner_text: String = ""
var banner_t: float = 0.0
var leak_flash: float = 0.0
var kraken = null
var tools: Array = []

var _dialog_t: float = 0.0
var _o2_beep: float = 0.0
var _hitstop: float = 0.0
var _shake_t: float = 0.0
var _end_t: float = -1.0
var _result: Dictionary = {}
var _intro_bubble: float = 0.0

@onready var world: Node2D = %World
@onready var bg_murky: Sprite2D = %BgMurky
@onready var bg_clean: Sprite2D = %BgClean
@onready var kraken_slot: Node2D = %KrakenSlot
@onready var boat = %Boat
@onready var entities = %Entities
@onready var raka = %Raka
@onready var hook_tool = %HookTool
@onready var net_tool = %NetTool
@onready var magnet_tool = %MagnetTool
@onready var floating_texts: Node2D = %FloatingTexts
@onready var waves = %WaveDirector
@onready var fight = %KrakenFight
@onready var hints = %Hints
@onready var hud = %Hud
@onready var pause_menu = %PauseMenu


# ================================================================== persiapan
func _ready() -> void:
	seg = LevelData.SEGMENTS[seg_id]
	is_boss = seg_id == "2-3"
	target = float(seg["target"])
	current = float(seg["current"])
	oxygen_max = float(seg["oxygen"])
	oxygen = oxygen_max
	total_trash = int(seg["total"])
	var stage1 = int(seg["stage"]) == 1
	meter_label = "Sungai bersih" if stage1 else "Laut bersih"
	dialog = StoryData.SEGMENT_DIALOGS[seg_id]

	var key = seg_id.replace("-", "_")
	bg_murky.texture = load("res://art/bg_%s_murky.png" % key)
	bg_clean.texture = load("res://art/bg_%s_clean.png" % key)

	# Alat terbuka bertahap: Jaring sejak 1-2, Magnet sejak 2-1.
	var idx = Game.index_of(seg_id)
	tools = [hook_tool, net_tool, magnet_tool]
	var unlocked = [true, idx >= 1, idx >= 3]
	for i in range(tools.size()):
		tools[i].setup(is_boss, unlocked[i])

	if is_boss:
		kraken = KRAKEN_SCENE.instantiate()
		kraken_slot.add_child(kraken)
		kraken.setup(Game.boss_extra())
		Game.play_music("music_boss")
	else:
		waves.load_waves(seg_id)
		Game.play_music("music_river" if stage1 else "music_sea")

	hud.setup(self)
	pause_menu.restart_requested.connect(restart)
	pause_menu.quit_requested.connect(quit_to_menu)
	raka.dive_finished.connect(_on_dive_finished)
	_start_intro()


# ================================================================== alur: intro -> dialog -> play -> ended
func _start_intro() -> void:
	state = "intro"
	raka.play_dive(_on_splash)


func _on_splash() -> void:
	Game.sfx("bubble")
	for i in range(8):
		var p = Vector2(400.0 + randf_range(-70.0, 70.0), Arena.SURFACE_Y + randf_range(10.0, 70.0))
		var e = entities.spawn_decor("fx_bubble", p, Vector2(randf_range(-40.0, 40.0), randf_range(-160.0, -80.0)))
		e.scale = Vector2.ONE * randf_range(0.6, 1.3)


func _on_dive_finished() -> void:
	if state != "intro":
		return
	state = "dialog"
	_dialog_t = 0.0
	boat.sail_away()


func _skip_intro() -> void:
	raka.finish_dive()


func _start_play() -> void:
	if state != "dialog":
		return
	state = "play"
	if is_boss:
		fight.begin()
	else:
		waves.begin()
	if seg_id == "1-1":
		hints.request("aim", Game.t("Gerakkan mouse untuk membidik", "Geser jari untuk membidik"), "aim")
	elif seg_id == "1-2":
		hints.request("net", Game.t("Tekan 2: Jaring untuk gerombolan", "Ketuk slot 2: Jaring untuk gerombolan"), "net")
	elif seg_id == "2-1":
		hints.request("magnet", Game.t("Tekan 3, tahan klik: Magnet untuk kaleng", "Ketuk slot 3, lalu tahan: Magnet untuk kaleng"), "magnet")


func _process(delta: float) -> void:
	clock += delta
	raka.aim_at(get_global_mouse_position())
	if banner_t > 0.0:
		banner_t -= delta
	if leak_flash > 0.0:
		leak_flash -= delta
	_update_shake(delta)

	match state:
		"intro":
			_process_intro(delta)
		"dialog":
			_dialog_t += delta
			if _dialog_t > dialog_auto_start:
				_start_play()
		"ended":
			_process_ended(delta)
		"play":
			_process_play(delta)


func _process_intro(delta: float) -> void:
	entities.tick_ambient(delta, current)
	_intro_bubble -= delta
	if _intro_bubble <= 0.0 and raka.position.y > Arena.SURFACE_Y + 20.0:
		_intro_bubble = 0.2
		var b = entities.spawn_decor("fx_bubble", raka.helmet(), Vector2(randf_range(-20.0, 20.0), -130.0))
		b.scale = Vector2.ONE * randf_range(0.5, 1.0)


func _process_ended(delta: float) -> void:
	entities.tick_ambient(delta, current)
	if kraken != null:
		kraken.tick(delta)
	_end_t -= delta
	if _end_t <= 0.0 and not _result.is_empty():
		var r = _result
		_result = {}
		main.show_summary(r)


func _process_play(delta: float) -> void:
	if _hitstop > 0.0:
		_hitstop -= delta
		return
	tutorial_hold = entities.has_hold("tutorial")
	if not tutorial_hold:
		oxygen -= oxygen_drain * delta
	if oxygen < oxygen_max * 0.2:
		_o2_beep -= delta
		if _o2_beep <= 0.0:
			_o2_beep = 2.0
			Game.sfx("o2_low")

	for t in tools:
		t.update_tool(delta)
	entities.tick_all(delta, current, tutorial_hold, _on_leak)
	_update_collecting(delta)
	if state != "play":
		return
	if is_boss:
		kraken.tick(delta)
		fight.tick(delta)
	else:
		waves.tick(delta)
	if state != "play":
		return
	if oxygen <= 0.0:
		oxygen = 0.0
		if is_boss:
			finish_boss(false)
		else:
			finish_normal(true)


func _update_shake(delta: float) -> void:
	if _shake_t > 0.0 and Game.shake:
		_shake_t -= delta
		world.position = Vector2(randf_range(-7.0, 7.0), randf_range(-7.0, 7.0))
	else:
		_shake_t = 0.0
		world.position = Vector2.ZERO


# ================================================================== input
# Tombol HUD (slot alat, jeda) adalah Button di hud.tscn, jadi kliknya tidak sampai ke sini.
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		hints.complete("aim")
		return
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				raka.aim_at(event.position)
				_press()
			else:
				tools[cur_tool].release()
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_cycle_tool(-1)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_cycle_tool(1)
		return
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_1:
				select_tool(0)
			KEY_2:
				select_tool(1)
			KEY_3:
				select_tool(2)
			KEY_ESCAPE, KEY_P:
				open_pause()
			KEY_F3:
				toggle_debug_hitbox()
			KEY_SPACE, KEY_ENTER, KEY_KP_ENTER:
				if state == "intro":
					_skip_intro()
				elif state == "dialog":
					_start_play()


func _press() -> void:
	if state == "intro":
		_skip_intro()
	elif state == "dialog":
		_start_play()
	elif state == "play":
		tools[cur_tool].press()


func select_tool(i: int) -> void:
	if i < 0 or i >= tools.size() or not tools[i].unlocked:
		return
	if cur_tool != i:
		Game.sfx("click")
		tools[cur_tool].release()
	cur_tool = i
	raka.show_tool(i)
	magnet_tool.cancel()


# Alat bantu tes: tampilkan/sembunyikan semua hitbox.
func toggle_debug_hitbox() -> void:
	Game.debug_hitbox = not Game.debug_hitbox
	for e in entities.items:
		if is_instance_valid(e):
			e.refresh_debug()


func _cycle_tool(step: int) -> void:
	var i = cur_tool
	for n in range(tools.size()):
		i = (i + step + tools.size()) % tools.size()
		if tools[i].unlocked:
			select_tool(i)
			return


func open_pause() -> void:
	if state == "ended":
		return
	magnet_tool.cancel()
	pause_menu.open()
	get_viewport().set_input_as_handled()


# Tombol kembali Android.
func go_back() -> void:
	if pause_menu.visible:
		pause_menu.resume()
	else:
		open_pause()


func restart() -> void:
	main.play(seg_id, false)


func quit_to_menu() -> void:
	Game.save_game()
	main.show_menu()


# ================================================================== API untuk komponen
func mult() -> int:
	if streak < 5:
		return 1
	if streak < 10:
		return 2
	return 3


func banner(text: String) -> void:
	banner_text = text
	banner_t = banner_time


func float_text(pos: Vector2, text: String, color: Color = Color.WHITE) -> void:
	var l = FLOATING_TEXT.instantiate()
	floating_texts.add_child(l)
	l.popup(pos, text, color)


# Sampah/pickup terbang ke keranjang Raka, lalu dihitung di collect().
func start_collect(e) -> void:
	e.state = "collecting"
	e.collect_from = e.position
	e.collect_t = 0.0


func _update_collecting(delta: float) -> void:
	for e in entities.items.duplicate():
		if e.state != "collecting":
			continue
		e.collect_t += delta
		var u = minf(1.0, e.collect_t / collect_time)
		e.position = e.collect_from.lerp(Arena.BASKET, u)
		e.scale = Vector2.ONE * (1.0 - 0.5 * u)
		if u >= 1.0:
			collect(e)


# Objek sampai di keranjang: beri skor, oksigen, atau amunisi.
func collect(e) -> void:
	if e.cat == "trash":
		var m = mult()
		var gained = e.pts * m
		score += gained
		streak += 1
		if not is_boss:
			caught += 1
		if e.hold == "tutorial":
			hints.complete("fire")
		var txt = "+%d" % gained
		if m > 1:
			txt += " x%d" % m
		float_text(Arena.BASKET + Vector2(60, -120), txt)
		if e.has_turtle or e.is_boss_net:
			_rescue(e)
		Game.sfx("catch")
		_hitstop = 0.04
	elif e.kind == "bubble":
		oxygen = minf(oxygen_max, oxygen + bubble_oxygen)
		float_text(Arena.BASKET + Vector2(60, -120), "+%d Oksigen" % int(bubble_oxygen), Color(0.7, 0.9, 1))
		Game.sfx("bubble")
	elif e.kind == "box":
		_open_box()
	entities.remove(e)


func _rescue(e) -> void:
	score += rescue_points
	oxygen = minf(oxygen_max, oxygen + rescue_oxygen)
	if e.has_turtle:
		turtles += 1
	float_text(Arena.BASKET + Vector2(60, -170), "+%d Bebas!" % rescue_points, Color(0.6, 1, 0.7))
	entities.spawn_decor(e.passenger_texture_name(), e.position, Vector2(220, -140))


func _open_box() -> void:
	var got = []
	if net_tool.refill():
		got.append("+1 Jaring")
	if magnet_tool.refill():
		got.append("+1 Magnet")
	if got.is_empty():
		got.append("Amunisi penuh")
	float_text(Arena.BASKET + Vector2(60, -120), ", ".join(PackedStringArray(got)), Color(1, 0.9, 0.6))
	Game.sfx("box")


func hit_creature(e) -> void:
	creature_hits += 1
	score = maxi(0, score - creature_penalty)
	oxygen = maxf(0.0, oxygen - creature_oxygen_penalty)
	streak = 0
	Game.sfx("startle")
	float_text(e.position, "-%d" % creature_penalty, Color(1, 0.55, 0.5))
	if e.kind == "fish":
		e.state = "fleeing"
		e.motion = "flee"
		var d = e.dir if e.dir != 0 else -1
		e.vel = Vector2(560.0 * d, -160.0)
	else:
		e.flash = 0.6


# Alat mengenai kulit kraken: nyawa kraken berkurang. Nyawa habis = kalah.
func hurt_kraken(amount: float, p: Vector2) -> void:
	kraken.hurt(amount)
	creature_hits += 1
	score = maxi(0, score - creature_penalty)
	streak = 0
	Game.sfx("startle")
	float_text(p, "Aduh! Kraken -%d" % int(amount), Color(1, 0.5, 0.5))
	hints.request("krakenhit", "Bidik sampahnya, bukan tubuh kraken!", "", 2.5)
	if kraken.hp <= 0.0:
		finish_boss(false, true)


# Raka terkena lemparan atau serpihan.
func hurt_raka(amount: float) -> void:
	oxygen = maxf(0.0, oxygen - amount)
	Game.sfx("hurt")
	_shake_t = 0.25
	float_text(Arena.RAKA_POS + Vector2(0, -200), "-%d Oksigen" % int(amount), Color(1, 0.55, 0.5))


func _on_leak(e) -> void:
	leaked += 1
	streak = 0
	leak_flash = 1.0
	Game.sfx("leak")
	hints.request("leak", "Sampah lolos ke laut!", "", 2.0)
	entities.remove(e)


# ================================================================== selesai
func _flush_pending() -> void:
	for e in entities.items.duplicate():
		if e.state == "hooked" or e.state == "collecting":
			collect(e)
	for t in tools:
		t.cancel()


func finish_normal(o2_out: bool) -> void:
	if state != "play":
		return
	_flush_pending()
	state = "ended"
	leaked = maxi(0, total_trash - caught)
	var meter = float(caught) / float(maxi(total_trash, 1))
	var needed = int(ceil(target * float(total_trash) - 0.0001))
	var passed = caught >= needed
	var bonus = 0
	var stars_n = 0
	if passed:
		bonus = 5 * maxi(0, int(round((meter - target) * 100.0))) + int(oxygen) + (200 if creature_hits == 0 else 0)
		score += bonus
		stars_n = 1
		if meter >= 0.9:
			stars_n += 1
			if creature_hits == 0:
				stars_n += 1
	_result = {
		"id": seg_id, "passed": passed, "is_boss": false, "stars": stars_n, "score": score, "bonus": bonus,
		"caught": caught, "total": total_trash, "meter": meter, "leaked": leaked,
		"creature_hits": creature_hits, "turtles": turtles, "oxygen_left": oxygen, "o2_out": o2_out,
	}
	if passed:
		banner("Segmen bersih!")
		_celebrate()
		_end_t = 3.0
	else:
		banner("Oksigen habis!" if o2_out else "Belum mencapai target")
		if o2_out:
			raka.surface()
		_end_t = 2.0
	banner_t = 2.5
	Game.save_game()


func finish_boss(win: bool, kraken_down: bool = false) -> void:
	if state != "play":
		return
	_flush_pending()
	state = "ended"
	var bonus = 0
	var stars_n = 0
	if win:
		bonus = int(oxygen) + int(kraken.hp) * 2 + (200 if creature_hits == 0 else 0)
		score += bonus
		stars_n = 1
		if oxygen >= 30.0:
			stars_n += 1
			if creature_hits == 0:
				stars_n += 1
	var taken = kraken.total - kraken.remaining()
	_result = {
		"id": seg_id, "passed": win, "is_boss": true, "stars": stars_n, "score": score, "bonus": bonus,
		"caught": taken, "total": kraken.total, "meter": float(taken) / float(maxi(kraken.total, 1)), "leaked": 0,
		"creature_hits": creature_hits, "turtles": turtles, "oxygen_left": oxygen, "o2_out": not win and not kraken_down,
		"kraken_hp": int(round(kraken.hp)), "kraken_down": kraken_down,
	}
	if win:
		banner("Kraken bebas!")
		kraken.set_happy()
		var tw = kraken.create_tween()
		tw.tween_interval(0.8)
		tw.tween_property(kraken, "position", Vector2(2400, 260), 3.0).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
		entities.spawn_decor("turtle", kraken.global_position + Vector2(-200, 0), Vector2(-160, -120))
		_celebrate()
		_end_t = 4.0
	elif kraken_down:
		banner("Kraken terluka parah!")
		var tw2 = kraken.create_tween()
		tw2.tween_property(kraken, "modulate", Color(0.6, 0.55, 0.6, 0.85), 1.0)
		_end_t = 2.8
	else:
		banner("Oksigen habis!")
		raka.surface()
		_end_t = 2.0
	banner_t = 2.5
	Game.save_game()


# Air menjernih dan ikan berdatangan.
func _celebrate() -> void:
	Game.sfx("win")
	var tw = bg_clean.create_tween()
	tw.tween_property(bg_clean, "modulate:a", 1.0, 2.0)
	for i in range(5):
		var fname = "fish_%d" % (1 + i % 3)
		entities.spawn_decor(fname, Vector2(-60.0 - i * 90.0, 330.0 + i * 110.0), Vector2(320.0, -10.0))
