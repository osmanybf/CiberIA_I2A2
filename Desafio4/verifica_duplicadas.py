import pandas as pd

def verificar_duplicadas(path_csv):
    df = pd.read_csv(path_csv)
    duplicadas = df[df.duplicated(subset=['matricula'], keep=False)]
    if duplicadas.empty:
        print('Não há matrículas duplicadas na base consolidada.')
    else:
        print('Matrículas duplicadas encontradas:')
        print(duplicadas[['matricula']])
        print(f'Total de duplicadas: {duplicadas["matricula"].nunique()}')

if __name__ == "__main__":
    verificar_duplicadas('saida/base_consolidada.csv')
