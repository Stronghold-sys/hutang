class ApiClient {
    constructor() {
        this.baseUrl = CONFIG.API_BASE_URL;
    }

    getToken() {
        return localStorage.getItem("access_token") || "";
    }

    setSession(accessToken, refreshToken, user) {
        localStorage.setItem("access_token", accessToken);
        if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
        if (user) localStorage.setItem("user_profile", JSON.stringify(user));
    }

    clearSession() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user_profile");
    }

    getUser() {
        const u = localStorage.getItem("user_profile");
        return u ? JSON.parse(u) : null;
    }

    isAuthenticated() {
        return !!this.getToken();
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = options.headers || {};
        
        // Only attach Authorization header if not calling login or register
        const token = this.getToken();
        if (token && !endpoint.includes("/auth/login") && !endpoint.includes("/auth/register")) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        if (!options.isMultipart) {
            headers["Content-Type"] = "application/json";
        }

        const config = {
            method: options.method || "GET",
            headers: headers,
            ...options
        };

        if (options.body && !options.isMultipart && typeof options.body === "object") {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            const resData = await response.json().catch(() => ({}));

            if (response.status === 401) {
                if (!endpoint.includes("/auth/login") && !endpoint.includes("/auth/register")) {
                    this.clearSession();
                    if (window.app && typeof window.app.tampilkanViewAuth === "function") {
                        window.app.tampilkanViewAuth();
                    }
                    throw new Error("Sesi telah berakhir. Silakan login kembali.");
                }
            }

            if (!response.ok || resData.success === false) {
                const errMsg = resData.message || (resData.error && resData.error.code) || "Terjadi kesalahan pada request API";
                throw new Error(errMsg);
            }

            return resData;
        } catch (err) {
            console.error("API Request Error:", err);
            if (err.name === "TypeError" && (err.message.includes("Failed to fetch") || err.message.includes("NetworkError") || err.message.includes("Load failed"))) {
                throw new Error("Gagal terhubung ke Server Backend (Cloudflare Worker). Periksa koneksi internet atau status Worker Anda.");
            }
            throw err;
        }
    }

    get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullEndpoint = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(fullEndpoint, { method: "GET" });
    }

    post(endpoint, body = {}, isMultipart = false) {
        return this.request(endpoint, { method: "POST", body, isMultipart });
    }

    patch(endpoint, body = {}) {
        return this.request(endpoint, { method: "PATCH", body });
    }

    delete(endpoint) {
        return this.request(endpoint, { method: "DELETE" });
    }

    upload(endpoint, formData) {
        return this.request(endpoint, {
            method: "POST",
            body: formData,
            isMultipart: true
        });
    }
}

const api = new ApiClient();
