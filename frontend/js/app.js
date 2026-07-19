// ==========================================
// UI CONTROLLER & DATA EKSEKUSI
// ==========================================

class AppUI {
    constructor() {
        this.daftarTransaksi = [];
        this.filterAktif = "Semua";
    }

    tambahTransaksi(transaksi) {
        this.daftarTransaksi.push(transaksi);
    }

    pindahHalaman(idHalamanTujuan, tombolYangDiklik) {
        // Sembunyikan semua halaman
        document.querySelectorAll('.page-view').forEach(hal => hal.style.display = 'none');
        // Munculkan halaman tujuan
        document.getElementById(idHalamanTujuan).style.display = 'block';

        // Ganti warna menu yang diklik
        if (tombolYangDiklik && tombolYangDiklik.classList.contains('nav-item')) {
            // Hapus kelas 'active' dari semua tombol
            document.querySelectorAll('.nav-item').forEach(btn => {
                btn.classList.remove('active');
            });
            // Tambahkan kelas 'active' ke tombol yang sedang diklik
            tombolYangDiklik.classList.add('active');
        }
    }

    bukaForm(judul, subjudul, mode) {
        document.getElementById("form-title").innerText = judul;
        document.getElementById("form-subtitle").innerText = subjudul;
        
        if (mode === 'edit_surat_utang') {
            document.getElementById("input-jenis-transaksi").style.display = "none";
            document.getElementById("input-no-hp").style.display = "block";
            document.getElementById("input-alamat").style.display = "block";
            document.getElementById("action-tambah").style.display = "none";
            document.getElementById("action-edit").style.display = "flex";
        } else {
            document.getElementById("input-jenis-transaksi").style.display = "block";
            document.getElementById("input-no-hp").style.display = "none";
            document.getElementById("input-alamat").style.display = "none";
            document.getElementById("action-tambah").style.display = "flex";
            document.getElementById("action-edit").style.display = "none";
        }

        this.pindahHalaman('page-tambah', null);
    }

    filterRiwayat(status, tombol) {
        this.filterAktif = status;
        document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
        tombol.classList.add('active');
        this.renderHalaman();
    }

    buatHTMLItem(t, statusOverride = null) {
        let textNominalColor = t.jenis === "Utang" ? "#A34A4A" : "#436F54";
        let statusText = statusOverride || t.waktuStatus;
        
        return `
            <div class="list-item" onclick="app.bukaForm('Surat Utang', 'Isi data utang', 'edit_surat_utang')">
                <div class="avatar" style="background-color: ${t.kontak.inisialWarna}; color: ${t.kontak.teksWarna};">
                    ${t.kontak.getInisial()}
                </div>
                <div class="item-info">
                    <h4>${t.kontak.nama}</h4>
                    <p>${t.deskripsi}</p>
                </div>
                <div class="item-value">
                    <h4 style="color: ${textNominalColor};">${t.getNominalFormat()}</h4>
                    <span class="badge ${t.isLunas ? 'outline' : ''}" style="background-color: ${t.badgeBg}; color: ${t.badgeColor};">
                        ${statusText}
                    </span>
                </div>
            </div>
        `;
    }

