import sqlite3

from analysis import charts as ch
from etl import extract as ext
from etl import load as ld
from etl import transform as tf
from etl import rl 


HISTORICAL_DASHBOARDS = {
    "1": ("btc_1semana", "1 Semana"),
    "2": ("btc_1mes", "1 Mes"),
    "3": ("btc_1ano", "1 Ano"),
    "4": ("btc_macro_10anos", "Macro 10 Anos"),
}

# Reorganizado para dar destaque ao Dashboard Principal
MENU_OPTIONS = {
    "1": ("Dashboard Principal", "principal_dashboard"),
    "2": ("Valor atual", "current_price"),
    "3": ("Dashboard de preco", "price_dashboard"),
    "4": ("Intraday", "intraday"),
    "5": ("Log-retornos", "log_returns"),
    "6": ("Mayer Multiple", "mayer_multiple"),
    "7": ("Relatório", "relatório"),
    "8": ("Halving", "halving"),
    "9": ("Atualizar banco novamente", "refresh"),
    "0": ("Sair", "exit"),
}


def run_pipeline():
    """
    Executa o pipeline ETL completo e salva as tabelas no SQLite.
    """
    print("\nAtualizando dados do Bitcoin...")

    raw_prices = ext.bit_history(3650)
    raw_fng = ext.fetch_fear_and_greed(3650)
    raw_intraday = ext.btc_intraday()

    if raw_prices is None or raw_intraday is None:
        if has_cached_data():
            print("\nAtualizacao falhou. Mantendo os ultimos dados validos do banco local.")
            return {}

        print("\nFalha critica ao buscar dados essenciais de preco e nenhum cache local foi encontrado.")
        return None

    if raw_fng is None:
        print("\nAviso: Fear & Greed nao foi coletado. O restante do pipeline continuara.")

    tables = tf.clean_data(raw_prices, raw_fng, raw_intraday)
    ld.save_all_tables_to_sqlite(tables)

    print("\nBanco local atualizado com sucesso.")
    return tables


def has_cached_data(db_path="database/bitcoin.db"):
    """
    Verifica se existem dados locais suficientes para manter o dashboard ativo.
    """
    required_tables = {"btc_1ano", "btc_intraday"}

    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
    except sqlite3.Error:
        return False

    available_tables = {row[0] for row in rows}
    return required_tables.issubset(available_tables)


def open_principal_dashboard():
    """
    Abre o Dashboard Principal consolidado com KPIs e tendencia.
    """
    print_section("Dashboard Principal Executivo")
    print("Gerando painel mestre. Isso pode levar alguns segundos...")
    ch.plot_principal_dashboard().show()


def show_actual_price():
    """
    Mostra o valor atual do Bitcoin em USD.
    """
    print_section("Bitcoin atual")
    btc_usd = ext.actual_value()

    if btc_usd is None:
        print("\nFalha ao buscar o valor atual.")
        return

    print(f"\nUSD: US$ {btc_usd:,.2f}")


def open_dashboard():
    """
    Abre um dashboard historico escolhido pelo usuario.
    """
    table_name, label = choose_dashboard("Escolha um periodo de preco")

    if not table_name:
        return

    print(f"\nAbrindo dashboard: {label}")
    ch.plot_interactive_trend(table_name).show()


def open_intraday():
    """
    Abre o dashboard intraday.
    """
    print_section("Intraday")
    ch.plot_interactive_trend("btc_intraday").show()


def open_log_returns():
    """
    Abre o grafico de log-retornos para um periodo historico.
    """
    table_name, label = choose_dashboard("Escolha um periodo para log-retornos")

    if not table_name:
        return

    if table_name == "btc_intraday":
        print("\nIntraday nao possui log-retornos calculados.")
        return

    print(f"\nAbrindo log-retornos: {label}")
    ch.plot_log_returns(table_name).show()


def relatorio():
    """
    Envia um Relatório no Email 
    """
    print("Enviando Relatório")
    dados_mercado = rl.extrair_contexto()
    html = rl.gerar_analise_ia(dados_mercado)
    rl.disparar_email(html, dados_mercado)


def open_mayer_multiple():
    """
    Abre o painel de Mayer Multiple.
    """
    print_section("Mayer Multiple")
    ch.plot_mayer_multiple("btc_macro_10anos").show()


def open_halving():
    """
    Abre o painel de halving.
    """
    print_section("Halving")
    ch.plot_halving_analysis().show()


def choose_dashboard(title):
    """
    Mostra um submenu de periodos e retorna a tabela escolhida.
    """
    print_section(title)

    for option, (_, label) in HISTORICAL_DASHBOARDS.items():
        print(f"{option} -> {label}")

    option = input("\nDigite a opcao: ").strip()

    if option not in HISTORICAL_DASHBOARDS:
        print("\nOpcao invalida.")
        return None, None

    return HISTORICAL_DASHBOARDS[option]


def print_section(title):
    print("\n" + "=" * 42)
    print(title.upper())
    print("=" * 42)


def print_main_menu():
    print_section("Bitcoin Analytics")

    for option, (label, _) in MENU_OPTIONS.items():
        print(f"{option} -> {label}")


def dispatch(action):
    # Dicionario atualizado com a nova acao principal
    actions = {
        "principal_dashboard": open_principal_dashboard,
        "current_price": show_actual_price,
        "price_dashboard": open_dashboard,
        "intraday": open_intraday,
        "log_returns": open_log_returns,
        "mayer_multiple": open_mayer_multiple,
        "relatório": relatorio,
        "halving": open_halving,
        "refresh": run_pipeline,
    }

    handler = actions.get(action)

    if handler:
        handler()


def main():
    """
    Executa o fluxo principal do Bitcoin Analytics.
    """
    if run_pipeline() is None:
        return

    while True:
        print_main_menu()
        choice = input("\nDigite a opcao: ").strip()

        if choice not in MENU_OPTIONS:
            print("\nOpcao invalida.")
            continue

        _, action = MENU_OPTIONS[choice]

        if action == "exit":
            print("\nEncerrado.")
            break

        dispatch(action)


if __name__ == "__main__":
    main()

    