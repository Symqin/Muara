"""Pemeriksa statis proyek Muara (tanpa Godot).

Memeriksa skrip GDScript dan scene .tscn:
- indentasi tab, kurung seimbang, pola yang ditolak GDScript
- referensi antar-skrip (level.x, kraken.x, Game.x, LevelData.X, ...)
- path res:// yang dipakai benar-benar ada
- di setiap scene: induk node ada, %NamaUnik dan $Path yang dipakai skrip ada,
  koneksi sinyal mengarah ke fungsi yang ada, properti @export yang diisi memang ada,
  dan theme_type_variation terdaftar di tema.

Pemakaian: python3 tools/check_project.py <folder_proyek>
"""
import os, re, sys, glob

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
problems = []


def rel(p):
    return os.path.relpath(p, ROOT)


def res_to_path(r):
    return os.path.join(ROOT, r.replace("res://", ""))


# ---------------------------------------------------------------- skrip
scripts = {}
for p in glob.glob(os.path.join(ROOT, "scripts", "**", "*.gd"), recursive=True):
    scripts["res://" + rel(p).replace(os.sep, "/")] = open(p, encoding="utf-8").read()


def strip_strings(src):
    src = re.sub(r'"(?:\\.|[^"\\])*"', '""', src)
    return re.sub(r"#.*", "", src)


def members(src):
    m = set(re.findall(r"^(?:static )?func (\w+)", src, re.M))
    m |= set(re.findall(r"^(?:@export(?:_\w+)?(?:\([^)]*\))? |@onready )?var (\w+)", src, re.M))
    m |= set(re.findall(r"^const (\w+)", src, re.M))
    m |= set(re.findall(r"^signal (\w+)", src, re.M))
    return m


class_of = {}
for path, src in scripts.items():
    cm = re.search(r"^class_name (\w+)", src, re.M)
    if cm:
        class_of[cm.group(1)] = path

base_of = {}
for path, src in scripts.items():
    em = re.search(r"^extends (\w+)", src, re.M)
    base_of[path] = em.group(1) if em else "RefCounted"


def all_members(path):
    m = set(members(scripts[path]))
    base = base_of.get(path)
    if base in class_of:
        m |= all_members(class_of[base])
    return m


MEM = {p: all_members(p) for p in scripts}

# Node bawaan Godot yang sering dipakai lewat titik (tidak perlu diperiksa)
BUILTIN = {"position", "global_position", "rotation", "scale", "modulate", "visible", "z_index", "queue_free",
           "create_tween", "add_child", "get_tree", "process_mode", "texture", "flip_h", "offset", "centered",
           "size", "text", "disabled", "pressed", "get_children", "to_global", "to_local", "has_method",
           "theme_type_variation", "value", "is_instance_valid", "connect", "emit", "call", "is_valid",
           "resource_path", "get_file", "get_basename", "add_theme_color_override", "get_global_mouse_position"}

# 1. gaya dasar
for path, src in scripts.items():
    for i, line in enumerate(src.split("\n"), 1):
        lead = re.match(r"^[ \t]*", line).group(0)
        if " " in lead and line.strip():
            problems.append(f"{path}:{i} indentasi memakai spasi")
        s = line.strip()
        if ":=" in s:
            problems.append(f"{path}:{i} memakai ':=' (hindari, tulis tipe eksplisit)")
        if re.match(r"^(if|elif|for|while)\b.*:\s*\S", s) and " else:" in s:
            problems.append(f"{path}:{i} if/else satu baris")
    code = strip_strings(src)
    for a, b in ["()", "[]", "{}"]:
        if code.count(a) != code.count(b):
            problems.append(f"{path} kurung tidak seimbang {a}{b}: {code.count(a)} vs {code.count(b)}")

