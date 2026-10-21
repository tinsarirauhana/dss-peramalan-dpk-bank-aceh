# Sistem Pendukung Keputusan Peramalan DPK PT Bank Aceh Syariah

Repositori ini memuat aplikasi sistem pendukung keputusan (*Decision Support System*/DSS) untuk menyajikan hasil peramalan Dana Pihak Ketiga (DPK) PT Bank Aceh Syariah. Aplikasi dikembangkan sebagai bagian dari Tugas Akhir **Tinsari Rauhana (2308107010038)**.

Penelitian membandingkan ARIMA, Prophet, dan XGBoost berbasis *lag features* pada komponen Giro, Tabungan, dan Deposito. Model terpilih pada setiap komponen diterapkan dalam dashboard berbasis Streamlit untuk menghasilkan informasi prediksi sebagai pendukung perencanaan likuiditas.

## Data dan pemodelan

Data penelitian mencakup 116 observasi bulanan periode Oktober 2016 hingga Mei 2026. Pembagian data dilakukan secara kronologis, dengan periode pengujian Juli 2024 hingga Mei 2026. Nilai DPK pada berkas data menggunakan satuan juta rupiah.

- **ARIMA:** pemodelan melalui pemeriksaan stasioneritas dan pemilihan orde.
- **Prophet:** pemodelan tren dan pola musiman tahunan dengan penyesuaian hyperparameter.
- **XGBoost:** pemodelan menggunakan lag_1 hingga lag_12 dan fitur bulan. Tuning pada tahap penelitian menggunakan GridSearchCV dengan validasi rekursif.

Pemodelan, tuning, dan evaluasi dilakukan pada notebook penelitian. Repositori ini memuat aplikasi DSS beserta berkas hasil dan konfigurasi yang digunakan aplikasi.

## Hasil pemilihan model

Pemilihan model menggunakan MAPE data uji sebagai acuan utama, dengan MAE dan RMSE sebagai metrik pendukung.

| Komponen DPK | Model terpilih | MAPE data uji |
|---|---|---:|
| Giro | Prophet | 16,50% |
| Tabungan | Prophet | 2,65% |
| Deposito | XGBoost | 15,81% |

Hasil tersebut berlaku pada periode pengujian dan perbandingan tiga model dalam penelitian.

## Fitur aplikasi

**Halaman Hasil Penelitian** menyajikan model terpilih, grafik aktual dan prediksi, tabel evaluasi ketiga model, diagnostik kesalahan data latih dan data uji, serta prediksi tetap Juni–November 2026. Hasil pada halaman ini tidak berubah ketika data operasional diperbarui.

**Halaman Operasional** menyediakan pembaruan data bulanan melalui formulir, pemeriksaan dan konfirmasi masukan, penyimpanan histori pada Google Sheets, serta penghapusan terbatas pada periode terakhir. Pengguna dapat mengisi nilai total DPK atau komponen mentah yang kemudian dijumlahkan.

Model operasional dilatih ulang (*refit*) menggunakan seluruh histori yang tersedia, dengan jenis model dan hyperparameter tetap mengikuti hasil penelitian. Aplikasi menghasilkan prediksi enam bulan setelah periode data terakhir. Tuning dan pemilihan model tidak diulang pada tahap operasional.

Akses aplikasi menggunakan autentikasi satu akun admin. Keluaran DSS berupa informasi prediksi untuk mendukung penelaahan perkembangan DPK; keputusan pengelolaan likuiditas tetap berada pada pengguna.

## Struktur kode

| Lokasi | Fungsi |
|---|---|
| `app.py` | Pengaturan awal aplikasi dan navigasi halaman. |
| `pages/` | Halaman hasil penelitian dan operasional. |
| `utils/auth.py` | Autentikasi admin. |
| `utils/data_loader.py` | Pembacaan berkas hasil penelitian. |
| `utils/model_utils.py` | Pelatihan ulang model dan pembentukan prediksi. |
| `utils/sheets.py` | Pembacaan dan pembaruan histori pada Google Sheets. |
| `utils/styling.py` | Pengaturan tampilan dan format nilai. |
| `data/` | Hasil evaluasi, prediksi penelitian, dan konfigurasi model. |
| `requirements.txt` | Dependensi aplikasi. |

## Menjalankan aplikasi

Pasang dependensi pada lingkungan Python, kemudian jalankan aplikasi:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Aplikasi memerlukan konfigurasi akun admin pada bagian `[auth]` dan koneksi Google Sheets pada bagian `[connections.gsheets]` di Streamlit Secrets. Lembar `Sheet1` memuat kolom `Periode`, `Giro`, `Tabungan`, dan `Deposito`. Akun layanan Google yang digunakan aplikasi memerlukan akses untuk membaca dan memperbarui lembar tersebut.

Untuk penggunaan lokal, konfigurasi disimpan dalam `.streamlit/secrets.toml`. Untuk Streamlit Community Cloud, konfigurasi dimasukkan melalui pengaturan **Secrets** aplikasi. Berkas kredensial tidak disertakan dalam repositori.

## Identitas pengembang

- **Nama:** Tinsari Rauhana
- **NIM:** 2308107010038
- **Keperluan:** Tugas Akhir
