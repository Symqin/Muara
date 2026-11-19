# Muara

*Muara* adalah **game menyelam pembersihan sampah** untuk **satu pemain**, dibuat dengan **Godot 4** untuk PC dan HP (HTML5/Android).

Pemain berperan sebagai **Raka, seorang anak penyelam** yang membersihkan sampah dari **sungai (muara)** sampai ke **laut** agar air kembali bersih. Pakai **Harpun, Jaring Lontar, dan Magnet Pulsa**, Raka mengangkat sampah sebelum hanyut ke laut — tanpa melukai ikan, ubur-ubur, atau penyu. Puncaknya, Raka menyelamatkan **kraken yang terlilit sampah** di sarangnya.

## Fitur

- 6 segmen dalam 2 babak: *Sungai* (1-1 s.d. 1-3) dan *Laut* (2-1 s.d. 2-3)
- Alat yang terbuka bertahap: Harpun, Jaring, Magnet
- 3 gelombang sampah per segmen, makin lama makin deras
- Boss di segmen 2-3: selamatkan kraken dari lilitan sampah
- Sistem oksigen, skor, combo, dan bintang per segmen
- Progres tersimpan, bisa dimainkan di PC dan HP

## Cara main

Buka proyek dengan **Godot 4.7** (Import `project.godot`, lalu tekan **F5**).

| Input | Fungsi |
|---|---|
| Mouse | Membidik |
| Klik kiri | Tembak (Magnet: tahan) |
| 1 / 2 / 3 atau scroll | Ganti alat |
| Esc / P | Jeda |

Di HP: ketuk untuk membidik & menembak, geser untuk membidik, tahan untuk Magnet. Ketuk slot alat untuk ganti alat.

## Struktur

```
project.godot          main scene + autoload "Game"
scenes/                semua scene (menu, level, kraken, HUD, dll.)
scripts/               skrip logika (data cerita & level, alat, bos, dll.)
art/                   gambar
audio/                 suara & musik
resources/theme/       tema UI global
```