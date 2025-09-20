# Express CRUD API

Proyek ini memberikan contoh struktur lengkap aplikasi **Express.js** untuk operasi CRUD sederhana. API menggunakan penyimpanan data in-memory sehingga dapat langsung dijalankan tanpa database eksternal dan mudah dijadikan titik awal untuk kebutuhan yang lebih kompleks.

## Fitur Utama

- Struktur folder terorganisir (controllers, services, repositories, middlewares, validators, dan utils).
- Validasi request menggunakan `express-validator`.
- Penanganan error terpusat dengan pesan yang konsisten.
- Logging request menggunakan `morgan` dan dukungan CORS.
- Endpoint *health check* untuk memastikan aplikasi berjalan.

## Struktur Proyek

```
.
├── package.json
├── README.md
└── src
    ├── app.js
    ├── config
    │   └── index.js
    ├── controllers
    │   └── itemController.js
    ├── middlewares
    │   ├── errorHandler.js
    │   ├── notFoundHandler.js
    │   └── validateRequest.js
    ├── repositories
    │   └── itemRepository.js
    ├── routes
    │   ├── index.js
    │   └── itemRoutes.js
    ├── services
    │   └── itemService.js
    ├── utils
    │   ├── apiResponse.js
    │   ├── errors.js
    │   └── httpStatus.js
    └── validators
        └── itemValidator.js
```

## Menjalankan Aplikasi

1. **Instal dependensi**

   ```bash
   npm install
   ```

2. **Jalankan server (mode pengembangan)**

   ```bash
   npm run dev
   ```

3. **Jalankan server (mode produksi)**

   ```bash
   npm start
   ```

Secara default aplikasi akan berjalan pada port `3000`. Anda dapat mengubah port melalui variabel lingkungan `PORT`.

## Endpoint

Semua endpoint tersedia di bawah prefix `/api`.

| Method | Endpoint       | Deskripsi                   |
|--------|----------------|-----------------------------|
| GET    | `/health`      | Mengecek status aplikasi.   |
| GET    | `/api/items`   | Mengambil seluruh item.     |
| POST   | `/api/items`   | Membuat item baru.          |
| GET    | `/api/items/:id` | Mengambil detail item.    |
| PUT    | `/api/items/:id` | Memperbarui data item.    |
| DELETE | `/api/items/:id` | Menghapus item.           |

### Contoh Payload

**Membuat item**

```json
{
  "name": "Kopi Hitam",
  "description": "Minuman tanpa gula"
}
```

**Memperbarui item**

```json
{
  "name": "Kopi Susu"
}
```

## Catatan

Repository ini menggunakan penyimpanan data in-memory. Untuk integrasi dengan database sungguhan, Anda dapat menyesuaikan lapisan `repositories` dan `services` tanpa mengubah lapisan lain.