# 2. referensi antar-skrip berdasarkan nama variabel penerima
L = "res://scripts/level/"
RECEIVERS = [
    (r"\blevel\.(\w+)", L + "level.gd"),
    (r"\blv\.(\w+)", L + "level.gd"),
    (r"\blevel\.raka\.(\w+)", L + "raka.gd"),
    (r"\blevel\.entities\.(\w+)", L + "entity_layer.gd"),
    (r"\blevel\.hints\.(\w+)", L + "hint_system.gd"),
    (r"\blevel\.waves\.(\w+)", L + "wave_director.gd"),
    (r"\blevel\.fight\.(\w+)", L + "kraken_fight.gd"),
    (r"\blevel\.kraken\.(\w+)", L + "kraken/kraken.gd"),
    (r"\bkraken\.(\w+)", L + "kraken/kraken.gd"),
    (r"\bk\.(\w+)", L + "kraken/kraken.gd"),
    (r"\braka\.(\w+)", L + "raka.gd"),
    (r"\bentities\.(\w+)", L + "entity_layer.gd"),
    (r"\bents\.(\w+)", L + "entity_layer.gd"),
    (r"\bhints\.(\w+)", L + "hint_system.gd"),
    (r"\bwaves\.(\w+)", L + "wave_director.gd"),
    (r"\bfight\.(\w+)", L + "kraken_fight.gd"),
    (r"\bboat\.(\w+)", L + "boat.gd"),
    (r"\bhud\.(\w+)", L + "hud.gd"),
    (r"\bpause_menu\.(\w+)", L + "pause_menu.gd"),
    (r"\b(?:e|piece|b|fsh|item_e)\.(\w+)", L + "water_object.gd"),
    (r"\b(?:hook_tool|net_tool|magnet_tool|tool)\.(\w+)", L + "tools/level_tool.gd"),
    (r"\bmain\.(\w+)", "res://scripts/core/main.gd"),
    (r"\bGame\.(\w+)", "res://scripts/autoload/game.gd"),
]
for cname, cpath in class_of.items():
    RECEIVERS.append((r"\b" + cname + r"\.(\w+)", cpath))

TOOL_EXTRA = MEM.get(L + "tools/magnet_tool.gd", set()) | MEM.get(L + "tools/net_tool.gd", set()) | MEM.get(L + "tools/hook_tool.gd", set())
for path, src in scripts.items():
    code = strip_strings(src)
    for pat, target in RECEIVERS:
        if target not in MEM:
            problems.append(f"pemeriksa: skrip target {target} tidak ada")
            continue
        for m in re.finditer(pat, code):
            # lewati level.raka.x dst. pada pola umum level.x (ditangani pola khusus)
            name = m.group(1)
            if name in BUILTIN or name in MEM[target]:
                continue
            if target.endswith("level_tool.gd") and name in TOOL_EXTRA:
                continue
            # "level.raka" -> raka adalah anggota level; aman
            problems.append(f"{path}: '{m.group(0)}' -> '{name}' tidak ada di {target}")

# 3. pemanggilan fungsi privat di file yang sama (atau kelas induk)
for path, src in scripts.items():
    code = strip_strings(src)
    for m in re.finditer(r"(?<![\.\w])(_\w+)\(", code):
        n = m.group(1)
        if n not in MEM[path] and n not in ("_ready", "_process", "_draw", "_init", "_notification"):
            problems.append(f"{path}: memanggil {n}() yang tidak ada")
    for m in re.finditer(r"\.connect\(([_a-zA-Z]\w*)\)", code):
        n = m.group(1)
        if n not in MEM[path]:
            problems.append(f"{path}: connect ke {n} yang tidak ada")

# 4. path res:// literal
all_text = dict(scripts)
for p in glob.glob(os.path.join(ROOT, "**", "*.tscn"), recursive=True) + glob.glob(os.path.join(ROOT, "**", "*.tres"), recursive=True):
    all_text["res://" + rel(p).replace(os.sep, "/")] = open(p, encoding="utf-8").read()
for path, src in all_text.items():
    for m in re.finditer(r'"(res://[^"%]+)"', src):
        if not os.path.exists(res_to_path(m.group(1))):
            problems.append(f"{path}: file tidak ada {m.group(1)}")
art = {os.path.basename(p)[:-4] for p in glob.glob(os.path.join(ROOT, "art", "*.png"))}
data = scripts.get("res://scripts/data/level_data.gd", "")
for t in re.findall(r'"(trash_\w+|fish_\d|jelly|wood|bubble|box|turtle)"', data):
    if t not in art:
        problems.append(f"level_data.gd: tekstur {t} tidak ada")
