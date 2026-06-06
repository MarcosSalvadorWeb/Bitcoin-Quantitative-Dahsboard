import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from etl import extract as ext
from etl import transform as tf


def plot_bitcoin_trend_matplot(days=30):
    """
    Busca o histórico do Bitcoin e gera um gráfico estático em Matplotlib.

    Args:
        days (int): Quantidade de dias exibidos no gráfico.

    Returns:
        None: O gráfico é aberto em uma janela Matplotlib.
    """
    raw_data = ext.bit_history(days)
    raw_fng = ext.fetch_fear_and_greed(days)
    intraday_data = ext.btc_intraday()

    if raw_data is None or intraday_data is None:
        print("Nao foi possivel buscar os dados para o grafico.")
        return

    tables = tf.clean_data(raw_data, raw_fng, intraday_data)
    df_data = tables["btc_1mes"] if days <= 30 else tables["btc_1ano"].tail(days)

    plt.figure(figsize=(11, 5))
    plt.plot(
        df_data["data"],
        df_data["price_USD"],
        color="#F7931A",
        linewidth=2.5,
        label="Preco BTC (USD)",
    )

    plt.title(f"Tendencia do Bitcoin - Ultimos {days} dias", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Data", fontsize=11, labelpad=10)
    plt.ylabel("Preco em dolares (USD)", fontsize=11, labelpad=10)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.grid(True, linestyle="--", alpha=0.25)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
