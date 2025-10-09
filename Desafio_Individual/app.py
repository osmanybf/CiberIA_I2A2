import streamlit as st
from agent_gemini import get_agent, get_available_models
import os

# =============================
# Função para consultar modelos disponíveis
# =============================
def consultar_modelos(api_key):
    try:
        modelos = get_available_models(api_key)
        if not modelos:
            return ["gemini-2.5-flash"]
        return modelos
    except Exception:
        return ["gemini-2.5-flash"]

# =============================
# TELA DE LOGIN
# =============================
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(os.path.join("data", "img", "logo.png"), width=180)
        st.title("Login")
        nome = st.text_input("Digite seu nome")
        api_key = st.text_input("Digite sua API KEY do Gemini", type="password")
        if st.button("Entrar"):
            if nome and api_key:
                st.session_state["nome"] = nome
                st.session_state["api_key"] = api_key
                st.session_state["logged_in"] = True
                # Consulta os modelos disponíveis para este usuário
                st.session_state["modelos_gemini"] = consultar_modelos(api_key)
                st.rerun()
            else:
                st.warning("Preencha todos os campos para continuar.")
        st.stop()

st.set_page_config(page_title="Agente CiberIA", page_icon="🤖", layout="wide")

st.title("🤖 Agente Autônomo - Gemini")
st.write("Escolha o modelo Gemini, faça o upload do arquivo CSV e realize perguntas sobre os dados!")

# =============================
# INICIALIZAÇÃO DE ESTADO E CHAT
# =============================
# Inicializa o histórico de mensagens
if "messages" not in st.session_state:
    st.session_state.messages = []
    

if "file_loaded" not in st.session_state:
    st.session_state.file_loaded = None

# Combo para seleção do modelo (preenchido após login)
modelos_gemini = st.session_state.get("modelos_gemini", ["gemini-2.5-flash"])
modelo_selecionado = st.selectbox("Selecione o modelo Gemini:", modelos_gemini, index=0)
st.session_state["modelo_gemini"] = modelo_selecionado

# Inicializa o agente Gemini com a API KEY e modelo do usuário
if "agent" not in st.session_state or st.session_state.get("modelo_gemini_last") != modelo_selecionado:
    st.session_state.agent = get_agent(st.session_state["api_key"], modelo_selecionado)
    st.session_state["modelo_gemini_last"] = modelo_selecionado
agent = st.session_state.agent

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

    # 2. Padroniza o caminho para usar barras frontais ('/')
    file_path_safe = file_path_local.replace(os.path.sep, '/')
    
    # 3. Informa o agente para carregar o arquivo
    with st.spinner(f"Carregando {uploaded_file.name} e resetando a memória do agente..."):
        png_dir = os.path.join("data")
        os.makedirs(png_dir, exist_ok=True)
        for file in os.listdir(png_dir):
            if file.endswith(".png"):
                os.remove(os.path.join(png_dir, file))
        result = agent.run(f"Carregue o arquivo {file_path_safe}")
    
    # 4. Atualiza o estado e o histórico de chat
    st.session_state.file_loaded = uploaded_file.name
    st.session_state.messages.clear()
    
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
        # Limpa todos os PNGs do diretório 'data' antes de gerar novo gráfico
        data_dir = os.path.join("data")
        for file in os.listdir(data_dir):
            if file.endswith(".png"):
                os.remove(os.path.join(data_dir, file))

        response = agent.run(query)
        st.write("### Resposta:")
        st.write(response)

        # Exibe apenas o(s) gráfico(s) gerado(s) na resposta atual
        for file in os.listdir(data_dir):
            if file.endswith(".png"):
                st.image(os.path.join(data_dir, file), caption=file)
