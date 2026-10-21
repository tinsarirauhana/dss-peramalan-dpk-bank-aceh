"""Membaca hasil penelitian dari folder data untuk ditampilkan pada dashboard.
Metrik dan prediksi pada halaman penelitian berasal dari berkas hasil eksperimen.
Pembaruan data operasional tidak menghitung ulang hasil penelitian tersebut."""

from pathlib import Path
import json
import pandas as pd
import streamlit as st

# Menentukan folder data relatif terhadap lokasi kode, bukan folder kerja terminal.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _baca_csv(nama_file: str) -> pd.DataFrame:
    """Membaca tabel CSV dan menghentikan halaman jika berkas tidak tersedia."""
    path = DATA_DIR / nama_file
    # Memeriksa ketersediaan berkas sebelum melanjutkan pembacaan.
    if not path.exists():
        st.error(
            f"Berkas `{nama_file}` tidak ditemukan di folder `data/`. "
            "Pastikan seluruh hasil ekspor notebook sudah disalin ke folder ini."
        )
        st.stop()
    return pd.read_csv(path)


def _baca_json(nama_file: str) -> dict:
    """Membaca konfigurasi JSON dan menghentikan halaman jika berkas tidak tersedia."""
    path = DATA_DIR / nama_file
    # Memeriksa ketersediaan berkas sebelum melanjutkan pembacaan.
    if not path.exists():
        st.error(f"Berkas `{nama_file}` tidak ditemukan di folder `data/`.")
        st.stop()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Menyimpan hasil pembacaan sementara agar berkas tidak dibaca pada setiap interaksi.
@st.cache_data
def load_model_terbaik() -> pd.DataFrame:
    """Membaca pasangan komponen DPK dan model terpilih dari hasil penelitian."""
    return _baca_csv("model_terbaik_per_target.csv")


# Menyimpan hasil pembacaan sementara agar berkas tidak dibaca pada setiap interaksi.
@st.cache_data
def load_evaluasi_test() -> pd.DataFrame:
    """Membaca nilai MAE, RMSE, dan MAPE setiap model pada data uji."""
    return _baca_csv("hasil_evaluasi_test_semua_model.csv")


# Menyimpan hasil pembacaan sementara agar berkas tidak dibaca pada setiap interaksi.
@st.cache_data
def load_diagnostik_overfitting() -> pd.DataFrame | None:
    """Membaca perbandingan kesalahan latih dan uji jika berkas diagnostik tersedia."""
    path = DATA_DIR / "hasil_diagnostik_train_test.csv"
    # Memeriksa ketersediaan berkas sebelum melanjutkan pembacaan.
    if not path.exists():
        return None
    return pd.read_csv(path)


# Menyimpan hasil pembacaan sementara agar berkas tidak dibaca pada setiap interaksi.
@st.cache_data
def load_actual_vs_predicted() -> pd.DataFrame:
    """Membaca nilai aktual dan prediksi pada periode pengujian."""
    df = _baca_csv("dss_actual_vs_predicted_test.csv")
    # Mengubah teks periode menjadi tanggal agar dapat digunakan pada sumbu waktu.
    df["Periode"] = pd.to_datetime(df["Periode"])
    return df


# Menyimpan hasil pembacaan sementara agar berkas tidak dibaca pada setiap interaksi.
@st.cache_data
def load_forecast_6_bulan() -> pd.DataFrame:
    """Membaca prediksi enam bulan yang ditetapkan pada tahap penelitian."""
    df = _baca_csv("forecast_6_bulan_final.csv")
    # Mengubah teks periode menjadi tanggal agar dapat digunakan pada sumbu waktu.
    df["Periode"] = pd.to_datetime(df["Periode"])
    return df


# Menyimpan hasil pembacaan sementara agar berkas tidak dibaca pada setiap interaksi.
@st.cache_data
def load_config_frozen() -> dict:
    """Membaca arsip konfigurasi sebelum pengujian; tidak dipanggil oleh halaman saat ini."""
    return _baca_json("CONFIG_FROZEN_SEBELUM_TEST.json")


def get_model_terbaik_dict() -> dict:
    """Menyusun pasangan nama komponen DPK dan model terpilih dalam dictionary."""
    df = load_model_terbaik()
    return dict(zip(df["Target"], df["Model_terbaik"]))
