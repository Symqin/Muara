# Antrean petunjuk tutorial yang tampil satu per satu di tengah atas layar.
# Petunjuk "sekali saja" disimpan di Game.seen_hints supaya tidak muncul lagi.
class_name HintSystem
extends Node

## Batas waktu tampil untuk petunjuk yang menunggu aksi pemain
@export var max_wait: float = 12.0

var active = null           # Dictionary petunjuk yang sedang tampil, atau null
var _queue: Array = []


# key: nama unik. until: kunci aksi yang menutup petunjuk ("" = tutup setelah dur detik).
func request(key: String, text: String, until: String = "", dur: float = 3.0, once: bool = true) -> void:
	if once and Game.seen_hints.has(key):
		return
	if active != null and active["key"] == key:
		return
	for h in _queue:
		if h["key"] == key:
			return
	_queue.append({"key": key, "text": text, "until": until, "dur": dur, "time": 0.0, "met": false, "once": once})


# Pemain sudah melakukan aksi yang diminta petunjuk ini.
func complete(key: String) -> void:
	if active != null and active["key"] == key:
		active["met"] = true
	for h in _queue:
		if h["key"] == key:
			h["met"] = true


func current_text() -> String:
	return "" if active == null else active["text"]


func _process(delta: float) -> void:
	if active == null:
		if _queue.is_empty():
			return
		active = _queue.pop_front()
		if active["once"]:
			Game.mark_hint(active["key"])
	active["time"] = active["time"] + delta
	var done = false
	if active["until"] == "":
		done = active["time"] >= active["dur"]
	else:
		done = (active["met"] and active["time"] >= 1.0) or active["time"] >= max_wait
	if done:
		active = null
