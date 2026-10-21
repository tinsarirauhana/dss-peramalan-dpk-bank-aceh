"""Mengatur tampilan bersama untuk seluruh halaman DSS.
Menyediakan warna, tata letak, kartu ringkasan, serta format nilai dan periode."""

import pandas as pd
import streamlit as st

# Menyimpan kode warna yang digunakan bersama oleh komponen tampilan.
PALET = {
    "hijau_tua": "#0B3D2E",
    "hijau_medium": "#145C43",
    "hijau_terang": "#1F7A5C",
    "emas": "#B08D2B",
    "putih": "#FFFFFF",
    "abu_bg": "#FAFAF9",
    "garis": "#E7E5E1",
    "teks_gelap": "#1A1F1D",
    "teks_muted": "#6B7268",
    "merah_alert": "#B3432D",
}


def inject_global_css():
    """Menerapkan pengaturan huruf, warna, navigasi, dan komponen tampilan."""
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

        <style>
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, sans-serif;
        }}

        .stApp {{
            background: {PALET['abu_bg']};
        }}

        /* ---------- Paksa hilangkan "kotak putih" di belakang konten ----------
           Beda versi Streamlit kadang kasih background/shadow/rounded-corner
           default ke wrapper utama (nama elemennya beda-beda tergantung versi),
           jadi di-reset semua kemungkinan elemen ini sekaligus. */
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > div,
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        html, body, #root,
        .main,
        .block-container {{
            background: transparent !important;
            box-shadow: none !important;
            border-radius: 0 !important;
            border: none !important;
        }}

        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{
            background: {PALET['putih']};
            border-bottom: 1px solid {PALET['garis']};
            box-shadow: 0 2px 6px rgba(11,61,46,0.05);
        }}

        /* ---------- Navigasi atas custom (dibuat manual di app.py) ---------- */
        /* Dibatasi cuma ke 3 tombol nav (key="nav_..."), BUKAN semua tombol
           secondary di seluruh app -- supaya tombol secondary di halaman lain
           (mis. tombol Hapus/Batal) tetap kelihatan normal. */
        div[class*="st-key-nav_"] button[kind*="secondary" i] {{
            background: transparent !important;
            color: {PALET['teks_muted']} !important;
            border: 1px solid transparent !important;
            font-weight: 500 !important;
            box-shadow: none !important;
        }}
        div[class*="st-key-nav_"] button[kind*="secondary" i]:hover {{
            background: {PALET['abu_bg']} !important;
            color: {PALET['teks_gelap']} !important;
            border-color: {PALET['garis']} !important;
        }}

        /* ---------- Tombol secondary default (dipakai di luar nav) ---------- */
        button[kind*="secondary" i] {{
            background: {PALET['putih']} !important;
            color: {PALET['teks_gelap']} !important;
            border: 1px solid {PALET['garis']} !important;
            font-weight: 500 !important;
        }}
        button[kind*="secondary" i]:hover {{
            background: {PALET['abu_bg']} !important;
            border-color: {PALET['hijau_tua']} !important;
        }}
        button[kind*="primary" i] {{
            background: {PALET['hijau_tua']} !important;
            color: {PALET['putih']} !important;
            border: none !important;
            font-weight: 600 !important;
        }}
        button[kind*="primary" i]:hover {{
            background: {PALET['hijau_medium']} !important;
        }}
        div.stButton button, div.stFormSubmitButton button {{
            border-radius: 8px;
            padding: 0.45rem 1.1rem;
        }}

        /* ---------- Kontainer utama, batasi lebar biar rapi ---------- */
        .block-container {{
            max-width: 1180px;
            padding-top: 3.8rem;
        }}

        /* ---------- Kartu flat, bukan glass ---------- */
        .card {{
            background: {PALET['putih']};
            border: 1px solid {PALET['garis']};
            border-radius: 14px;
            padding: 1.5rem 1.6rem;
            margin-bottom: 1.1rem;
        }}
        .card-dark {{
            background: {PALET['hijau_tua']};
            border-radius: 14px;
            padding: 1.5rem 1.6rem;
            color: {PALET['putih']};
            margin-bottom: 1.1rem;
        }}

        /* ---------- Kartu metrik ---------- */
        .metric-card {{
            background: {PALET['putih']};
            border: 1px solid {PALET['garis']};
            border-radius: 14px;
            padding: 1.3rem 1.4rem;
            height: 100%;
        }}
        .metric-card .label {{
            font-size: 0.82rem;
            font-weight: 500;
            color: {PALET['teks_muted']};
            margin-bottom: 0.4rem;
        }}
        .metric-card .value {{
            font-size: 1.7rem;
            font-weight: 700;
            color: {PALET['teks_gelap']};
            line-height: 1.2;
        }}
        .metric-card .value.accent {{ color: {PALET['hijau_tua']}; }}
        .metric-card .sub {{
            font-size: 0.8rem;
            color: {PALET['teks_muted']};
            margin-top: 0.3rem;
        }}

        /* ---------- Badge ---------- */
        .badge {{
            display: inline-block;
            padding: 0.28rem 0.8rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8rem;
            background: {PALET['hijau_tua']};
            color: {PALET['putih']};
        }}
        .badge-outline {{
            display: inline-block;
            padding: 0.26rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8rem;
            border: 1px solid {PALET['emas']};
            color: {PALET['emas']};
            background: transparent;
        }}

        /* ---------- Tipografi ---------- */
        .page-title {{
            font-size: 1.9rem;
            font-weight: 700;
            color: {PALET['teks_gelap']};
            letter-spacing: -0.02em;
            margin-bottom: 0.2rem;
        }}
        .page-subtitle {{
            font-size: 0.98rem;
            color: {PALET['teks_muted']};
            margin-bottom: 1.6rem;
            max-width: 780px;
            line-height: 1.55;
        }}
        .section-heading {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {PALET['teks_gelap']};
            margin: 2rem 0 0.9rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid {PALET['garis']};
        }}

        /* ---------- Form / container bordered ---------- */
        div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            background: {PALET['putih']};
            border: 1px solid {PALET['garis']} !important;
            border-radius: 14px !important;
            padding: 1.4rem 1.5rem;
        }}

        /* ---------- Alert ---------- */
        .alert-info {{
            background: #F2F6F3;
            border-left: 3px solid {PALET['hijau_tua']};
            border-radius: 8px;
            padding: 0.85rem 1.05rem;
            font-size: 0.9rem;
            color: {PALET['teks_gelap']};
        }}
        .alert-warn {{
            background: #FBF6E9;
            border-left: 3px solid {PALET['emas']};
            border-radius: 8px;
            padding: 0.85rem 1.05rem;
            font-size: 0.9rem;
            color: {PALET['teks_gelap']};
        }}

        /* ---------- Alias untuk kompatibilitas kelas lama ---------- */
        .glass-card {{
            background: {PALET['putih']};
            border: 1px solid {PALET['garis']};
            border-radius: 14px;
            padding: 1.5rem 1.6rem;
            margin-bottom: 1.1rem;
        }}
        .badge-model {{
            display: inline-block;
            padding: 0.28rem 0.8rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8rem;
            background: {PALET['hijau_tua']};
            color: {PALET['putih']};
        }}
        .badge-emas {{
            display: inline-block;
            padding: 0.26rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8rem;
            border: 1px solid {PALET['emas']};
            color: {PALET['emas']};
            background: transparent;
        }}
        .emas-divider {{
            border: none;
            border-top: 1px solid {PALET['garis']};
            margin: 1.8rem 0;
        }}

        hr {{ border-color: {PALET['garis']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, sub: str = "", accent: bool = False):
    """Menampilkan satu kartu berisi nama indikator, nilai, dan keterangan."""
    # Menentukan penekanan warna pada nilai kartu ringkasan.
    accent_class = "accent" if accent else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value {accent_class}">{value}</div>
            <div class="sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(text: str):
    """Menampilkan judul bagian dengan format yang seragam."""
    st.markdown(f'<div class="section-heading">{text}</div>', unsafe_allow_html=True)


def page_header(title: str, subtitle: str):
    """Menampilkan judul halaman beserta deskripsinya."""
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def format_rupiah(nilai_juta: float) -> str:
    """Mengubah nilai dalam juta rupiah menjadi teks juta, miliar, atau triliun."""
    nilai_juta = float(nilai_juta)
    # Satu juta satuan juta rupiah setara dengan satu triliun rupiah.
    if abs(nilai_juta) >= 1_000_000:
        return f"Rp {nilai_juta / 1_000_000:,.2f} triliun"
    # Seribu satuan juta rupiah setara dengan satu miliar rupiah.
    if abs(nilai_juta) >= 1_000:
        return f"Rp {nilai_juta / 1_000:,.2f} miliar"
    return f"Rp {nilai_juta:,.0f} juta"


# Memetakan nomor bulan ke nama bulan dalam bahasa Indonesia.
_NAMA_BULAN = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}


def format_bulan(tanggal) -> str:
    """Mengubah tanggal menjadi nama bulan dan tahun dalam bahasa Indonesia."""
    tanggal = pd.Timestamp(tanggal)
    return f"{_NAMA_BULAN[tanggal.month]} {tanggal.year}"
