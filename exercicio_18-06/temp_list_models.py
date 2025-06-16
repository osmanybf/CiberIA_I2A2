# temp_list_models.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv() # Certifique-se de carregar sua GOOGLE_API_KEY do .env

# Configure a API Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    for m in genai.list_models():
        # A API pode retornar diferentes tipos de modelos (texto, visão, embeddings)
        # Verificamos se o modelo suporta o método 'generateContent'
        # e se é para geração de texto (não embeddings ou visão para este caso)
        if 'generateContent' in m.supported_generation_methods:
            print(f"Model ID: {m.name}, Display Name: {m.display_name}, Supported Methods: {m.supported_generation_methods}")
except Exception as e:
    print(f"Erro ao listar modelos: {e}")