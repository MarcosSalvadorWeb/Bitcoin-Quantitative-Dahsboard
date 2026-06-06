import os
from sqlalchemy import create_engine

def save_all_tables_to_sqlite(dict_dataframes, db_path="database/bitcoin.db"):
    """
    Salva todas as tabelas do pipeline no banco SQLite local,
    garantindo a criação das pastas necessárias.
    """
    # 1. Boa prática de engenharia: garante que a pasta 'database' existe antes de tentar gravar o arquivo
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        print(f"📁 Diretório '{db_dir}' criado com sucesso.")

    # 2. Conecta ao motor do SQLite
    engine = create_engine(f"sqlite:///{db_path}")

    for table_name, dataframe in dict_dataframes.items():
        if dataframe.empty:
            print(f"⚠️ Aviso: Tabela '{table_name}' está vazia, mas será salva com o schema disponível.")

        dataframe.to_sql(table_name, con=engine, if_exists="replace", index=False)
        print(f"📥 Tabela '{table_name}' ({len(dataframe)} linhas) salva com sucesso no SQLite!")
