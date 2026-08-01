# Application Catatan Utang Piutang (Full-Stack)

Aplikasi manajemen catatan Utang & Piutang modern berbasis web seluler (Mobile Web UI) yang terintegrasi secara penuh dengan **Python FastAPI Backend** dan **Supabase** (Database PostgreSQL, Authentication, Storage, dan Realtime).

## Struktur Project

```text
root-project/
 ├── frontend/               # Single Page Application (HTML, CSS, JS)
 │    ├── index.html         # Tampilan Utama & Form App
 │    ├── style.css          # Desain & Token CSS Modern
 │    └── js/
 │         ├── config.js     # Environment & Endpoint Config
 │         ├── api.js        # API Client Terpusat & Interceptor JWT
 │         ├── models.js     # Model Class Transaksi & Kontak
 │         └── app.js        # Controller & Realtime Manager
 ├── backend/                # Server API Python FastAPI
 │    ├── app/
 │    │    ├── main.py       # Entrypoint FastAPI
 │    │    ├── core/         # Config, Security, Exception, Rate Limit
 │    │    ├── middleware/   # CORS & Error Handlers
 │    │    ├── dependencies/ # Auth & Database Injectors
 │    │    ├── schemas/      # Validation Schemas Pydantic
 │    │    ├── repositories/ # Access Layer Supabase
 │    │    ├── services/     # Business Logic & Financial Calc
 │    │    └── routes/       # API Route Handlers
 │    ├── tests/             # Pytest Test Suite
 │    ├── requirements.txt
 │    ├── .env.example
 │    └── Dockerfile
 ├── supabase/
 │    ├── migrations/       # SQL Migration Scheme, Triggers & RLS
 │    ├── seed.sql           # Data Pengujian awal
 │    └── config.toml        # Supabase Local CLI Config
 ├── .env.example
 └── README.md
```

## Fitur Utama

1. **Autentikasi Nyata (Supabase Auth)**:
   - Registrasi, Login, Logout, Verifikasi, & Reset Password.
   - Token JWT Bearer verification pada FastAPI backend.
   - Profil terhubung otomatis dengan `auth.users` via SQL Trigger.

2. **Manajemen Utang & Piutang**:
   - Pemisahan kategori **Piutang** (receivable) dan **Utang** (payable).
   - Pengelompokan status otomatis: `active`, `partially_paid`, `paid`, `overdue`, `cancelled`.
   - Perhitungan presisi keuangan: `sisa_utang = nilai_pokok + bunga + denda - total_pembayaran`.
   - Pencatatan pembayaran sebagian / pelunasan dengan proteksi overpayment.

3. **Integritas & Keamanan**:
   - **Row Level Security (RLS)** pada seluruh tabel PostgreSQL.
   - Idempotency key untuk mencegah pembayaran ganda saat klik berulang.
   - Sanitisasi input, Rate Limiting (slowapi), CORS aman.
   - Supabase Storage dengan Signed URL untuk bukti transaksi sensitif.
   - Real-time updates via Supabase Realtime Channels.

## Cara Mengoperasikan Project

### 1. Migrasi Database Supabase
Jalankan file migration di Supabase SQL Editor atau Supabase CLI:
`supabase/migrations/00001_initial_schema.sql`

### 2. Menjalankan Backend FastAPI
```bash
cd backend
python -m venv venv

# Mengaktifkan venv:
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend berjalan pada: `http://localhost:8000`  
Dokumentasi Swagger API: `http://localhost:8000/docs`

### 3. Menjalankan Pengujian (Pytest)
```bash
pytest backend/tests
```

### 4. Menjalankan Frontend
Jalankan lokal HTTP server di folder `frontend/` (misal dengan VS Code Live Server atau Python http.server):
```bash
cd frontend
python -m http.server 5500
```
Akses di browser: `http://localhost:5500`

---
*Dikembangkan dengan Python FastAPI & Supabase.*
