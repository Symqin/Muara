# Menjalankan gelombang sampah segmen biasa (1-1 sampai 2-2) dari LevelData.WAVES.
class_name WaveDirector
extends Node

## Gelombang berikutnya mulai paling lambat sekian detik setelah sampah terakhir muncul
@export var min_wave_wait: float = 8.0
@export var wave_gap: float = 1.5
@export var banner_time: float = 1.5

var level = null
var waves: Array = []
var wave_i: int = -1
var _wave_t: float = 0.0
var _ev_i: int = 0
var _since_last: float = 0.0
var _gap_t: float = -1.0


func _ready() -> void:
	level = owner


# Muat jadwal gelombang (dipanggil saat level disiapkan, supaya HUD sudah tahu jumlahnya).
func load_waves(seg_id: String) -> void:
	waves = LevelData.WAVES[seg_id]


func begin() -> void:
	_start_wave(0)


func wave_count() -> int:
	return waves.size()


func _start_wave(i: int) -> void:
	wave_i = i
	_wave_t = -banner_time
	_ev_i = 0
	_since_last = 0.0
	_gap_t = -1.0
	level.banner("Gelombang %d/%d" % [i + 1, waves.size()])


func tick(delta: float) -> void:
	if level.tutorial_hold:
		return
	_check_clog()
	if _gap_t >= 0.0:
		_gap_t -= delta
		if _gap_t < 0.0:
			_start_wave(wave_i + 1)
		return
	_wave_t += delta
	var evs = waves[wave_i]
	while _ev_i < evs.size() and _wave_t >= float(evs[_ev_i]["t"]):
		_spawn(evs[_ev_i])
		_ev_i += 1
		_since_last = 0.0
	if _ev_i < evs.size():
		return
	_since_last += delta
	if wave_i < waves.size() - 1:
		if level.entities.trash_count(wave_i) == 0 or _since_last >= min_wave_wait:
			_gap_t = wave_gap
	elif level.entities.trash_count(-1) == 0:
		level.finish_normal(false)


func _spawn(ev: Dictionary) -> void:
	var k = ev["k"]
	var e = level.entities.spawn(k, Vector2(float(ev["x"]), float(ev["y"])))
	e.wave = wave_i
	var hold = str(ev.get("hold", ""))
	if e.cat == "trash" or k == "wood" or k == "jelly":
		e.motion = "drift"
		if hold != "":
			e.hold = hold
			e.motion = "hold"
	var hints = level.hints
	if k == "fish":
		var d = int(ev.get("dir", -1))
		e.motion = "swim"
		e.face(d)
		e.vel = Vector2(170.0 * d, 0.0)
		hints.request("fish", "Jangan kena ikan!", "", 3.0)
	elif k == "jelly":
		hints.request("jelly", "Kresek berpegangan, ubur-ubur bertentakel", "", 3.5)
	elif k == "wood":
		hints.request("wood", "Kayu menghalangi harpun", "", 2.5)
	elif k == "bubble":
		e.motion = "rise"
		hints.request("bubble", "Tarik gelembung, tambah oksigen", "", 3.0)
	elif k == "box":
		e.motion = "fall"
		hints.request("box", "Tarik kotak: amunisi dari warga", "", 3.0)
	if hold == "tutorial":
		hints.request("fire", Game.t("Klik untuk menembak harpun", "Ketuk ke arah sampah untuk menembak"), "fire")


# Sumbatan pintu air (1-3): sampah di belakang ban baru mengalir setelah semua ban diangkat.
func _check_clog() -> void:
	var ents = level.entities
	if ents.has_free_hold("clog") or not ents.has_hold("clog_behind"):
		return
	for e in ents.items:
		if e.hold == "clog_behind":
			e.hold = ""
			if e.state == "free":
				e.motion = "drift"
	level.float_text(Vector2(1500, 560), "Pintu air terbuka!", Color(1, 0.9, 0.6))
