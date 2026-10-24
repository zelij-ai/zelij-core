# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · [Español](README.es.md) · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · **Bahasa Indonesia** · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Bangun startup Anda yang 100 % AI-native.** Satu kantor tempat empat agen bekerja untuk Anda: mereka mengusulkan, Anda memutuskan. Mesin Anda, kunci Claude Anda, data Anda; tidak ada yang mengirim apa pun ke mana pun.

![Akuarium Zelij Core: pendiri dan empat agen berbincang, mengusulkan keputusan, dan menjalankan apa yang disetujui](docs/img/aquarium.gif)

*Akuarium dalam satu hari simulasi (di sini dalam bahasa Prancis). Dalam instalasi Anda, setiap kartu adalah tindakan nyata agen Anda, langsung dan dapat diputar ulang selama dua puluh empat jam. Emas adalah Anda: tidak ada hal mengikat yang terjadi sebelum keputusan Anda. Wajah-wajahnya adalah tokoh fiktif.*

## Apa yang dilakukan inti

- **Kantor**: satu halaman. Keputusan yang menunggu, permintaan kepada kepala staf, eksekusi terakhir beserta biayanya, jurnal, para agen, modul yang terpasang.
- **Paket keputusan**: tujuan, usulan, mengapa sekarang, pilihan, rekomendasi, risiko, keterbalikan, rencana, pengembalian, dampak. Paket yang tidak lengkap tidak terbuka. Setujui, tolak, atau minta perubahan dengan instruksi wajib yang diteruskan ke agen.
- **Aturan rumah**: tidak ada hal mengikat (uang, paparan publik, penghapusan, yang tidak dapat dibatalkan) yang dilakukan tanpa keputusan; sebuah fakta bertanggal dan bersumber atau ditandai « belum diverifikasi »; jurnal tidak pernah dihapus.
- **Gerbang**: kunci Claude milik pendiri, biaya setiap panggilan dihitung dari pemakaian dan tarif publik bertanggal, batas bulanan yang memblokir.
- **Pelaksana**: loop panggilan terbatas (anggaran giliran per agen), perkakas hemat, penolakan model diperlakukan sebagai hasil.
- **Modul**: satu-satunya cara memperluas inti. Antarmuka stabil, manifes `pack.json` ditandatangani penerbit dengan Ed25519, hash setiap berkas tercakup tanda tangan, verifikasi sebelum pemasangan. Target penerapan dan agen tambahan semuanya lewat sini.
- **Keuangan**: penjualan terkonfirmasi (impor Stripe hanya-baca atau entri manual dengan bukti), biaya terdeklarasi yang berulang tiap bulan, biaya agen terukur, jurnal bulanan, ekspor CSV untuk akuntan. Tidak ada yang dilaporkan atau ditagihkan.
- **Kontak**: satu kartu per orang, dasar hukum wajib, masa retensi, percakapan, hak yang dijalankan; kontak yang keberatan tidak menerima apa pun lagi, kontak yang kedaluwarsa dilupakan dan hanya jurnal hak yang tersisa.
- **Publikasi**: halaman yang ditulis agen pemasaran menjadi draf, lalu keputusan; setelah disetujui, diusulkan ke situs sebagai pull request GitHub atau draf WordPress. Langkah terakhir, menggabungkan atau menerbitkan, adalah milik Anda.
- **Di saku**: setiap keputusan sampai ke ponsel Anda, lewat e-mail dengan dua tautan bertanda tangan sekali pakai, atau lewat Telegram dengan tiga tombol. Anda menyetujui dari antrean kereta; akuarium bergerak begitu Anda menjawab. Gerbang yang sama, jurnal yang sama seperti dari meja kerja.
- **Akuarium**: saksikan agen Anda bekerja; setiap gelembung adalah tindakan nyata 24 jam terakhir, cincin putus-putus adalah posisi kosong. Halaman publik yang dapat dibagikan, dengan lencana « by zelij.ai ».
- **Katalog**: apa yang tidak ada di edisi bebas, disebut dengan jujur; modul yang dibeli dari penerbit dipasang di sini, bertanda tangan dan terverifikasi. Tidak ada pembayaran yang lewat kantor.
- **Software factory**: Si Pembangun membaca dan mengusulkan pada satu repositori saja, lewat pull request yang melewati gerbang keamanan (300 baris, hanya teks, tanpa rahasia, tanpa berkas infrastruktur, dependensi tanpa kerentanan yang diketahui menurut OSV); penerapan ke server Linux lewat SSH atau ke OVH (domain dan DNS lewat API) dengan peralihan atomik, uji asap, dan pengembalian; probe domain; cadangan harian kantor. Ia tidak pernah menggabungkan, tidak pernah membayar, tidak pernah menyentuh kantor.
- **Para agen**: satu folder per agen, sebuah `agent.md` dengan kepala sederhana dan instruksi dalam bahasa Prancis. Empat agen: Camille Aubert (kepala staf), Élise Tanguy (pertumbuhan, pemasaran, dan produk), Nour Bellamy (keuangan dan klien), Sacha Ferrand (pembangun, software factory). Pendiri berbicara dengan masing-masing dari kantor; paket yang disetujui yang menunjuk agen dan tugas langsung dijalankan, dalam batas rencana.

