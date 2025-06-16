🤖 Agente de Consulta de Notas Fiscais (CSV)
Este projeto implementa um agente de Inteligência Artificial usando o framework LangChain e modelos Gemini da Google para permitir que usuários façam perguntas em linguagem natural sobre dados contidos em arquivos CSV de notas fiscais. A solução inclui uma interface web simples construída com Streamlit.

🎯 Objetivo
O objetivo principal é criar um agente de IA que possa interagir com o usuário, entender suas perguntas sobre os dados de notas fiscais (cabeçalho e itens), processar os arquivos CSV, executar consultas de dados (utilizando a biblioteca Pandas) e retornar as respostas de forma inteligível.

Exemplos de perguntas que o agente pode responder:

"Qual é o fornecedor que teve maior montante recebido?"
"Qual item teve maior volume entregue (em quantidade)?"
"Quantas notas fiscais foram emitidas?"
"Qual o valor total de todas as notas fiscais?"
📂 Estrutura do Projeto
A estrutura de pastas e arquivos do projeto é organizada da seguinte forma:

seu_projeto/
├── .venv/                     # Ambiente virtual Python (IGNORADO pelo Git)
├── .gitignore                 # Regras para arquivos/pastas ignorados pelo Git
├── .env                       # Variáveis de ambiente (sua API Key - IGNORADO pelo Git)
├── requirements.txt           # Lista de dependências do projeto
├── csv/                       # Diretório contendo os arquivos CSV de dados
│   ├── 202401_NFs_Cabecalho.csv
│   └── 202401_NFs_Itens.csv
├── data_loader.py             # Módulo para carregar os dados CSV em DataFrames Pandas
├── main.py                    # Lógica principal do agente, incluindo LLM e definições de ferramentas
├── app.py                     # Aplicação web com interface do usuário (Streamlit)
└── README.md                  # Este arquivo
🧩 Módulos e Componentes
data_loader.py
Este módulo é responsável por carregar os dados brutos dos arquivos CSV para a memória, transformando-os em DataFrames da biblioteca Pandas. Ele gerencia o caminho dos arquivos e fornece uma função centralizada para o carregamento.

Função Principal: carregar_csvs()
Lê os arquivos 202401_NFs_Cabecalho.csv e 202401_NFs_Itens.csv localizados no diretório csv/.
Retorna dois DataFrames Pandas (df_cabecalho, df_itens) contendo os dados.
Inclui tratamento básico de erros para FileNotFoundError.
main.py
Este é o coração do projeto, onde o agente de IA é definido e orquestrado. Ele integra o LLM com as ferramentas personalizadas para interagir com os dados.

Variáveis Globais de Dados: global_df_cabecalho, global_df_itens
Estas variáveis são usadas para armazenar os DataFrames carregados de forma global no escopo do main.py, permitindo que todas as ferramentas do agente acessem o mesmo estado dos dados.
Configuração do LLM:
Instancia um modelo Gemini da Google (especificamente gemini-1.5-flash ou gemini-1.5-pro dependendo da configuração) usando ChatGoogleGenerativeAI do LangChain.
Funções de Ferramentas (tool_*):
tool_carregar_dados_csvs(): Uma ferramenta que o agente pode chamar para iniciar o carregamento dos dados dos CSVs na memória. Ela invoca a função carregar_csvs() de data_loader.py e popula as variáveis globais.
tool_consultar_cabecalho(query: str): Permite que o agente execute consultas Pandas arbitrárias no global_df_cabecalho. A entrada query deve ser uma única linha de código Pandas que retorna um valor.
tool_consultar_itens(query: str): Semelhante à anterior, mas opera no global_df_itens.
Aviso de Segurança: Ambas as ferramentas de consulta utilizam eval(), o que representa um risco de segurança se a entrada do LLM não for estritamente controlada. Para produção, é altamente recomendável substituir eval() por um parser de consulta mais seguro ou por um conjunto de ferramentas mais estruturadas.
Agente LangChain:
Utiliza o modelo ReAct (Reasoning and Acting) via create_react_agent do LangChain, permitindo que o LLM "pense" sobre qual ferramenta usar e em que sequência para responder à pergunta do usuário.
AgentExecutor: O motor que executa o agente, as ferramentas e gerencia o ciclo de vida da interação.
Função perguntar_ao_agente(pergunta: str):
A interface principal para interagir com o agente a partir de outros módulos (como app.py). Envia a pergunta do usuário para o agent_executor e retorna a resposta final.
app.py
Este arquivo contém o código da interface web do usuário, construída com o Streamlit. Ele fornece um campo de entrada para o usuário digitar perguntas e exibe as respostas do agente.

