
"""
Dokumentasi Proyek: Bot Analisis Trading Cerdas dengan Validasi AI

File ini berisi semua informasi dokumentasi untuk proyek bot trading,
disajikan dalam format skrip Python yang terstruktur.
"""

# Kamus utama yang menyimpan semua bagian dokumentasi
PROJECT_DOCUMENTATION = {
    "project_title": "Bot Analisis Trading Cerdas dengan Validasi AI",
    "introduction": (
        "Ini adalah proyek bot trading otomatis yang dirancang dengan arsitektur bersih "
        "(*Clean Architecture*) untuk menganalisis pasar kripto. Bot ini menggunakan "
        "strategi konfirmasi multi-timeframe yang divalidasi oleh AI generatif "
        "(Google Gemini) untuk menghasilkan sinyal trading dengan probabilitas tinggi."
    ),
    "main_features": [
        "Arsitektur Bersih (Clean Architecture): Kode dipisahkan menjadi tiga lapisan (Domain, Application, Infrastructure) untuk memastikan modularitas, kemudahan pengujian, dan skalabilitas.",
        "Strategi Multi-Timeframe: Menggunakan timeframe yang lebih tinggi (4 jam) untuk konfirmasi tren utama dan timeframe yang lebih rendah (1 jam) untuk mencari sinyal masuk, memfilter sinyal palsu.",
        "Analisis Konfluens Berbasis AI: Memanfaatkan Google Gemini untuk menganalisis berbagai faktor (tren, momentum RSI/MACD, level support/resistance) dan memberikan skor keyakinan (*confidence score*) pada setiap sinyal.",
        "Manajemen Risiko Dinamis: Secara otomatis menghitung level Stop Loss (berdasarkan SuperTrend) dan Take Profit (berdasarkan level swing high/low terdekat) untuk setiap sinyal.",
        "Eksekusi Otomatis: Dijalankan secara terjadwal menggunakan GitHub Actions, menghilangkan kebutuhan akan server pribadi.",
        "Notifikasi Telegram yang Kaya Informasi: Mengirimkan peringatan sinyal yang detail, termasuk insight dari AI, level manajemen risiko, dan data teknikal kunci."
    ],
    "how_it_works": [
        "1. Pemicu Otomatis: GitHub Actions menjalankan skrip `main.py` pada jadwal yang telah ditentukan (`cron`).",
        "2. Pengambilan Data: Bot terhubung ke KuCoin (melalui CCXT) untuk mengambil data harga OHLCV terbaru untuk semua pasangan mata uang yang dikonfigurasi.",
        "3. Analisis Teknikal: Untuk setiap pasangan, bot melakukan analisis teknikal (tren 4 jam, SuperTrend, Pivot Points, RSI, dan MACD pada 1 jam).",
        "4. Validasi oleh AI: Jika analisis teknikal menghasilkan sinyal awal, semua data yang relevan dikemas dan dikirim ke Google Gemini.",
        "5. Analisis Konfluens AI: Gemini menganalisis data untuk menemukan faktor-faktor yang mendukung (konfluens) dan memberikan kesimpulan (BUY/SELL/NEUTRAL) beserta skor keyakinan.",
        "6. Keputusan Akhir: Sinyal teknikal hanya akan dianggap VALID jika kesimpulan dari AI sesuai dan skor keyakinannya melebihi ambang batas yang ditentukan.",
        "7. Pengiriman Notifikasi: Jika sinyal divalidasi, notifikasi yang kaya informasi akan dikirim ke channel Telegram yang telah ditentukan."
    ],
    "project_structure": """
/
├── .github/workflows/         # Skrip otomatisasi GitHub Actions
├── application/               # Lapisan Aplikasi (Use Cases)
│   └── use_cases.py           # Orkestrator utama alur kerja bot
├── config/                    # Konfigurasi
│   └── settings.py            # Manajemen pengaturan dari environment variables
├── domain/                    # Lapisan Domain (Inti Bisnis)
│   ├── entities.py            # Objek bisnis inti (mis. TradingSignal)
│   └── services.py            # Kontrak/interface untuk layanan
├── infrastructure/            # Lapisan Infrastruktur (Detail Teknis)
│   ├── exchanges.py           # Koneksi ke bursa (KuCoin)
│   ├── gemini_service.py      # Interaksi dengan Google Gemini API
│   ├── technical_analysis.py  # Implementasi algoritma analisis teknikal
│   └── telegram_service.py    # Pengiriman notifikasi ke Telegram
├── main.py                    # Titik masuk utama aplikasi
└── requirements.txt           # Daftar dependensi Python
""",
    "setup_and_configuration": {
        "title": "Setup dan Konfigurasi",
        "steps": [
            "1. Prasyarat: Pastikan Anda memiliki akun GitHub.",
            "2. Fork/Clone Repositori: Buat fork dari repositori ini atau salin kodenya ke repositori baru Anda.",
            "3. Dapatkan Kunci API:\n   - Buat bot Telegram dari @BotFather untuk mendapatkan `TELEGRAM_BOT_TOKEN`.\n   - Dapatkan `TELEGRAM_CHAT_ID` Anda.\n   - Dapatkan kunci API untuk Gemini dari Google AI Studio.",
            "4. Konfigurasi GitHub Secrets: Di repositori GitHub Anda (Settings > Secrets and variables > Actions), tambahkan secrets berikut:\n   - `TELEGRAM_BOT_TOKEN`: Token bot Telegram Anda.\n   - `TELEGRAM_CHAT_ID`: ID chat atau channel tujuan notifikasi.\n   - `GEMINI_API_KEY`: Kunci API Google Gemini Anda.\n   - `HTTP_PROXY` / `HTTPS_PROXY` (Opsional): Jika diperlukan.",
            "5. Aktifkan Actions: Pastikan GitHub Actions diaktifkan untuk repositori Anda. Bot akan mulai berjalan sesuai jadwal."
        ]
    },
    "customization": {
        "title": "Kustomisasi",
        "description": "Anda dapat dengan mudah menyesuaikan perilaku bot dengan mengubah parameter di file `.github/workflows/trading-bot.yml` pada bagian `env`:",
        "parameters": [
            "`TRADING_PAIRS`: Ubah daftar pasangan mata uang yang ingin dianalisis.",
            "`PIVOT_PERIOD`: Sesuaikan sensitivitas deteksi swing high/low.",
            "`AI_CONFIDENCE_THRESHOLD`: Atur skor keyakinan minimum (1-10) dari AI agar sebuah sinyal dianggap valid.",
            "`ATR_PERIOD`, `ATR_FACTOR`: Sesuaikan parameter indikator sesuai strategi Anda."
        ]
    },
    "disclaimer": (
        "Bot ini adalah alat untuk analisis dan tidak boleh dianggap sebagai nasihat keuangan. "
        "Trading mata uang kripto memiliki risiko yang tinggi. Selalu lakukan riset Anda "
        "sendiri (DYOR) sebelum melakukan trading. Penulis tidak bertanggung jawab atas "
        "keuntungan atau kerugian apa pun yang mungkin timbul dari penggunaan skrip ini."
    )
}

