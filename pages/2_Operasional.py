"""Mengelola data historis dan menampilkan prediksi enam bulan setelah data terakhir.
Admin memeriksa dan mengonfirmasi data sebelum disimpan pada Google Sheets.
Model dilatih ulang menggunakan konfigurasi hasil penelitian tanpa tuning ulang."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.styling import inject_global_css, page_header, section_heading, metric_card, format_rupiah, format_bulan, PALET
from utils.auth import require_login
from utils.model_utils import load_model_config, refit_semua_komponen
from utils.sheets import baca_data_historis, tambah_data_baru, validasi_periode_baru, hapus_data_terakhir

inject_global_css()
require_login()

page_header(
    "Operasional & Forecast",
    "Data historis terbaru dan peramalan rolling 6 bulan ke depan.",
)


try:
    # Membaca histori operasional dari Google Sheets.
    df_historis = baca_data_historis()
    # Membaca jenis model dan hyperparameter hasil penelitian.
    model_config = load_model_config()
except Exception as exc:
    st.markdown(
        f'<div class="alert-warn">Gagal memuat data/koneksi: {exc}</div>',
        unsafe_allow_html=True,
    )
    st.stop()

periode_terakhir = df_historis["Periode"].max()


section_heading("Data historis terbaru")

# Mengambil nilai ketiga komponen pada bulan terakhir untuk kartu ringkasan.
baris_terakhir = df_historis[df_historis["Periode"] == periode_terakhir].iloc[0]

kartu_data = [
    ("Periode terakhir", format_bulan(periode_terakhir), f"{len(df_historis)} observasi total", False),
    ("Giro", format_rupiah(baris_terakhir['Giro']), "", True),
    ("Tabungan", format_rupiah(baris_terakhir['Tabungan']), "", True),
    ("Deposito", format_rupiah(baris_terakhir['Deposito']), "", True),
]
grid_html = '<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; align-items:stretch;">'
for label, value, sub, accent in kartu_data:
    accent_class = "accent" if accent else ""
    grid_html += (
        '<div class="metric-card" style="height:100%; box-sizing:border-box;">'
        f'<div class="label">{label}</div>'
        f'<div class="value {accent_class}">{value}</div>'
        f'<div class="sub">{sub}</div>'
        '</div>'
    )
grid_html += '</div>'
st.markdown(grid_html, unsafe_allow_html=True)

with st.expander("Lihat seluruh data historis"):
    st.dataframe(
        df_historis.sort_values("Periode", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <style>
        div[class*="st-key-btn_hapus_trigger"] button,
        div[class*="st-key-btn_hapus_ya"] button {
            background: #FFFFFF !important;
            color: #B3261E !important;
            border: 1px solid #B3261E !important;
            font-weight: 600 !important;
        }
        div[class*="st-key-btn_hapus_trigger"] button:hover,
        div[class*="st-key-btn_hapus_ya"] button:hover {
            background: #B3261E !important;
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Hapus data terakhir**")
    st.caption(
        "Hanya periode paling terakhir yang bisa dihapus (bukan baris di "
        "tengah), supaya urutan bulan tetap berurutan tanpa lompat."
    )

    # Meminta konfirmasi sebelum menjalankan penghapusan periode terakhir.
    if "konfirmasi_hapus" not in st.session_state:
        if st.button(f"Hapus data {format_bulan(periode_terakhir)}", key="btn_hapus_trigger"):
            st.session_state["konfirmasi_hapus"] = True
            st.rerun()
    else:
        st.markdown(
            f'<div class="alert-warn">Yakin mau hapus data periode '
            f"<strong>{format_bulan(periode_terakhir)}</strong>? Giro "
            f"{format_rupiah(baris_terakhir['Giro'])}, Tabungan "
            f"{format_rupiah(baris_terakhir['Tabungan'])}, Deposito "
            f"{format_rupiah(baris_terakhir['Deposito'])}. Tindakan ini tidak "
            "bisa dibatalkan.</div>",
            unsafe_allow_html=True,
        )
        col_hapus_ya, col_hapus_tidak = st.columns(2)
        with col_hapus_ya:
            if st.button("Ya, hapus", use_container_width=True, key="btn_hapus_ya"):
                try:
                    with st.spinner("Menghapus data..."):
                        # Menghapus periode terakhir setelah pemeriksaan batas minimum histori.
                        hapus_data_terakhir()
                        del st.session_state["konfirmasi_hapus"]
                    st.success("Data periode tersebut sudah dihapus.")
                    st.rerun()
                except ValueError as exc:
                    st.markdown(f'<div class="alert-warn">{exc}</div>', unsafe_allow_html=True)
        with col_hapus_tidak:
            if st.button("Batal", use_container_width=True, key="btn_hapus_batal"):
                del st.session_state["konfirmasi_hapus"]
                st.rerun()

st.markdown('<hr class="emas-divider">', unsafe_allow_html=True)


section_heading("Tambah data bulanan baru")

# Menetapkan bulan input secara otomatis agar penambahan data tetap berurutan.
periode_seharusnya = (pd.Timestamp(periode_terakhir) + pd.DateOffset(months=1)).replace(day=1)

st.markdown(
    f'<div class="alert-info">Periode berikutnya yang valid: '
    f'<strong>{format_bulan(periode_seharusnya)}</strong>. Data harus ditambahkan '
    f"berurutan tanpa lompat bulan.</div>",
    unsafe_allow_html=True,
)

# Memilih pengisian nilai total atau penjumlahan komponen mentah.
mode_input = st.radio(
    "Metode pengisian data",
    ["Isi total langsung", "Isi berdasarkan komponen mentah (Wadiah + Non PS)"],
    horizontal=True,
)

# Mengumpulkan masukan untuk diperiksa sebelum disimpan.
with st.form("form_data_baru"):
    st.markdown(
        f"**Periode: {format_bulan(periode_seharusnya)}** &nbsp; "
        "(otomatis, bulan berikutnya setelah data historis terakhir)"
    )

    if mode_input == "Isi total langsung":
        col_g, col_t, col_d = st.columns(3)
        with col_g:
            giro_input = st.number_input("Giro (juta Rp)", min_value=0.0, step=1000.0, format="%.0f")
        with col_t:
            tabungan_input = st.number_input("Tabungan (juta Rp)", min_value=0.0, step=1000.0, format="%.0f")
        with col_d:
            deposito_input = st.number_input("Deposito (juta Rp)", min_value=0.0, step=1000.0, format="%.0f")
        rincian = None

    else:
        st.markdown("**Giro** &nbsp;·&nbsp; total = Wadiah + Non PS")
        col_gw, col_gn = st.columns(2)
        with col_gw:
            giro_wadiah = st.number_input("Giro - Wadiah (juta Rp)", min_value=0.0, step=1000.0, format="%.0f", key="gw")
        with col_gn:
            giro_nonps = st.number_input("Giro - Non PS (juta Rp)", min_value=0.0, step=1000.0, format="%.0f", key="gn")

        st.markdown("**Tabungan** &nbsp;·&nbsp; total = Wadiah + Non PS")
        col_tw, col_tn = st.columns(2)
        with col_tw:
            tabungan_wadiah = st.number_input("Tabungan - Wadiah (juta Rp)", min_value=0.0, step=1000.0, format="%.0f", key="tw")
        with col_tn:
            tabungan_nonps = st.number_input("Tabungan - Non PS (juta Rp)", min_value=0.0, step=1000.0, format="%.0f", key="tn")

        st.markdown("**Deposito**")
        deposito_input = st.number_input("Deposito - Non PS (juta Rp)", min_value=0.0, step=1000.0, format="%.0f", key="dn")
        st.caption(
            "Deposito hanya memiliki komponen Non Profit Sharing (tidak ada Deposito "
            "Wadiah), sesuai struktur data penelitian."
        )

        # Menjumlahkan komponen Wadiah dan Non PS menjadi nilai Giro dan Tabungan.
        giro_input = giro_wadiah + giro_nonps
        tabungan_input = tabungan_wadiah + tabungan_nonps
        rincian = {
            "Giro_Wadiah": giro_wadiah, "Giro_NonPS": giro_nonps,
            "Tabungan_Wadiah": tabungan_wadiah, "Tabungan_NonPS": tabungan_nonps,
        }

    submit_cek = st.form_submit_button("Periksa data", use_container_width=True, type="primary")

# Memeriksa periode dan nilai total setelah formulir dikirim.
if submit_cek:
    periode_ts = periode_seharusnya
    valid, pesan = validasi_periode_baru(periode_ts, df_historis)

    if not valid:
        st.markdown(f'<div class="alert-warn">{pesan}</div>', unsafe_allow_html=True)
    elif giro_input <= 0 or tabungan_input <= 0 or deposito_input <= 0:
        st.markdown(
            '<div class="alert-warn">Total Giro, Tabungan, dan Deposito harus lebih besar dari nol.</div>',
            unsafe_allow_html=True,
        )
    else:
        # Menyimpan sementara masukan yang lolos pemeriksaan untuk dikonfirmasi admin.
        st.session_state["data_menunggu_konfirmasi"] = {
            "periode": periode_ts, "giro": giro_input, "tabungan": tabungan_input,
            "deposito": deposito_input, "rincian": rincian,
        }

# Menampilkan kembali masukan sebelum admin menyetujui penyimpanan.
if "data_menunggu_konfirmasi" in st.session_state:
    data = st.session_state["data_menunggu_konfirmasi"]
    with st.container(border=True):
        st.markdown("**Konfirmasi data sebelum disimpan:**")
        if data.get("rincian"):
            st.caption(
                f"Giro = Wadiah {data['rincian']['Giro_Wadiah']:,.0f} + "
                f"Non PS {data['rincian']['Giro_NonPS']:,.0f} = {data['giro']:,.0f} juta Rp &nbsp;|&nbsp; "
                f"Tabungan = Wadiah {data['rincian']['Tabungan_Wadiah']:,.0f} + "
                f"Non PS {data['rincian']['Tabungan_NonPS']:,.0f} = {data['tabungan']:,.0f} juta Rp"
            )
        st.write(
            pd.DataFrame([{
                "Periode": format_bulan(data["periode"]),
                "Giro": format_rupiah(data['giro']),
                "Tabungan": format_rupiah(data['tabungan']),
                "Deposito": format_rupiah(data['deposito']),
            }])
        )
        col_ya, col_tidak = st.columns(2)
        with col_ya:
            if st.button("Simpan dan refit model", use_container_width=True, type="primary"):
                try:
                    with st.spinner("Menyimpan data..."):
                        # Memeriksa ulang periode terhadap histori terbaru, kemudian menyimpan data.
                        tambah_data_baru(data["periode"], data["giro"], data["tabungan"], data["deposito"])
                except ValueError as exc:
                    st.warning(f"Data belum disimpan. {exc} Periksa kembali data terbaru.")
                    del st.session_state["data_menunggu_konfirmasi"]
                    st.cache_data.clear()
                else:
                    del st.session_state["data_menunggu_konfirmasi"]
                    st.cache_data.clear()
                    # Memberi tahu bahwa data tersimpan; refit dijalankan pada pemuatan halaman berikutnya.
                    st.success("Data tersimpan. Prediksi akan diperbarui.")
                    st.rerun()
        with col_tidak:
            if st.button("Batalkan", use_container_width=True):
                del st.session_state["data_menunggu_konfirmasi"]
                st.rerun()

st.markdown('<hr class="emas-divider">', unsafe_allow_html=True)


section_heading(f"Peramalan 6 bulan setelah {format_bulan(periode_terakhir)}")

with st.spinner("Melatih ulang model dengan konfigurasi yang telah dikunci..."):
    # Melatih ulang model saat alur halaman mencapai bagian ini dan memprediksi enam bulan.
    df_forecast = refit_semua_komponen(df_historis, model_config, horizon_bulan=6)

tab_giro, tab_tabungan, tab_deposito = st.tabs(["Giro", "Tabungan", "Deposito"])
for tab, target in zip([tab_giro, tab_tabungan, tab_deposito], ["Giro", "Tabungan", "Deposito"]):
    with tab:
        fc_target = df_forecast[df_forecast["Target"] == target]
        model_dipakai = model_config[target]["model"]

        # Membatasi grafik pada 18 bulan terakhir; pelatihan tetap memakai seluruh histori.
        hist_tampil = df_historis[["Periode", target]].tail(18)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hist_tampil["Periode"], y=hist_tampil[target], name="Historis",
            mode="lines+markers", line=dict(color=PALET["hijau_tua"], width=3),
        ))
        fig.add_trace(go.Scatter(
            x=fc_target["Periode"], y=fc_target["Forecast"], name="Forecast",
            mode="lines+markers", line=dict(color=PALET["emas"], width=2.5, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        ))
        fig.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=30, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            font=dict(family="Plus Jakarta Sans", color=PALET["teks_gelap"]),
            yaxis=dict(showgrid=True, gridcolor="rgba(11,61,46,0.08)", title="Nilai DPK (juta Rp)"),
            xaxis=dict(showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Membandingkan prediksi bulan keenam dengan aktual terakhir untuk ringkasan arah.
        arah = "naik" if fc_target["Forecast"].iloc[-1] > df_historis[target].iloc[-1] else "turun"
        st.markdown(
            f'<div class="alert-info">Model yang digunakan: <span class="badge-model">{model_dipakai}</span> '
            f"&nbsp; Tren perkiraan {arah} dibandingkan nilai historis terakhir.</div>",
            unsafe_allow_html=True,
        )

        baris_html = ""
        # Menyusun tabel nilai prediksi per bulan untuk komponen yang dipilih.
        for _, r in fc_target.iterrows():
            baris_html += (
                "<tr>"
                f"<td>{format_bulan(r['Periode'])}</td>"
                f"<td style='text-align:right;'>{format_rupiah(r['Forecast'])}</td>"
                "</tr>"
            )
        html_tabel = (
            '<div class="glass-card" style="padding: 0.6rem 1rem;">'
            '<table style="width:100%; border-collapse:collapse; font-size:0.92rem;">'
            '<thead><tr style="border-bottom: 2px solid rgba(11,61,46,0.15);">'
            '<th style="text-align:left; padding:0.6rem 0.4rem; width:60%;">Periode</th>'
            '<th style="text-align:right; padding:0.6rem 0.4rem; width:40%;">Forecast</th>'
            "</tr></thead>"
            f"<tbody>{baris_html}</tbody>"
            "</table></div>"
        )
        st.markdown(html_tabel, unsafe_allow_html=True)
        st.markdown(
            '<style>.glass-card table tr td {padding: 0.55rem 0.4rem; '
            "border-bottom: 1px solid rgba(11,61,46,0.06);}</style>",
            unsafe_allow_html=True,
        )

st.caption(
    "Jenis model dan hyperparameter setiap komponen dikunci dari hasil eksperimen "
    "penelitian (lihat Halaman Hasil Penelitian) dan tidak dipilih ulang di sini."
)
