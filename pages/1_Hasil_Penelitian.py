"""Menyajikan hasil pengujian ARIMA, Prophet, dan XGBoost pada setiap komponen DPK.
Grafik, metrik evaluasi, dan prediksi enam bulan dibaca dari hasil penelitian.
Nilai pada halaman ini tetap saat data operasional diperbarui."""

import streamlit as st
import plotly.graph_objects as go
from utils.styling import inject_global_css, page_header, section_heading, metric_card, format_rupiah, format_bulan, PALET
from utils.auth import require_login
from utils.data_loader import (
    load_model_terbaik,
    load_evaluasi_test,
    load_diagnostik_overfitting,
    load_actual_vs_predicted,
    load_forecast_6_bulan,
)

inject_global_css()
require_login()

page_header(
    "Sistem Pendukung Keputusan DPK - Hasil Penelitian",
    "Sistem Pendukung Keputusan peramalan Dana Pihak Ketiga PT Bank Aceh Syariah. "
    "Halaman ini menyajikan hasil penelitian dari perbandingan ARIMA, "
    "Prophet, dan XGBoost, serta model terbaik untuk setiap komponen DPK, berdasarkan "
    "evaluasi pada data uji (23 bulan, periode 2024-07 s/d 2026-05).",
)
st.caption(
    "Nilai pada halaman ini bersifat tetap dan tidak berubah saat data operasional "
    "pada halaman Operasional & Forecast diperbarui."
)

# Membaca hasil penelitian yang disimpan sebagai berkas CSV.
model_terbaik_df = load_model_terbaik()
evaluasi_df = load_evaluasi_test()
diagnostik_df = load_diagnostik_overfitting()
avp_df = load_actual_vs_predicted()

# Memasangkan setiap komponen DPK dengan nama model terpilih.
model_terbaik_dict = dict(zip(model_terbaik_df["Target"], model_terbaik_df["Model_terbaik"]))


section_heading("Model terbaik per komponen DPK")

cols = st.columns(3)
for col, target in zip(cols, ["Giro", "Tabungan", "Deposito"]):
    model = model_terbaik_dict.get(target, "-")
    # Mengambil metrik untuk model terpilih pada komponen yang sedang ditampilkan.
    baris = evaluasi_df[(evaluasi_df["Target"] == target) & (evaluasi_df["Model"] == model)]
    mape = baris["MAPE"].values[0] if len(baris) else None
    with col:
        metric_card(
            label=f"{target}",
            value=model,
            sub=f"MAPE data uji: {mape:.2f}%" if mape is not None else "",
            accent=True,
        )

st.markdown(
    '<div class="alert-info" style="margin-top:0.8rem;">'
    "Model dipilih berdasarkan MAPE data uji terendah sebagai acuan utama, "
    "dengan MAE dan RMSE ditampilkan sebagai informasi pendukung."
    "</div>",
    unsafe_allow_html=True,
)


section_heading("Actual vs predicted - model terbaik per komponen")

# Menyediakan pilihan grafik model terpilih atau perbandingan ketiga model.
pilihan_tampilan = st.radio(
    "Tampilkan",
    ["Model terbaik saja", "Seluruh model (perbandingan)"],
    horizontal=True,
    label_visibility="collapsed",
)

cols_chart = st.columns(3)
for col, target in zip(cols_chart, ["Giro", "Tabungan", "Deposito"]):
    with col:
        st.markdown(f"**{target}**")
        fig = go.Figure()
        data_target = avp_df[avp_df["Target"] == target]

        # Mengambil satu salinan nilai aktual yang sama untuk ketiga model.
        actual = data_target[data_target["Model"] == data_target["Model"].iloc[0]]
        fig.add_trace(go.Scatter(
            x=actual["Periode"], y=actual["Actual"], name="Aktual",
            mode="lines+markers", line=dict(color=PALET["hijau_tua"], width=3),
            marker=dict(size=5),
        ))

        # Membatasi garis prediksi sesuai pilihan tampilan pengguna.
        if pilihan_tampilan == "Model terbaik saja":
            model = model_terbaik_dict.get(target)
            pred = data_target[data_target["Model"] == model]
            fig.add_trace(go.Scatter(
                x=pred["Periode"], y=pred["Predicted"], name=f"Prediksi ({model})",
                mode="lines+markers", line=dict(color=PALET["emas"], width=2.5, dash="dash"),
                marker=dict(size=5, symbol="square"),
            ))
        else:
            warna_garis = {"ARIMA": "#8B5E3C", "Prophet": PALET["emas"], "XGBoost": "#3C6E8B"}
            for model in ["ARIMA", "Prophet", "XGBoost"]:
                pred = data_target[data_target["Model"] == model]
                fig.add_trace(go.Scatter(
                    x=pred["Periode"], y=pred["Predicted"], name=model,
                    mode="lines", line=dict(color=warna_garis[model], width=1.8, dash="dash"),
                ))

        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10)),
            font=dict(family="Plus Jakarta Sans", color=PALET["teks_gelap"]),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(11,61,46,0.08)"),
        )
        st.plotly_chart(fig, use_container_width=True)


