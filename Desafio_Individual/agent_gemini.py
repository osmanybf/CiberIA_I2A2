# agent_gemini.py
from dotenv import load_dotenv
load_dotenv()  # 🔹 Carrega variáveis de ambiente (.env)

from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==============================================
# 🔹 VARIÁVEL GLOBAL DE DATAFRAME
# ==============================================
df = None

# ==============================================
# 🔹 FERRAMENTAS DE ANÁLISE DE DADOS (CORRIGIDAS)
# ==============================================

def load_csv(file_path: str):
    """Carrega um arquivo CSV para análise, configurando-o na variável global df."""
    global df
    if not os.path.exists(file_path):
        return f"Arquivo não encontrado: {file_path}"
    df = pd.read_csv(file_path)
    return f"Arquivo '{file_path}' carregado com {len(df)} linhas e {len(df.columns)} colunas.\n\nColunas: {', '.join(df.columns)}"

def describe_data(query: str = None): # 🎯 CORREÇÃO 1: Aceita argumento, mas ignora.
    """Mostra estatísticas descritivas básicas do dataset carregado."""
    global df
    if df is None:
        return "Nenhum CSV carregado ainda."
    
    # Adiciona tratamento básico de erro para dataframe misto
    try:
        description = df.describe(include='all').to_string()
    except Exception:
        description = df.describe(include='number').to_string()

    return description

def plot_distribution(column: str):
    """Cria gráfico de distribuição (histograma) para uma coluna numérica específica."""
    global df
    if df is None:
        return "Nenhum CSV carregado ainda."
    if column not in df.columns:
        return f"A coluna '{column}' não existe no dataset."
    
    # Tenta converter a coluna para garantir que seja numérica ou possa ser plotada
    try:
        data_to_plot = pd.to_numeric(df[column], errors='coerce').dropna()
        if data_to_plot.empty:
             return f"A coluna '{column}' é não numérica ou está vazia após limpeza."
             
        plt.figure(figsize=(8, 5))
        sns.histplot(data_to_plot, kde=True, bins=30)
        plt.title(f"Distribuição da coluna: {column}")
        path = f"distribution_{column}.png"
        plt.savefig(path)
        plt.close()
        return f"Gráfico salvo em {path}"
        
    except Exception as e:
        return f"Erro ao plotar distribuição para a coluna '{column}'. Erro: {e}"


def correlation_matrix(query: str = None): # 🎯 CORREÇÃO 1: Aceita argumento, mas ignora.
    """Gera e salva a matriz de correlação (heatmap) entre variáveis numéricas."""
    global df
    if df is None:
        return "Nenhum CSV carregado ainda."
        
    corr = df.corr(numeric_only=True)
    
    # Adiciona verificação de correlação para evitar erro em datasets com poucas colunas
    if corr.empty:
        return "O dataset não possui colunas numéricas suficientes para gerar uma matriz de correlação."
        
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, cmap='coolwarm', annot=False)
    plt.title("Matriz de Correlação")
    path = "correlation_matrix.png"
    plt.savefig(path)
    plt.close()
    return f"Gráfico de correlação salvo em {path}"

def detect_outliers(column: str):
    """Identifica valores atípicos (outliers) usando o método IQR para uma coluna numérica."""
    global df
    if df is None:
        return "Nenhum CSV carregado ainda."
    if column not in df.columns:
        return f"A coluna '{column}' não existe no dataset."
        
    # Tenta usar a coluna como numérica
    try:
        data = pd.to_numeric(df[column], errors='coerce').dropna()
        if data.empty:
            return f"A coluna '{column}' é não numérica ou está vazia e não pode ter outliers detectados."
            
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = data[(data < lower) | (data > upper)]
        return f"Foram encontrados {len(outliers)} outliers na coluna '{column}'. Intervalo considerado normal: [{lower:.2f}, {upper:.2f}]"
    
    except Exception as e:
        return f"Erro ao detectar outliers. Certifique-se que a coluna '{column}' é numérica. Erro: {e}"

# agent_gemini.py

# ... (após detect_outliers) ...

def plot_scatter(column_x: str, column_y: str):
    """Cria um gráfico de dispersão (Scatter Plot) entre duas colunas numéricas."""
    global df
    if df is None:
        return "Nenhum CSV carregado ainda."
    if column_x not in df.columns or column_y not in df.columns:
        return f"Colunas '{column_x}' ou '{column_y}' não existem no dataset."
    
    # Tentativa de plotar, garantindo que as colunas são numéricas
    try:
        data_x = pd.to_numeric(df[column_x], errors='coerce')
        data_y = pd.to_numeric(df[column_y], errors='coerce')
        
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=data_x, y=data_y)
        plt.title(f"Dispersão entre {column_x} e {column_y}")
        plt.xlabel(column_x)
        plt.ylabel(column_y)
        path = f"scatter_{column_x}_vs_{column_y}.png"
        plt.savefig(path)
        plt.close()
        return f"Gráfico de dispersão salvo em {path}"
    
    except Exception as e:
        return f"Erro ao plotar gráfico de dispersão. Certifique-se de que as colunas são numéricas. Erro: {e}"

