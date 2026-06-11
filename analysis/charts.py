import sqlite3

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


DB_PATH = "database/bitcoin.db"
BITCOIN_ORANGE = "#F7931A"
POSITIVE_GREEN = "#16A34A"
NEGATIVE_RED = "#DC2626"
INK = "#172033"
MUTED = "#667085"
PANEL = "#FFFFFF"
GRID = "#E4E7EC"

PRICE_COLUMN = "price_USD"
LOG_RETURN_COLUMN = "log_return_USD"


PERIOD_CONFIG = {
    "btc_1semana": {
        "title": "Bitcoin - 1 Semana",
        "subtitle": "Leitura curta da semana",
        "x_tick": "%d/%m",
        "hover_date": "%d/%m/%Y",
        "range_buttons": [("7D", 7, "day"), ("Tudo", None, "all")],
        "moving_average": None,
    },
    "btc_1mes": {
        "title": "Bitcoin - 1 Mes",
        "subtitle": "Tendencia dos ultimos 30 dias",
        "x_tick": "%d/%m",
        "hover_date": "%d/%m/%Y",
        "range_buttons": [("7D", 7, "day"), ("1M", 1, "month"), ("Tudo", None, "all")],
        "moving_average": 7,
    },
    "btc_1ano": {
        "title": "Bitcoin - 1 Ano",
        "subtitle": "Visao historica anual",
        "x_tick": "%b/%Y",
        "hover_date": "%d/%m/%Y",
        "range_buttons": [
            ("1M", 1, "month"),
            ("3M", 3, "month"),
            ("6M", 6, "month"),
            ("1A", 1, "year"),
            ("Tudo", None, "all"),
        ],
        "moving_average": 21,
    },
    "btc_intraday": {
        "title": "Bitcoin - Intraday",
        "subtitle": "Preco medio por hora no horario de Brasilia",
        "x_tick": "%H:%M",
        "hover_date": "%d/%m %H:%M",
        "range_buttons": [],
        "moving_average": None,
    },
    "btc_macro_10anos": {
        "title": "Bitcoin - Macro 10 Anos",
        "subtitle": "Ciclos longos, halvings e media de 200 dias",
        "x_tick": "%Y",
        "hover_date": "%d/%m/%Y",
        "range_buttons": [
            ("1A", 1, "year"),
            ("3A", 3, "year"),
            ("5A", 5, "year"),
            ("Tudo", None, "all"),
        ],
        "moving_average": 200,
    },
}

HALVING_DATES = {
    "2020-05-11": "3o Halving",
    "2024-04-19": "4o Halving",
}


def get_data_from_db(table_name, db_path=None):
    """
    Le uma tabela do SQLite e devolve os dados ordenados por data.
    """
    db_path = db_path or DB_PATH

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)

    if df.empty:
        raise ValueError(f"A tabela {table_name} esta vazia.")

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"])
        return df.sort_values("data").reset_index(drop=True)

    return df


def create_title(table_name):
    """Retorna o titulo amigavel para uma tabela de periodo."""
    return PERIOD_CONFIG.get(table_name, {}).get("title", "Dashboard Bitcoin")


def choose_color(df, value_column=PRICE_COLUMN):
    """Escolhe verde para alta no periodo e vermelho para queda."""
    initial_price = df[value_column].iloc[0]
    final_price = df[value_column].iloc[-1]
    return POSITIVE_GREEN if final_price >= initial_price else NEGATIVE_RED


def _format_currency(value):
    if pd.isna(value):
        return ""
    return f"US$ {value:,.2f}"


def _format_percent(value, show_sign=True):
    if pd.isna(value):
        return "N/A"
    sign = "+" if show_sign and value >= 0 else ""
    return f"{sign}{value:.2f}%"


def _period_stats(df, value_column=PRICE_COLUMN):
    initial_price = df[value_column].iloc[0]
    current_price = df[value_column].iloc[-1]
    percent_change = ((current_price / initial_price) - 1) * 100

    return {
        "current": current_price,
        "max": df[value_column].max(),
        "min": df[value_column].min(),
        "percent_change": percent_change,
    }


