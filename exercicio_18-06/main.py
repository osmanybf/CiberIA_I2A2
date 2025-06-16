# main.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.tools import Tool
import pandas as pd

# Importa SOMENTE a função de carregamento, não as variáveis globais
from data_loader import carregar_csvs

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- Variáveis globais para armazenar os DataFrames no ESCOPO GLOBAL de main.py ---
# Elas serão preenchidas pela ferramenta de carregamento
global_df_cabecalho = None
global_df_itens = None

# --- Funções Wrappers para as Ferramentas (agora em main.py) ---
# Essas funções terão acesso às variáveis globais de main.py

def tool_carregar_dados_csvs(arg: str = None) -> str: # <--- MUDANÇA AQUI: Adicionei 'arg: str = None'
    """
    Esta ferramenta deve ser usada primeiro e apenas uma vez para carregar os dados
    dos arquivos CSV de cabeçalho e itens em DataFrames Pandas na memória.
    Chame-a antes de qualquer consulta aos dados.
    """
    global global_df_cabecalho, global_df_itens
    if global_df_cabecalho is not None and global_df_itens is not None:
        return "Arquivos CSV de cabeçalho e itens já estão carregados na memória."
        
    df_c, df_i = carregar_csvs()
    if df_c is not None and df_i is not None:
        global_df_cabecalho = df_c
        global_df_itens = df_i
        print(global_df_itens.columns) # <--- MUDANÇA AQUI: Adicionada impressão das colunas de global_df_itens
        return "Arquivos CSV de cabeçalho e itens carregados com sucesso na memória."
    else:
        return "Erro ao carregar os arquivos CSV. Verifique os caminhos e permissões."

# main.py

# ... (outras importações e código) ...

def tool_consultar_cabecalho(query: str) -> str:
    """
    Executa uma operação Pandas no DataFrame 'global_df_cabecalho' e retorna o resultado.
    Útil para responder perguntas sobre o cabeçalho das notas fiscais, como fornecedores,
    valores totais, datas de emissão.
    A entrada DEVE ser uma ÚNICA LINHA de código Pandas que RETORNA UM VALOR.
    NÃO inclua blocos try/except ou múltiplas linhas de código.
    Exemplos de query: "global_df_cabecalho['ValorTotal'].max()",
    "global_df_cabecalho['Fornecedor'].value_counts().idxmax()",
    "global_df_cabecalho[global_df_cabecalho['ValorTotal'] > 1000].shape[0]".
    Certifique-se de usar 'global_df_cabecalho' como o nome do DataFrame na sua query.
    """
    global global_df_cabecalho
    if global_df_cabecalho is None:
        return "Erro: O DataFrame de cabeçalho não está carregado. Por favor, solicite 'carregar os dados' primeiro."
    try:
        # Garante que a query é uma única linha e remove aspas/backticks
        clean_query = query.strip().strip('"').strip("'").strip("`").split('\n')[0] # Only take the first line
        
        # Optionally, check if the query looks like a method call for extra safety
        # if not (clean_query.startswith("global_df_cabecalho.") or clean_query.startswith("pd.")):
        #     return "Consulta inválida: A query deve começar com 'global_df_cabecalho.' ou 'pd.' para ser segura."
            
        result = eval(clean_query)
        return str(result)
    except Exception as e:
        return f"Erro ao executar a consulta no cabeçalho: {e}. Certifique-se de que a query é válida e usa 'global_df_cabecalho'."

