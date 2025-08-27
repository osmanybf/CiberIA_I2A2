# Importa as bibliotecas necessárias
import pandas as pd
import os
import PyPDF2
from langchain.agents import tool, initialize_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import re 
from pydantic import BaseModel, Field

# Define o LLM que o agente irá usar UMA ÚNICA VEZ
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", api_key="AIzaSyBd2mGjnCKwjnycz-xSZeLZ2gP-uYjFq4s")

# --- Ferramentas (Tools) ---
@tool
def ler_pdf(caminho_arquivo: str) -> str:
    """
    Função para ler o texto de um arquivo PDF.
    """
    if not os.path.exists(caminho_arquivo):
        return f"Erro: Arquivo PDF não encontrado no caminho: {caminho_arquivo}"
    
    texto_completo = ""
    try:
        with open(caminho_arquivo, 'rb') as arquivo:
            leitor_pdf = PyPDF2.PdfReader(arquivo)
            for pagina in leitor_pdf.pages:
                texto_completo += pagina.extract_text() or ""
        return texto_completo
    except Exception as e:
        return f"Erro ao ler o arquivo PDF: {e}"

@tool
def extrair_regras_beneficios_sindicato(caminho_pdf: str) -> dict:
    """
    Extrai regras de cálculo e valores de benefícios (VR e VA) de um PDF de convenção.
    """
    texto_pdf = ler_pdf(caminho_pdf)
    
    # Pergunta para o LLM
    prompt = f"Com base no texto da convenção, extraia o valor diário do Auxílio-Alimentação/Refeição e as regras de cálculo para VR. Texto: '{texto_pdf[:2000]}...'"
    
    resposta_llm = llm.invoke(prompt)
    
    # Lógica simplificada para extrair valor da resposta do LLM
    match_va = re.search(r"R\$\s*(\d+,\d{2})", resposta_llm.content)
    valor_va = float(match_va.group(1).replace(',', '.')) if match_va else 0.0

    return {
        "valor_va": valor_va,
        "regras": resposta_llm.content
    }

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
        df = pd.read_csv(file_path, sep=';', encoding='utf-8')
        return df.to_json(orient='records')
    except FileNotFoundError:
        return f"Erro: Arquivo não encontrado no caminho: {file_path}"
    except Exception as e:
        return f"Erro ao processar o arquivo: {e}"

# Cria o agente, que usa o LLM para decidir qual ferramenta chamar
agent = initialize_agent(
    [ler_pdf, extrair_regras_beneficios_sindicato, ler_e_processar_csv],
    llm,
    agent="zero-shot-react-description",
    verbose=False
)

