from datetime import datetime

import numpy as np
import pandas as pd
from yfinance import data


BR_TZ = "America/Sao_Paulo"
NEXT_HALVING_DATE = datetime(2028, 4, 17)
LAST_HALVING_DATE = datetime(2024, 4, 19)

HALVINGS = {
    "2020-05-11": "3o Halving (6.25 BTC)",
    "2024-04-19": "4o Halving (3.125 BTC)",
}


def retorno_log(df, price_column="price_USD"):
    """
    Calcula retorno logaritmico e volatilidade anualizada de 21 periodos.
    """
    df = df.copy()
    df["log_return_USD"] = np.log(df[price_column] / df[price_column].shift(1))
    df["volatility_21d_USD"] = df["log_return_USD"].rolling(window=21).std() * np.sqrt(365)
    return df


def mayer_multiple(df, price_column="price_USD"):
    """
    Calcula o Mayer Multiple: preco dividido pela media movel de 200 dias.
    """
    df = df.copy()
    moving_average = df[price_column].rolling(window=200, min_periods=1).mean()
    df["mayer_multiple"] = (df[price_column] / moving_average).round(4)
    return df


def Mayers_Multiply(df):
    """
    Alias mantido para compatibilidade com chamadas antigas.
    """
    return mayer_multiple(df)


def transform_fear_and_greed(raw_json):
    """
    Transforma o JSON bruto do Fear and Greed Index em um DataFrame limpo.
    """
    if not raw_json or "data" not in raw_json:
        print("Aviso: Dados do Fear & Greed invalidos ou vazios.")
        return pd.DataFrame(columns=["data", "fng_value", "fng_classification"])

    df = pd.DataFrame(raw_json["data"])

    if df.empty:
        return pd.DataFrame(columns=["data", "fng_value", "fng_classification"])

    df["data"] = pd.to_datetime(df["timestamp"].astype(int), unit="s").dt.normalize()
    df["fng_value"] = pd.to_numeric(df["value"], errors="coerce")
    df["fng_classification"] = df["value_classification"]

    return (
        df[["data", "fng_value", "fng_classification"]]
        .dropna(subset=["data"])
        .sort_values("data")
        .reset_index(drop=True)
    )


def calculate_halving_countdown(reference_date=None):
    """
    Calcula dias restantes e progresso percentual estimado do ciclo atual.
    """
    today = reference_date or datetime.now()
    days_remaining = max((NEXT_HALVING_DATE - today).days, 0)
    cycle_days = max((NEXT_HALVING_DATE - LAST_HALVING_DATE).days, 1)
    days_passed = min(max((today - LAST_HALVING_DATE).days, 0), cycle_days)
    cycle_progress_pct = round((days_passed / cycle_days) * 100, 2)

    return {
        "data": today.strftime("%Y-%m-%d"),
        "days_remaining": days_remaining,
        "next_halving_date": NEXT_HALVING_DATE.strftime("%Y-%m-%d"),
        "cycle_progress_percentage": cycle_progress_pct,
    }


def analyze_past_halvings(df):
    """
    Analisa o preco 90 dias antes/depois dos halvings presentes na base.
    """
    price_df = df.copy()
    price_df["data"] = pd.to_datetime(price_df["data"]).dt.normalize()
    results = []

    for date_text, name in HALVINGS.items():
        halving_date = pd.to_datetime(date_text)
        price_on_day = _price_on_or_nearest_date(price_df, halving_date)
        price_before = _price_on_or_nearest_date(price_df, halving_date - pd.Timedelta(days=90))
        price_after = _price_on_or_nearest_date(price_df, halving_date + pd.Timedelta(days=90))

        if price_on_day is None:
            continue

        before_pct = (
            round(((price_on_day - price_before) / price_before) * 100, 2)
            if price_before
            else np.nan
        )
        after_pct = (
            round(((price_after - price_on_day) / price_on_day) * 100, 2)
            if price_after
            else np.nan
        )

        results.append(
            {
                "evento": name,
                "data_evento": halving_date.strftime("%Y-%m-%d"),
                "preco_no_dia": round(price_on_day, 2),
                "retorno_90d_antes_pct": before_pct,
                "retorno_90d_depois_pct": after_pct,
            }
        )

    return pd.DataFrame(results)


