// ==========================================
// KUMPULAN CLASS OOP 
// ==========================================

class Kontak {
    constructor(nama, inisialWarna, teksWarna) {
        this.nama = nama;
        this.inisialWarna = inisialWarna; 
        this.teksWarna = teksWarna;
    }
    getInisial() {
        return this.nama.charAt(0).toUpperCase();
    }
}

// Superclass
class Transaksi {
    constructor(kontak, nominal, deskripsi, waktuStatus, badgeBg, badgeColor, isLunas, kategoriWaktu = "Dalam 7 Hari") {
        this.kontak = kontak; 
        this.nominal = nominal;
        this.deskripsi = deskripsi;
        this.waktuStatus = waktuStatus; 
        this.badgeBg = badgeBg;
        this.badgeColor = badgeColor;
        this.isLunas = isLunas;
        this.kategoriWaktu = kategoriWaktu;
    }
    
    getNominalFormat() {
        return "Rp " + this.nominal.toLocaleString('id-ID');
    }
}

// Subclass
class Piutang extends Transaksi {
    constructor(kontak, nominal, deskripsi, waktuStatus, badgeBg, badgeColor, isLunas, kategoriWaktu) {
        super(kontak, nominal, deskripsi, waktuStatus, badgeBg, badgeColor, isLunas, kategoriWaktu);
        this.jenis = "Piutang";
    }
}

class Utang extends Transaksi {
    constructor(kontak, nominal, deskripsi, waktuStatus, badgeBg, badgeColor, isLunas, kategoriWaktu) {
        super(kontak, nominal, deskripsi, waktuStatus, badgeBg, badgeColor, isLunas, kategoriWaktu);
        this.jenis = "Utang";
    }
}
