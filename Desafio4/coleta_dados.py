# Importa as classes necessárias da LangChain e outras bibliotecas
from langchain.agents import tool, AgentExecutor
from langchain.agents import initialize_agent
from langchain_google_genai import GoogleGenerativeAI
import pandas as pd
import os
from datetime import datetime

#Consolidação dos Dados dos Colaboradores

# Define o LLM que o agente irá usar
# Substitua pela sua chave de API
llm = GoogleGenerativeAI(model="gemini-2.5-flash", api_key="put-your-api-key-here")

@tool
def ler_e_processar_csv(file_path: str) -> str:
    """
    Ferramenta para ler um arquivo CSV, processá-lo e retornar seus dados em formato de string.
    
    Args:
        file_path (str): O caminho para o arquivo CSV a ser lido.

    Returns:
        str: Uma string contendo os dados do arquivo CSV em formato JSON.
    """
    try:
        df = pd.read_csv(file_path)
        return df.to_json(orient='records')
    except FileNotFoundError:
        return f"Erro: Arquivo não encontrado no caminho: {file_path}"
    except Exception as e:
        return f"Erro ao processar o arquivo: {e}"

# Lista das ferramentas disponíveis para o agente
tools = [ler_e_processar_csv]

# Cria o agente, que usa o LLM para decidir qual ferramenta chamar
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=False
)

def unificar_dados(dataframes: list) -> pd.DataFrame:
    """
    Função utilitária para unificar uma lista de DataFrames com base na matrícula.
    
    Args:
        dataframes (list): Uma lista de DataFrames do pandas.

    Returns:
        pd.DataFrame: O DataFrame unificado.
    """
    # Inicia com o primeiro DataFrame como base
    base_consolidada = dataframes[0]
    
    # Faz um merge com os demais DataFrames
    for df in dataframes[1:]:
        # O 'how' left garante que não perdemos nenhum colaborador da base principal
        base_consolidada = pd.merge(base_consolidada, df, on='matricula', how='left')
    
    return base_consolidada