def _title_text(config, stats):
    return (
        f"<b>{config['title']}</b><br>"
        f"<span style='font-size:14px;color:{MUTED}'>{config['subtitle']}</span><br>"
        f"<span style='font-size:13px;color:{INK}'>"
        f"Atual: <b>{_format_currency(stats['current'])}</b> &nbsp;|&nbsp; "
        f"Variacao: <b>{_format_percent(stats['percent_change'])}</b>"
        f"</span><br>"
        f"<span style='font-size:13px;color:{MUTED}'>"
        f"Maximo: {_format_currency(stats['max'])} &nbsp;|&nbsp; "
        f"Minimo: {_format_currency(stats['min'])}"
        f"</span>"
    )


def _range_selector(buttons):
    if not buttons:
        return None

    plotly_buttons = []
    for label, count, step in buttons:
        if step == "all":
            plotly_buttons.append({"label": label, "step": "all"})
            continue

        plotly_buttons.append(
            {
                "count": count,
                "label": label,
                "step": step,
                "stepmode": "backward",
            }
        )

    return {
        "bgcolor": "#F2F4F7",
        "activecolor": "#FFD7A3",
        "bordercolor": GRID,
        "borderwidth": 1,
        "buttons": plotly_buttons,
    }


def _price_annotations(df, stats, line_color):
    return [
        {
            "x": df["data"].iloc[-1],
            "y": stats["current"],
            "text": _format_currency(stats["current"]),
            "showarrow": True,
            "arrowhead": 2,
            "arrowcolor": line_color,
            "bgcolor": line_color,
            "bordercolor": PANEL,
            "borderwidth": 1,
            "font": {"color": "#FFFFFF", "size": 12},
            "ax": 28,
            "ay": -30,
        },
        {
            "xref": "paper",
            "yref": "paper",
            "x": 0,
            "y": -0.15,
            "showarrow": False,
            "align": "left",
            "text": "Fontes: CoinGecko API e Alternative.me. Base em USD.",
            "font": {"size": 11, "color": MUTED},
        },
    ]


def _current_price_shape(stats):
    return [
        {
            "type": "line",
            "xref": "paper",
            "x0": 0,
            "x1": 1,
            "y0": stats["current"],
            "y1": stats["current"],
            "line": {"width": 1, "dash": "dash", "color": "#98A2B3"},
            "opacity": 0.6,
        }
    ]


def _halving_shapes_and_annotations(df):
    shapes = []
    annotations = []
    min_date = df["data"].min()
    max_date = df["data"].max()

    for date_text, label in HALVING_DATES.items():
        event_date = pd.to_datetime(date_text)

        if event_date < min_date or event_date > max_date:
            continue

        shapes.append(
            {
                "type": "line",
                "xref": "x",
                "yref": "paper",
                "x0": event_date,
                "x1": event_date,
                "y0": 0,
                "y1": 1,
                "line": {"color": BITCOIN_ORANGE, "width": 1.5, "dash": "dot"},
            }
        )
        annotations.append(
            {
                "x": event_date,
                "y": 1,
                "xref": "x",
                "yref": "paper",
                "text": label,
                "showarrow": False,
                "yanchor": "bottom",
                "font": {"size": 11, "color": BITCOIN_ORANGE},
            }
        )

    return shapes, annotations


def _apply_base_layout(fig, height=650, top_margin=130):
    fig.update_layout(
        height=height,
        paper_bgcolor="#F8FAFC",
        plot_bgcolor=PANEL,
        font={"family": "Arial", "size": 13, "color": INK},
        hovermode="x unified",
        margin={"l": 72, "r": 44, "t": top_margin, "b": 74},
    )