def tool_consultar_itens(query: str) -> str:
    """
    Executa uma operação Pandas no DataFrame 'global_df_itens' e retorna o resultado.
    Útil para responder perguntas sobre os itens das notas fiscais, como quantidades,
    descrições de itens, valores unitários.
    A entrada DEVE ser uma ÚNICA LINHA de código Pandas que RETORNA UM VALOR.
    NÃO inclua blocos try/except ou múltiplas linhas de código.
    Exemplos de query: "global_df_itens['Quantidade'].sum()",
    "global_df_itens['ItemDescricao'].value_counts().idxmax()",
    "global_df_itens[global_df_itens['ValorUnitario'] < 5].shape[0]".
    Certifique-se de usar 'global_df_itens' como o nome do DataFrame na sua query.
    """
    global global_df_itens
    if global_df_itens is None:
        return "Erro: O DataFrame de itens não está carregado. Por favor, solicite 'carregar os dados' primeiro."
    try:
        # Garante que a query é uma única linha e remove aspas/backticks
        clean_query = query.strip().strip('"').strip("'").strip("`").split('\n')[0] # Only take the first line

        result = eval(clean_query)
        return str(result)
    except Exception as e:
        return f"Erro ao executar a consulta nos itens: {e}. Certifique-se de que a query é válida e usa 'global_df_itens'."

# --- Configuração do LLM ---
# Escolha um dos modelos validados:
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0) # Ou gemini-1.5-flash etc.

# --- Definição das Ferramentas para o Agente ---
tools = [
    Tool(
        name="Carregar Dados CSVs",
        func=tool_carregar_dados_csvs,
        description="Esta ferramenta deve ser usada primeiro e apenas uma vez para carregar os dados dos arquivos CSV de cabeçalho e itens em DataFrames Pandas na memória. Chame-a antes de qualquer consulta aos dados."
    ),
    Tool(
        name="Consultar Cabeçalho NFs",
        func=tool_consultar_cabecalho,
        description="Útil para responder perguntas sobre o cabeçalho das notas fiscais. Recebe uma string que é uma operação válida do Pandas no DataFrame 'global_df_cabecalho'. Por exemplo: 'global_df_cabecalho['ValorTotal'].max()', 'global_df_cabecalho['Fornecedor'].value_counts().head(5)'. Lembre-se de usar 'global_df_cabecalho'."
    ),
    Tool(
        name="Consultar Itens NFs",
        func=tool_consultar_itens,
        description=(
            "Útil para responder perguntas sobre os itens das notas fiscais. "
            "Recebe uma string que é uma operação válida do Pandas no DataFrame 'global_df_itens'. "
            "Por exemplo: "
            "'global_df_itens[\"DESCRIÇÃO DO PRODUTO/SERVIÇO\"].value_counts().idxmax()', "
            "'global_df_itens.groupby(\"DESCRIÇÃO DO PRODUTO/SERVIÇO\")[\"QUANTIDADE\"].sum().idxmax()', "
            "'global_df_itens[global_df_itens[\"VALOR UNITÁRIO\"] < 5].shape[0]'. "
            "Lembre-se de usar 'global_df_itens' e os nomes corretos das colunas: "
            "'DESCRIÇÃO DO PRODUTO/SERVIÇO', 'QUANTIDADE', 'VALOR UNITÁRIO', etc."
        )
    )
]

# --- Criação do Agente ---
prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def perguntar_ao_agente(pergunta: str) -> str:
    """
    Envia uma pergunta ao agente de IA e retorna a resposta.
    """
    try:
        # A lógica para "carregar os dados" pode ser mais sofisticada se necessário.
        # Aqui, estamos contando com o agente para chamar a ferramenta correta.
        response = agent_executor.invoke({"input": pergunta})
        return response['output']
    except Exception as e:
        return f"Ocorreu um erro ao processar sua pergunta: {e}"

if __name__ == "__main__":
    print("Bem-vindo ao Agente de Consulta de Notas Fiscais!")
    print("Para começar, digite 'Carregar os dados'.")
    print("Para sair, digite 'sair'.")

    while True:
        user_input = input("\nSua pergunta: ")
        if user_input.lower() == 'sair':
            print("Encerrando o agente.")
            break
        
        resposta = perguntar_ao_agente(user_input)
        print(f"Resposta do Agente: {resposta}")