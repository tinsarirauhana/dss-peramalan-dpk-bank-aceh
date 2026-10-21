"""Menjalankan DSS peramalan DPK PT Bank Aceh Syariah.
Mengatur tampilan awal, autentikasi, dan navigasi kedua halaman.
Jalankan aplikasi dengan perintah: streamlit run app.py."""

import streamlit as st
from utils.auth import require_login
from utils.styling import inject_global_css

# Mengatur judul tab browser dan lebar halaman aplikasi.
st.set_page_config(
    page_title="DSS DPK - Bank Aceh Syariah",
    page_icon=":material/account_balance:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_global_css()
# Memeriksa status login sebelum menampilkan navigasi dan isi dashboard.
require_login()

# Mendaftarkan halaman hasil penelitian sebagai halaman awal.
halaman_hasil = st.Page(
    "pages/1_Hasil_Penelitian.py", title="Hasil Penelitian",
    icon=":material/bar_chart:", default=True,
)
# Mendaftarkan halaman pembaruan data dan prediksi operasional.
halaman_operasional = st.Page(
    "pages/2_Operasional.py", title="Operasional & Forecast",
    icon=":material/autorenew:",
)


# Menyerahkan perpindahan halaman kepada Streamlit dengan menu buatan sendiri.
navigasi = st.navigation([halaman_hasil, halaman_operasional], position="hidden")

st.markdown('<div style="padding-top: 0.6rem;"></div>', unsafe_allow_html=True)
# Membagi baris navigasi untuk identitas aplikasi, dua menu, dan tombol keluar.
col_logo, col_menu1, col_menu2, col_spacer, col_logout = st.columns([2.6, 1.9, 2.6, 1.5, 0.9])

with col_logo:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:0.55rem; height:100%;">
            <div style="width:30px; height:30px; border-radius:7px; background:#0B3D2E;
                        display:flex; align-items:center; justify-content:center;
                        color:#FFFFFF; font-weight:700; font-size:0.82rem; flex-shrink:0;">BA</div>
            <div style="line-height:1.15;">
                <div style="font-weight:600; font-size:0.9rem; color:#1A1F1D;">Bank Aceh Syariah</div>
                <div style="font-size:0.72rem; color:#6B7268;">Sistem Pendukung Keputusan DPK</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_menu1:
    # Menandai menu aktif dan membuka halaman hasil penelitian ketika dipilih.
    if st.button("Hasil Penelitian", key="nav_hasil", use_container_width=True,
                 type="primary" if navigasi.title == "Hasil Penelitian" else "secondary"):
        st.switch_page(halaman_hasil)
with col_menu2:
    if st.button("Operasional & Forecast", key="nav_operasional", use_container_width=True,
                 type="primary" if navigasi.title == "Operasional & Forecast" else "secondary"):
        st.switch_page(halaman_operasional)
with col_logout:
    if st.button("Keluar", key="nav_logout", use_container_width=True, type="secondary"):
        # Menghapus status login agar akses berikutnya kembali melalui formulir autentikasi.
        st.session_state["logged_in"] = False
        st.rerun()
st.markdown('<hr style="margin: 0.9rem 0 1.7rem 0;">', unsafe_allow_html=True)

# Menjalankan halaman yang sedang dipilih.
navigasi.run()
