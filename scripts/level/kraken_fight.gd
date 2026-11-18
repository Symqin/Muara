# Jalannya pertarungan segmen 2-3: fase, lemparan sampah, jaring hantu, badai serpihan,
# kotak bantuan, gelembung, dan ikan yang lewat. Kraken sendiri ada di kraken/kraken.gd.
class_name KrakenFight
extends Node

@export var throw_interval: Array = [3.5, 4.5]   # fase 1, fase 2
@export var throw_damage: float = 6.0
@export var ghost_net_interval: float = 8.0
@export var ghost_net_drag_time: float = 6.0
@export var flake_interval: float = 7.0
@export var flake_lanes: int = 2
@export var flakes_per_lane: int = 6
@export var flake_damage: float = 3.0
@export var box_interval: float = 25.0
@export var bubble_interval: float = 15.0
@export var fish_interval: float = 10.0

var level = null
var phase: int = 1
var _throw_t: float = 0.0
var _net_t: float = 0.0
var _flake_t: float = 0.0
var _box_t: float = 0.0
var _bubble_t: float = 0.0
var _fish_t: float = 0.0


func _ready() -> void:
	level = owner


func begin() -> void:
	phase = 1
	_box_t = box_interval
	_throw_t = 3.0
	_net_t = 3.0
	_flake_t = 2.0
	_bubble_t = bubble_interval
	_fish_t = 6.0
	level.banner("Kraken terlilit sampah!")
	level.hints.request("boss1", "Ambil sampahnya, jangan kena tubuh kraken!", "", 4.0, false)
	level.hints.request("boss1b", "Magnet aman untuk kraken: tarik semua kalengnya", "", 3.5, false)


func tick(delta: float) -> void:
	var kraken = level.kraken
	if kraken.remaining() <= 0:
		level.finish_boss(true)
		return
	_update_phase(kraken)
	if phase <= 2:
		_throw_t -= delta
		if _throw_t <= 0.0:
			_throw_t = float(throw_interval[phase - 1])
			_throw(kraken)
	if phase == 2:
		_net_t -= delta
		if _net_t <= 0.0:
			_net_t = ghost_net_interval
			_ghost_net(kraken)
	if phase == 3:
		_flake_t -= delta
		if _flake_t <= 0.0:
			_flake_t = flake_interval
			_flakes(kraken)
	_box_t -= delta
	if _box_t <= 0.0:
		_box_t = box_interval
		spawn_box()
	_bubble_t -= delta
	if _bubble_t <= 0.0:
		_bubble_t = bubble_interval
		var b = level.entities.spawn("bubble", Vector2(randf_range(600.0, 1100.0), 950.0))
		b.motion = "rise"
	_fish_t -= delta
	if _fish_t <= 0.0:
		_fish_t = fish_interval
		_passing_fish()
	_resolve_projectiles(kraken)


func _update_phase(kraken) -> void:
	var f = kraken.fraction()
	var np = 1
	if f <= 0.3:
		np = 3
	elif f <= 0.6:
		np = 2
	if np <= phase:
		return
	phase = np
	kraken.agitation = phase
	level.banner("Fase %d" % phase)
	spawn_box()
	if phase == 2:
		_net_t = 2.0
		_throw_t = 2.0
		level.hints.request("boss2", "Fase 2: tarik jaring hantu sebelum melilit kraken", "", 3.5, false)
	else:
		_flake_t = 1.5
		level.hints.request("boss3", "Fase 3: kraken panik! Tentakel makin cepat", "", 3.5, false)


# Lemparan yang mendarat di Raka mengurangi oksigen; jaring hantu yang sampai membuat kraken terlilit lagi.
func _resolve_projectiles(kraken) -> void:
	for e in level.entities.items.duplicate():
		if e.state != "free":
			continue
		if e.motion == "proj" and e.proj_done():
			if Arena.RAKA_BOX.has_point(e.position):
				level.hurt_raka(throw_damage)
				level.entities.remove(e)
			else:
				e.motion = "sink"
		elif e.motion == "toboss" and e.toboss_done():
			kraken.heal(2)
			level.float_text(kraken.bar_anchor() + Vector2(0, 80), "Kraken terlilit lagi! +2 sampah", Color(1, 0.55, 0.5))
			Game.sfx("throw")
			level.entities.remove(e)
		elif e.motion == "fly" and Arena.RAKA_BOX.has_point(e.position):
			level.hurt_raka(flake_damage)
			level.entities.remove(e)


func spawn_box() -> void:
	var e = level.entities.spawn("box", Vector2(randf_range(820.0, 1250.0), 215.0))
	e.motion = "fall"


func _throw(kraken) -> void:
	var k = "bag" if randf() < 0.5 else "sachet"
	var start = kraken.throw_point()
	var e = level.entities.spawn(k, start)
	e.is_proj = true
	e.motion = "proj"
	e.t = 0.0
	e.dur = 2.4
	var tgt = Arena.RAKA_POS + Vector2(0, -60)
	if randf() < 0.5:
		tgt += Vector2(randf_range(170.0, 380.0), randf_range(-260.0, -120.0))
	e.p0 = start
	e.p2 = tgt
	e.p1 = Vector2((start.x + tgt.x) * 0.5, maxf(Arena.SURFACE_Y + 30.0, minf(start.y, tgt.y) - 300.0))
	Game.sfx("throw")


func _ghost_net(kraken) -> void:
	var start = Vector2(randf_range(700.0, 1050.0), LevelData.LANES[randi_range(0, 4)])
	var e = level.entities.spawn("ghostnet", start)
	e.is_boss_net = true
	e.set_passenger("turtle" if randf() < 0.5 else "fish_%d" % randi_range(1, 3))
	e.motion = "toboss"
	e.t = 0.0
	e.dur = ghost_net_drag_time
	e.p0 = start
	e.p2 = kraken.global_position + Vector2(-120, 0)
	level.hints.request("bossnet", "Tarik jaring itu sebelum melilit kraken!", "", 3.0)


func _flakes(kraken) -> void:
	var lanes = [0, 1, 2, 3, 4]
	lanes.shuffle()
	var left = minf(kraken.left_edge() - 20.0, 1400.0)
	for li in range(flake_lanes):
		var y = LevelData.LANES[lanes[li]]
		for j in range(flakes_per_lane):
			var e = level.entities.spawn("flake", Vector2(left - j * 40.0, y + randf_range(-16.0, 16.0)))
			e.motion = "fly"
			e.vel = Vector2(-220.0, 0.0)
	Game.sfx("throw")


func _passing_fish() -> void:
	var d = -1 if randf() < 0.5 else 1
	var x0 = 1980.0 if d < 0 else -80.0
	var fsh = level.entities.spawn("fish", Vector2(x0, LevelData.LANES[randi_range(0, 3)]))
	fsh.motion = "swim"
	fsh.face(d)
	fsh.vel = Vector2(170.0 * d, 0.0)
