# Muara: Proyek Godot (Tim HaMinAtu, Gimersia Inspire 2026)

Ini game *Muara* dalam versi yang sudah bisa dimainkan dari awal sampai akhir: menu, cerita, 6 segmen (Sungai 1-1 s.d. 1-3, Laut 2-1 s.d. 2-3 menyelamatkan kraken yang terlilit sampah), ringkasan, simpanan progres, pengaturan, dan credits.

> **PENTING: semua gambar, suara, dan musik di `art/` dan `audio/` adalah ASET ACUAN buatan generator (Python, dibuat oleh AI).**
> Aturan Gimersia melarang aset buatan AI. **Semua file itu wajib diganti dengan karya tim sebelum submit.**
> Yang boleh tetap dipakai: kode, font DejaVu (lisensi bebas, lihat `fonts/LICENSE-DejaVu.txt`), dan Godot.
> Cek juga aturan Gimersia tentang penggunaan kode buatan AI dan cantumkan sesuai yang diminta panitia.

## 1. Membuka proyek
1. Pasang **Godot 4.7** (versi standar, bukan .NET). Kode juga jalan di 4.3–4.6. Saat pertama dibuka, Godot akan membuat file `.uid` di samping script; itu normal, ikut di-commit saja.
2. Godot → *Import* → pilih `project.godot` di folder ini.
3. Tunggu editor selesai meng-import aset (pertama kali agak lama), lalu tekan **F5**.

Renderer: *Compatibility* (aman untuk web dan laptop lama). Resolusi dasar 1920×1080, otomatis menyesuaikan layar.

**Catatan jujur:** game ini ditulis tanpa bisa menjalankan Godot (hanya dicek dengan pemeriksa statis). Jalankan dulu, mainkan semua segmen, dan kalau muncul error merah di panel *Debugger/Output*, salin pesannya (beserta nama file dan nomor baris) untuk diperbaiki.

## 2. Kontrol
| Input | Fungsi |
|---|---|
| Mouse | Membidik (−10° sampai 90°) |
| Klik kiri | Tembak. Magnet: tahan 1 detik, lepas lebih cepat = batal |
| 1 / 2 / 3 atau scroll | Ganti alat: Harpun, Jaring, Magnet |
| Esc atau P | Jeda |
| Klik / Spasi / Enter | Lanjut dialog |
| F3 | Tampilkan/sembunyikan hitbox (alat bantu tes). Kuning = kulit kraken/kayu, hijau = sampah, merah = makhluk, biru = pickup, putih = kait |

Hitbox kepala kraken adalah poligon `HeadHitbox/Shape` di `scenes/level/kraken/kraken.tscn`: titiknya bisa digeser langsung di editor supaya pas dengan gambar kepala.

Alat terbuka bertahap: Harpun sejak 1-1, Jaring sejak 1-2, Magnet sejak 2-1.

Setiap segmen dibuka dengan adegan singkat: Raka terjun dari kapal kakek lalu turun ke dasar (klik atau Spasi untuk melewati). Kalau oksigen habis, Raka naik ke permukaan. Menu "Peta Perjalanan" menampilkan peta dunia: klik titik untuk melihat info, klik lagi atau tekan Main untuk bermain.

### Main di HP (ramah sentuh)
- Ketuk layar: Raka membidik ke titik itu lalu menembak. Geser jari untuk membidik; tahan untuk Magnet.
- Ketuk slot alat di kanan bawah untuk ganti alat; tombol jeda ada di kanan atas (juga bisa diklik di PC).
- Tombol kembali Android: membuka jeda saat bermain, kembali ke menu di layar lain.
- Teks petunjuk otomatis berganti ke versi sentuh di Android/iOS dan browser HP. Pilihan layar penuh disembunyikan di HP dan web.
- Layar dikunci mendatar (landscape). Di HP yang lebih panjang dari 16:9 akan ada pita hitam di kiri-kanan.
- Untuk export Android, Godot 4.7 butuh **OpenJDK 17** (atur di *Editor Settings → Export → Android → Java SDK Path*).

## 3. Export
1. *Editor → Manage Export Templates → Download and Install* (sekali saja).
2. *Project → Export*. Preset sudah disiapkan:
   - **Web** → `build/web/index.html`. *Thread Support* **mati** supaya jalan di itch.io tanpa pengaturan SharedArrayBuffer. Zip isi folder `build/web/` lalu upload ke itch.io sebagai *HTML*, viewport 1920×1080 (centang *fullscreen button*).
   - **Windows** → `build/windows/Muara.exe` (cadangan untuk juri).