story = scripts.get("res://scripts/data/story_data.gd", "")
for key in set(re.findall(r'\["(\w+)", "', story)):
    if f"portrait_{key}" not in art:
        problems.append(f"story_data.gd: potret {key} tidak ada")
for seg in ["1_1", "1_2", "1_3", "2_1", "2_2", "2_3"]:
    for v in ["murky", "clean"]:
        if f"bg_{seg}_{v}" not in art:
            problems.append(f"latar bg_{seg}_{v} tidak ada")
joined = "".join(scripts.values())
for snd in set(re.findall(r'Game\.sfx\("(\w+)"', joined)):
    if not os.path.exists(os.path.join(ROOT, "audio", snd + ".wav")):
        problems.append(f"suara {snd}.wav tidak ada")
for mus in set(re.findall(r'"(music_(?:menu|river|sea|boss))"', joined)):
    if not os.path.exists(os.path.join(ROOT, "audio", mus + ".ogg")):
        problems.append(f"musik {mus}.ogg tidak ada")
for name in set(re.findall(r'spawn_decor\("(\w+)"', joined)):
    if name not in art:
        problems.append(f"tekstur hiasan {name} tidak ada")

# ---------------------------------------------------------------- tema
theme_src = all_text.get("res://resources/theme/muara_theme.tres", "")
theme_types = set(re.findall(r"^(\w+)/", theme_src, re.M))
sub_ids = set(re.findall(r'\[sub_resource type="\w+" id="(\w+)"\]', theme_src))
for sid in re.findall(r'SubResource\("(\w+)"\)', theme_src):
    if sid not in sub_ids:
        problems.append(f"tema: SubResource {sid} tidak ada")
for path, src in all_text.items():
    for v in set(re.findall(r'&"(\w+)"', re.sub(r'base_type = &"\w+"', "", src))):
        if v not in theme_types:
            problems.append(f"{path}: variasi tema '{v}' tidak ada di muara_theme.tres")

# ---------------------------------------------------------------- scene
NODE_PROP_OK = {"layout_mode", "anchors_preset", "anchor_left", "anchor_top", "anchor_right", "anchor_bottom",
                "offset_left", "offset_top", "offset_right", "offset_bottom", "grow_horizontal", "grow_vertical",
                "script", "width", "texture_mode", "joint_mode", "texture_repeat", "points", "unique_name_in_owner", "position", "scale", "rotation", "texture", "centered", "offset",
                "flip_h", "modulate", "z_index", "visible", "mouse_filter", "theme_type_variation", "text",
                "horizontal_alignment", "vertical_alignment", "custom_minimum_size", "size_flags_horizontal",
                "size_flags_vertical", "expand_mode", "stretch_mode", "color", "icon", "alignment", "focus_mode",
                "process_mode", "layer", "value", "show_percentage", "max_value", "step", "button_pressed",
                "autowrap_mode", "columns",
                # Area2D / CollisionPolygon2D (hitbox kepala kraken)
                "collision_layer", "collision_mask", "monitoring", "monitorable", "polygon"}

scenes = {}
for p in glob.glob(os.path.join(ROOT, "scenes", "**", "*.tscn"), recursive=True):
    scenes["res://" + rel(p).replace(os.sep, "/")] = open(p, encoding="utf-8").read()


def parse_scene(src):
    ext = dict((i, (t, path)) for t, path, i in re.findall(r'\[ext_resource type="(\w+)"(?: uid="[^"]*")? path="([^"]+)" id="([^"]+)"\]', src))
    nodes = []
    for block in re.split(r"\n(?=\[)", src):
        hm = re.match(r'\[node name="([^"]+)"(.*?)\]', block)
        if not hm:
            continue
        attrs = hm.group(2)
        parent = re.search(r'parent="([^"]*)"', attrs)
        inst = re.search(r'instance=ExtResource\("([^"]+)"\)', attrs)
        props = dict(re.findall(r"^(\w[\w/]*) = (.+)$", block, re.M))
        nodes.append({"name": hm.group(1), "parent": parent.group(1) if parent else None,
                      "instance": ext[inst.group(1)][1] if inst and inst.group(1) in ext else None, "props": props})
    conns = re.findall(r'\[connection signal="(\w+)" from="([^"]*)" to="([^"]*)" method="(\w+)"\]', src)
    return ext, nodes, conns


