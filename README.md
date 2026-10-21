# DSS DPK — PT Bank Aceh Syariah

Sistem Pendukung Keputusan untuk peramalan Dana Pihak Ketiga (Giro, Tabungan,
Deposito), sesuai rancangan pada proposal penelitian: dua halaman (Hasil
Penelitian yang tetap, dan Operasional yang rolling), model dikunci dari
hasil eksperimen, refit otomatis saat data baru ditambahkan.

## Struktur folder

```
dss_bankaceh/
├── app.py                      # Entry point + login + landing
├── pages/
│   ├── 1_Hasil_Penelitian.py   # Halaman 1 (tetap)
│   └── 2_Operasional.py        # Halaman 2 (rolling forecast)
├── utils/
│   ├── styling.py              # CSS glassmorphism, warna Bank Aceh
│   ├── auth.py                 # Login admin tunggal
│   ├── data_loader.py          # Load hasil eksperimen (Halaman 1)
│   ├── model_utils.py          # Refit ARIMA/Prophet/XGBoost (Halaman 2)
│   └── sheets.py                # Koneksi Google Sheets
├── data/                        # LETAKKAN hasil ekspor notebook di sini
├── .streamlit/
│   └── secrets.toml.example    # Template kredensial (salin jadi secrets.toml)
└── requirements.txt
```

## Langkah 1 — Siapkan berkas data (dari notebook eksperimen)

Salin berkas berikut dari hasil ekspor notebook
`Eksperimen_Pemodelan_DPK_PT_Bank_Aceh_Syariah.ipynb` ke folder `data/`:

- `model_terbaik_per_target.csv`
- `hasil_evaluasi_test_semua_model.csv`
- `hasil_diagnostik_train_test.csv` (opsional)
- `dss_actual_vs_predicted_test.csv`
- `forecast_6_bulan_final.csv`

**Khusus `model_config.json`** — berkas ini format-nya spesifik untuk aplikasi
ini (dibuat supaya Halaman 2 tahu jenis model & hyperparameter yang harus
dipakai saat refit). Tambahkan sel berikut di notebook eksperimen kamu
(setelah model terbaik & konfigurasi final diperoleh), jalankan, lalu salin
`model_config.json` yang dihasilkan ke folder `data/`:

```python
import json

def _config_xgb(var):
    cfg = hasil_xgb[var]["config"]
    return {
        "n_estimators": cfg["effective_n_estimators"],
        "learning_rate": cfg["learning_rate"],
        "max_depth": cfg["max_depth"],
    }

model_config = {}
for var in ["Giro", "Tabungan", "Deposito"]:
    jenis = model_terbaik[var]
    if jenis == "ARIMA":
        cfg = {"order": list(hasil_arima[var]["order"])}
    elif jenis == "Prophet":
        cfg = hasil_prophet[var]["config"]
    else:
        cfg = _config_xgb(var)
    model_config[var] = {"model": jenis, "config": cfg}

with open("model_config.json", "w", encoding="utf-8") as f:
    json.dump(model_config, f, indent=2, ensure_ascii=False)

print(json.dumps(model_config, indent=2, ensure_ascii=False))
```

## Langkah 2 — Siapkan Google Sheet untuk data operasional

1. Buat Google Sheet baru. Baris pertama (header) diisi persis:
   `Periode | Giro | Tabungan | Deposito`
2. Isi baris-baris berikutnya dengan seluruh 116 data historis penelitian
   (Oktober 2016 – Mei 2026) sebagai titik awal data operasional. Format
   kolom `Periode` sebagai teks tanggal `YYYY-MM-DD` (mis. `2016-10-01`).
3. Buat **Google Cloud Service Account**:
   - Buka [Google Cloud Console](https://console.cloud.google.com/) → buat
     project baru (atau pakai yang sudah ada).
   - Aktifkan **Google Sheets API** dan **Google Drive API**.
   - Buat *Service Account*, lalu buat *Key* baru bertipe JSON — unduh
     filenya.
4. Buka Google Sheet yang tadi dibuat → klik **Share** → tambahkan email
   service account (ada di file JSON, field `client_email`) sebagai
   **Editor**.

## Langkah 3 — Isi secrets

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Buka `.streamlit/secrets.toml`, isi:
- `[auth]` — username & password admin (bebas kamu tentukan sendiri).
- `[connections.gsheets]` — salin nilai dari file JSON service account tadi,
  dan `spreadsheet` diisi URL Google Sheet kamu.

## Langkah 4 — Install dependensi & jalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

Buka `http://localhost:8501`, login dengan kredensial yang kamu isi di
`secrets.toml`.

## Deploy ke Streamlit Community Cloud

1. Push seluruh folder ini ke repository GitHub (**pastikan `.streamlit/secrets.toml`
   TIDAK ikut ter-push** — sudah ada di `.gitignore`).
2. Buka [share.streamlit.io](https://share.streamlit.io) → New app → pilih
   repo & `app.py` sebagai entry point.
3. Di menu **Settings → Secrets**, tempel isi `secrets.toml` kamu (bukan
   contohnya).
4. Deploy.

## Catatan penting sesuai metodologi

- Halaman **Hasil Penelitian** murni membaca berkas statis di `data/` —
  tidak menghitung ulang apa pun. Nilai di halaman ini tetap sebagai hasil
  ilmiah, tidak berubah walau data operasional bertambah.
- Halaman **Operasional** melakukan refit dengan **jenis model dan
  hyperparameter yang sudah dikunci** (dari `model_config.json`) — tidak
  ada pemilihan model ulang maupun tuning ulang di sini, sesuai proposal.
- Validasi input data baru: periode belum ada, periode = bulan berikutnya
  secara kronologis, nilai harus lebih besar dari nol. Data ditampilkan
  untuk konfirmasi sebelum disimpan.
- Forecast selalu dihitung 6 bulan setelah periode historis terakhir
  (rolling), tidak di-hardcode ke periode tertentu.
