// ==========================================
// UI CONTROLLER & REAL-TIME DATA INTEGRATION
// ==========================================

class AppUI {
    constructor() {
        this.daftarTransaksi = [];
        this.daftarKontak = [];
        this.filterAktif = "Semua";
        this.currentJenisTransaksi = "receivable"; // 'receivable' (Piutang) or 'payable' (Utang)
        this.activeDebtId = null;
        this.realtimeChannel = null;
        this.initDate();
    }

    initDate() {
        const dateElem = document.getElementById("dashboard-date");
        if (dateElem) {
            const now = new Date();
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            dateElem.innerText = now.toLocaleDateString('id-ID', options);
        }
    }

    showToast(message, type = "info") {
        const container = document.getElementById("toast-container");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        toast.innerText = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.remove();
        }, 3500);
    }

    // ================= RUPIAH FORMATTER =================
    handleRupiahInput(input) {
        let raw = input.value || "";
        if (!raw) {
            input.value = "";
            return;
        }

        let parts = raw.split(",");
        let intPart = parts[0].replace(/\D/g, "");

        if (!intPart) {
            input.value = "";
            return;
        }

        let formattedInt = parseInt(intPart, 10).toLocaleString("id-ID");
        let result = "Rp" + formattedInt;

        if (parts.length > 1) {
            let decPart = parts[1].replace(/\D/g, "").slice(0, 2);
            result += "," + decPart;
        }

        input.value = result;
    }

    parseRupiah(val) {
        if (!val) return 0;
        let str = String(val).replace(/^Rp/, "").replace(/\./g, "").replace(",", ".");
        let num = parseFloat(str);
        return isNaN(num) ? 0 : num;
    }

    formatRupiahValue(val) {
        if (val === undefined || val === null || isNaN(val) || val === 0) return "";
        let num = Number(val);
        let parts = num.toString().split(".");
        let intPart = parseInt(parts[0], 10).toLocaleString("id-ID");
        let result = "Rp" + intPart;
        if (parts[1]) {
            result += "," + parts[1].slice(0, 2);
        }
        return result;
    }

    // ================= AUTENTIKASI =================
    switchAuthTab(tab) {
        document.getElementById("tab-login").classList.toggle("active", tab === "login");
        document.getElementById("tab-register").classList.toggle("active", tab === "register");
        document.getElementById("form-login").style.display = tab === "login" ? "block" : "none";
        document.getElementById("form-register").style.display = tab === "register" ? "block" : "none";
        document.getElementById("auth-subtitle").innerText = tab === "login" ? "Masuk ke akun Anda" : "Buat akun baru";
    }

    tampilkanViewAuth() {
        document.querySelectorAll('.page-view').forEach(hal => hal.style.display = 'none');
        document.getElementById("page-auth").style.display = 'block';
        document.getElementById("app-bottom-nav").style.display = 'none';
        if (this.realtimeChannel) {
            this.realtimeChannel.unsubscribe();
            this.realtimeChannel = null;
        }
    }

    tampilkanAppUtama() {
        document.getElementById("page-auth").style.display = 'none';
        document.getElementById("app-bottom-nav").style.display = 'flex';
        this.pindahHalaman('page-ringkasan', document.getElementById('nav-ringkasan'));
        this.loadAllData();
        this.initRealtime();
    }

    async handleLogin(event) {
        event.preventDefault();
        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;

        try {
            this.showToast("Sedang masuk...", "info");
            const res = await api.post("/auth/login", { email, password });
            api.setSession(res.data.access_token, res.data.refresh_token, res.data.user);
            this.showToast("Login berhasil!", "success");
            this.tampilkanAppUtama();
        } catch (err) {
            this.showToast(err.message || "Login gagal", "error");
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        const full_name = document.getElementById("reg-name").value.trim();
        const email = document.getElementById("reg-email").value.trim();
        const phone = document.getElementById("reg-phone").value.trim();
        const password = document.getElementById("reg-password").value;

        try {
            this.showToast("Mendaftarkan akun...", "info");
            const res = await api.post("/auth/register", { email, password, full_name, phone });
            this.showToast(res.message || "Registrasi berhasil! Silakan login.", "success");
            this.switchAuthTab("login");
            document.getElementById("login-email").value = email;
        } catch (err) {
            this.showToast(err.message || "Registrasi gagal", "error");
        }
    }

    logoutUser() {
        api.clearSession();
        this.tutupModalProfil();
        this.tampilkanViewAuth();
        this.showToast("Anda telah keluar", "info");
    }

    // ================= REALTIME SUBSCRIPTION =================
    initRealtime() {
        const user = api.getUser();
        if (!user || !user.id || typeof supabase === 'undefined' || !CONFIG.SUPABASE_URL.includes("supabase.co")) return;

        try {
            const client = supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);
            this.realtimeChannel = client.channel('public-changes')
                .on(
                    'postgres_changes',
                    { event: '*', schema: 'public', table: 'debts', filter: `user_id=eq.${user.id}` },
                    (payload) => {
                        console.log('Realtime debt change:', payload);
                        this.loadAllData();
                    }
                )
                .on(
                    'postgres_changes',
                    { event: '*', schema: 'public', table: 'debt_payments', filter: `user_id=eq.${user.id}` },
                    (payload) => {
                        console.log('Realtime payment change:', payload);
                        this.loadAllData();
                    }
                )
                .subscribe();
        } catch (e) {
            console.warn("Realtime init warning:", e);
        }
    }

    // ================= NAVIGASI & FORM =================
    pindahHalaman(idHalamanTujuan, tombolYangDiklik) {
        document.querySelectorAll('.page-view').forEach(hal => hal.style.display = 'none');
        document.getElementById(idHalamanTujuan).style.display = 'block';

        if (tombolYangDiklik && tombolYangDiklik.classList.contains('nav-item')) {
            document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
            tombolYangDiklik.classList.add('active');
        }
    }

    toggleJenisTransaksi() {
        const btn = document.getElementById("btn-toggle-jenis");
        if (this.currentJenisTransaksi === "receivable") {
            this.currentJenisTransaksi = "payable";
            btn.innerText = "Utang";
            btn.classList.add("payable");
        } else {
            this.currentJenisTransaksi = "receivable";
            btn.innerText = "Piutang";
            btn.classList.remove("payable");
        }
    }

    bukaForm(judul, subjudul, mode, debtData = null) {
        document.getElementById("form-title").innerText = judul;
        document.getElementById("form-subtitle").innerText = subjudul;
        
        const lunasBanner = document.getElementById("lunas-banner");
        const btnBayar = document.getElementById("btn-edit-bayar");
        const btnSimpan = document.getElementById("btn-edit-simpan");
        const btnBatal = document.getElementById("btn-edit-batal");

        const formInputs = [
            document.getElementById("input-nama-kontak"),
            document.getElementById("input-nominal"),
            document.getElementById("input-due-date"),
            document.getElementById("input-hp"),
            document.getElementById("input-alamat-text"),
            document.getElementById("input-deskripsi")
        ];

        if (mode === 'edit_surat_utang' && debtData) {
            this.activeDebtId = debtData.id;
            document.getElementById("edit-debt-id").value = debtData.id;
            document.getElementById("input-nama-kontak").value = debtData.kontak ? debtData.kontak.nama : (debtData.contacts ? debtData.contacts.name : "");
            
            const rawAmount = debtData.principal_amount || debtData.nominal || 0;
            document.getElementById("input-nominal").value = this.formatRupiahValue(rawAmount);
            
            document.getElementById("input-due-date").value = debtData.due_date || "";
            document.getElementById("input-deskripsi").value = debtData.description || debtData.deskripsi || "";
            
            document.getElementById("input-jenis-transaksi").style.display = "none";
            document.getElementById("input-no-hp").style.display = "block";
            document.getElementById("input-alamat").style.display = "block";
            document.getElementById("action-tambah").style.display = "none";
            document.getElementById("action-edit").style.display = "flex";

            // Cek apakah transaksi sudah LUNAS
            const isLunas = debtData.isLunas === true || 
                            debtData.status === "paid" || 
                            (debtData.raw && debtData.raw.status === "paid") ||
                            (debtData.remaining_amount !== undefined && Number(debtData.remaining_amount) <= 0);

            if (isLunas) {
                if (lunasBanner) lunasBanner.style.display = "flex";
                if (btnBayar) btnBayar.style.display = "none";
                if (btnSimpan) btnSimpan.style.display = "none";
                if (btnBatal) btnBatal.innerText = "Kembali";

                formInputs.forEach(inp => { if (inp) inp.disabled = true; });
            } else {
                if (lunasBanner) lunasBanner.style.display = "none";
                if (btnBayar) btnBayar.style.display = "block";
                if (btnSimpan) btnSimpan.style.display = "block";
                if (btnBatal) btnBatal.innerText = "Batal";

                formInputs.forEach(inp => { if (inp) inp.disabled = false; });
            }
        } else {
            this.activeDebtId = null;
            if (lunasBanner) lunasBanner.style.display = "none";
            if (btnBatal) btnBatal.innerText = "Batal";
            formInputs.forEach(inp => { if (inp) inp.disabled = false; });

            document.getElementById("edit-debt-id").value = "";
            document.getElementById("input-nama-kontak").value = "";
            document.getElementById("input-nominal").value = "";
            document.getElementById("input-due-date").value = "";
            document.getElementById("input-hp").value = "";
            document.getElementById("input-alamat-text").value = "";
            document.getElementById("input-deskripsi").value = "";

            this.currentJenisTransaksi = "receivable";
            const btn = document.getElementById("btn-toggle-jenis");
            btn.innerText = "Piutang";
            btn.classList.remove("payable");

            document.getElementById("input-jenis-transaksi").style.display = "block";
            document.getElementById("input-no-hp").style.display = "none";
            document.getElementById("input-alamat").style.display = "none";
            document.getElementById("action-tambah").style.display = "flex";
            document.getElementById("action-edit").style.display = "none";
        }

        this.pindahHalaman('page-tambah', null);
    }

    // ================= DATA FETCHING =================
    async loadAllData() {
        if (!api.isAuthenticated()) {
            this.tampilkanViewAuth();
            return;
        }

        try {
            await Promise.all([
                this.fetchDashboardSummary(),
                this.fetchDebts(),
                this.fetchKontak()
            ]);
            this.renderHalaman();
        } catch (err) {
            console.error("Gagal memuat data:", err);
        }
    }

    async fetchDashboardSummary() {
        try {
            const res = await api.get("/dashboard/summary");
            const d = res.data;
            document.getElementById("total-piutang").innerText = "Rp" + (d.total_piutang || 0).toLocaleString('id-ID');
            document.getElementById("jumlah-orang").innerText = `${d.jumlah_orang_berutang || 0} orang berutang ke kamu`;
            
            const saldoBersih = d.saldo_bersih || 0;
            document.getElementById("saldo-bersih").innerText = (saldoBersih < 0 ? "– " : "") + "Rp" + Math.abs(saldoBersih).toLocaleString('id-ID');
        } catch (err) {
            console.error("Dashboard summary error:", err);
        }
    }

    async fetchDebts() {
        try {
            const res = await api.get("/debts", { limit: 100 });
            const items = res.data || [];
            
            this.daftarTransaksi = items.map(d => {
                const contactName = d.contacts ? d.contacts.name : "Kontak";
                const kontakObj = new Kontak(contactName, "#F5E8D3", "#C19A6B");
                const isLunas = d.status === "paid";
                
                let badgeBg = isLunas ? "transparent" : "#FCE8E8";
                let badgeColor = isLunas ? "#436F54" : "#A34A4A";
                let waktuStatus = isLunas ? "LUNAS" : (d.due_date ? `Jt Tempo: ${d.due_date}` : "Belum Lunas");

                let tInstance;
                if (d.type === "receivable" || d.type === "Piutang") {
                    tInstance = new Piutang(kontakObj, d.remaining_amount || d.principal_amount, d.title || d.description, waktuStatus, badgeBg, badgeColor, isLunas, "Dalam 7 Hari");
                } else {
                    tInstance = new Utang(kontakObj, d.remaining_amount || d.principal_amount, d.title || d.description, waktuStatus, badgeBg, badgeColor, isLunas, "Dalam 7 Hari");
                }
                
                // Retain raw API model properties for edits/payments
                tInstance.raw = d;
                tInstance.id = d.id;
                tInstance.due_date = d.due_date;
                return tInstance;
            });
        } catch (err) {
            console.error("Fetch debts error:", err);
        }
    }

    async fetchKontak() {
        try {
            const res = await api.get("/contacts");
            this.daftarKontak = res.data || [];
            document.getElementById("kontak-subtitle").innerText = `${this.daftarKontak.length} kontak tercatat`;
        } catch (err) {
            console.error("Fetch contacts error:", err);
        }
    }

    // ================= CRUD ACTION HANDLERS =================
    async simpanTransaksi() {
        const namaKontak = document.getElementById("input-nama-kontak").value.trim();
        const rawNominalInput = document.getElementById("input-nominal").value;
        const nominal = this.parseRupiah(rawNominalInput);
        const dueDate = document.getElementById("input-due-date").value;
        const deskripsi = document.getElementById("input-deskripsi").value.trim();

        if (!namaKontak) {
            this.showToast("Nama kontak wajib diisi", "error");
            return;
        }
        if (!nominal || nominal <= 0) {
            this.showToast("Nominal transaksi harus lebih dari Rp0", "error");
            return;
        }

        try {
            this.showToast("Menyimpan transaksi...", "info");
            await api.post("/debts", {
                contact_name: namaKontak,
                type: this.currentJenisTransaksi,
                title: deskripsi || `Transaksi ${this.currentJenisTransaksi === 'receivable' ? 'Piutang' : 'Utang'}`,
                description: deskripsi,
                principal_amount: nominal,
                due_date: dueDate || null
            });
            this.showToast("Transaksi berhasil disimpan!", "success");
            this.loadAllData();
            this.pindahHalaman('page-ringkasan', document.getElementById('nav-ringkasan'));
        } catch (err) {
            this.showToast(err.message || "Gagal menyimpan transaksi", "error");
        }
    }

    async simpanEditTransaksi() {
        if (!this.activeDebtId) return;
        const deskripsi = document.getElementById("input-deskripsi").value.trim();
        const dueDate = document.getElementById("input-due-date").value;

        try {
            this.showToast("Memperbarui...", "info");
            await api.patch(`/debts/${this.activeDebtId}`, {
                description: deskripsi,
                due_date: dueDate || null
            });
            this.showToast("Catatan berhasil diperbarui", "success");
            this.loadAllData();
            this.pindahHalaman('page-ringkasan', document.getElementById('nav-ringkasan'));
        } catch (err) {
            this.showToast(err.message || "Gagal memperbarui catatan", "error");
        }
    }

    // ================= MODAL & PEMBAYARAN =================
    bukaModalBayar() {
        if (!this.activeDebtId) return;
        const targetDebt = this.daftarTransaksi.find(t => t.id === this.activeDebtId);
        if (targetDebt) {
            const isLunas = targetDebt.isLunas === true || 
                            targetDebt.status === "paid" || 
                            (targetDebt.raw && targetDebt.raw.status === "paid") ||
                            (targetDebt.remaining_amount !== undefined && Number(targetDebt.remaining_amount) <= 0);
            
            if (isLunas) {
                this.showToast("Transaksi ini sudah lunas!", "info");
                return;
            }

            document.getElementById("modal-bayar-debt-title").innerText = `${targetDebt.kontak.nama} - ${this.formatRupiahValue(targetDebt.nominal)}`;
            document.getElementById("bayar-nominal").value = this.formatRupiahValue(targetDebt.nominal);
            document.getElementById("modal-bayar").style.display = "flex";
        }
    }

    tutupModalBayar() {
        document.getElementById("modal-bayar").style.display = "none";
    }

    async prosesPembayaran(event) {
        event.preventDefault();
        if (!this.activeDebtId) return;

        const rawNominalInput = document.getElementById("bayar-nominal").value;
        const amount = this.parseRupiah(rawNominalInput);
        const method = document.getElementById("bayar-metode").value.trim();
        const notes = document.getElementById("bayar-catatan").value.trim();

        if (!amount || amount <= 0) {
            this.showToast("Nominal pembayaran harus lebih dari Rp0", "error");
            return;
        }

        try {
            this.showToast("Memproses pembayaran...", "info");
            await api.post(`/debts/${this.activeDebtId}/payments`, {
                amount: amount,
                payment_method: method,
                notes: notes,
                idempotency_key: `pay-${this.activeDebtId}-${Date.now()}`
            });
            this.showToast("Pembayaran berhasil dicatat!", "success");
            this.tutupModalBayar();
            this.loadAllData();
            this.pindahHalaman('page-ringkasan', document.getElementById('nav-ringkasan'));
        } catch (err) {
            this.showToast(err.message || "Gagal memproses pembayaran", "error");
        }
    }

    // ================= MODAL PROFIL & EXPORT =================
    bukaModalProfil() {
        const u = api.getUser();
        if (u) {
            document.getElementById("user-email-text").innerText = u.email || "-";
            document.getElementById("user-name-text").innerText = u.full_name || u.email || "-";
        }
        document.getElementById("modal-profil").style.display = "flex";
    }

    tutupModalProfil() {
        document.getElementById("modal-profil").style.display = "none";
    }

    async exportReport(fmt = "xlsx") {
        try {
            const token = api.getToken();
            if (!token) {
                this.showToast("Sesi telah berakhir. Silakan login kembali.", "error");
                if (typeof this.tampilkanViewAuth === "function") this.tampilkanViewAuth();
                return;
            }

            this.showToast("Mengunduh laporan...", "info");

            let res = null;
            try {
                res = await fetch(`${CONFIG.API_BASE_URL}/reports/export?format=${fmt}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
            } catch (fetchErr) {
                console.warn("Backend report fetch error, falling back to client-side exporter:", fetchErr);
            }

            if (res && res.status === 401) {
                api.clearSession();
                if (typeof this.tampilkanViewAuth === "function") this.tampilkanViewAuth();
                throw new Error("Sesi telah berakhir. Silakan login kembali.");
            }

            if (res && res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                const fileExt = (fmt === "excel" || fmt === "xlsx") ? "xlsx" : fmt;
                a.download = `laporan_utang_piutang.${fileExt}`;
                document.body.appendChild(a);
                a.click();
                a.remove();
                setTimeout(() => window.URL.revokeObjectURL(url), 1000);
                this.showToast("Laporan Excel berhasil diunduh!", "success");
                return;
            }

            // Client-side fallback exporter if server endpoint is busy or network issue
            console.log("Generating report client-side from loaded transaction data...");
            this.exportReportClientSide(fmt);
        } catch (err) {
            console.error("Export report error:", err);
            this.showToast(err.message || "Gagal mengunduh laporan", "error");
        }
    }

    exportReportClientSide(fmt = "xlsx") {
        try {
            const debts = this.daftarTransaksi || [];
            const csvRows = [
                ["ID Transaksi", "Jenis", "Nama Kontak", "Judul Catatan", "Nominal Pokok", "Sudah Dibayar", "Sisa Utang", "Status", "Tanggal Transaksi", "Jatuh Tempo"]
            ];

            debts.forEach((d, i) => {
                const contactName = d.kontak ? d.kontak.nama : (d.contact_name || "-");
                const typeStr = d.jenis === "Utang" ? "Utang" : "Piutang";
                const statusStr = d.isLunas ? "LUNAS" : "BELUM LUNAS";
                const rawObj = d.raw || {};
                const tDate = rawObj.transaction_date || "";
                const dDate = rawObj.due_date || "-";

                csvRows.push([
                    d.id || (i + 1),
                    typeStr,
                    `"${(contactName || "").replace(/"/g, '""')}"`,
                    `"${(d.deskripsi || "").replace(/"/g, '""')}"`,
                    d.nominal || 0,
                    d.sudahDibayar || 0,
                    d.sisaUtang || 0,
                    statusStr,
                    tDate,
                    dDate
                ]);
            });

            const csvContent = "\ufeff" + csvRows.map(row => row.join(",")).join("\n");
            const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "laporan_utang_piutang.csv";
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(() => window.URL.revokeObjectURL(url), 1000);
            this.showToast("Laporan berhasil diunduh!", "success");
        } catch (err) {
            console.error("Client-side export failed:", err);
            this.showToast("Gagal memproses file laporan", "error");
        }
    }

    filterRiwayat(status, tombol) {
        this.filterAktif = status;
        document.querySelectorAll('.tab').forEach(btn => btn.classList.remove('active'));
        tombol.classList.add('active');
        this.renderHalaman();
    }

    handleSearchRiwayat(query) {
        this.renderHalaman(query.toLowerCase());
    }

    buatHTMLItem(t, statusOverride = null) {
        let textNominalColor = t.jenis === "Utang" ? "#A34A4A" : "#436F54";
        let statusText = statusOverride || t.waktuStatus;
        const rawJson = JSON.stringify(t.raw || t).replace(/"/g, '&quot;');
        
        return `
            <div class="list-item" onclick="app.bukaForm('Surat Utang', 'Detail utang', 'edit_surat_utang', ${rawJson})">
                <div class="avatar" style="background-color: ${t.kontak.inisialWarna}; color: ${t.kontak.teksWarna};">
                    ${t.kontak.getInisial()}
                </div>
                <div class="item-info">
                    <h4>${t.kontak.nama}</h4>
                    <p>${t.deskripsi}</p>
                </div>
                <div class="item-value">
                    <h4 style="color: ${textNominalColor};">${this.formatRupiahValue(t.nominal)}</h4>
                    <span class="badge ${t.isLunas ? 'outline' : ''}" style="background-color: ${t.badgeBg}; color: ${t.badgeColor};">
                        ${statusText}
                    </span>
                </div>
            </div>
        `;
    }

    renderHalaman(searchQuery = "") {
        let totalPiutang = 0; let totalUtang = 0; let jmlOrang = 0;
        let htmlDashboard = ""; let htmlRiwayat = ""; let htmlKontak = ""; 
        let htmlJatuhTempo7Hari = `<div class="group-label">Dalam 7 Hari</div>`;
        let htmlJatuhTempoMendatang = `<div class="group-label" style="color: #436F54;">Mendatang</div>`;

        let unlunasCount = 0;

        this.daftarTransaksi.forEach(t => {
            if (searchQuery && !t.kontak.nama.toLowerCase().includes(searchQuery) && !t.deskripsi.toLowerCase().includes(searchQuery)) {
                return;
            }

            if (!t.isLunas) {
                unlunasCount++;
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

        document.getElementById("riwayat-subtitle").innerText = `${this.daftarTransaksi.length} catatan • ${unlunasCount} belum lunas`;
        document.getElementById("jatuhtempo-subtitle").innerText = `${unlunasCount} belum lunas`;

        document.getElementById("total-piutang").innerText = this.formatRupiahValue(totalPiutang) || "Rp0";
        document.getElementById("jumlah-orang").innerText = `${jmlOrang} orang berutang ke kamu`;
        let saldoBersih = totalPiutang - totalUtang;
        document.getElementById("saldo-bersih").innerText = (saldoBersih < 0 ? "– " : "") + (this.formatRupiahValue(Math.abs(saldoBersih)) || "Rp0");

        document.getElementById("list-dashboard").innerHTML = htmlDashboard || `<p style="text-align:center; color:#8A9A90; margin: 20px 0;">Belum ada utang/piutang aktif</p>`;
        document.getElementById("list-riwayat").innerHTML = htmlRiwayat || `<p style="text-align:center; color:#8A9A90; margin: 20px 0;">Belum ada riwayat transaksi</p>`;
        document.getElementById("list-kontak").innerHTML = htmlKontak || `<p style="text-align:center; color:#8A9A90; margin: 20px 0;">Belum ada kontak</p>`;
        document.getElementById("list-jatuhtempo-page").innerHTML = (htmlJatuhTempo7Hari + htmlJatuhTempoMendatang);
    }
}

// Inisialisasi Aplikasi
const app = new AppUI();
window.app = app;

// Cek autentikasi saat aplikasi dimuat
document.addEventListener("DOMContentLoaded", () => {
    if (api.isAuthenticated()) {
        app.tampilkanAppUtama();
    } else {
        app.tampilkanViewAuth();
    }
});