def plot_cluster(column_x: str, column_y: str, n_clusters: int = 3):
    """Aplica o algoritmo K-Means e plota os clusters em um gráfico de dispersão. Argumentos: column_x, column_y e n_clusters (opcional)."""
    global df
    if df is None:
        return "Nenhum CSV carregado ainda."
    if column_x not in df.columns or column_y not in df.columns:
        return f"Colunas '{column_x}' ou '{column_y}' não existem no dataset."
        
    try:
        # Importa KMeans apenas quando a ferramenta é usada (melhor prática)
        from sklearn.cluster import KMeans
        
        features = df[[column_x, column_y]].copy()
        
        # Remove valores não numéricos/ausentes para o clustering
        features_clean = features.dropna()
        if len(features_clean) < n_clusters:
            return "Dados insuficientes para aplicar K-Means após limpeza."
            
        # Aplica K-Means
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        features_clean['Cluster'] = kmeans.fit_predict(features_clean)
        
        # Adiciona a coluna de cluster de volta ao DataFrame original para plotagem
        df_plot = df.copy()
        df_plot = pd.merge(df_plot, features_clean[['Cluster']], left_index=True, right_index=True, how='left')
        
        plt.figure(figsize=(10, 6))
        # Plota os pontos, colorindo pelo cluster
        sns.scatterplot(x=column_x, y=column_y, hue='Cluster', data=df_plot.dropna(subset=['Cluster']), palette='viridis')
        
        plt.title(f"Agrupamento K-Means ({n_clusters} Clusters) em {column_x} vs {column_y}")
        plt.xlabel(column_x)
        plt.ylabel(column_y)
        path = f"cluster_{column_x}_vs_{column_y}_{n_clusters}.png"
        plt.savefig(path)
        plt.close()
        return f"Gráfico de agrupamento salvo em {path}"
    
    except ImportError:
        return "Erro: A biblioteca 'scikit-learn' (sklearn) não está instalada. Instale com 'pip install scikit-learn'."
    except Exception as e:
        return f"Erro ao plotar agrupamento. Certifique-se de que as colunas são numéricas. Erro: {e}"

# ==============================================
# 🔹 CONFIGURAÇÃO DO AGENTE COM GEMINI 2.5 FLASH
# ==============================================

tools = [
    Tool(name="Carregar CSV", func=load_csv, description="Carrega um arquivo CSV para análise. O único argumento é o file_path: str"),
    Tool(name="Descrever Dados", func=describe_data, description="Mostra estatísticas descritivas do dataset carregado. Não requer argumentos."),
    Tool(name="Plotar Distribuição", func=plot_distribution, description="Cria gráfico de distribuição de uma coluna. Argumento: column: str"),
    Tool(name="Matriz de Correlação", func=correlation_matrix, description="Cria gráfico de correlação entre variáveis numéricas. Não requer argumentos."),
    Tool(name="Detectar Outliers", func=detect_outliers, description="Identifica valores atípicos em uma coluna numérica. Argumento: column: str"),
    # 🎯 NOVAS FERRAMENTAS:
    Tool(name="Gráfico de Dispersão", func=plot_scatter, description="Cria um gráfico de dispersão entre duas colunas numéricas. Argumentos: column_x: str, column_y: str"),
    Tool(name="Gráfico de Agrupamento", func=plot_cluster, description="Aplica K-Means e plota os clusters em um gráfico. Argumentos: column_x: str, column_y: str, n_clusters: int (opcional, padrão 3)"),


]

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# 🎯 CORREÇÃO 2: Prefixo para evitar alucinação de carregamento
CUSTOM_PREFIX = """Você é um Agente de Análise Exploratória de Dados (EDA). Seu objetivo é ajudar o usuário a analisar o DataFrame que JÁ ESTÁ CARREGADO na memória global ('df').

Regras estritas de uso de ferramenta:
1. Use as ferramentas de análise ('Descrever Dados', 'Plotar Distribuição', 'Matriz de Correlação', 'Detectar Outliers', 'Gráfico de Dispersão', 'Gráfico de Agrupamento') apenas quando solicitado pelo usuário.
2. Após o sucesso da ferramenta 'Carregar CSV', você deve parar de raciocinar e retornar a resposta FINAL com a confirmação do carregamento, **sem tentar usar qualquer outra ferramenta imediatamente depois**.
3. NUNCA, em hipótese alguma, use 'Carregar CSV' com nomes de arquivo genéricos como 'dados.csv' ou 'dataset.csv'.
4. Responda em Português.
"""

agent_kwargs = {
    "prefix": CUSTOM_PREFIX
}


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.3
)


agent = initialize_agent(
    tools,
    llm,
    agent_type="conversational-react-description",
    memory=memory,
    verbose=True,
    agent_kwargs=agent_kwargs,
    # 🎯 CORREÇÃO FINAL: Permite que o agente se recupere de erros de formatação
    handle_parsing_errors=True 
)