def plot_interactive_trend(table_name="btc_1ano"):
    """
    Cria um dashboard interativo de preco do Bitcoin em USD.
    """
    df = get_data_from_db(table_name)

    if PRICE_COLUMN not in df.columns:
        raise ValueError(f"A tabela {table_name} precisa ter a coluna {PRICE_COLUMN}.")

    config = PERIOD_CONFIG.get(table_name, PERIOD_CONFIG["btc_1ano"])
    is_intraday = table_name == "btc_intraday"
    hover_label = "Hora" if is_intraday else "Data"
    stats = _period_stats(df)
    line_color = choose_color(df)
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df["data"],
            y=df[PRICE_COLUMN],
            mode="lines",
            name="Preco BTC (USD)",
            line={"color": line_color, "width": 3},
            fill="tozeroy",
            fillcolor="rgba(247, 147, 26, 0.12)",
            customdata=[_format_currency(value) for value in df[PRICE_COLUMN]],
            hovertemplate=(
                f"<b>{hover_label}:</b> %{{x|{config['hover_date']}}}"
                "<br><b>Preco:</b> %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    if config["moving_average"] and len(df) > config["moving_average"]:
        moving_average = df[PRICE_COLUMN].rolling(window=config["moving_average"]).mean()
        fig.add_trace(
            go.Scatter(
                x=df["data"],
                y=moving_average,
                mode="lines",
                name=f"Media movel {config['moving_average']}p",
                line={"color": "#475467", "width": 2, "dash": "dot"},
                customdata=[_format_currency(value) for value in moving_average],
                hovertemplate="<b>Media:</b> %{customdata}<extra></extra>",
            )
        )

    halving_shapes, halving_annotations = _halving_shapes_and_annotations(df)
    shapes = _current_price_shape(stats) + halving_shapes
    annotations = _price_annotations(df, stats, line_color) + halving_annotations

    fig.update_layout(
        title={
            "text": _title_text(config, stats),
            "x": 0.03,
            "xanchor": "left",
            "font": {"size": 24, "family": "Arial", "color": INK},
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(255, 255, 255, 0.7)",
        },
        annotations=annotations,
        shapes=shapes,
    )
    _apply_base_layout(fig, height=680, top_margin=150)

    fig.update_xaxes(
        title_text="Horario" if is_intraday else "Data",
        tickformat=config["x_tick"],
        showgrid=True,
        gridcolor=GRID,
        showline=True,
        linecolor="#D0D5DD",
        zeroline=False,
        rangeselector=_range_selector(config["range_buttons"]),
        rangeslider={"visible": not is_intraday, "thickness": 0.06},
    )
    fig.update_yaxes(
        title_text="Preco do Bitcoin (USD)",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        tickprefix="US$ ",
    )

    return fig


def plot_log_returns(table_name="btc_1ano"):
    """
    Cria grafico de barras de log-retornos do Bitcoin.
    """
    df = get_data_from_db(table_name)

    if LOG_RETURN_COLUMN not in df.columns:
        raise ValueError(f"A tabela {table_name} nao possui a coluna {LOG_RETURN_COLUMN}.")

    config = PERIOD_CONFIG.get(table_name, PERIOD_CONFIG["btc_1ano"])
    chart_df = df.dropna(subset=[LOG_RETURN_COLUMN]).copy()
    chart_df["return_percent"] = chart_df[LOG_RETURN_COLUMN] * 100
    colors = [POSITIVE_GREEN if value >= 0 else NEGATIVE_RED for value in chart_df["return_percent"]]

    fig = go.Figure(
        go.Bar(
            x=chart_df["data"],
            y=chart_df["return_percent"],
            name="Log-retorno",
            marker={"color": colors, "line": {"width": 0}},
            hovertemplate=(
                f"<b>Data:</b> %{{x|{config['hover_date']}}}"
                "<br><b>Log-retorno:</b> %{y:.2f}%"
                "<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title={
            "text": (
                "<b>Bitcoin - Log-retornos</b><br>"
                f"<span style='font-size:14px;color:{MUTED}'>"
                "Variacao percentual logaritmica em USD</span>"
            ),
            "x": 0.03,
            "xanchor": "left",
            "font": {"size": 24, "family": "Arial", "color": INK},
        },
        showlegend=False,
    )
    _apply_base_layout(fig, height=620, top_margin=108)

    fig.update_xaxes(
        title_text="Data",
        tickformat=config["x_tick"],
        showgrid=True,
        gridcolor=GRID,
        showline=True,
        linecolor="#D0D5DD",
        rangeselector=_range_selector(config["range_buttons"]),
        rangeslider={"visible": True, "thickness": 0.06},
    )
    fig.update_yaxes(
        title_text="Log-retorno (%)",
        ticksuffix="%",
        showgrid=True,
        gridcolor=GRID,
        zeroline=True,
        zerolinecolor="#98A2B3",
        zerolinewidth=1,
    )

    return fig


def plot_fear_and_greed(table_name="btc_macro_10anos"):
    """
    Cria painel combinado de preco e Fear & Greed Index.
    """
    df = get_data_from_db(table_name)

    if "fng_value" not in df.columns:
        raise ValueError(f"A tabela {table_name} nao possui dados de Fear & Greed.")

    chart_df = df.dropna(subset=["fng_value"]).copy()

    if chart_df.empty:
        raise ValueError("Nao ha valores validos de Fear & Greed para exibir.")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=chart_df["data"],
            y=chart_df[PRICE_COLUMN],
            mode="lines",
            name="Preco BTC",
            line={"color": BITCOIN_ORANGE, "width": 2.5},
            hovertemplate="<b>Preco:</b> %{customdata}<extra></extra>",
            customdata=[_format_currency(value) for value in chart_df[PRICE_COLUMN]],
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=chart_df["data"],
            y=chart_df["fng_value"],
            mode="lines",
            name="Fear & Greed",
            line={"color": "#2563EB", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.10)",
            hovertemplate="<b>F&G:</b> %{y}<br>%{text}<extra></extra>",
            text=chart_df["fng_classification"],
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title={
            "text": (
                "<b>Bitcoin - Fear & Greed</b><br>"
                f"<span style='font-size:14px;color:{MUTED}'>"
                "Sentimento de mercado comparado ao preco em USD</span>"
            ),
            "x": 0.03,
            "xanchor": "left",
            "font": {"size": 24, "family": "Arial", "color": INK},
        },
        legend={"orientation": "h", "y": 1.02, "x": 1, "xanchor": "right"},
    )
    _apply_base_layout(fig, height=680, top_margin=120)

    fig.update_xaxes(
        title_text="Data",
        tickformat="%Y",
        showgrid=True,
        gridcolor=GRID,
        rangeselector=_range_selector(PERIOD_CONFIG["btc_macro_10anos"]["range_buttons"]),
        rangeslider={"visible": True, "thickness": 0.06},
    )
    fig.update_yaxes(title_text="Preco BTC (USD)", tickprefix="US$ ", secondary_y=False)
    fig.update_yaxes(title_text="Fear & Greed", range=[0, 100], secondary_y=True)

    return fig


def plot_mayer_multiple(table_name="btc_macro_10anos"):
    """
    Cria grafico do Mayer Multiple.
    """
    df = get_data_from_db(table_name)

    if "mayer_multiple" not in df.columns:
        raise ValueError(f"A tabela {table_name} nao possui a coluna mayer_multiple.")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["data"],
            y=df["mayer_multiple"],
            mode="lines",
            name="Mayer Multiple",
            line={"color": BITCOIN_ORANGE, "width": 2.5},
            hovertemplate="<b>Mayer:</b> %{y:.2f}<extra></extra>",
        )
    )
    fig.add_hline(y=1, line={"color": POSITIVE_GREEN, "dash": "dot"}, annotation_text="Preco abaixo/proximo da MM200")
    fig.add_hline(y=2.4, line={"color": NEGATIVE_RED, "dash": "dot"}, annotation_text="Zona historicamente aquecida")
    fig.update_layout(
        title={
            "text": (
                "<b>Bitcoin - Mayer Multiple</b><br>"
                f"<span style='font-size:14px;color:{MUTED}'>"
                "Preco dividido pela media movel de 200 dias</span>"
            ),
            "x": 0.03,
            "xanchor": "left",
            "font": {"size": 24, "family": "Arial", "color": INK},
        },
        showlegend=False,
    )
    _apply_base_layout(fig, height=620, top_margin=108)

    fig.update_xaxes(
        title_text="Data",
        tickformat="%Y",
        showgrid=True,
        gridcolor=GRID,
        rangeselector=_range_selector(PERIOD_CONFIG["btc_macro_10anos"]["range_buttons"]),
        rangeslider={"visible": True, "thickness": 0.06},
    )
    fig.update_yaxes(title_text="Mayer Multiple", showgrid=True, gridcolor=GRID, zeroline=False)

    return fig


