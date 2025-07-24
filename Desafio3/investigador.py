# investigador.py
import requests
import time
import os

from dotenv import load_dotenv
load_dotenv()

RECEITAWS_TOKEN = os.getenv("RECEITAWS_TOKEN")

def consultar_cnpj(cnpj):
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}?token={RECEITAWS_TOKEN}"
    headers = {"Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()

        if response.status_code != 200 or data.get("status") != "OK":
            return {"erro": f"Erro ao consultar: {data.get('message', 'desconhecido')}"}

        return {
            "CNPJ": cnpj,
            "Razão Social": data.get("nome"),
            "Nome Fantasia": data.get("fantasia"),
            "Situação": data.get("situacao"),
            "Tipo": data.get("tipo"),
            "Porte": data.get("porte"),
            "Natureza Jurídica": data.get("natureza_juridica"),
            "Abertura": data.get("abertura"),
            "Capital Social": data.get("capital_social"),
            "Email": data.get("email"),
            "Telefone": data.get("telefone"),
            "Endereço": f"{data.get('logradouro', '')}, {data.get('numero', '')}, {data.get('bairro', '')} - {data.get('municipio', '')}/{data.get('uf', '')} - CEP {data.get('cep', '')}",
            "Atividade Principal": data.get("atividade_principal", [{}])[0].get("text", "N/A"),
            "Atividades Secundárias": data.get("atividades_secundarias", []),
            "QSA": data.get("qsa", []),
            "Simples": data.get("simples", {}),
            "Simei": data.get("simei", {}),
        }

    except Exception as e:
        return {"erro": str(e)}


import re

def tool_investigar_fornecedor(cnpj: str) -> str:
    cnpj = re.sub(r'\D', '', cnpj)
    dados = consultar_cnpj(cnpj)
    if "erro" in dados:
        return dados["erro"]

    atividades_sec = "\n".join(
        f"  - {a['code']}: {a['text']}" for a in dados.get("Atividades Secundárias", [])
    ) or "  - Nenhuma"

    socios = "\n".join(
        f"  - {s['nome']} ({s['qual']})" for s in dados.get("QSA", [])
    ) or "  - Não informado"

    simples = dados.get("Simples", {})
    simei = dados.get("Simei", {})

    return (
        f"🕵️‍♂️ **Investigação do CNPJ {cnpj}**\n"
        f"- Razão Social: {dados['Razão Social']}\n"
        f"- Nome Fantasia: {dados['Nome Fantasia'] or 'N/A'}\n"
        f"- Situação: {dados['Situação']}\n"
        f"- Tipo: {dados['Tipo']} | Porte: {dados['Porte']} | Natureza Jurídica: {dados['Natureza Jurídica']}\n"
        f"- Abertura: {dados['Abertura']}\n"
        f"- Capital Social: R$ {dados['Capital Social']}\n"
        f"- Endereço: {dados['Endereço']}\n"
        f"- Email: {dados['Email']} | Telefone: {dados['Telefone']}\n\n"

        f"🏢 **Atividade Principal**:\n  - {dados['Atividade Principal']}\n\n"
        f"📂 **Atividades Secundárias:**\n{atividades_sec}\n\n"
        f"👥 **Quadro Societário:**\n{socios}\n\n"
        f"💼 **Tributação:**\n"
        f"  - Simples Nacional: {'Sim' if simples.get('optante') else 'Não'}\n"
        f"  - MEI: {'Sim' if simei.get('optante') else 'Não'}"
    )