def validar_e_corrigir_dados(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica as validações e correções necessárias na base de dados consolidada.
    
    Args:
        df (pd.DataFrame): O DataFrame consolidado.
        
    Returns:
        pd.DataFrame: O DataFrame validado e corrigido.
    """
    print("Iniciando a fase de validação e correção de dados...")
    
    # Fase 1: Exclusão de colaboradores inelegíveis
    # A base deve ter apenas colaboradores elegíveis ao benefício
    df_filtrado = df[df['elegivel_beneficio'] == 'Sim'].copy()

    # Exclui os colaboradores que estão em licença maternidade, afastados em geral, etc.
    df_filtrado = df_filtrado[df_filtrado['DESC. SITUACAO_principal'] != 'Licença Maternidade']
    
    print(f"✔ {len(df) - len(df_filtrado)} colaboradores inelegíveis excluídos (Diretores, Estagiários, Aprendizes, Afastados).")
    
    # Fase 2: Tratamento de datas e desligamentos
    # Converte colunas de data para o tipo datetime
    df_filtrado['Admissão'] = pd.to_datetime(df_filtrado['Admissão'], format='%m/%d/%Y', errors='coerce')
    df_filtrado['DATA DEMISSÃO'] = pd.to_datetime(df_filtrado['DATA DEMISSÃO'], format='%m/%d/%Y', errors='coerce')
    
    # Aplica a regra de desligamento (comunicado até o dia 15 exclui do pagamento)
    # Apenas para colaboradores com DATA DEMISSÃO válida e COMUNICADO DE DESLIGAMENTO 'OK'
    def deve_receber_beneficio(row):
        if pd.notna(row['DATA DEMISSÃO']) and row['COMUNICADO DE DESLIGAMENTO'] == 'OK':
            if row['DATA DEMISSÃO'].day <= 15:
                return False
        return True

    df_filtrado['deve_receber_beneficio'] = df_filtrado.apply(deve_receber_beneficio, axis=1)
    df_filtrado = df_filtrado[df_filtrado['deve_receber_beneficio'] == True]
    
    print("✔ Regras de desligamento aplicadas.")
    
    # Fase 3: Ajuste de dias úteis com base nas condições de férias/admissão
    df_filtrado['DIAS A RECEBER'] = df_filtrado['dias_uteis']
    
    # Ajusta para admissões no meio do mês
    df_filtrado.loc[df_filtrado['Admissão'].notna(), 'DIAS A RECEBER'] = df_filtrado.apply(
        lambda row: row['dias_uteis'] - row['Admissão'].day + 1 if row['Admissão'].day > 1 else row['dias_uteis'], axis=1
    )
    
    # Ajusta para desligamentos depois do dia 15
    df_filtrado.loc[(df_filtrado['DATA DEMISSÃO'].notna()) & (df_filtrado['DATA DEMISSÃO'].dt.day > 15), 'DIAS A RECEBER'] = df_filtrado.apply(
        lambda row: row['DATA DEMISSÃO'].day if row['DATA DEMISSÃO'].day > 15 else row['DIAS A RECEBER'], axis=1
    )
    
    # Lógica de férias: se a quantidade for menor que 30, subtrai do total de dias a receber. Se for 30 ou mais, o valor é zero.
    df_filtrado.loc[(df_filtrado['DIAS DE FÉRIAS'].notna()) & (df_filtrado['DIAS DE FÉRIAS'] < 30), 'DIAS A RECEBER'] = df_filtrado.apply(
        lambda row: row['DIAS A RECEBER'] - row['DIAS DE FÉRIAS'], axis=1
    )
    df_filtrado.loc[(df_filtrado['DIAS DE FÉRIAS'].notna()) & (df_filtrado['DIAS DE FÉRIAS'] >= 30), 'DIAS A RECEBER'] = 0
    
    print("✔ Cálculo de dias úteis ajustado para admissões, desligamentos e férias.")

    return df_filtrado

def coletar_e_unificar_dados():
    """
    Orquestra a coleta de todos os arquivos CSV e a unificação dos dados.
    """
    directory_path = 'dados'
    
    files_to_process = [
        '1.ativos.csv', 
        '2.ferias.csv', 
        '3.desligados.csv', 
        '4.admissao_abril.csv', 
        '5.base_sindicato_x_valor.csv', 
        '6.dias_uteis.csv',
        'afastamentos.csv',
        'aprendiz.csv',
        'estagio.csv'
    ]

    # Verifica se o diretório de dados existe
    if not os.path.exists(directory_path):
        print(f"Erro: O diretório '{directory_path}' não foi encontrado.")
        return
    
    # Verifica se todos os arquivos necessários estão no diretório
    for filename in files_to_process:
        file_path = os.path.join(directory_path, filename)
        if not os.path.exists(file_path):
            print(f"Erro: Arquivo '{filename}' não encontrado em '{directory_path}'.")
            return
    
    print(f"Iniciando a leitura dos arquivos no diretório '{directory_path}'...")
    
    # Fase 1: Leitura dos arquivos
    ativos = pd.read_csv(os.path.join(directory_path, '1.ativos.csv'), sep=';')
    ferias = pd.read_csv(os.path.join(directory_path, '2.ferias.csv'), sep=';')
    desligados = pd.read_csv(os.path.join(directory_path, '3.desligados.csv'), sep=';')
    admissao = pd.read_csv(os.path.join(directory_path, '4.admissao_abril.csv'), sep=';')
    sindicato_valor = pd.read_csv(os.path.join(directory_path, '5.base_sindicato_x_valor.csv'), sep=',')
    dias_uteis = pd.read_csv(os.path.join(directory_path, '6.dias_uteis.csv'), sep=';', header=1)
    afastamentos = pd.read_csv(os.path.join(directory_path, 'afastamentos.csv'), sep=';')
    aprendiz = pd.read_csv(os.path.join(directory_path, 'aprendiz.csv'), sep=';')
    estagio = pd.read_csv(os.path.join(directory_path, 'estagio.csv'), sep=';')
    
    print("✔ Todos os arquivos lidos com sucesso.")

    # Fase 2: Padronização dos nomes de coluna e tipos de dados
    ativos.columns = [col.strip() for col in ativos.columns]
    ferias.columns = [col.strip() for col in ferias.columns]
    desligados.columns = [col.strip() for col in desligados.columns]
    admissao.columns = [col.strip() for col in admissao.columns]
    afastamentos.columns = [col.strip() for col in afastamentos.columns]
    aprendiz.columns = [col.strip() for col in aprendiz.columns]
    estagio.columns = [col.strip() for col in estagio.columns]

    # Renomeia as colunas de matrícula para 'matricula'
    ativos.rename(columns={"MATRICULA": "matricula", "Sindicato": "sindicato"}, inplace=True)
    ferias.rename(columns={"MATRICULA": "matricula"}, inplace=True)
    desligados.rename(columns={"MATRICULA": "matricula"}, inplace=True)
    admissao.rename(columns={"MATRICULA": "matricula"}, inplace=True)
    afastamentos.rename(columns={"MATRICULA": "matricula"}, inplace=True)
    aprendiz.rename(columns={"MATRICULA": "matricula"}, inplace=True)
    estagio.rename(columns={"MATRICULA": "matricula"}, inplace=True)

    # Padroniza tipo da coluna matricula para string para facilitar o merge
    ativos["matricula"] = ativos["matricula"].astype(str).str.strip()
    ferias["matricula"] = ferias["matricula"].astype(str).str.strip()
    desligados["matricula"] = desligados["matricula"].astype(str).str.strip()
    admissao["matricula"] = admissao["matricula"].astype(str).str.strip()
    afastamentos["matricula"] = afastamentos["matricula"].astype(str).str.strip()
    aprendiz["matricula"] = aprendiz["matricula"].astype(str).str.strip()
    estagio["matricula"] = estagio["matricula"].astype(str).str.strip()
    
    # Renomeia e padroniza colunas dos arquivos de sindicato/dias úteis
    sindicato_valor.rename(columns={sindicato_valor.columns[0]: "estado", sindicato_valor.columns[1]: "valor_sindicato"}, inplace=True)
    dias_uteis.rename(columns={dias_uteis.columns[0]: "sindicato_dias", dias_uteis.columns[1]: "dias_uteis"}, inplace=True)

    # Fase 3: Merge dos DataFrames principais (outer join para garantir todas as matrículas)
    df_merged = pd.merge(ativos, ferias[["matricula", "DIAS DE FÉRIAS"]], on="matricula", how="outer")
    df_merged = pd.merge(df_merged, desligados[["matricula", "DATA DEMISSÃO", "COMUNICADO DE DESLIGAMENTO"]], on="matricula", how="outer")
    df_merged = pd.merge(df_merged, admissao[["matricula", "Admissão", "cargo_admissao"]], on="matricula", how="outer")

    # Fase 4: Integração de exclusões e marcação de elegibilidade
    # Inicialmente, todos são considerados elegíveis
    df_merged['elegivel_beneficio'] = 'Sim'
    
    # Adiciona a informação de afastamentos e atualiza a elegibilidade
    df_merged = pd.merge(df_merged, afastamentos[["matricula", "DESC. SITUACAO"]], on="matricula", how="left", suffixes=('_principal', '_afastamento'))
    df_merged.loc[df_merged['DESC. SITUACAO_afastamento'].notna(), 'elegivel_beneficio'] = 'Não'

    # Cria uma flag para aprendizes e estagiários para evitar o KeyError
    aprendiz['is_aprendiz'] = 'Não'
    estagio['is_estagio'] = 'Não'

    # Adiciona a informação de aprendizes e estagiários
    df_merged = pd.merge(df_merged, aprendiz[["matricula", "is_aprendiz"]], on="matricula", how="left")
    df_merged.loc[df_merged['is_aprendiz'] == 'Não', 'elegivel_beneficio'] = 'Não'

    df_merged = pd.merge(df_merged, estagio[["matricula", "is_estagio"]], on="matricula", how="left")
    df_merged.loc[df_merged['is_estagio'] == 'Não', 'elegivel_beneficio'] = 'Não'

    # Remove colunas auxiliares
    df_merged.drop(columns=['is_aprendiz', 'is_estagio'], inplace=True)

    # Fase 5: Integração do valor do sindicato
    # Extrai o estado do sindicato do colaborador
    def extrair_estado(sindicato_nome):
        if "SÃO PAULO" in str(sindicato_nome).upper():
            return "São Paulo"
        elif "RIO GRANDE DO SUL" in str(sindicato_nome).upper():
            return "Rio Grande do Sul"
        elif "PARANÁ" in str(sindicato_nome).upper():
            return "Paraná"
        elif "RIO DE JANEIRO" in str(sindicato_nome).upper():
            return "Rio de Janeiro"
        return None

    df_merged["estado_sindicato"] = df_merged["sindicato"].apply(extrair_estado)
    df_merged = pd.merge(df_merged, sindicato_valor, left_on="estado_sindicato", right_on="estado", how="left")
    df_merged.drop(columns=["estado"], inplace=True)

    # Fase 6: Integração dos dias úteis
    df_merged = pd.merge(df_merged, dias_uteis[["sindicato_dias", "dias_uteis"]], left_on="sindicato", right_on="sindicato_dias", how="left")
    df_merged.drop(columns=["sindicato_dias"], inplace=True)

    print("✔ Dados unificados e enriquecidos com sucesso!")
    dados_finais = df_merged
    
    # Fase 7: Invocação da nova função de validação e correção
    dados_finais = validar_e_corrigir_dados(dados_finais)

    # Adicionando a nova etapa: salvar o arquivo CSV
    output_directory = 'saida'
    output_filename = 'base_consolidada.csv'
    output_path = os.path.join(output_directory, output_filename)
    
    # Verifica se o diretório de saída existe, senão o cria
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Salva o DataFrame em um arquivo CSV
    dados_finais.to_csv(output_path, index=False, sep=';')
    print(f"\n✔ Dados consolidados salvos com sucesso em: {output_path}")

    # Exibe o resultado final para visualização
    print("\nDataFrame Consolidado (primeiras 5 linhas):")
    print(dados_finais.head())
    
    return dados_finais

# Executa o processo completo
if __name__ == "__main__":
    dados_consolidados = coletar_e_unificar_dados()