import os
import requests

try:
    import yfinance as yf
except ImportError:
    yf = None

# Configuração dinâmica: se houver API Key no ambiente, usa o subdomínio correto da CoinGecko
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")

if COINGECKO_API_KEY:
    COINGECKO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
else:
    COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

REQUEST_TIMEOUT = 30  # Aumentado para 30s devido ao volume de dados macro.
SESSION = requests.Session()
SESSION.headers.update(
    {
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }
)

if COINGECKO_API_KEY:
    SESSION.headers.update({"x-cg-pro-api-key": COINGECKO_API_KEY})


def _get_json(url, params=None, quiet=False):
    """
    Faz uma requisição GET incluindo cabeçalhos de autenticação se necessário.
    """
    try:
        response = SESSION.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        if not quiet:
            print(f"Erro ao acessar a API CoinGecko: {error}")
        return None


def actual_value():
    """
    Busca o preço atual do Bitcoin em dólar (USD).
    """
    data = _get_json(
        f"{COINGECKO_BASE_URL}/simple/price",
        params={"ids": "bitcoin", "vs_currencies": "usd"},
    )

    if not data:
        return None

    return data.get("bitcoin", {}).get("usd")


def btc_intraday():
    """
    Busca a série intraday do Bitcoin nas últimas 24 horas em USD.
    """
    data = _get_json(
        f"{COINGECKO_BASE_URL}/coins/bitcoin/market_chart",
        params={"vs_currency": "usd", "days": 1},
    )

    if data and data.get("prices"):
        return data

    return _ohlc_as_prices(days=1)


def bit_history(days=3650):
    """
    Busca o histórico diário do Bitcoin em dólar.
    Usa yfinance para o historico longo e CoinGecko apenas para atualizacao recente.
    """
    if days and int(days) > 365:
        bootstrap_data = _yfinance_history_as_prices()
        recent_data = _coingecko_market_chart(days=30, quiet=True)

        if bootstrap_data and bootstrap_data.get("prices"):
            if recent_data and recent_data.get("prices"):
                return _merge_price_series(bootstrap_data, recent_data)

            return bootstrap_data

        print("\nAviso: yfinance falhou. Tentando manter atualizacao pela CoinGecko.")

    return _coingecko_market_chart(days=days)


def _coingecko_market_chart(days=365, quiet=False):
    """
    Busca market_chart na CoinGecko com fallback para OHLC.
    """
    url = f"{COINGECKO_BASE_URL}/coins/bitcoin/market_chart"
    attempts = []

    if days and int(days) > 365:
        attempts.extend(
            [
                {"vs_currency": "usd", "days": str(days), "interval": "daily"},
                {"vs_currency": "usd", "days": "max", "interval": "daily"},
                {"vs_currency": "usd", "days": "365", "interval": "daily"},
            ]
        )
    else:
        attempts.append({"vs_currency": "usd", "days": str(days), "interval": "daily"})

    for index, params in enumerate(attempts, start=1):
        data = _get_json(url, params=params, quiet=quiet or index < len(attempts))

        if data and data.get("prices"):
            requested_days = params["days"]

            if requested_days != str(days) and not quiet:
                print(
                    "\nAviso: CoinGecko bloqueou o historico solicitado. "
                    f"Usando fallback de {requested_days} dias."
                )

            return data

    ohlc_days = "max" if int(days) > 365 else int(days)
    data = _ohlc_as_prices(days=ohlc_days)

    if data and data.get("prices"):
        if not quiet:
            print("\nAviso: usando endpoint alternativo OHLC da CoinGecko para atualizar precos.")
        return data

    return None


def _yfinance_history_as_prices():
    """
    Baixa o historico completo BTC-USD e converte para o formato ``prices``.
    """
    if yf is None:
        print("\nAviso: yfinance nao esta instalado. Instale as dependencias do requirements.txt.")
        return None

    try:
        btc = yf.download(
            "BTC-USD",
            period="max",
            auto_adjust=True,
            progress=False,
        )
    except Exception as error:
        print(f"\nErro ao acessar yfinance: {error}")
        return None

    if btc is None or btc.empty:
        return None

    btc = btc.copy()

    if isinstance(btc.columns, tuple) or getattr(btc.columns, "nlevels", 1) > 1:
        btc.columns = btc.columns.get_level_values(0)

    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_columns = [column for column in required_columns if column not in btc.columns]

    if missing_columns:
        print(f"\nAviso: yfinance retornou dados sem colunas esperadas: {missing_columns}")
        return None

    btc = btc[required_columns]
    btc.index = btc.index.tz_localize(None) if btc.index.tz is not None else btc.index
    btc = btc.sort_index()
    btc = btc[~btc.index.duplicated(keep="last")]
    btc = btc.dropna(subset=["Close"])

    prices = [
        [int(index.timestamp() * 1000), float(row["Close"])]
        for index, row in btc.iterrows()
    ]

    return {"prices": prices} if prices else None


def _merge_price_series(base_data, recent_data):
    """
    Une historico yfinance com atualizacao recente da CoinGecko sem duplicatas.
    """
    prices_by_timestamp = {
        int(timestamp): float(price)
        for timestamp, price in base_data.get("prices", [])
    }

    for timestamp, price in recent_data.get("prices", []):
        prices_by_timestamp[int(timestamp)] = float(price)

    return {
        "prices": [
            [timestamp, price]
            for timestamp, price in sorted(prices_by_timestamp.items())
        ]
    }


def _ohlc_as_prices(days=365):
    """
    Usa o endpoint OHLC da CoinGecko como alternativa ao market_chart.
    O fechamento de cada candle alimenta a mesma estrutura ``prices``.
    """
    data = _get_json(
        f"{COINGECKO_BASE_URL}/coins/bitcoin/ohlc",
        params={"vs_currency": "usd", "days": str(days)},
    )

    if not data:
        return None

    prices = [[row[0], row[4]] for row in data if len(row) >= 5]
    return {"prices": prices} if prices else None
    
    
def fetch_fear_and_greed(limit=3650):
    """
    Busca o histórico do Fear and Greed Index.
    Padrão de limit=3650 para tentar buscar até 10 anos de histórico de sentimento.
    """
    url = "https://api.alternative.me/fng/"
    params = {"limit": str(limit)}
    
    try:
        # Fazemos a requisição para a API do Alternative.me
        response = SESSION.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        print(f"Erro ao acessar a API do Fear and Greed: {error}")
        return None