def display_documentation():
    """Fungsi untuk menampilkan dokumentasi ke konsol."""
    
    print("=" * 80)
    print(f"📄 {PROJECT_DOCUMENTATION['project_title'].upper()} 📄")
    print("=" * 80)
    print(f"\n{PROJECT_DOCUMENTATION['introduction']}\n")

    print("\n✨ FITUR UTAMA ✨")
    for feature in PROJECT_DOCUMENTATION['main_features']:
        print(f"- {feature}")

    print("\n⚙️ BAGAIMANA CARA KERJANYA? ⚙️")
    for step in PROJECT_DOCUMENTATION['how_it_works']:
        print(step)

    print("\n🗂️ STRUKTUR PROYEK 🗂️")
    print(PROJECT_DOCUMENTATION['project_structure'])

    print(f"\n🔧 {PROJECT_DOCUMENTATION['setup_and_configuration']['title'].upper()} 🔧")
    for step in PROJECT_DOCUMENTATION['setup_and_configuration']['steps']:
        print(step)

    print(f"\n🎨 {PROJECT_DOCUMENTATION['customization']['title'].upper()} 🎨")
    print(PROJECT_DOCUMENTATION['customization']['description'])
    for param in PROJECT_DOCUMENTATION['customization']['parameters']:
        print(f"- {param}")

    print("\n⚠️ DISCLAIMER ⚠️")
    print(PROJECT_DOCUMENTATION['disclaimer'])
    print("\n" + "=" * 80)

if __name__ == "__main__":
    # Jika skrip ini dijalankan secara langsung, tampilkan dokumentasi.
    display_documentation()
