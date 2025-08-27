
# Automação de Cálculo de Benefícios - Vale Refeição e Auxílio Alimentação

## Visão Geral

Este projeto automatiza o cálculo e a compra dos benefícios de **Vale Refeição (VR)** e **Auxílio Alimentação (VA)**, garantindo que cada colaborador receba o valor correto. A solução utiliza um agente autônomo com um Large Language Model (LLM) para interpretar regras de negócio complexas e orquestrar o processamento de dados. O processo substitui a conferência manual de planilhas por um fluxo de trabalho automatizado e escalável.

---

## Arquitetura da Solução

A arquitetura do projeto é dividida em três componentes principais:

- **LLM (Large Language Model):** Atua como o "cérebro" do sistema, interpretando e aplicando regras de negócio complexas, como as encontradas em documentos de convenção coletiva.
- **Agente:** Gerencia e orquestra as ações do LLM, decidindo quais ferramentas utilizar e em que momento, garantindo que o fluxo de trabalho seja executado de forma lógica e eficiente.
- **Ferramentas (Tools):** Funções específicas que o agente pode chamar para interagir com o ambiente externo, como leitura de arquivos CSV (`ler_e_processar_csv`) e extração de texto de documentos PDF (`ler_pdf`).

---

## Fases e Etapas de Processamento

O processo completo de cálculo de benefícios é dividido em três fases:

### Fase 1: Coleta e Unificação de Dados

1. **Coleta de Dados:** O sistema acessa e lê diversas planilhas (.csv) contendo informações de colaboradores ativos, desligados, em férias, estagiários e aprendizes.
2. **Padronização:** Os nomes das colunas são padronizados (ex: `Matricula` para `matricula`) para garantir a consistência dos dados.
3. **Unificação da Base:** As planilhas são combinadas em uma única base de dados consolidada (`base_consolidada.csv`), usando a matrícula do colaborador como chave de unificação.

### Fase 2: Validação e Tratamento

1. **Regras de Exclusão:** Colaboradores não elegíveis aos benefícios (estagiários, aprendizes, diretores e afastados) são identificados e removidos da base de cálculo.
2. **Ajuste de Dias Úteis:** O número de dias úteis para o cálculo é ajustado com base em eventos como:
	- Admissões no meio do mês: cálculo proporcional à data de admissão.
	- Desligamentos: excluído do pagamento se o comunicado de desligamento ocorrer até o dia 15; após o dia 15, cálculo proporcional.
	- Férias: excluído se tiver 30 ou mais dias de férias; se menos, os dias de férias são subtraídos do total a receber.

### Fase 3: Cálculo e Geração de Relatório

1. **Processamento de Convenções (Otimizado):** O agente lê os arquivos PDF das convenções coletivas de cada sindicato. O processamento é feito por sindicato, uma única vez, para otimizar as chamadas à LLM. O agente extrai o valor do Auxílio Alimentação e outras regras aplicáveis diretamente do texto do documento.
2. **Cálculo de Benefícios:** Com as regras e valores extraídos, o sistema calcula o valor total de VR e VA para cada colaborador. A regra de custo é aplicada (80% para a empresa e 20% para o profissional).
3. **Geração de Relatório:** A base de dados com todos os valores calculados é formatada para o modelo de relatório de saída (`VR MENSAL 05.2025.csv`), contendo as colunas e informações necessárias para o envio ao fornecedor.