    renderHalaman() {
        let totalPiutang = 0; let totalUtang = 0; let jmlOrang = 0;
        let htmlDashboard = ""; let htmlRiwayat = ""; let htmlKontak = ""; 
        let htmlJatuhTempo7Hari = `<div class="group-label">Dalam 7 Hari</div>`;
        let htmlJatuhTempoMendatang = `<div class="group-label" style="color: #436F54;">Mendatang</div>`;

        this.daftarTransaksi.forEach(t => {
            if (!t.isLunas) {
                if (t.jenis === "Piutang") { totalPiutang += t.nominal; jmlOrang++; }
                else if (t.jenis === "Utang") { totalUtang += t.nominal; }
                
                htmlDashboard += this.buatHTMLItem(t);

                if (t.kategoriWaktu === "Dalam 7 Hari") {
                    htmlJatuhTempo7Hari += this.buatHTMLItem(t);
                } else {
                    htmlJatuhTempoMendatang += this.buatHTMLItem(t);
                }
            }

            if (this.filterAktif === "Semua" || 
               (this.filterAktif === "Lunas" && t.isLunas) || 
               (this.filterAktif === "Belum Lunas" && !t.isLunas)) {
                let badgeTeksRiwayat = t.isLunas ? "LUNAS" : "BELUM LUNAS";
                let t_temp = Object.assign(Object.create(Object.getPrototypeOf(t)), t);
                if(!t_temp.isLunas) {
                    t_temp.badgeBg = "#FCE8E8"; t_temp.badgeColor = "#A34A4A";
                }
                htmlRiwayat += this.buatHTMLItem(t_temp, badgeTeksRiwayat);
            }

            let statusKontak = t.isLunas ? "semua lunas" : "1 aktif";
            let badgeTeksKontak = t.isLunas ? "LUNAS" : "BELUM LUNAS";
            
            let t_kontak = Object.assign(Object.create(Object.getPrototypeOf(t)), t);
            if(!t_kontak.isLunas) {
                t_kontak.badgeBg = "#FCE8E8"; t_kontak.badgeColor = "#A34A4A";
            }
            htmlKontak += `<div class="kontak-label">${t.kontak.nama} • ${statusKontak}</div>` + this.buatHTMLItem(t_kontak, badgeTeksKontak);
        });

        document.getElementById("total-piutang").innerText = "Rp " + totalPiutang.toLocaleString('id-ID');
        document.getElementById("jumlah-orang").innerText = `${jmlOrang} orang berutang ke kamu`;
        let saldoBersih = totalPiutang - totalUtang;
        document.getElementById("saldo-bersih").innerText = (saldoBersih < 0 ? "– " : "") + "Rp " + Math.abs(saldoBersih).toLocaleString('id-ID');

        document.getElementById("list-dashboard").innerHTML = htmlDashboard;
        document.getElementById("list-riwayat").innerHTML = htmlRiwayat;
        document.getElementById("list-kontak").innerHTML = htmlKontak;
        document.getElementById("list-jatuhtempo-page").innerHTML = htmlJatuhTempo7Hari + htmlJatuhTempoMendatang;
    }
}

// Inisialisasi dan pengisian data dummy
const app = new AppUI();

const k1 = new Kontak("Rian Saputra", "#F5E8D3", "#C19A6B");
const k2 = new Kontak("Dita Amelia", "#F5E8D3", "#C19A6B");
const k6 = new Kontak("Siti Rahma", "#EAF2EB", "#537A5A"); 
const k5 = new Kontak("Fajar Nugroho", "#E8DFD1", "#96866C");
const k7 = new Kontak("Budi Santoso", "#E6EBF5", "#5A7294"); 
const k3 = new Kontak("Pak Hendra", "#F0E1E1", "#A87A7A");
const k4 = new Kontak("Koperasi RT", "#D8E4D8", "#6B8E73");

app.tambahTransaksi(new Piutang(k1, 500000, "Pinjaman motor bulan lalu", "Hari ini", "#FCE8E8", "#A34A4A", false, "Dalam 7 Hari"));
app.tambahTransaksi(new Piutang(k2, 150000, "Patungan kado ultah Sari", "3 hari", "#FCE8E8", "#A34A4A", false, "Dalam 7 Hari"));
app.tambahTransaksi(new Piutang(k6, 220000, "Titip beli buku kuliah", "LUNAS", "transparent", "#436F54", true, "Selesai")); 
app.tambahTransaksi(new Piutang(k5, 100000, "Talangan bensin tol", "12 hari", "#F5E9D3", "#A8834F", false, "Mendatang"));
app.tambahTransaksi(new Piutang(k7, 725000, "Pinjam buat servis motor", "LUNAS", "transparent", "#436F54", true, "Selesai")); 
app.tambahTransaksi(new Utang(k3, 175000, "Utang warung makan", "6 hari", "#FCE8E8", "#A34A4A", false, "Dalam 7 Hari"));
app.tambahTransaksi(new Utang(k4, 700000, "Cicilan simpan pinjam", "11 hari", "#F5E9D3", "#A8834F", false, "Mendatang"));

app.renderHalaman();