Interface do Usuário: Cria um título, uma caixa de texto para a pergunta e um botão para enviar.
Integração: Importa a função perguntar_ao_agente de main.py para enviar as perguntas ao agente e exibir as respostas no navegador.
🚀 Como Configurar e Executar
Siga os passos abaixo para configurar e rodar o projeto localmente.

Pré-requisitos
Python 3.8+
Conta Google Cloud com acesso à API Gemini (e uma API Key).
1. Clonar o Repositório
Bash

git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
2. Baixar os Arquivos CSV
Certifique-se de que os arquivos 202401_NFs_Cabecalho.csv e 202401_NFs_Itens.csv estejam localizados dentro da pasta csv/ na raiz do projeto.

3. Configurar o Ambiente Virtual
Crie e ative um ambiente virtual para isolar as dependências do projeto:

Bash

python -m venv .venv
# No Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# No Windows (CMD):
.\.venv\Scripts\activate.bat
# No macOS/Linux (Bash/Zsh):
source ./.venv/bin/activate
4. Instalar Dependências
Com o ambiente virtual ativado, instale as bibliotecas necessárias:

Bash

pip install -r requirements.txt
# Se o requirements.txt ainda não existir, você pode instalar manualmente:
# pip install langchain langchain-google-genai pandas python-dotenv streamlit
5. Configurar sua API Key do Google Gemini
Crie um arquivo chamado .env na raiz do seu projeto e adicione sua chave de API nele. Não inclua este arquivo no controle de versão (ele já deve estar no .gitignore)!

# .env
GOOGLE_API_KEY="SUA_CHAVE_API_GEMINI_AQUI"
6. Executar a Aplicação
Com o ambiente virtual ativado, execute o aplicativo Streamlit:

Bash

streamlit run app.py
Isso abrirá uma nova aba no seu navegador padrão (geralmente http://localhost:8501) onde você poderá interagir com o agente.

💡 Como Usar
No navegador, na interface do Streamlit, na caixa de texto, digite: Carregar os dados dos arquivos CSV. e clique em "Perguntar". Aguarde a confirmação de que os dados foram carregados.
Após a confirmação, você pode começar a fazer suas perguntas sobre os dados das notas fiscais.
Exemplos de Perguntas:
Qual o fornecedor que teve maior montante recebido?
Qual item teve maior volume entregue (em quantidade)?
Quantas notas fiscais foram emitidas?
Qual o valor total de todas as notas fiscais?
Liste os 5 itens mais vendidos por quantidade.
Qual a data da nota fiscal de maior valor?
⚠️ Aviso de Segurança (Uso de eval())
Este projeto, para fins de demonstração e aprendizado, utiliza a função Python eval() para executar as consultas Pandas geradas pelo LLM. O uso de eval() com entrada não confiável (como a saída de um LLM) é inerentemente inseguro e pode levar à execução de código malicioso.

Para uma aplicação em ambiente de produção, é altamente recomendável substituir a lógica baseada em eval() por uma abordagem mais segura, como:

Parsing Controlado: Criar um parser que converte a intenção da linguagem natural em operações Pandas seguras e pré-definidas.
Ferramentas Estruturadas: Definir ferramentas LangChain que aceitam parâmetros específicos (e.g., nome da coluna, tipo de agregação) em vez de strings de código arbitrárias.
🤝 Contribuição
Contribuições são bem-vindas! Se você tiver sugestões, melhorias ou encontrar bugs, sinta-se à vontade para abrir uma issue ou enviar um pull request.