parsed = {k: parse_scene(v) for k, v in scenes.items()}


def node_paths(scene_path):
    """Kembalikan dict path->node (path relatif ke root, root = '.'), termasuk isi scene instance."""
    ext, nodes, _ = parsed[scene_path]
    out = {}
    for n in nodes:
        if n["parent"] is None:
            p = "."
        elif n["parent"] == ".":
            p = n["name"]
        else:
            p = n["parent"] + "/" + n["name"]
        out[p] = n
        if n["instance"] and n["instance"] in parsed:
            for sub, sn in node_paths(n["instance"]).items():
                if sub != ".":
                    out[(p + "/" + sub) if p != "." else sub] = sn
    return out


def script_of(n, ext):
    s = n["props"].get("script")
    if s:
        m = re.match(r'ExtResource\("([^"]+)"\)', s)
        if m and m.group(1) in ext:
            return ext[m.group(1)][1]
    if n["instance"] and n["instance"] in parsed:
        e2, n2, _ = parsed[n["instance"]]
        return script_of(n2[0], e2)
    return None


for spath, (ext, nodes, conns) in parsed.items():
    for i, (t, path) in ext.items():
        if not os.path.exists(res_to_path(path)):
            problems.append(f"{spath}: ext_resource tidak ada {path}")
    paths = node_paths(spath)
    own = {}
    for n in nodes:
        p = "." if n["parent"] is None else (n["name"] if n["parent"] == "." else n["parent"] + "/" + n["name"])
        own[p] = n
        if n["parent"] not in (None, ".") and n["parent"] not in paths:
            problems.append(f"{spath}: induk '{n['parent']}' untuk node '{n['name']}' tidak ada")
    uniques = {n["name"] for n in nodes if n["props"].get("unique_name_in_owner") == "true"}
    # skrip yang dipasang di scene ini memakai %Nama dan $Path milik scene ini
    for p, n in own.items():
        sc = script_of(n, ext) if n["instance"] is None else None
        if not sc or sc not in scripts:
            continue
        raw = strip_strings(scripts[sc])
        for u in re.findall(r"%(\w+)", raw):
            if u not in uniques:
                problems.append(f"{spath}: skrip {sc} memakai %{u} tetapi tidak ada node unik bernama {u}")
        for d in re.findall(r"\$([\w/]+)", raw):
            target = d if p == "." else p + "/" + d
            if target not in paths:
                problems.append(f"{spath}: skrip {sc} memakai ${d} tetapi node itu tidak ada")
    # properti kustom yang diisi harus ada di skripnya
    for p, n in paths.items():
        sc = script_of(n, ext if p in own else parsed[n.get("_scene", spath)][0]) if p in own else None
        if p not in own:
            continue
        sc = script_of(n, ext)
        for key in n["props"]:
            if key in NODE_PROP_OK or "/" in key:
                continue
            if sc and key in MEM.get(sc, set()):
                continue
            problems.append(f"{spath}: node '{p}' mengisi properti '{key}' yang tidak dikenal")
    for sig, frm, to, method in conns:
        f = "." if frm == "." else frm
        tt = "." if to == "." else to
        if f not in paths:
            problems.append(f"{spath}: koneksi dari node '{frm}' yang tidak ada")
        if tt not in paths:
            problems.append(f"{spath}: koneksi ke node '{to}' yang tidak ada")
            continue
        sc = script_of(paths[tt], ext)
        if not sc or method not in MEM.get(sc, set()):
            problems.append(f"{spath}: koneksi {sig} -> {method}() tidak ada di skrip {sc}")

# preload scene di skrip harus ada
for path, src in scripts.items():
    for m in re.findall(r'preload\("(res://[^"]+)"\)', src):
        if not os.path.exists(res_to_path(m)):
            problems.append(f"{path}: preload {m} tidak ada")

# main scene & autoload
proj = open(os.path.join(ROOT, "project.godot"), encoding="utf-8").read()
for m in re.findall(r'"\*?(res://[^"]+)"', proj):
    if not os.path.exists(res_to_path(m)):
        problems.append(f"project.godot: {m} tidak ada")

print("\n".join(sorted(set(problems))) if problems else "tidak ada masalah")
print(f"{len(scripts)} skrip dan {len(scenes)} scene diperiksa")