## 4. Struktur proyek

Proyek memakai **scene untuk semua yang terlihat** (layar, HUD, Raka, kapal, kraken, objek di air) dan
**satu skrip kecil per tanggung jawab**. Tampilan diatur di editor; skrip hanya berisi logika.
Gaya UI (tombol, panel, pita, bar, slider) ada di satu **Theme**, jadi warna/tekstur cukup diganti di satu tempat.

```
project.godot                      main scene, autoload "Game", tema global
resources/theme/muara_theme.tres   Theme: Button, PrimaryButton, PanelContainer, RibbonPanel, HudPanel,
                                   HudBarGreen/Blue/Red, ToolSlot, MapNodeRiver/Sea, BannerLabel, dll.
scenes/
  main.tscn                        Main: hanya mengganti layar
  ui/
    main_menu.tscn                 menu utama
    world_map.tscn                 Peta Perjalanan (titik segmen = instance map_node.tscn, geser di editor)
    map_node.tscn                  satu titik segmen
    settings_menu.tscn  credits_screen.tscn  story_screen.tscn  summary_screen.tscn
    components/ocean_backdrop.tscn latar laut hidup untuk menu (tambah ikan = tambah Sprite2D di Fishes)
  level/
    level.tscn                     SATU SEGMEN. Pohon node:
                                     World (BgMurky, BgClean, KrakenSlot, Boat, Entities, Raka,
                                            HookTool, NetTool, MagnetTool, FloatingTexts)
                                     WaveDirector, KrakenFight, Hints, HudLayer/Hud, PauseLayer/PauseMenu
    raka.tscn  boat.tscn           Raka (badan + alat di bahu), kapal kakek
    water_object.tscn              satu objek di air (sampah, ikan, kayu, gelembung, kotak)
    hud.tscn  tool_slot.tscn       HUD dan slot alat (bisa diklik/disentuh)
    pause_menu.tscn  floating_text.tscn
    kraken/kraken.tscn             bos: kepala, wajah, 6 tentakel (tiap tentakel 3 potongan Line2D), bar nyawa
scripts/
  autoload/game.gd                 progres, simpanan (user://muara_save.cfg), audio, pengaturan, deteksi HP
  core/main.gd                     pengatur layar
  data/level_data.gd               DATA LEVEL: jenis objek, segmen, gelombang
  data/story_data.gd               SEMUA TEKS CERITA: adegan, dialog awal segmen, deskripsi peta
  ui/...                           satu skrip per layar + components/ (juicy_button, ocean_backdrop)
  level/
    level.gd                       koordinator: alur intro→dialog→main→selesai, oksigen, skor, combo, hasil
    arena.gd                       konstanta posisi (permukaan, dasar, bahu Raka, keranjang)
    entity_layer.gd water_object.gd  objek di air
    tools/level_tool.gd            dasar semua alat; hook_tool, net_tool, magnet_tool turunan darinya
    wave_director.gd               gelombang segmen biasa
    kraken_fight.gd kraken/kraken.gd  pertarungan 2-3 dan kraken-nya
    hint_system.gd hud.gd tool_slot.gd pause_menu.gd raka.gd boat.gd floating_text.gd
```

### Cara mengubah hal yang sering diubah
| Mau mengubah | Buka |
|---|---|
| Tata letak HUD, menu, peta, ringkasan | scene-nya di `scenes/`, geser node di editor |
| Warna/tekstur tombol, panel, bar | `resources/theme/muara_theme.tres` (Inspector → tipe yang dipakai) |
| Kecepatan harpun, radius jaring, amunisi, jangkauan magnet | pilih node `HookTool`/`NetTool`/`MagnetTool` di `level.tscn`, ubah di Inspector |
| Oksigen, penalti, bonus penyelamatan | node root `Level` di `level.tscn` (Inspector) |
| Lemparan, jaring hantu, badai serpihan kraken | node `KrakenFight` di `level.tscn` |
| Nyawa kraken, jumlah sampah dasar, porsi kaleng | root `kraken.tscn` |
| Teks cerita/dialog/deskripsi peta | `scripts/data/story_data.gd` |
| Isi gelombang | `scripts/data/level_data.gd` |
| Posisi titik di peta | geser node `Node1_1` … `Node2_3` di `world_map.tscn` |

