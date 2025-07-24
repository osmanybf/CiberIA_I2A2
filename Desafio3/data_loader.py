# data_loader.py
import pandas as pd
import os

# Caminhos dos arquivos CSV
CSV_DIR = "csv"
NF_CABECALHO_CSV = os.path.join(CSV_DIR, "202401_NFs_Cabecalho.csv")
NF_ITENS_CSV = os.path.join(CSV_DIR, "202401_NFs_Itens.csv")

def carregar_csvs():
    """
    Carrega os arquivos CSV de cabeçalho e itens em DataFrames Pandas.
    Retorna uma tupla (df_cabecalho, df_itens) ou (None, None) em caso de erro.
    """
    try:
        df_cabecalho = pd.read_csv(NF_CABECALHO_CSV, decimal='.', sep=',')
        df_itens = pd.read_csv(NF_ITENS_CSV, decimal='.', sep=',')

        print(f"Arquivos CSV carregados com sucesso de '{CSV_DIR}/'.")
        # Retornamos os DataFrames
        return df_cabecalho, df_itens
    except FileNotFoundError:
        print(f"Erro: Certifique-se de que '{NF_CABECALHO_CSV}' e '{NF_ITENS_CSV}' estão no diretório '{CSV_DIR}'.")
        return None, None
    except Exception as e:
        print(f"Erro ao carregar os CSVs: {e}")
        return None, None

if __name__ == "__main__":
    df_c, df_i = carregar_csvs()
    if df_c is not None:
        print("\nPrimeiras 5 linhas do Cabeçalho:")
        print(df_c.head())
    if df_i is not None:
        print("\nPrimeiras 5 linhas dos Itens:")
        print(df_i.head())