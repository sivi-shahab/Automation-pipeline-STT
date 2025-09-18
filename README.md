# Automation-pipeline-STT

Kerangka proyek ini menyediakan dua alur ETL untuk memproses file audio format GSM menjadi WAV
berdasarkan data yang tersimpan di Postgres.

## Arsitektur

- **Batch ETL** (`scripts/run_batch.py`)
  - Mengambil data dari database setiap jam 22.00 hingga 09.00 menggunakan APScheduler.
  - Mengambil daftar `ticket_id` dan `file_path` yang belum diproses.
  - Mencari file `.gsm` di server fisik berdasarkan `file_path` dan mengonversinya menjadi `.wav`
    dengan nama file `{{ticket_id}}.wav`.
  - Menandai tiket yang berhasil diproses pada database.
- **Near real-time ETL** (`scripts/run_webhook.py`)
  - Menyediakan endpoint FastAPI (`POST /webhook`) yang bisa dipanggil melalui webhook ketika ada
    data baru.
  - Payload harus berisi `ticket_id` dan `file_path`; proses konversi akan dilakukan segera.
  - Setelah file `.wav` terbentuk, tiket akan dimasukkan ke antrean untuk dikirim ke layanan
    Speech-to-Text (STT) melalui HTTP API.

## Persiapan Lingkungan

1. Pastikan Python 3.10+ tersedia.
2. Instal dependensi proyek:

   ```bash
   pip install -e .
   ```

3. Setel variabel lingkungan berikut:

   - `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DBNAME`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
   - `ETL_SOURCE_ROOT` : direktori root tempat file `.gsm` disimpan.
   - `ETL_OUTPUT_ROOT` : direktori tujuan file `.wav`.
   - Opsional: `ETL_ARCHIVE_ROOT` untuk memindahkan file sumber setelah diproses,
     `ETL_BATCH_SIZE` untuk mengatur jumlah data sekali proses,
     `ETL_FFMPEG_BINARY` jika lokasi `ffmpeg` berbeda.
   - Untuk integrasi STT near real-time:
     - `STT_API_URL` : endpoint yang menerima permintaan transkripsi.
     - Opsional: `STT_API_KEY` dan `STT_API_KEY_HEADER` bila endpoint memerlukan otorisasi,
       `STT_TIMEOUT`, `STT_MAX_RETRIES`, `STT_RETRY_BACKOFF` untuk mengatur perilaku retry.

## Menjalankan Batch ETL

```bash
python scripts/run_batch.py
```

Scheduler akan berjalan blocking; hentikan dengan `Ctrl+C`.

## Menjalankan Webhook Near Real-Time

```bash
python scripts/run_webhook.py
```

Secara bawaan server akan berjalan pada `0.0.0.0:8000`. Anda dapat menyesuaikannya dengan
variabel `WEBHOOK_HOST` dan `WEBHOOK_PORT`.

Ketika webhook menerima data baru, proses ETL akan langsung berjalan dan hasil `.wav` akan
dimasukkan ke dalam antrean STT. Worker latar belakang akan mengirimkan file tersebut ke API
`STT_API_URL` dengan retry sesuai konfigurasi sehingga proses transkripsi dapat berlangsung
tanpa menahan request webhook.

Contoh payload webhook:

```json
{
  "ticket_id": "TICKET-001",
  "file_path": "2024/05/recording-001.gsm"
}
```

## Struktur Modul

- `datachain_etl.config` : pembacaan konfigurasi dari environment.
- `datachain_etl.db` : utilitas koneksi dan query Postgres.
- `datachain_etl.file_system` : pencarian dan penanganan file sumber.
- `datachain_etl.audio_conversion` : konversi audio menggunakan `ffmpeg`.
- `datachain_etl.etl_core` : logika utama ETL.
- `datachain_etl.scheduler` : penjadwalan batch job.
- `datachain_etl.webhook` : aplikasi FastAPI untuk webhook near real-time.
- `datachain_etl.stt_queue` : worker antrean untuk mengirim file hasil ETL ke layanan STT.
- `datachain_etl.logging_config` : konfigurasi logging standar.

## Catatan

Konversi `.gsm` ke `.wav` mengandalkan `ffmpeg`. Pastikan binari tersebut tersedia pada server.