### Menambah alat baru (contoh: Vakum)
1. Buat `scripts/level/tools/vacuum_tool.gd` yang `extends LevelTool` dan isi `press/release/update_tool/cancel/_draw`.
2. Tambah node `VacuumTool` di `World` pada `level.tscn`, pasang skripnya, isi `slot = 3`.
3. Tambah ke array `tools` di `level.gd` dan tambah `Slot4` (instance `tool_slot.tscn`) di `hud.tscn`.

Sebelum commit, buka proyek di Godot 4.7.2 dan mainkan segmen yang diubah untuk memastikan tidak ada error di panel *Debugger*.

## 5. Mengubah keseimbangan level
- Edit angka di `scripts/data/level_data.gd` (`KINDS` = jenis sampah/makhluk, `SEGMENTS` = target, oksigen, arus; `WAVES` = jadwal muncul tiap gelombang).
- Kalau menambah atau mengurangi sampah di `WAVES`, samakan `total` segmen itu di `SEGMENTS` dengan jumlah sampah di semua gelombangnya (target dan bintang dihitung dari angka ini).
- Angka alat (kecepatan harpun, radius jaring, kerucut magnet, dsb.) diatur di Inspector node alat pada `scenes/level/level.tscn`.
- Teks dialog awal tiap segmen dan cerita: `scripts/data/story_data.gd`.

### Aturan yang ditetapkan di implementasi (melengkapi GDD)
- Gelombang berikutnya mulai setelah semua sampah gelombang ini muncul **dan** (semuanya sudah tertangkap/lolos **atau** sudah lewat 8 detik), lalu jeda 1,5 detik + banner 1,5 detik.
- Bos 2-3 adalah **kraken yang terlilit sampah**. Tujuannya menyelamatkan, bukan mengalahkan:
  - Menang: semua sampah di kepala dan tentakel kraken terambil. Kraken bebas lalu berenang pergi.
  - Kalah: **nyawa kraken habis** (terlalu sering kena tembakan) atau oksigen Raka habis.
  - Harpun kena sampah: sampah tercabut (tarikan 0,5 detik). Harpun kena kulit kraken: nyawa −8, skor −30, combo putus.
  - Jaring: mengambil sampai 4 sampah di area jatuhnya; jatuh di kulit tanpa sampah: nyawa −5.
  - Magnet: tidak pernah melukai kraken, menarik sampai 5 kaleng (25% sampah adalah kaleng).
  - Jumlah sampah 30 + tambahan dari sampah yang lolos di Stage 1 (maksimal +20).
  - Fase 1: lemparan sampah dari ujung tentakel tiap 3,5 detik. Fase 2: jaring hantu hanyut ke kraken (kalau sampai, +2 sampah), lemparan tiap 4,5 detik. Fase 3: tentakel makin cepat dan badai serpihan 2 jalur × 6.
  - Jangkauan Jaring 1.350 px dan Magnet 1.400 px khusus di segmen ini. Amunisi awal Jaring 4, Magnet 3. Kotak bantuan tiap 25 detik dan di awal fase 2 dan 3. Oksigen 170.
  - Bintang: 1 = kraken bebas; 2 = sisa oksigen ≥ 30; 3 = juga tanpa sekali pun mengenai makhluk. Bonus = sisa oksigen + 2 × nyawa kraken + 200 jika tanpa kena makhluk.
  - Angka-angka diatur di Inspector: node `NetTool`/`MagnetTool`/`HookTool` dan `KrakenFight` di `level.tscn`, serta root `kraken.tscn`.
- Bonus +100 menyelamatkan penyu diberikan saat itu juga (tidak dihitung ulang di bonus akhir).
- Satu baris dialog di awal setiap segmen; petunjuk tutorial hanya muncul sekali (bisa diulang lewat Pengaturan).

## 6. Daftar aset yang WAJIB diganti
Ganti dengan **nama file dan ukuran yang sama** supaya tidak perlu mengubah kode. PNG harus transparan (kecuali latar). Jika ukuran berubah, posisi titik pivot di bawah harus ikut disesuaikan di kode.

