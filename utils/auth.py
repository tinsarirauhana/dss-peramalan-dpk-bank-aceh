"""Mengatur autentikasi satu akun admin.
Nama pengguna dan kata sandi dibaca dari bagian auth pada Streamlit Secrets.
Status login disimpan selama sesi aplikasi berlangsung."""

import streamlit as st


def _cek_kredensial(username: str, password: str) -> bool:
    """Membandingkan masukan admin dengan nama pengguna dan kata sandi pada Secrets."""
    # Membaca kredensial dari Secrets tanpa menuliskan nilainya pada kode.
    kredensial = st.secrets.get("auth", {})
    return (
        username == kredensial.get("username", "")
        and password == kredensial.get("password", "")
    )


def require_login():
    """Menampilkan formulir login dan membatasi akses sampai autentikasi berhasil."""

    # Menggunakan status sesi agar admin tidak perlu login pada setiap perpindahan halaman.
    if st.session_state.get("logged_in"):
        return


    st.markdown(
        """
        <style>
        .login-illustrasi {
            background: linear-gradient(135deg, #0B3D2E 0%, #1F7A5C 100%);
            border-radius: 24px;
            padding: 2.6rem 2.2rem;
            min-height: 560px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            color: #FFFFFF;
        }
        .login-illustrasi .brand {
            display: flex; align-items: center; gap: 0.6rem;
        }
        .login-illustrasi .brand .mark {
            width: 34px; height: 34px; border-radius: 9px;
            background: rgba(255,255,255,0.15);
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 0.85rem;
        }
        .login-illustrasi .tagline {
            font-size: 1.3rem; font-weight: 700; line-height: 1.4; max-width: 260px;
        }
        .login-illustrasi .subtagline {
            font-size: 0.85rem; color: rgba(255,255,255,0.75);
            margin-top: 0.6rem; max-width: 270px; line-height: 1.55;
        }
        div[class*="st-key-login_card"] {
            background: #FFFFFF;
            border-radius: 24px;
            padding: 2.4rem 2.6rem 1.8rem 2.6rem;
            box-shadow: 0 20px 45px rgba(11,61,46,0.10);
            min-height: 560px;
            box-sizing: border-box;
        }
        div[data-testid="stForm"],
        div[data-testid="stForm"] div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stForm"] div[data-testid="stVerticalBlockBorderWrapper"] > div {
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            background: transparent !important;
        }
        div[class*="st-key-login_wrapper"] {
            min-height: 72vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        div[data-baseweb="input"] { border-radius: 10px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    # Menyusun bagian identitas aplikasi dan formulir login dalam dua kolom.
    with st.container(key="login_wrapper"):
        col_kiri, col_kanan = st.columns([1, 1.1], gap="medium")

        with col_kiri:
            st.markdown(
                '<div class="login-illustrasi">'
                '<div class="brand"><div class="mark">BA</div>'
                '<div style="font-weight:600; font-size:0.92rem;">Bank Aceh Syariah</div></div>'
                "<div>"
                '<svg width="150" height="90" viewBox="0 0 150 90" fill="none" '
                'xmlns="http://www.w3.org/2000/svg" style="margin-bottom:1.2rem;">'
                '<polyline points="5,70 35,55 65,60 95,30 125,15 145,10" '
                'stroke="#B08D2B" stroke-width="3" fill="none" '
                'stroke-linecap="round" stroke-linejoin="round"/>'
                '<circle cx="35" cy="55" r="4" fill="#FFFFFF"/>'
                '<circle cx="95" cy="30" r="4" fill="#FFFFFF"/>'
                '<circle cx="145" cy="10" r="4" fill="#B08D2B"/>'
                "</svg>"
                '<div class="tagline">Peramalan DPK yang lebih akurat</div>'
                '<div class="subtagline">Mendukung perencanaan likuiditas PT Bank '
                "Aceh Syariah berbasis model ARIMA, Prophet, dan XGBoost.</div>"
                "</div>"
                '<div style="font-size:0.72rem; color:rgba(255,255,255,0.55);">'
                "Sistem Pendukung Keputusan DPK</div>"
                "</div>",
                unsafe_allow_html=True,
            )

        with col_kanan:
            with st.container(key="login_card"):
                st.markdown(
                    '<div style="font-weight:700; font-size:0.95rem; color:#0B3D2E; '
                    'margin-bottom:1.5rem;">Masuk ke Dashboard</div>'
                    '<div class="page-title" style="font-size:1.55rem; margin-bottom:0.2rem;">'
                    "Selamat datang kembali</div>"
                    '<div class="page-subtitle" style="margin-bottom:1.6rem;">'
                    "Masuk menggunakan akun admin yang telah terdaftar.</div>",
                    unsafe_allow_html=True,
                )

                # Mengirim nama pengguna dan kata sandi saat tombol Masuk ditekan.
                with st.form("form_login"):
                    username = st.text_input("Nama pengguna")
                    password = st.text_input("Kata sandi", type="password")
                    submit = st.form_submit_button("Masuk", use_container_width=True, type="primary")

                if submit:
                    if _cek_kredensial(username, password):
                        # Menyimpan keberhasilan autentikasi selama sesi berlangsung.
                        st.session_state["logged_in"] = True
                        st.rerun()
                    else:
                        st.markdown(
                            '<div class="alert-warn" style="margin-top:0.9rem;">'
                            "Nama pengguna atau kata sandi salah.</div>",
                            unsafe_allow_html=True,
                        )

                st.markdown(
                    '<div style="text-align:center; font-size:0.76rem; color:#6B7268; '
                    'margin-top:1.3rem;">Akses khusus admin — sistem ini tidak '
                    "menyediakan pendaftaran akun baru.</div>",
                    unsafe_allow_html=True,
                )

    # Menghentikan isi halaman bagi pengguna yang belum berhasil login.
    st.stop()


def logout_button():
    """Mengakhiri status login melalui tombol keluar pada sidebar."""
    if st.sidebar.button("Keluar", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
