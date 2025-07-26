# tools.py
import pandas as pd
from langchain.tools import tool
# Importa as variáveis globais e a função de data_loader
from data_loader import df_cabecalho, df_itens, carregar_csvs

# Ferramenta para carregar os dados. Agora ela chama a função de data_loader.
@tool
def carregar_dados_csvs() -> str:
    """
    Esta ferramenta deve ser usada primeiro e apenas uma vez para carregar os dados
    dos arquivos CSV de cabeçalho e itens em DataFrames Pandas na memória.
    Chame-a antes de qualquer consulta aos dados.
    """
    return carregar_csvs()

# Ferramenta para consultar o DataFrame de cabeçalho
@tool
def consultar_cabecalho(query: str) -> str:
    """
    Executa uma operação Pandas no DataFrame 'df_cabecalho' e retorna o resultado.
    Útil para responder perguntas sobre o cabeçalho das notas fiscais, como fornecedores,
    valores totais, datas de emissão.
    Exemplos de query: "df_cabecalho['ValorTotal'].max()",
    "df_cabecalho['Fornecedor'].value_counts().idxmax()",
    "df_cabecalho[df_cabecalho['ValorTotal'] > 1000].shape[0]".
    Certifique-se de usar 'df_cabecalho' como o nome do DataFrame na sua query.
    """
    global df_cabecalho # Garante que estamos usando a variável global
    if df_cabecalho is None:
        return "Erro: O DataFrame de cabeçalho não está carregado. Por favor, solicite 'carregar os dados' primeiro."
    try:
        # ATENÇÃO: Usar eval() com entrada gerada por LLM é um risco de segurança.
        # Para um ambiente de produção, implemente um parser de query mais seguro.
        result = eval(query)
        return str(result)
    except Exception as e:
        return f"Erro ao executar a consulta no cabeçalho: {e}"

# Ferramenta para consultar o DataFrame de itens
@tool
def consultar_itens(query: str) -> str:
    """
    Executa uma operação Pandas no DataFrame 'df_itens' e retorna o resultado.
    Útil para responder perguntas sobre os itens das notas fiscais, como quantidades,
    descrições de itens, valores unitários.
    Exemplos de query: "df_itens['Quantidade'].sum()",
    "df_itens['ItemDescricao'].value_counts().idxmax()",
    "df_itens[df_itens['ValorUnitario'] < 5].shape[0]".
    Certifique-se de usar 'df_itens' como o nome do DataFrame na sua query.
    """
    global df_itens # Garante que estamos usando a variável global
    if df_itens is None:
        return "Erro: O DataFrame de itens não está carregado. Por favor, solicite 'carregar os dados' primeiro."
    try:
        # ATENÇÃO: Usar eval() com entrada gerada por LLM é um risco de segurança.
        result = eval(query)
        return str(result)
    except Exception as e:
        return f"Erro ao executar a consulta nos itens: {e}"