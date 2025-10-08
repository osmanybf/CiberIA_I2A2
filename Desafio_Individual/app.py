import streamlit as st
from agent_gemini import agent
import os

st.set_page_config(page_title="Agente EDA - Gemini 2.5 Flash", page_icon="🤖", layout="wide")

st.title("🤖 Agente Autônomo de EDA com Gemini 2.5 Flash")
st.write("Envie um arquivo CSV e faça perguntas sobre os dados!")

# =============================
# INICIALIZAÇÃO DE ESTADO E CHAT
# =============================
# Inicializa o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []
    
# ✅ CORREÇÃO: Inicializa a variável 'file_loaded'
# Se a chave 'file_loaded' não existir, inicialize-a com None.
if "file_loaded" not in st.session_state:
    st.session_state.file_loaded = None # <-- Esta linha estava faltando ou incorreta!


# =============================
# UPLOAD DE ARQUIVO
# =============================
uploaded_file = st.file_uploader("Selecione o arquivo CSV", type="csv")

if uploaded_file and st.session_state.file_loaded != uploaded_file.name:
    
    # 1. Salva o arquivo localmente
    os.makedirs("data", exist_ok=True)
    file_path_local = os.path.join("data", uploaded_file.name)
    with open(file_path_local, "wb") as f:
        f.write(uploaded_file.getvalue())

    # 2. ✅ CORREÇÃO: Padroniza o caminho para usar barras frontais ('/')
    # Isso evita problemas de 'escape' de caracteres ao enviar o caminho para o agente.
    file_path_safe = file_path_local.replace(os.path.sep, '/')
    
    # 3. Informa o agente para carregar o arquivo
    with st.spinner(f"Carregando {uploaded_file.name} e resetando a memória do agente..."):
        # Limpa arquivos png antigos
        for file in os.listdir():
            if file.endswith(".png"):
                os.remove(file)
                
        # Usa o caminho seguro no comando
        result = agent.run(f"Carregue o arquivo {file_path_safe}")
    
    # 4. Atualiza o estado e o histórico de chat
    st.session_state.file_loaded = uploaded_file.name
    st.session_state.messages.clear()
    
    # Adiciona a confirmação de carregamento ao chat
    st.session_state.messages.append({"role": "assistant", "content": result, "image_path": None})
    st.toast(f"✅ Arquivo '{uploaded_file.name}' carregado com sucesso!")
    st.rerun()

# =============================
# CHAT INTERATIVO
# =============================
st.subheader("💬 Converse com o agente")

query = st.text_input("Digite sua pergunta sobre o CSV:", "")
if st.button("Enviar Pergunta"):
    if query.strip() == "":
        st.warning("Digite uma pergunta primeiro.")
    else:
        response = agent.run(query)
        st.write("### Resposta:")
        st.write(response)

        # Mostra imagens geradas (gráficos)
        for file in os.listdir():
            if file.endswith(".png"):
                st.image(file, caption=file)