def plot_halving_analysis():
    """
    Cria painel com countdown e retornos ao redor dos halvings anteriores.
    """
    countdown = get_data_from_db("btc_halving_countdown")
    analysis = get_data_from_db("btc_halving_analysis")

    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "indicator"}, {"type": "bar"}]],
        column_widths=[0.38, 0.62],
        subplot_titles=("Proximo halving", "Retornos historicos de 90 dias"),
    )

    countdown_row = countdown.iloc[-1]
    fig.add_trace(
        go.Indicator(
            mode="number+gauge",
            value=float(countdown_row["cycle_progress_percentage"]),
            number={"suffix": "%", "font": {"size": 42}},
            title={
                "text": (
                    f"{int(countdown_row['days_remaining'])} dias restantes<br>"
                    f"<span style='font-size:13px;color:{MUTED}'>"
                    f"Estimativa: {countdown_row['next_halving_date']}</span>"
                )
            },
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": BITCOIN_ORANGE},
                "bgcolor": "#F2F4F7",
                "bordercolor": GRID,
            },
        ),
        row=1,
        col=1,
    )

    if not analysis.empty:
        fig.add_trace(
            go.Bar(
                x=analysis["evento"],
                y=analysis["retorno_90d_antes_pct"],
                name="90d antes",
                marker_color="#2563EB",
                hovertemplate="<b>%{x}</b><br>90d antes: %{y:.2f}%<extra></extra>",
            ),
            row=1,
            col=2,
        )
        fig.add_trace(
            go.Bar(
                x=analysis["evento"],
                y=analysis["retorno_90d_depois_pct"],
                name="90d depois",
                marker_color=BITCOIN_ORANGE,
                hovertemplate="<b>%{x}</b><br>90d depois: %{y:.2f}%<extra></extra>",
            ),
            row=1,
            col=2,
        )

    fig.update_layout(
        title={
            "text": (
                "<b>Bitcoin - Halving</b><br>"
                f"<span style='font-size:14px;color:{MUTED}'>"
                "Progresso do ciclo atual e leitura dos ciclos passados</span>"
            ),
            "x": 0.03,
            "xanchor": "left",
            "font": {"size": 24, "family": "Arial", "color": INK},
        },
        barmode="group",
        legend={"orientation": "h", "y": 1.02, "x": 1, "xanchor": "right"},
    )
    _apply_base_layout(fig, height=560, top_margin=120)
    fig.update_yaxes(title_text="Retorno (%)", ticksuffix="%", row=1, col=2)

    return fig