def calcular_beneficios(df: pd.DataFrame, valores_va: dict) -> pd.DataFrame:
    """
    Calcula os valores de Vale Refeição e Auxílio Alimentação com base nos dados consolidados.
    
    Args:
        df (pd.DataFrame): O DataFrame consolidado com as informações de dias a receber.
        valores_va (dict): Dicionário com os valores de Auxílio Alimentação por sindicato.
        
    Returns:
        pd.DataFrame: O DataFrame com os valores de benefício calculados.
    """
    print("Iniciando a fase de cálculo dos benefícios...")

    # Garante que 'valor_sindicato' seja numérico para VR
    df['VALOR DIÁRIO VR'] = df['valor_sindicato'].str.replace('R$', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    
    # Adiciona o valor diário de VA
    df['VALOR DIÁRIO VA'] = df['sindicato'].map(valores_va).fillna(0.0)

    # Preenche valores nulos para evitar erros nos cálculos
    df['DIAS A RECEBER'].fillna(0, inplace=True)
    df['VALOR DIÁRIO VR'].fillna(0, inplace=True)

    # Aplica a regra de elegibilidade final
    df.loc[df['DIAS A RECEBER'] <= 0, 'elegivel_beneficio'] = 'Não'

    # Filtra os colaboradores que não são elegíveis, resultando na base para o cálculo final
    df_calculo = df[df['elegivel_beneficio'] == 'Sim'].copy()

    # Realiza os cálculos
    df_calculo['TOTAL VR'] = df_calculo['DIAS A RECEBER'] * df_calculo['VALOR DIÁRIO VR']
    df_calculo['Custo empresa VR'] = df_calculo['TOTAL VR'] * 0.8
    df_calculo['Desconto profissional VR'] = df_calculo['TOTAL VR'] * 0.2

    df_calculo['TOTAL VA'] = df_calculo['DIAS A RECEBER'] * df_calculo['VALOR DIÁRIO VA']
    df_calculo['Custo empresa VA'] = df_calculo['TOTAL VA'] * 0.8
    df_calculo['Desconto profissional VA'] = df_calculo['TOTAL VA'] * 0.2
    
    # Cria a coluna de observações
    df_calculo['OBS GERAL'] = ''
    
    # Renomeia e seleciona as colunas finais para o relatório
    relatorio_final = df_calculo.rename(columns={
        'matricula': 'Matricula',
        'Admissão': 'Admissão',
        'sindicato': 'Sindicato do Colaborador',
        'DIAS A RECEBER': 'Dias'
    })
    
    relatorio_final['Competência'] = datetime.now().strftime('%Y-%m-%d')
    
    colunas_finais = [
        'Matricula', 'Admissão', 'Sindicato do Colaborador', 'Competência',
        'Dias', 'VALOR DIÁRIO VR', 'TOTAL VR', 'Custo empresa VR', 'Desconto profissional VR', 'OBS GERAL'
    ]
    
    relatorio_final = relatorio_final[colunas_finais]

    print("✔ Cálculos finalizados com sucesso!")
    
    return relatorio_final

def main():
    """
    Orquestra a leitura da base consolidada, a extração de dados das convenções e a
    geração do relatório final de benefícios.
    """
    # Define o caminho do arquivo de entrada
    input_directory = 'saida'
    input_filename = 'base_consolidada.csv'
    input_path = os.path.join(input_directory, input_filename)

    # Define o caminho do diretório de convenções
    convencoes_directory = 'convencoes'
    
    try:
        # Lê a base consolidada gerada na etapa anterior
        df_consolidado = pd.read_csv(input_path, sep=';', parse_dates=['Admissão', 'DATA DEMISSÃO'])
        print(f"✔ Base consolidada lida com sucesso de: {input_path}")
        print("Colunas disponíveis:", df_consolidado.columns.tolist())
        
        # Mapeia sindicatos para caminhos de arquivo PDF
        sindicatos_map = {
            'SINDPD SP - SIND.TRAB.EM PROC DADOS E EMPR.EMPRESAS PROC DADOS ESTADO DE SP.': os.path.join(convencoes_directory, 'SINDPD SP.pdf'),
            'SITEPD PR - SIND DOS TRAB EM EMPR PRIVADAS DE PROC DE DADOS DE CURITIBA E REGIAO METROPOLITANA': os.path.join(convencoes_directory, 'SITEPD PR.pdf'),
            'SINDPPD RS - SINDICATO DOS TRAB. EM PROC. DE DADOS RIO GRANDE DO SUL': os.path.join(convencoes_directory, 'SINDPPD RS.pdf'),
            'SINDPD RJ - SINDICATO PROFISSIONAIS DE PROC DADOS DO RIO DE JANEIRO': os.path.join(convencoes_directory, 'SINDPD RJ.pdf')
        }

        # Dicionário para armazenar as regras de cada sindicato
        regras_por_sindicato = {}
        sindicatos_unicos = df_consolidado['sindicato'].unique()
        print("Sindicatos únicos no CSV:", sindicatos_unicos)
        # Extrai as regras e valores para cada sindicato com o agente
        for sindicato in sindicatos_unicos:
            caminho_pdf = sindicatos_map.get(sindicato)
            print(f"{sindicato}: PDF encontrado? {os.path.exists(caminho_pdf) if caminho_pdf else 'Não mapeado'}")
            if caminho_pdf and os.path.exists(caminho_pdf):
                print(f"Buscando regras para o sindicato: {sindicato}")
                # Chamada do agente para extrair informações do PDF
                regras_por_sindicato[sindicato] = agent.invoke(f"Analise o PDF em '{caminho_pdf}' e extraia as regras para auxílio alimentação e o valor diário. Gere a resposta como um dicionário.")
            else:
                regras_por_sindicato[sindicato] = {"valor_va": 0.0, "regras": "Nenhuma regra encontrada."}
        
        # Debug: Exibe os valores de VA extraídos para cada sindicato
        for sindicato, regras in regras_por_sindicato.items():
            print(f"{sindicato}: valor_va extraído = {regras.get('valor_va')}")
        
        # Mapeia os valores de VA para o DataFrame consolidado
        df_consolidado['VALOR DIÁRIO VA'] = df_consolidado['sindicato'].map(
            lambda s: regras_por_sindicato.get(s, {}).get('valor_va', 0.0)
        )

        # Executa a fase de cálculo
        df_relatorio = calcular_beneficios(df_consolidado, df_consolidado['VALOR DIÁRIO VA'].to_dict())
        
        # Salva o relatório final em um novo arquivo CSV
        output_directory = 'saida'
        output_filename = 'VR MENSAL 05.2025.csv'
        output_path = os.path.join(output_directory, output_filename)
        
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        df_relatorio.to_csv(output_path, index=False, sep=';')
        
        print(f"\n✔ Relatório final de VR e VA salvo com sucesso em: {output_path}")

        # Exibe o resultado final para visualização
        print("\nRelatório Final (primeiras 5 linhas):")
        print(df_relatorio.head())
        
    except FileNotFoundError:
        print(f"Erro: Um dos arquivos necessários não foi encontrado. Verifique se 'base_consolidada.csv' está em '{input_directory}' e os arquivos de convenção estão em '{convencoes_directory}'.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()