section_heading("Prediksi enam bulan menggunakan model terpilih")

st.caption(
    "Prediksi ini bersifat tetap: dihasilkan sekali dari model final yang "
    "di-refit menggunakan seluruh data historis penelitian sampai Mei 2026, "
    "dan tidak berubah walau data operasional pada halaman Operasional "
    "diperbarui. Untuk prediksi rolling terbaru, lihat halaman Operasional."
)

# Membaca ramalan tetap hasil refit pada seluruh data penelitian hingga Mei 2026.
forecast_df = load_forecast_6_bulan()

# Menyimpan uraian hasil ramalan tetap untuk setiap komponen DPK.
INTERPRETASI_FORECAST = {
    "Giro": (
        "Nilai diperkirakan menurun dari Rp6,195 triliun pada Juni menjadi "
        "Rp5,625 triliun pada Agustus, kemudian meningkat hingga Rp7,123 "
        "triliun pada Oktober dan berada pada Rp6,574 triliun pada November."
    ),
    "Tabungan": (
        "Proyeksi berada pada kisaran Rp11,638 hingga Rp11,902 triliun. "
        "Nilai prediksi meningkat dari Rp11,680 triliun pada Juni menjadi "
        "Rp11,833 triliun pada Juli, lalu relatif stabil hingga November."
    ),
    "Deposito": (
        "Nilai prediksi menurun dari Rp6,253 triliun pada Juni menjadi "
        "Rp6,208 triliun pada Juli, kemudian meningkat menjadi Rp6,282 "
        "triliun pada Agustus dan Rp6,357 triliun pada September."
    ),
}

cols_fc = st.columns(3)
for col, target in zip(cols_fc, ["Giro", "Tabungan", "Deposito"]):
    with col:
        st.markdown(f"**{target}**")
        fc_target = forecast_df[forecast_df["Target"] == target].sort_values("Periode")


        # Mengambil aktual terakhir sebagai titik penghubung menuju garis ramalan.
        aktual_target = avp_df[avp_df["Target"] == target]
        aktual_terakhir = aktual_target[
            aktual_target["Model"] == aktual_target["Model"].iloc[0]
        ].sort_values("Periode").iloc[-1]

        fig_fc = go.Figure()
        fig_fc.add_trace(go.Scatter(
            x=[aktual_terakhir["Periode"]] + list(fc_target["Periode"]),
            y=[aktual_terakhir["Actual"]] + list(fc_target["Forecast"]),
            name="Forecast", mode="lines+markers",
            line=dict(color=PALET["emas"], width=2.5, dash="dash"),
            marker=dict(size=6, symbol="diamond"),
        ))
        fig_fc.update_layout(
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans", color=PALET["teks_gelap"]),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(11,61,46,0.08)"),
        )
        st.plotly_chart(fig_fc, use_container_width=True)

        baris_html = ""
        # Menyusun baris tabel untuk setiap bulan prediksi.
        for _, r in fc_target.iterrows():
            baris_html += (
                "<tr><td>" + format_bulan(r["Periode"]) + "</td>"
                f"<td style='text-align:right;'>{format_rupiah(r['Forecast'])}</td></tr>"
            )
        st.markdown(
            '<div class="glass-card" style="padding:0.5rem 0.8rem;">'
            '<table style="width:100%; border-collapse:collapse; font-size:0.88rem;">'
            f"<tbody>{baris_html}</tbody></table></div>",
            unsafe_allow_html=True,
        )
        st.caption(INTERPRETASI_FORECAST[target])


section_heading("Perbandingan seluruh model (data uji)")

tab_giro, tab_tabungan, tab_deposito = st.tabs(["Giro", "Tabungan", "Deposito"])
for tab, target in zip([tab_giro, tab_tabungan, tab_deposito], ["Giro", "Tabungan", "Deposito"]):
    with tab:
        # Mengurutkan model berdasarkan MAPE data uji dari yang paling kecil.
        sub = evaluasi_df[evaluasi_df["Target"] == target].sort_values("MAPE").reset_index(drop=True)
        sub_tampil = sub.rename(columns={
            "Model": "Model", "MAE": "MAE (Rp juta)", "RMSE": "RMSE (Rp juta)", "MAPE": "MAPE (%)"
        })[["Model", "MAE (Rp juta)", "RMSE (Rp juta)", "MAPE (%)"]]
        st.dataframe(
            sub_tampil.style.format({"MAE (Rp juta)": "{:,.0f}", "RMSE (Rp juta)": "{:,.0f}", "MAPE (%)": "{:.2f}"})
            .highlight_min(subset=["MAPE (%)"], color=f"{PALET['emas']}33"),
            use_container_width=True,
            hide_index=True,
        )