def plot_principal_dashboard():
    """
    Dashboard Executivo Quantitativo.
    Apresenta KPIs macro, Ação de Preço (1 Ano com zoom para 1M/3M) e Volatilidade.
    """
    # 1. Base ampliada para 1 Ano para permitir zoom dinâmico
    df_base = get_data_from_db("btc_1ano")
    df_macro = get_data_from_db("btc_macro_10anos")

    # --- EXTRAÇÃO DE MÉTRICAS ATUAIS ---
    current_price = df_base[PRICE_COLUMN].iloc[-1]
    
    current_mayer = df_macro["mayer_multiple"].dropna().iloc[-1]
    current_zscore = df_macro["z_score_200"].dropna().iloc[-1]
    current_drawdown = df_macro["drawdown"].dropna().iloc[-1]
    current_fng = df_macro["fng_value"].dropna().iloc[-1]
    fng_class = df_macro["fng_classification"].dropna().iloc[-1]

    # --- CONFIGURAÇÃO DO GRID ---
    fig = make_subplots(
        rows=3, cols=5,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
            [{"type": "xy", "colspan": 5}, None, None, None, None],
            [{"type": "xy", "colspan": 5}, None, None, None, None]
        ],
        row_heights=[0.18, 0.60, 0.22],
        vertical_spacing=0.08,
        subplot_titles=("", "", "", "", "", "Ação de Preço (Selecione o Período)", "Volatilidade Diária (Log-Retornos)")
    )

    # ==========================================
    # ANDAR 1: KPIs (Termômetros do Mercado)
    # ==========================================

    # 1. Preço Atual [Trace 0]
    fig.add_trace(go.Indicator(
        mode="number", value=current_price,
        number={"prefix": "US$ ", "valueformat": ",.0f", "font": {"size": 28, "color": INK, "family": "Arial Black"}},
        title={"text": "PREÇO ATUAL", "font": {"size": 11, "color": MUTED, "family": "Arial"}}
    ), row=1, col=1)

    # 2. Múltiplo de Mayer [Trace 1]
    mayer_color = POSITIVE_GREEN if current_mayer < 1.0 else (NEGATIVE_RED if current_mayer > 2.4 else INK)
    fig.add_trace(go.Indicator(
        mode="number", value=current_mayer,
        number={"valueformat": ".2f", "font": {"size": 28, "color": mayer_color, "family": "Arial Black"}},
        title={"text": "MÚLTIPLO DE MAYER", "font": {"size": 11, "color": MUTED}}
    ), row=1, col=2)

    # 3. Z-Score (MM200) [Trace 2]
    zscore_color = NEGATIVE_RED if current_zscore > 2 else (POSITIVE_GREEN if current_zscore < -2 else INK)
    fig.add_trace(go.Indicator(
        mode="number", value=current_zscore,
        number={"valueformat": "+.2f", "font": {"size": 28, "color": zscore_color, "family": "Arial Black"}},
        title={"text": "Z-SCORE (MM200)", "font": {"size": 11, "color": MUTED}}
    ), row=1, col=3)

    # 4. Drawdown [Trace 3]
    drawdown_color = POSITIVE_GREEN if current_drawdown >= -0.15 else NEGATIVE_RED
    fig.add_trace(go.Indicator(
        mode="number", value=current_drawdown,
        number={"valueformat": ".1%", "font": {"size": 28, "color": drawdown_color, "family": "Arial Black"}},
        title={"text": "DRAWDOWN ATUAL", "font": {"size": 11, "color": MUTED}}
    ), row=1, col=4)

    # 5. Fear & Greed [Trace 4]
    fng_color = NEGATIVE_RED if current_fng < 40 else (POSITIVE_GREEN if current_fng > 70 else INK)
    fig.add_trace(go.Indicator(
        mode="number", value=current_fng,
        number={"font": {"size": 28, "color": fng_color, "family": "Arial Black"}},
        title={"text": f"FEAR & GREED<br><span style='font-size:10px;color:{MUTED}'>{fng_class.upper()}</span>", "font": {"size": 11, "color": MUTED}}
    ), row=1, col=5)

    # ==========================================
    # ANDAR 2: TENDÊNCIA (Preço e Médias)
    # ==========================================

    # Linha do Preço [Trace 5]
    line_color = choose_color(df_base)
    fig.add_trace(go.Scatter(
        x=df_base["data"], y=df_base[PRICE_COLUMN],
        mode="lines", name="Preço BTC",
        line={"color": line_color, "width": 2.5},
        fill="tozeroy", fillcolor="rgba(247, 147, 26, 0.05)",
        hovertemplate="<b>%{x|%d/%m/%Y}</b><br>US$ %{y:,.2f}<extra></extra>"
    ), row=2, col=1)

    # Calcula as médias no macro para não ter buracos no inicio do df_base
    df_macro_tail = df_macro.tail(len(df_base)).copy()
    mm21 = df_macro[PRICE_COLUMN].rolling(window=21).mean().tail(len(df_base))
    mm200 = df_macro[PRICE_COLUMN].rolling(window=200).mean().tail(len(df_base))

    # MM21 [Trace 6]
    fig.add_trace(go.Scatter(
        x=df_base["data"], y=mm21,
        mode="lines", name="MM 21", visible=True,
        line={"color": "#2563EB", "width": 2}, # Azul corporativo
        hovertemplate="<b>MM21:</b> US$ %{y:,.2f}<extra></extra>"
    ), row=2, col=1)

    # MM200 [Trace 7]
    fig.add_trace(go.Scatter(
        x=df_base["data"], y=mm200,
        mode="lines", name="MM 200", visible=False,
        line={"color": "#9333EA", "width": 2}, # Roxo institucional
        hovertemplate="<b>MM200:</b> US$ %{y:,.2f}<extra></extra>"
    ), row=2, col=1)

    # ==========================================
    # ANDAR 3: VOLATILIDADE (Log-Retornos)
    # ==========================================
    log_returns_pct = df_base[LOG_RETURN_COLUMN] * 100
    bar_colors = [POSITIVE_GREEN if val >= 0 else NEGATIVE_RED for val in log_returns_pct]
    
    # Log-Retornos [Trace 8]
    fig.add_trace(go.Bar(
        x=df_base["data"], y=log_returns_pct,
        name="Log-Retorno", marker={"color": bar_colors, "line": {"width": 0}},
        hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Retorno: %{y:.2f}%<extra></extra>"
    ), row=3, col=1)

    # --- FORMATAÇÃO VISUAL E MENUS ---
    fig.update_layout(
        title={
            "text": "<b>DASHBOARD QUANTITATIVO - BITCOIN</b><br><span style='font-size:13px;color:#667085'>Consolidação Analítica de Tendência, Risco e Volatilidade</span>",
            "x": 0.04, "y": 0.96, "xanchor": "left", "font": {"size": 22, "family": "Arial", "color": INK},
        },
        height=900, paper_bgcolor="#F8FAFC", plot_bgcolor=PANEL,
        font={"family": "Arial", "size": 12, "color": INK},
        hovermode="x unified", showlegend=False,
        margin={"l": 60, "r": 60, "t": 130, "b": 60},
        
        # Botão seletor de Médias Móveis (Top Direito)
        updatemenus=[{
            "type": "buttons", "direction": "left", "x": 1.0, "y": 1.05, "xanchor": "right", "yanchor": "bottom",
            "showactive": True, "bgcolor": "#FFFFFF", "bordercolor": GRID,
            "buttons": [
                {"label": "📊 MM 21 (Curto)", "method": "update", "args": [{"visible": [True]*6 + [True, False, True]}]},
                {"label": "📈 MM 200 (Longo)", "method": "update", "args": [{"visible": [True]*6 + [False, True, True]}]},
            ],
        }],
    )

    # Botões Seletores de Tempo (Timeframes) no eixo X
    time_buttons = [
        dict(count=1, label="1M", step="month", stepmode="backward"),
        dict(count=3, label="3M", step="month", stepmode="backward"),
        dict(count=6, label="6M", step="month", stepmode="backward"),
        dict(step="all", label="1A (Tudo)")
    ]

    fig.update_xaxes(
        showgrid=True, gridcolor=GRID, row=2, col=1,
        rangeselector=dict(buttons=time_buttons, bgcolor="#F2F4F7", activecolor="#E4E7EC", font={"color": INK})
    )
    fig.update_yaxes(title_text="Preço (USD)", tickprefix="US$ ", showgrid=True, gridcolor=GRID, zeroline=False, row=2, col=1)
    
    fig.update_xaxes(showgrid=True, gridcolor=GRID, row=3, col=1)
    fig.update_yaxes(title_text="Retorno (%)", ticksuffix="%", showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#98A2B3", zerolinewidth=1.5, row=3, col=1)

    return fig