## Coba dalam satu menit, tanpa kunci

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Buka `http://localhost:8000` dan masuk ke demonstrasi: perusahaan fiktif, empat agen simulasi, keputusan untuk disetujui, akuarium yang memutar ulang hari mereka. Tanpa kunci, tanpa akun, tanpa biaya; tidak ada yang dikirim ke model dan semuanya hilang saat dihentikan. Setelah yakin, lanjutkan ke instalasi sebenarnya di bawah. Kantornya sendiri berbahasa Prancis.

## Memulai

```bash
cp .env.example .env     # kunci Claude, batas, SECRET_KEY, kata sandi basis data
docker compose up -d --build
```

Kantor merespons di `http://localhost:8000`. Tanpa SMTP, tautan masuk ditulis ke log kontainer (`docker compose logs core-app`).

Panduan lengkap (dalam bahasa Inggris): **[Instalasi](docs/INSTALLATION.en.md)** (mesin kosong → kantor di https, SMTP, software factory, cadangan, pemecahan masalah), **[Panduan pengguna](docs/MODE-D-EMPLOI.en.md)** (setiap halaman, para agen, keputusan, biaya). Foto pendiri dan agen diletakkan di [`portraits/`](portraits/README.md) (keterangan dalam bahasa Prancis).

Dari citra yang diterbitkan, tanpa build lokal (`CORE_IMAGE_TAG=v…` di `.env` untuk mengunci versi):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

Lokal tanpa Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Kunci publik penerbit

Modul katalog ditandatangani oleh zelij.ai. Kunci publik yang dipasang di `ZELIJ_CLE_PUBLIQUE` (sudah terisi di `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Keamanan

Apa yang dijamin inti, dan yang diuji (`tests/test_securite.py`):

- **Modul**: modul hanya terpasang dan berjalan jika ditandatangani penerbit (Ed25519), dan tanda tangan mencakup hash SHA-256 setiap berkas kode: berkas yang diubah, ditambah, atau dihapus setelah penandatanganan membuat modul tidak berlaku.
- **Masuk**: tautan sekali pakai berlaku 20 menit, di-hash dalam basis data; rem per alamat, per IP, dan global pada permintaan tautan, agar kantor tidak pernah menjadi relai e-mail; tanpa SMTP yang dikonfigurasi di produksi, tidak ada tautan yang dibuat atau dicatat.
- **Formulir**: cookie sesi HMAC `HttpOnly` `SameSite=Strict`, pemeriksaan asal dan token anti-CSRF per sesi pada setiap POST.
- **Halaman**: kebijakan keamanan konten ketat (`default-src 'self'`, tanpa skrip sebaris, tanpa bingkai), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS saat asal adalah https.
- **Agen**: apa pun yang dibaca agen (halaman web, berkas repositori) sampai kepadanya berbingkai sebagai konten eksternal, tidak pernah sebagai instruksi; agen hanya menjalankan perkakas pada kartunya dan, begitu membaca data privat, hanya dapat memanggil situs perusahaan; ia hanya membaca alamat https publik (alamat privat, loopback, link-local, dan nama internal ditolak pada setiap lompatan pengalihan, respons dibatasi); gerbang keamanan memblokir rahasia, berkas infrastruktur, skrip pihak ketiga, bingkai, dan panggilan jaringan.
- **Kontainer**: pengguna tanpa hak istimewa, sistem berkas hanya-baca, tanpa capability, tanpa peningkatan hak; kunci host server SSH dapat dikunci (`SSH_CLE_HOTE`).
- **Ekspor akuntansi**: sel yang tampak seperti rumus spreadsheet dinetralkan.

Laporkan kerentanan ke `securite@zelij.ai`, tanpa mempublikasikannya sebelum perbaikan. Sebelum setiap versi, `pip-audit -r requirements.txt` dan `bandit -r core scripts -ll` harus kosong.

## Berkontribusi dan mengikuti versi

`CONTRIBUTING.md` (bahasa Prancis) menjelaskan bagaimana kontribusi masuk ke versi, termasuk aturan: target penerapan yang dikontribusikan memberi paket yang sesuai gratis seumur hidup. `SECURITY.md` menjelaskan cara melaporkan kerentanan. `CHANGELOG.md` menyebutkan apa yang diubah setiap versi dan apa yang tersisa untuk pendiri.

## Pengujian dan kontrol publikasi

```bash
python -m pytest -q
python scripts/controle_publication.py
```

Kontrol publikasi menolak kunci, alamat IP, kode internal, alamat e-mail pribadi, kata sandi teks polos, dan istilah dari daftar privat (`ZELIJ_CORE_INTERDITS`) yang tidak pernah menjadi bagian dari repositori.

## Lisensi

GNU AGPL v3. Hak cipta (C) 2026 zelij.ai. Anda boleh menggunakan, mengubah, dan mendistribusikan ulang inti, dengan syarat menerbitkan perubahan Anda di bawah lisensi yang sama. Edisi lengkap yang menjalankan zelij.ai tetap milik penerbit.

by zelij.ai — https://zelij.ai/