def _price_on_or_nearest_date(df, target_date):
    match = df[df["data"] == target_date]

    if not match.empty:
        return float(match["price_USD"].iloc[0])

    window = df[(df["data"] >= target_date - pd.Timedelta(days=2)) & (df["data"] <= target_date + pd.Timedelta(days=2))]

    if window.empty:
        return None

    nearest_index = (window["data"] - target_date).abs().idxmin()
    return float(window.loc[nearest_index, "price_USD"])


def _prices_to_dataframe(prices):
    """
    Transforma a lista de precos da CoinGecko em DataFrame padronizado.
    """
    df = pd.DataFrame(prices, columns=["timestamp", "price_USD"])
    df["data"] = pd.to_datetime(df["timestamp"], unit="ms").dt.normalize()
    df["price_USD"] = pd.to_numeric(df["price_USD"], errors="coerce").round(2)

    return (
        df[["data", "price_USD"]]
        .dropna(subset=["data", "price_USD"])
        .drop_duplicates(subset=["data"], keep="last")
        .sort_values("data")
        .reset_index(drop=True)
    )


def intraday_data(dados_intraday):
    """
    Prepara a serie intraday do Bitcoin agrupada por hora.
    """
    if not dados_intraday or not dados_intraday.get("prices"):
        return pd.DataFrame(columns=["data", "price_USD"])

    df = pd.DataFrame(dados_intraday["prices"], columns=["timestamp", "price_USD"])
    df["data"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(BR_TZ)
    df["hora"] = df["data"].dt.floor("h")
    df["price_USD"] = pd.to_numeric(df["price_USD"], errors="coerce")

    hourly = df.groupby("hora", as_index=False)["price_USD"].mean()
    hourly["price_USD"] = hourly["price_USD"].round(2)

    return hourly.rename(columns={"hora": "data"})[["data", "price_USD"]]

def Drawdown(df):
    """
    Recebe o DataFrame limpo do banco e adiciona o Drawdown, que representa a queda percentual do preço em relação ao pico anterior.
    """
    df = df.copy()
    preço_max_acumulado = df["price_USD"].cummax()
    df["drawdown"] = (df["price_USD"] - preço_max_acumulado) / preço_max_acumulado
    return df

def Z_ScoreMM200(df):
    """_
    Recebe o DataFrame limpo do banco e adiciona o Z-Score da MM200, que indica quantos desvios padrão o preço atual está acima ou abaixo da média móvel de 200 dias.
    """
    df = df.copy()
    mm200 = df["price_USD"].rolling(window=200).mean()
    std200 = df["price_USD"].rolling(window=200).std()
    df["z_score_200"] = (df["price_USD"] - mm200) / std200
    return df


def clean_data(dados_brutos_precos, dados_brutos_fng=None, dados_intraday=None):
    """
    Orquestra a transformacao completa da base Bitcoin em USD.
    """
    if not dados_brutos_precos or not dados_brutos_precos.get("prices"):
        raise ValueError("Historico de precos da CoinGecko vazio ou invalido.")

    df_prices = _prices_to_dataframe(dados_brutos_precos["prices"])
    
    df_quant = Z_ScoreMM200(Drawdown(mayer_multiple(retorno_log(df_prices))))

    df_fng = transform_fear_and_greed(dados_brutos_fng)

    if df_fng.empty:
        df_final = df_quant.copy()
        df_final["fng_value"] = np.nan
        df_final["fng_classification"] = "Sem dados"
    else:
        df_final = pd.merge(df_quant, df_fng, on="data", how="left")
        df_final["fng_classification"] = df_final["fng_classification"].fillna("Sem dados")

    df_final = df_final.sort_values("data").reset_index(drop=True)
    df_intraday = intraday_data(dados_intraday)
    halving_countdown = pd.DataFrame([calculate_halving_countdown()])
    halving_analysis = analyze_past_halvings(df_final)

    return {
        "btc_1semana": df_final.tail(7).copy().reset_index(drop=True),
        "btc_1mes": df_final.tail(30).copy().reset_index(drop=True),
        "btc_1ano": df_final.tail(365).copy().reset_index(drop=True),
        "btc_macro_10anos": df_final.copy().reset_index(drop=True),
        "btc_intraday": df_intraday,
        "btc_halving_countdown": halving_countdown,
        "btc_halving_analysis": halving_analysis,
    }