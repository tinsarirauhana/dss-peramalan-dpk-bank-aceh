"""Melatih ulang model terpilih dan menghasilkan prediksi operasional.
Jenis model dan hyperparameter dibaca dari data/model_config.json.
Berkas konfigurasi diperoleh dari hasil pemilihan model di notebook penelitian.
Pelatihan memakai seluruh histori yang tersedia dengan horizon bawaan enam bulan."""

from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Menggunakan dua belas nilai bulanan sebelumnya sebagai fitur historis XGBoost.
MAX_LAG = 12
# Menentukan lokasi berkas konfigurasi model operasional.
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_model_config() -> dict:
    """Membaca jenis model dan hyperparameter untuk pelatihan ulang operasional."""
    path = DATA_DIR / "model_config.json"
    if not path.exists():
        raise FileNotFoundError(
            "data/model_config.json tidak ditemukan. Lihat docstring utils/model_utils.py "
            "untuk cara menghasilkan berkas ini dari notebook eksperimen."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _buat_fitur_lag(series: pd.Series, periode: pd.Series, max_lag: int = MAX_LAG) -> pd.DataFrame:
    """Membentuk lag_1 hingga lag_12 dan nomor bulan sebagai masukan XGBoost."""
    df = pd.DataFrame({"Periode": periode.values, "y": series.values})
    # Menggeser nilai historis: lag_1 berasal dari satu bulan sebelumnya, dan seterusnya.
    for k in range(1, max_lag + 1):
        df[f"lag_{k}"] = df["y"].shift(k)
    # Menambahkan nomor bulan 1 sampai 12 untuk mewakili posisi bulan dalam satu tahun.
    df["bulan"] = pd.to_datetime(df["Periode"]).dt.month
    return df


def refit_dan_forecast(
    target: str,
    df_historis: pd.DataFrame,
    model_config: dict,
    horizon_bulan: int = 6,
) -> pd.DataFrame:
    """Melatih ulang model satu komponen DPK dan memprediksi periode berikutnya.
    Masukan berupa histori berurutan dan konfigurasi; keluaran berupa Periode dan Forecast."""
    # Mengambil model dan konfigurasi khusus komponen yang akan diprediksi.
    info = model_config[target]
    jenis_model = info["model"]
    config = info["config"]

    # Mengurutkan histori sebelum menentukan periode akhir dan membentuk prediksi.
    df_historis = df_historis.sort_values("Periode").reset_index(drop=True)
    periode_terakhir = df_historis["Periode"].max()
    # Menyusun tanggal prediksi mulai bulan setelah histori terakhir.
    tanggal_forecast = pd.date_range(
        pd.Timestamp(periode_terakhir) + pd.DateOffset(months=1),
        periods=horizon_bulan, freq="MS",
    )

    # Menjalankan ARIMA jika jenis tersebut tercantum pada konfigurasi operasional.
    if jenis_model == "ARIMA":
        from statsmodels.tsa.arima.model import ARIMA as SM_ARIMA

        y = df_historis.set_index("Periode")[target].astype(float)
        # Menggunakan orde p, d, dan q dari konfigurasi tanpa pencarian orde ulang.
        order = tuple(config["order"])
        model = SM_ARIMA(y, order=order, enforce_stationarity=False, enforce_invertibility=False).fit()
        forecast_vals = np.asarray(model.forecast(steps=horizon_bulan))

    elif jenis_model == "Prophet":
        from prophet import Prophet
        import logging, os, sys, contextlib

        logging.getLogger("cmdstanpy").setLevel(logging.CRITICAL)

        @contextlib.contextmanager
        def _suppress():
            """Mengalihkan keluaran terminal sementara selama pelatihan dan prediksi Prophet."""
            with open(os.devnull, "w") as devnull:
                old_out, old_err = sys.stdout, sys.stderr
                sys.stdout, sys.stderr = devnull, devnull
                try:
                    yield
                finally:
                    sys.stdout, sys.stderr = old_out, old_err

        # Menyesuaikan nama kolom: ds untuk tanggal dan y untuk nilai yang diprediksi.
        dfp = df_historis[["Periode", target]].rename(columns={"Periode": "ds", target: "y"})
        # Menggunakan musim tahunan; musim harian dan mingguan dinonaktifkan untuk data bulanan.
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=False,
            daily_seasonality=False,
            # Mengatur keluwesan perubahan tren Prophet.
            changepoint_prior_scale=config["changepoint_prior_scale"],
            # Mengatur kekuatan regularisasi pada komponen musiman.
            seasonality_prior_scale=config["seasonality_prior_scale"],
            # Menentukan pola musiman aditif atau multiplikatif.
            seasonality_mode=config["seasonality_mode"],
        )
        with _suppress():
            # Mengestimasi kembali model Prophet menggunakan seluruh histori komponen tersebut.
            model.fit(dfp)
            # Menghasilkan prediksi pada tanggal mendatang yang telah disusun.
            hasil = model.predict(pd.DataFrame({"ds": tanggal_forecast}))
        # Mengambil yhat sebagai nilai prediksi Prophet.
        forecast_vals = hasil["yhat"].values

    elif jenis_model == "XGBoost":
        from xgboost import XGBRegressor

        fitur_df = _buat_fitur_lag(df_historis[target], df_historis["Periode"], MAX_LAG)
        # Membuang baris awal yang belum memiliki dua belas nilai lag lengkap.
        fitur_df = fitur_df.dropna().reset_index(drop=True)
        kolom_fitur = [f"lag_{k}" for k in range(1, MAX_LAG + 1)] + ["bulan"]

        # Memisahkan fitur masukan X dari nilai target y yang akan dipelajari.
        X = fitur_df[kolom_fitur]
        y = fitur_df["y"]

        # Menggunakan jumlah pohon, learning_rate, dan kedalaman hasil pemilihan konfigurasi.
        model = XGBRegressor(
            # Menggunakan jumlah pohon efektif yang ditetapkan pada penelitian.
            n_estimators=config["n_estimators"],
            # Mengatur besar kontribusi setiap pohon terhadap prediksi.
            learning_rate=config["learning_rate"],
            # Membatasi kedalaman pohon dalam membentuk aturan prediksi.
            max_depth=config["max_depth"],
            # Menetapkan sumber pengacakan agar pelatihan dapat diulang.
            random_state=42,
        )
        # Melatih seluruh baris yang memiliki lag lengkap tanpa mengulang tuning atau early stopping.
        model.fit(X, y)

        # Menyiapkan histori sebagai dasar pembentukan lag untuk prediksi bulan pertama.
        riwayat = list(df_historis[target].astype(float).values)
        forecast_vals = []
        # Membentuk prediksi secara rekursif, satu bulan pada setiap putaran.
        for tgl in tanggal_forecast:
            # Mengambil dua belas nilai terakhir dari histori yang tersedia.
            lag_values = {f"lag_{k}": riwayat[-k] for k in range(1, MAX_LAG + 1)}
            # Menjaga urutan fitur prediksi agar sama dengan urutan saat pelatihan.
            x_baris = pd.DataFrame([{**lag_values, "bulan": tgl.month}])[kolom_fitur]
            pred = float(model.predict(x_baris)[0])
            forecast_vals.append(pred)
            # Menambahkan prediksi bulan ini sebagai sumber lag untuk bulan berikutnya.
            riwayat.append(pred)
        forecast_vals = np.array(forecast_vals)

    else:
        raise ValueError(f"Jenis model tidak dikenali: {jenis_model}")

    # Memasangkan setiap tanggal dengan nilai prediksinya.
    return pd.DataFrame({"Periode": tanggal_forecast, "Forecast": forecast_vals})


def refit_semua_komponen(df_historis: pd.DataFrame, model_config: dict, horizon_bulan: int = 6) -> pd.DataFrame:
    """Menggabungkan prediksi Giro, Tabungan, dan Deposito beserta nama modelnya."""
    hasil = []
    # Melatih dan memprediksi setiap komponen secara terpisah.
    for target in ["Giro", "Tabungan", "Deposito"]:
        df_fc = refit_dan_forecast(target, df_historis, model_config, horizon_bulan)
        df_fc["Target"] = target
        df_fc["Model"] = model_config[target]["model"]
        hasil.append(df_fc)
    # Menggabungkan hasil ketiga komponen dalam satu tabel.
    return pd.concat(hasil, ignore_index=True)
