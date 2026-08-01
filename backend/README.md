# Backend Catatan Utang Piutang API (FastAPI + Supabase)

Backend service untuk aplikasi Catatan Utang Piutang menggunakan Python FastAPI, Pydantic, dan Supabase (Auth, Postgres, Storage, Realtime).

## Fitur Utama

- **Authentication**: Supabase Auth integration dengan verifikasi JWT Bearer Token & JWKS.
- **Profil & Pengguna**: Manajemen profil terhubung `auth.users`, avatar upload ke Supabase Storage, hapus akun.
- **Kontak & Utang-Piutang**: Manajemen Kontak, Piutang (receivable) & Utang (payable), tanggal jatuh tempo, suku bunga, denda.
- **Perhitungan Keuangan Presisi**: `sisa_utang = nilai_pokok + bunga + denda - total_pembayaran` dengan tipe data PostgreSQL `numeric` dan validasi pencegahan pembayaran berlebih (overpayment).
- **Idempotency Key**: Pencegahan pembayaran ganda akibat klik berulang.
- **Audit Logging**: Pencatatan riwayat transaksi ke `activity_logs`.
- **Ekspor Laporan**: Ekspor data laporan transaksi ke format CSV & JSON.
- **Pengujian (Testing)**: Automated test suite menggunakan Pytest & FastAPI TestClient.

## Prasyarat

- Python 3.13+
- Project Supabase (URL & API Keys)

## Panduan Instalasi & Jalankan Backend

1. **Buat Virtual Environment & Install Dependensi**:
   ```bash
   cd backend
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

2. **Pengaturan Environment Variables**:
   Salin `.env.example` ke `.env` lalu sesuaikan kredensial Supabase Anda:
   ```bash
   cp .env.example .env
   ```

3. **Menjalankan Server Backend**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Akses dokumentasi Swagger UI di `http://localhost:8000/docs` atau ReDoc di `http://localhost:8000/redoc`.

4. **Menjalankan Automated Tests**:
   ```bash
   pytest tests/
   ```