### Gambar (`art/`)
| File | Ukuran | Catatan |
|---|---|---|
| `bg_{1_1,1_2,1_3,2_1,2_2,2_3}_murky.png` | 1920×1080 | Latar keruh. Air dari y=200 (permukaan) sampai y=960 (dasar) |
| `bg_..._clean.png` (6 file) | 1920×1080 | Versi bersih, muncul saat segmen lulus |
| `raka_body.png` | 240×300 | Penyelam. Titik kaki/anchor (110,180), bahu (126,120) |
| `gun_harpun.png` `gun_jaring.png` `gun_magnet.png` | 220×64 | Menghadap kanan. Pivot (28,32), ujung laras x=188 |
| `hook.png` | 48×24 | Mata kail menghadap kanan |
| `net_open.png` | 240×240 | Jaring terbuka (lingkaran radius ±110) |
| `trash_sachet_1/2/3.png` | 64×52 | Sampah ringan |
| `trash_bag.png` 96×96, `trash_bottle.png` 104×44, `trash_styro.png` 92×64, `trash_sandal.png` 96×44 | | Sampah ringan/sedang |
| `trash_can.png` | 48×72 | Kaleng (logam, bisa ditarik Magnet) |
| `trash_tire.png` 112×112, `trash_ghostnet.png` 140×100 | | Sampah berat |
| `trash_flake_1/2.png` | 28×20 | Serpihan mikroplastik fase 3 bos |
| `fish_1/2/3.png` | 104×64 | **Menghadap kiri** |
| `jelly.png` 84×108, `turtle.png` 124×84, `wood.png` 184×54 | | Ubur-ubur, penyu, kayu penghalang |
| `bubble.png` 60×60, `box.png` 88×76 | | Gelembung oksigen, kotak suplai |
| `kraken_head.png` 360×380 | | Kepala kraken |
| `kraken_tentacle_<1-6>_base.png`, `_mid.png`, `_tip.png` | 176×96 | 6 tentakel dengan desain berbeda, masing-masing dipotong jadi pangkal, tengah, dan ujung (18 file). Gambar lurus mendatar, pangkal di kiri, alat isap di sisi bawah. Ketiga potongan sama tinggi dan bentuknya harus nyambung: tebal di ujung kanan `base` = tebal di ujung kiri `mid`, begitu juga `mid` ke `tip`. Ujung potongan dibiarkan rata (tanpa garis tepi) supaya sambungan tidak kelihatan. Node: `Tentacles/Tentacle0..5/Base, Mid, Tip` di `kraken.tscn` |
| `kraken_face.png`, `kraken_face_hurt.png`, `kraken_face_happy.png` | 260×150 | Wajah kraken: cemas, kesakitan, senang |
| `portrait_kakek/busari/raka.png` | 220×220 | Potret dialog |
| `story_intro/sea/end.png` | 1280×720 | Gambar cerita |
| `boat.png` | 480×240 | Kapal kakek di adegan pembuka segmen. Garis air di y=200, tengah x=240 |
| `fx_bubble.png` | 24×24 | Gelembung kecil hiasan (saat Raka terjun) |
| `map_world.png` | 1920×1080 | Peta Perjalanan. Titik segmen adalah node `Nodes/Node1_1` dst. di `scenes/ui/world_map.tscn`; kalau peta digambar ulang, geser node-nya di editor |
| `title_logo.png` | 1200×320 | Logo judul di menu |
| `ui_btn.png` `ui_btn_hover.png` `ui_btn_pressed.png` `ui_btn_disabled.png` | 120×120 | Tombol 9-slice, tepi 36 px tidak ikut melar |
| `ui_panel.png` | 160×160 | Panel 9-slice, tepi 56 px |
| `menu_bg.png`, `menu_rays.png` | 1920×1080 | Latar menu (permukaan laut di y=340) dan berkas cahaya yang berdenyut |
| `ui_btn_primary.png`, `_hover`, `_pressed` | 120×120 | Tombol utama oranye, 9-slice tepi 36 px |
| `icon_play/map/settings/credits/exit/back/retry/next.png` | 56×56 | Ikon bulat di tombol |
| `ui_ribbon.png` | 640×120 | Pita judul, 9-slice kiri/kanan 96 px |
| `ui_knob.png` 44×44, `ui_toggle_on/off.png` 96×52 | | Pegangan slider dan sakelar |
| `icon.png` | 128×128 | Ikon game |
| `fx_aim_dot.png` | 16×16 | Titik garis bidik (diwarnai oleh alat) |
| `fx_rope.png` | 32×8 | Tali harpun, diulang mendatar (harus bisa disambung kiri-kanan) |
| `fx_net_ring.png` | 240×240 | Cincin area jaring saat membidik, jari-jari cincin 110 px |
| `fx_magnet_cone.png` | 512×400 | Kerucut jangkauan Magnet: puncak di kiri tengah (0,200), jari-jari 512, sudut ±22,5° |
| `fx_leak_flash.png` | 64×64 | Kilatan merah di tepi kiri saat sampah lolos (pudar ke kanan) |
| `ui_leak_line.png` | 24×96 | Garis batas kiri air, diulang tegak |
| `ui_target_mark.png` | 16×44 | Penanda target di bar kebersihan |
| `ui_hud_panel.png` | 120×120 | Panel HUD, 9-slice tepi 36 px |
| `ui_hint_panel.png` | 96×64 | Kotak petunjuk gelap, 9-slice kiri/kanan 32, atas/bawah 30 |
| `ui_bar_bg.png`, `ui_bar_green/blue/red.png` | 64×28 | Bar (latar dan isi), 9-slice kiri/kanan 14 px |
| `ui_slider_track.png`, `ui_slider_fill.png` | 64×20 | Slider pengaturan, 9-slice kiri/kanan 10 px |
| `ui_slot.png`, `ui_slot_selected.png`, `ui_slot_locked.png` | 104×104 | Kotak alat di HUD, 9-slice tepi 30 px |
| `ui_round_btn.png` | 96×96 | Tombol bulat HUD (jeda) |
| `ui_node_river/sea/locked.png` (+ `_hover` untuk river dan sea) | 120×120 | Titik segmen di peta: lingkaran 96 px di tengah, sisanya bayangan |
| `ui_map_dot.png` 24×24, `ui_map_ring.png` 160×160, `ui_map_pin.png` 104×136 | | Titik jalur peta, cincin segmen terpilih, bingkai penanda posisi (wajah Raka di lingkaran atasnya) |

