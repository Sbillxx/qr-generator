# QR generator

Web app kecil untuk bikin QR code dari teks atau URL. Pilih ukuran dan warna, lalu unduh sebagai PNG atau SVG.

## Jalankan di komputer

```bash
pip install -r requirements.txt
python app.py
```

Buka http://localhost:5000

## Deploy ke Render

1. Push folder ini ke GitHub (repo baru).
2. Di Render: **New +** → **Web Service** → pilih repo-nya.
3. Isi pengaturan berikut (atau pakai **Blueprint** supaya `render.yaml` kebaca otomatis):
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - Health Check Path: `/healthz`
4. Klik **Create Web Service** dan tunggu build selesai.

Catatan: di plan Free, Render menidurkan service kalau lama nggak ada yang buka. Request pertama setelah itu bisa butuh sekitar semenit untuk bangun lagi.

## Endpoint

| Endpoint | Fungsi |
| --- | --- |
| `GET /` | Halaman utama |
| `GET /qr/png` dan `GET /qr/svg` | Gambar QR. Parameter: `text`, `size` (128–1200), `fg`, `bg` (format `#rrggbb`), `transparent` (`1`/`0`), `download` (`1` untuk unduh) |
| `GET /healthz` | Cek kesehatan untuk Render |
