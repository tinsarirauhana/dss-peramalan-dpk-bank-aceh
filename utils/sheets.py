"""Membaca, menambah, mengoreksi, dan menghapus data historis pada Google Sheets.
Sheet1 memuat kolom Periode, Giro, Tabungan, dan Deposito dalam juta rupiah.
Koneksi menggunakan bagian connections.gsheets pada Streamlit Secrets."""

from datetime import datetime
from math import isfinite
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


def get_connection():
    """Mengakses koneksi Google Sheets yang ditetapkan pada Streamlit Secrets."""
    return st.connection("gsheets", type=GSheetsConnection)


def _baca_data_historis(ttl: int) -> pd.DataFrame:
    """Membaca data historis serta menyeragamkan tipe tanggal dan nilai DPK."""
    conn = get_connection()
    # Membaca empat kolom histori; ttl menentukan masa penyimpanan sementara hasil baca.
    df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3], ttl=ttl)
    # Mengabaikan baris kosong pada lembar data.
    df = df.dropna(how="all").copy()
    # Menyeragamkan periode ke tanggal awal bulan.
    df["Periode"] = pd.to_datetime(df["Periode"], format="mixed").dt.to_period("M").dt.to_timestamp()
    # Mengubah nilai DPK menjadi angka; isian yang tidak dapat dibaca menjadi NaN.
    for kolom in ["Giro", "Tabungan", "Deposito"]:
        df[kolom] = pd.to_numeric(df[kolom], errors="coerce")
    # Mengurutkan histori dari bulan paling awal hingga bulan terakhir.
    df = df.sort_values("Periode").reset_index(drop=True)
    return df


@st.cache_data(ttl=60)
def baca_data_historis() -> pd.DataFrame:
    """Membaca histori untuk tampilan dengan penyimpanan sementara selama 60 detik."""
    return _baca_data_historis(ttl=60)


def periode_maksimal_input(hari_ini=None) -> pd.Timestamp:
    """Bulan terakhir yang SUDAH SELESAI menurut kalender WIB.

    Ini bukan verifikasi tanggal publikasi laporan keuangan; sumber angkanya
    tetap harus diperiksa admin sebelum memasukkan data.

    ``hari_ini`` hanya untuk pengujian agar hasil tidak bergantung jam komputer.
    """
    tanggal = hari_ini if hari_ini is not None else datetime.now(ZoneInfo("Asia/Jakarta")).date()
    bulan_berjalan = pd.Timestamp(tanggal).to_period("M").to_timestamp()
    return bulan_berjalan - pd.DateOffset(months=1)


def _pastikan_nominal_valid(giro: float, tabungan: float, deposito: float):
    """Validasi backend: antarmuka bukan satu-satunya penjaga nilai input."""
    for nama, nilai in {"Giro": giro, "Tabungan": tabungan, "Deposito": deposito}.items():
        try:
            angka = float(nilai)
        except (TypeError, ValueError):
            raise ValueError(f"{nama} harus berupa angka positif.") from None
        if not isfinite(angka) or angka <= 0:
            raise ValueError(f"{nama} harus lebih besar dari nol dan bernilai hingga.")


def tambah_data_baru(periode: pd.Timestamp, giro: float, tabungan: float, deposito: float):
    """Memeriksa periode terbaru, menyimpan satu bulan tambahan, dan membersihkan cache."""
    conn = get_connection()

    # Membaca langsung data terbaru sebelum mengubah isi Google Sheets.
    df_lama = _baca_data_historis(ttl=0)
    # Memeriksa ulang periode untuk menghindari penyimpanan dari konfirmasi yang sudah usang.
    valid, pesan = validasi_periode_baru(periode, df_lama)
    if not valid:
        raise ValueError(pesan)

    _pastikan_nominal_valid(giro, tabungan, deposito)

    # Menyusun satu baris yang memuat periode dan ketiga nilai DPK.
    baris_baru = pd.DataFrame([{
        "Periode": periode.strftime("%Y-%m-%d"),
        "Giro": giro,
        "Tabungan": tabungan,
        "Deposito": deposito,
    }])
    # Menyeragamkan tanggal lama dan tanggal baru ke format tahun-bulan-tanggal.
    df_lama_str = df_lama.copy()
    df_lama_str["Periode"] = df_lama_str["Periode"].dt.strftime("%Y-%m-%d")

    # Menggabungkan histori dengan satu bulan tambahan.
    df_baru = pd.concat([df_lama_str, baris_baru], ignore_index=True)
    # Menulis kembali tabel histori hasil perubahan ke Sheet1.
    conn.update(worksheet="Sheet1", data=df_baru)
    # Menghapus salinan sementara agar pembacaan berikutnya memakai data terbaru.
    st.cache_data.clear()