Tidak ada gambar yang dibuat oleh kode. Kode hanya menaruh, memutar, menekuk, dan mewarnai gambar dari `art/`. Satu-satunya yang bukan gambar adalah lapisan gelap polos (ColorRect) di belakang menu jeda, ringkasan, dan layar cerita.

### Suara (`audio/`, WAV pendek) dan musik (OGG, berulang)
| File | Dipakai saat |
|---|---|
| `shoot` | Menembak harpun |
| `pull` | Kail mengenai sampah, mulai ditarik |
| `catch` | Sampah masuk keranjang |
| `net` | Jaring terbuka |
| `magnet` | Magnet dilepas |
| `startle` | Ikan kaget/terkena |
| `bounce` | Kail memantul dari kayu |
| `bubble` | Mengambil gelembung oksigen |
| `leak` | Sampah lolos ke kiri |
| `throw` | Kraken melempar sampah |
| `piece` | Sampah tercabut dari kraken |
| `hurt` | Raka terkena |
| `click` | Tombol UI |
| `o2_low` | Oksigen di bawah 20% |
| `win` / `lose` | Ringkasan lulus/gagal |
| `box` | Membuka kotak suplai |
| `music_menu.ogg` `music_river.ogg` `music_sea.ogg` `music_boss.ogg` | Musik menu, Stage 1, Stage 2, bos (pastikan bisa di-loop rapi) |

Setelah mengganti, perbarui `scripts/credits.gd`: nama anggota tim, pembuat tiap aset, dan hapus/ubah baris "(Pastikan kalimat ini benar sebelum submit.)".

## 7. Checklist sebelum submit
- [ ] Semua file di `art/`, `audio/`, dan `icon.png` sudah diganti karya tim
- [ ] Nama anggota dan sumber aset di `credits.gd` sudah diisi
- [ ] Semua segmen 1-1 sampai 2-3 dicoba sampai lulus dan gagal, tanpa error di Output
- [ ] Build Web dicoba di itch.io (Chrome dan Firefox), build Windows dicoba di laptop lain
- [ ] Simpanan progres bertahan setelah game ditutup dan dibuka lagi
