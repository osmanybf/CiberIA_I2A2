import google.generativeai as genai
import os

# Configure sua API Key do Gemini
# Se você a salvou em uma variável de ambiente, pode usar:
# genai.configure(api_key=os.environ['SUA_VARIAVEL_DE_AMBIENTE_AQUI'])
# Caso contrário, pode colocar a chave diretamente:
genai.configure(api_key="AIzaSyBd2mGjnCKwjnycz-xSZeLZ2gP-uYjFq4s")

# Liste os modelos que suportam a geração de conteúdo
print("Modelos disponíveis:")
for m in genai.list_models():
  if 'generateContent' in m.supported_generation_methods:
    print(m.name)