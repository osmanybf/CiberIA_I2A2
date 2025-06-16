# app.py
import streamlit as st
from main import perguntar_ao_agente # Importa a função do seu main.py

st.set_page_config(page_title="Agente de Consulta de NFs")

st.title("🤖 Agente de Consulta de Notas Fiscais")
st.write("Pergunte sobre os dados dos arquivos CSV de Notas Fiscais.")

# Campo de entrada para a pergunta do usuário
user_query = st.text_input("Sua pergunta:", placeholder="Ex: Qual é o fornecedor que teve maior montante recebido?")

# Botão para enviar a pergunta
if st.button("Perguntar"):
    if user_query:
        with st.spinner("Processando..."):
            # Chama a função do seu agente para obter a resposta
            resposta = perguntar_ao_agente(user_query)
            st.success("Concluído!")
            st.write("---")
            st.subheader("Resposta:")
            st.write(resposta)
    else:
        st.warning("Por favor, digite uma pergunta.")

st.markdown("---")
st.markdown("### Dicas:")
st.markdown("- Para começar, digite: `Carregar os dados dos arquivos CSV.`")
st.markdown("- Exemplos de perguntas após carregar os dados:")
st.markdown("  - `Qual o valor total de todas as notas fiscais?`")
st.markdown("  - `Qual fornecedor aparece mais vezes no cabeçalho?`")
st.markdown("  - `Qual o item mais vendido em quantidade?`")