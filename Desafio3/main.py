# main.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.tools import Tool
from langchain_community.chat_models import ChatOpenAI
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

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
        print("🧾 Colunas do CABECALHO:", df_c.columns.tolist())
        print("📦 Colunas dos ITENS:", df_i.columns.tolist())

        return "Arquivos CSV de cabeçalho e itens carregados com sucesso na memória."
    else:
        return "Erro ao carregar os arquivos CSV. Verifique os caminhos e permissões."

from investigador import tool_investigar_fornecedor



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



from langchain.tools import Tool
# Listar Colunas
def tool_listar_colunas(_: str = None) -> str:
    global global_df_cabecalho, global_df_itens
    if global_df_cabecalho is None or global_df_itens is None:
        return "Os dados ainda não foram carregados."

    cab_cols = ", ".join(global_df_cabecalho.columns.tolist())
    itens_cols = ", ".join(global_df_itens.columns.tolist())

    return (
        f"📄 Colunas do cabeçalho: {cab_cols}\n\n"
        f"📦 Colunas dos itens: {itens_cols}"
    )

# --- Configuração do LLM ---
# Escolha um dos modelos validados:
#llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0) # Ou gemini-1.5-flash etc.
llm = ChatOpenAI(
    model_name="gpt-3.5-turbo",  # ou gpt-3.5-turbo, gpt-4o
    temperature=0
)
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
        description="Útil para responder perguntas sobre o cabeçalho das notas fiscais. Recebe uma string que é uma operação válida do Pandas no DataFrame 'global_df_cabecalho'. Por exemplo: 'global_df_cabecalho['VALOR NOTA FISCAL'].max()', 'global_df_cabecalho['RAZÃO SOCIAL EMITENTE'].value_counts().head(5)'. Lembre-se de usar 'global_df_cabecalho'. Lembre-se que o cnpj do fornecedor é do CNPJ emitente"
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
    ),
    Tool(
    name="Investigar Fornecedor",
    func=tool_investigar_fornecedor,
    description="Consulta dados do CNPJ de um fornecedor. Deve ter como entrada o numero do CNPJ. Se não tiver entrada um número de CNPJ, então é outra ferramenta."
    ),
    Tool(
    name="Listar Colunas",
    func=tool_listar_colunas,
    description="Mostra ao agente os nomes das colunas dos DataFrames global_df_cabecalho e global_df_itens para evitar erros de digitação ou nome incorreto."
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



from fpdf import FPDF
from datetime import datetime
import os
from fpdf import FPDF
from datetime import datetime

def gerar_relatorio_pdf():
    global global_df_cabecalho, global_df_itens

    if global_df_cabecalho is None or global_df_itens is None:
        return None, "Erro: Os dados não estão carregados. Use primeiro o botão 'Carregar os dados'."

    try:
        total_nfs = global_df_cabecalho.shape[0]
        valor_total = global_df_cabecalho["VALOR NOTA FISCAL"].sum()
        valor_medio = global_df_cabecalho["VALOR NOTA FISCAL"].mean()
        valor_max = global_df_cabecalho["VALOR NOTA FISCAL"].max()
        fornecedor_top = global_df_cabecalho["RAZÃO SOCIAL EMITENTE"].value_counts().idxmax()
        item_top = (
            global_df_itens
            .groupby("DESCRIÇÃO DO PRODUTO/SERVIÇO")["QUANTIDADE"]
            .sum()
            .idxmax()
        )

        # Top 5 fornecedores por valor emitido
        top_fornecedores = (
            global_df_cabecalho
            .groupby("RAZÃO SOCIAL EMITENTE")["VALOR NOTA FISCAL"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
        )

        # ➕ Top 5 fornecedores mais recorrentes por número de NFs
        top_recor = (
            global_df_cabecalho["RAZÃO SOCIAL EMITENTE"]
            .value_counts()
            .head(5)
        )

        # 📈 Criar gráfico de barras com matplotlib
        plt.figure(figsize=(10, 6))
        top_recor.plot(kind='bar', color='skyblue')
        plt.title("Top 5 Fornecedores Mais Recorrentes (Qtd. de NFs)")
        plt.xlabel("Fornecedor")
        plt.ylabel("Quantidade de Notas Fiscais")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        grafico_path = "grafico_top_fornecedores.png"
        plt.savefig(grafico_path)
        plt.close()


        # Criar o PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Relatório Estatístico de Notas Fiscais", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.ln(10)
        pdf.cell(0, 10, f"Data do Relatório: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.ln(10)

        # Estatísticas gerais
        pdf.cell(0, 10, f"- Total de Notas Fiscais: {total_nfs}", ln=True)
        pdf.cell(0, 10, f"- Valor Total: R$ {valor_total:,.2f}", ln=True)
        pdf.cell(0, 10, f"- Valor Médio por NF: R$ {valor_medio:,.2f}", ln=True)
        pdf.cell(0, 10, f"- Maior NF: R$ {valor_max:,.2f}", ln=True)
        pdf.cell(0, 10, f"- Fornecedor mais recorrente: {fornecedor_top}", ln=True)
        pdf.cell(0, 10, f"- Item mais vendido: {item_top}", ln=True)

        # Top 5 fornecedores
        pdf.ln(10)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Top 5 Fornecedores por Valor Emitido:", ln=True)
        pdf.set_font("Arial", "", 12)
        for fornecedor, total in top_fornecedores.items():
            pdf.cell(0, 10, f"{fornecedor}: R$ {total:,.2f}", ln=True)

        # ➕ Nova página com gráfico de barras
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Gráfico: Fornecedores Mais Recorrentes", ln=True)
        pdf.image(grafico_path, x=10, y=30, w=190)  # Insere imagem no PDF


        # Finalizar
        output_path = "relatorio_estatistico.pdf"
        pdf.output(output_path)

        return output_path, "Relatório gerado com sucesso!"
    except Exception as e:
        return None, f"Erro ao gerar o PDF: {e}"