# Menampilkan diagnostik jika berkas perbandingan latih dan uji tersedia.
if diagnostik_df is not None:
    section_heading("Diagnostik train vs test")

    def _render_tabel_diagnostik(df):
        """Menyajikan MAPE latih, MAPE uji, selisih, dan interpretasi dari tabel hasil."""
        baris_html = ""
        for _, r in df.iterrows():
            baris_html += (
                "<tr>"
                f"<td>{r['Target']}</td>"
                f"<td>{r['Model']}</td>"
                f"<td style='text-align:right;'>{r['MAPE_train']:.2f}%</td>"
                f"<td style='text-align:right;'>{r['MAPE_test']:.2f}%</td>"
                f"<td style='text-align:right;'>{r['Selisih_MAPE(test-train)']:.2f}</td>"
                f"<td>{r.get('Interpretasi', '-')}</td>"
                "</tr>"
            )

        html_tabel = (
            '<div class="glass-card" style="padding: 0.6rem 1rem;">'
            '<table style="width:100%; border-collapse:collapse; font-size:0.92rem;">'
            '<thead><tr style="border-bottom: 2px solid rgba(11,61,46,0.15);">'
            '<th style="text-align:left; padding:0.6rem 0.4rem;">Target</th>'
            '<th style="text-align:left; padding:0.6rem 0.4rem;">Model</th>'
            '<th style="text-align:right; padding:0.6rem 0.4rem;">MAPE train</th>'
            '<th style="text-align:right; padding:0.6rem 0.4rem;">MAPE test</th>'
            '<th style="text-align:right; padding:0.6rem 0.4rem;">Selisih</th>'
            '<th style="text-align:left; padding:0.6rem 0.4rem;">Interpretasi</th>'
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

    _render_tabel_diagnostik(diagnostik_df)
    st.caption(
        "Metrik train dan test dihitung dengan mekanisme berbeda per model "
        "(lihat catatan metodologi pada notebook eksperimen); selisih besar "
        "tidak selalu murni menandakan overfitting, khususnya untuk XGBoost "
        "yang mengevaluasi test melalui recursive multi-step forecasting."
    )


section_heading("Kenapa model ini yang paling cocok")

# Menyimpan penjelasan pemilihan model berdasarkan hasil pengujian penelitian.
ALASAN_MODEL = {
    "Giro": (
        "Prophet mampu mengikuti beberapa perubahan arah Giro, termasuk "
        "penurunan pada Desember 2024 dan Desember 2025. Model ini "
        "menghasilkan MAPE sebesar 16,50% serta MAE terendah, sedangkan "
        "XGBoost menghasilkan RMSE terendah. Berdasarkan MAPE data uji, "
        "Prophet dipilih sebagai model terbaik untuk Giro."
    ),
    "Tabungan": (
        "Prophet mampu mengikuti kecenderungan peningkatan Tabungan dan "
        "kenaikan pada akhir tahun melalui komponen tren dan pola musiman "
        "tahunan. Model ini menghasilkan MAE, RMSE, dan MAPE terendah "
        "di antara ketiga model pada Tabungan. MAPE sebesar 2,65% "
        "menunjukkan kedekatan hasil prediksi dengan nilai aktual "
        "selama periode pengujian."
    ),
    "Deposito": (
        "XGBoost menghasilkan lintasan prediksi yang lebih stabil dan "
        "berada pada rentang yang lebih sempit daripada nilai aktual. "
        "Model mempelajari pola historis melalui lag_1 hingga lag_12 "
        "dan fitur bulan, sehingga tidak selalu mereplikasi setiap "
        "fluktuasi ekstrem. Secara keseluruhan, XGBoost menghasilkan "
        "MAE, RMSE, dan MAPE terendah pada Deposito, dengan MAPE "
        "sebesar 15,81%, sehingga dipilih sebagai model terbaik."
    ),
}

cols_data_alasan = [(target, model_terbaik_dict.get(target, "-")) for target in ["Giro", "Tabungan", "Deposito"]]
grid_html = '<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:1.1rem; align-items:stretch;">'
for target, model in cols_data_alasan:
    grid_html += (
        '<div class="glass-card" style="height:100%; margin-bottom:0; display:flex; flex-direction:column; box-sizing:border-box;">'
        f'<div style="font-weight:700; color:#0B3D2E; margin-bottom:0.5rem;">{target} '
        f'<span class="badge-emas" style="margin-left:0.3rem;">{model}</span></div>'
        f'<div style="font-size:0.88rem; color:#3A4A44; line-height:1.55;">{ALASAN_MODEL[target]}</div>'
        '</div>'
    )
grid_html += '</div>'
st.markdown(grid_html, unsafe_allow_html=True)