def validasi_periode_baru(periode_baru: pd.Timestamp, df_historis: pd.DataFrame) -> tuple[bool, str]:
    """Memeriksa bahwa periode belum tersedia dan tepat setelah bulan terakhir."""
    # Menolak bulan yang sudah tersedia dalam histori.
    if periode_baru in set(df_historis["Periode"]):
        return False, "Periode ini sudah ada di data historis."

    periode_terakhir = df_historis["Periode"].max()
    # Menetapkan satu-satunya periode baru yang diterima: bulan setelah data terakhir.
    periode_seharusnya = (pd.Timestamp(periode_terakhir) + pd.DateOffset(months=1)).replace(day=1)

    if pd.Timestamp(periode_baru).to_period("M").to_timestamp() != periode_seharusnya:
        return False, (
            f"Periode berikutnya yang valid adalah {periode_seharusnya:%Y-%m}. "
            "Data harus ditambahkan berurutan tanpa lompat bulan."
        )
    # Menolak bulan berjalan (belum selesai) atau bulan masa depan.
    # Pemeriksaan ini DIULANG di backend pada saat menyimpan.
    if periode_seharusnya > periode_maksimal_input():
        return False, (
            f"Periode {periode_seharusnya:%Y-%m} belum selesai menurut kalender WIB. "
            f"Bulan terakhir yang dapat diinput adalah {periode_maksimal_input():%Y-%m}, "
            "jika laporan resminya sudah tersedia dan diverifikasi."
        )
    return True, ""


def ubah_data_historis(periode: pd.Timestamp, giro: float, tabungan: float, deposito: float,
                        nilai_awal: dict | None = None):
    """Koreksi nominal periode yang sudah ada tanpa mengubah indeks waktunya.

    Membaca Sheet1 secara fresh. ``nilai_awal`` opsional dipakai untuk mencegah
    penimpaan sunyi bila ada admin lain memperbarui bulan yang sama setelah
    formulir koreksi ditampilkan.
    """
    _pastikan_nominal_valid(giro, tabungan, deposito)
    periode = pd.Timestamp(periode).to_period("M").to_timestamp()
    conn = get_connection()
    df = _baca_data_historis(ttl=0)
    cocok = df["Periode"] == periode
    if int(cocok.sum()) != 1:
        raise ValueError("Periode yang akan diedit tidak ditemukan secara unik di histori.")

    if nilai_awal is not None:
        baris_asli = df.loc[cocok].iloc[0]
        for kolom in ("Giro", "Tabungan", "Deposito"):
            if float(baris_asli[kolom]) != float(nilai_awal[kolom]):
                raise ValueError(
                    "Data periode ini sudah diubah di Google Sheets sejak formulir dibuka. "
                    "Muat ulang halaman sebelum mengoreksi."
                )

    df.loc[cocok, ["Giro", "Tabungan", "Deposito"]] = [giro, tabungan, deposito]
    df["Periode"] = df["Periode"].dt.strftime("%Y-%m-%d")
    conn.update(worksheet="Sheet1", data=df)
    st.cache_data.clear()
    return periode


def hapus_data_terakhir():
    """Menghapus periode terakhir dengan menyisakan minimal 13 observasi bulanan."""
    conn = get_connection()
    # Membaca langsung data terbaru sebelum mengubah isi Google Sheets.
    df_lama = _baca_data_historis(ttl=0)

    periode_terakhir = df_lama["Periode"].max()
    # Mengeluarkan periode paling akhir tanpa menghapus bulan di tengah histori.
    df_baru = df_lama[df_lama["Periode"] != periode_terakhir].copy()

    # Mempertahankan 12 observasi pembentuk lag dan minimal satu observasi pelatihan.
    if len(df_baru) < 13:
        raise ValueError("Tidak bisa menghapus: data historis harus tersisa minimal 13 bulan.")
    df_baru["Periode"] = df_baru["Periode"].dt.strftime("%Y-%m-%d")

    # Menulis kembali tabel histori hasil perubahan ke Sheet1.
    conn.update(worksheet="Sheet1", data=df_baru)
    # Menghapus salinan sementara agar pembacaan berikutnya memakai data terbaru.
    st.cache_data.clear()
    return periode_terakhir
