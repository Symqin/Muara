# Ukuran dan titik penting arena (resolusi acuan 1920 x 1080).
# Semua skrip level memakai angka dari sini supaya tidak ada "angka ajaib" yang tersebar.
class_name Arena
extends RefCounted

const SURFACE_Y = 200.0          # permukaan air
const BED_Y = 960.0              # dasar sungai/laut
const RAKA_POS = Vector2(220, 880)
const PIVOT = Vector2(236, 820)  # bahu Raka, pusat putaran alat
const MUZZLE_LEN = 160.0         # jarak bahu ke ujung laras
const BASKET = Vector2(170, 800) # titik tujuan sampah yang tertangkap
const RAKA_BOX = Rect2(140, 690, 170, 290)
const AIM_MIN_DEG = -10.0
const AIM_MAX_DEG = 90.0
const SPAWN_X = 1980.0
const LEAK_X = 0.0
