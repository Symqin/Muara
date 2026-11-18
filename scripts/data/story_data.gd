# Semua teks cerita dan deskripsi segmen di satu tempat, supaya mudah disunting tanpa membuka kode lain.
class_name StoryData
extends RefCounted

# Adegan cerita: gambar + baris dialog [kunci potret, nama, teks].
# Kunci potret = nama file art/portrait_<kunci>.png
const STORIES = {
	"intro": {
		"image": "res://art/story_intro.png",
		"lines": [
			["kakek", "Kakek", "Ikannya pada pergi, Ka. Jaring kakek cuma dapat sampah."],
			["raka", "Raka", "Biar Raka yang menyelam, Kek. Sampahnya harus diangkat sebelum sampai ke laut!"],
		],
	},
	"sea": {
		"image": "res://art/story_sea.png",
		"lines": [
			["kakek", "Kakek", "Sampah yang lolos dari sungai sudah terbawa ke laut. Kata nelayan, ada kraken yang terlilit sampah di laut dalam."],
			["raka", "Raka", "Kita tolong krakennya juga, Kek! Ayo bersihkan lautnya."],
		],
	},
	"end": {
		"image": "res://art/story_end.png",
		"lines": [
			["raka", "Raka", "Krakennya bebas dari sampah! Penyu kecil yang ikut terlilit juga selamat."],
			["kakek", "Kakek", "Lihat, Ka! Kail kakek dapat ikan lagi."],
			["busari", "Bu Sari", "Ayo, semua bawa sampahnya ke bank sampah. Kita jaga sungai dan laut bersama-sama!"],
		],
	},
}

# Cerita yang diputar sebelum segmen tertentu.
const STORY_BEFORE_SEGMENT = {"1-1": "intro", "2-1": "sea"}

# Satu baris dialog di awal setiap segmen.
const SEGMENT_DIALOGS = {
	"1-1": ["raka", "Raka", "Sampah harus kutangkap sebelum hanyut ke laut. Bidik, lalu tembak!"],
	"1-2": ["kakek", "Kakek", "Pakai jaring kakek, Ka! Cocok untuk sampah yang bergerombol."],
	"1-3": ["raka", "Raka", "Sampahnya makin banyak... ternyata datangnya dari kota."],
	"2-1": ["busari", "Bu Sari", "Raka, ini Magnet dari bank sampah. Cocok untuk kaleng!"],
	"2-2": ["raka", "Raka", "Karangnya pucat. Hati-hati, kresek mirip ubur-ubur!"],
	"2-3": ["raka", "Raka", "Kraken itu terlilit sampah! Ambil sampahnya satu per satu, jangan sampai melukainya."],
}

# Deskripsi segmen di Peta Perjalanan.
const SEGMENT_DESC = {
	"1-1": "Belajar membidik, menembak, dan menarik sampah. Hati-hati, jangan kena ikan.",
	"1-2": "Kakek memberi Jaring Lontar untuk gerombolan sachet. Kayu hanyut menghalangi harpun.",
	"1-3": "Arus makin deras. Ban menyumbat pintu air kota dan sampah menumpuk di belakangnya.",
	"2-1": "Bu Sari mengirim Magnet Pulsa. Cocok untuk kelompok kaleng.",
	"2-2": "Kresek mirip ubur-ubur. Selamatkan penyu yang terjerat jaring hantu.",
	"2-3": "Kraken terlilit sampah yang lolos dari sungai. Ambil sampahnya tanpa melukai kraken.",
}
