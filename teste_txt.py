import streamlit as st
import os
import re
import requests
import json

# --- Funções para carregar e processar o dicionário ---

@st.cache_data
def carregar_dicionario_termos(nome_arquivo):
    """
    Carrega os termos e a hierarquia de um arquivo de texto.
    """
    termos = []
    mapa_hierarquia = {}
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                partes = [p.strip() for p in line.split('>') if p.strip()]
                if not partes:
                    continue
                termo_especifico = partes[-1]
                if termo_especifico:
                    termo_especifico = termo_especifico.replace('\t', '')
                    termos.append(termo_especifico)
                if len(partes) > 1:
                    termo_pai = partes[-2].replace('\t', '')
                    if termo_pai not in mapa_hierarquia:
                        mapa_hierarquia[termo_pai] = []
                    mapa_hierarquia[termo_pai].append(termo_especifico)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
        return [], {}
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o dicionário: {e}")
        return [], {}
    return termos, mapa_hierarquia

def aplicar_logica_hierarquia(termos_sugeridos, mapa_hierarquia):
    """
    Remove termos genéricos se um termo mais específico da mesma hierarquia estiver presente.
    """
    termos_finais = set(termos_sugeridos)
    mapa_inverso_hierarquia = {}
    for pai, filhos in mapa_hierarquia.items():
        for filho in filhos:
            mapa_inverso_hierarquia[filho] = pai
    termos_a_remover = set()
    for termo in termos_sugeridos:
        if termo in mapa_inverso_hierarquia:
            termo_pai = mapa_inverso_hierarquia[termo]
            if termo_pai in termos_finais:
                termos_a_remover.add(termo_pai)
    termos_finais = termos_finais - termos_a_remover
    return list(termos_finais)

# --- Funções para interagir com o Gemini API ---

def get_api_key():
    """
    Obtém a chave de API do Google de forma segura.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if api_key:
        return api_key
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    return api_key

def gerar_termos_llm(texto_original, termos_dicionario, num_termos):
    """
    Gera termos de indexação usando o Gemini e um dicionário de termos.
    A resposta é formatada como uma lista JSON.
    """
    api_key = get_api_key()
    
    if not api_key:
        st.error("Erro: A chave de API não foi configurada. Por favor, adicione-a como um segredo no Streamlit ou em variáveis de ambiente.")
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

    prompt_termos = f"""
    A partir do texto abaixo, selecione até {num_termos} termos de indexação relevantes.
    Os termos de indexação devem ser selecionados EXCLUSIVAMENTE da seguinte lista:
    {", ".join(termos_dicionario)}
    Se nenhum termo da lista for aplicável, a resposta deve ser uma lista JSON vazia: [].
    A resposta DEVE ser uma lista JSON de strings, sem texto adicional antes ou depois.
    
    Texto da Proposição: {texto_original}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_termos}]}],
        "tools": [{"google_search": {}}]
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        json_string = result.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
        
        termos_sugeridos = []
        matches = re.findall(r'(\[.*?\])', json_string, re.DOTALL)
        
        for match in matches:
            cleaned_string = match.replace("'", '"')
            try:
                parsed_list = json.loads(cleaned_string)
                if isinstance(parsed_list, list) and all(isinstance(item, str) for item in parsed_list):
                    termos_sugeridos = parsed_list
                    break
            except json.JSONDecodeError:
                continue
        
        return termos_sugeridos
        
    except requests.exceptions.HTTPError as http_err:
        st.error(f"Erro na comunicação com a API: {http_err}")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
        
    return []

# --- Bloco de código do Streamlit ---

st.title("Teste de Carregamento de Dicionário TXT")

# 1. Carrega o dicionário com o nome de arquivo ajustado
arquivo_txt = "saude_dicionario.txt"
termo_dicionario_txt, mapa_hierarquia_txt = carregar_dicionario_termos(arquivo_txt)

if not termo_dicionario_txt:
    st.warning("Teste não pode continuar: Dicionário não foi carregado.")
else:
    st.success(f"Dicionário TXT carregado com {len(termo_dicionario_txt)} termos.")
    
    st.subheader("Termos carregados do TXT:")
    st.write(termo_dicionario_txt)
    
    st.subheader("Mapa de hierarquia criado:")
    st.write(mapa_hierarquia_txt)

    st.markdown("---")
    st.subheader("Testar a Sugestão de Termos")

    texto_proposicao = st.text_area(
        "Digite um texto para testar a sugestão de termos:",
        "Esta lei visa tratar sobre a saúde e o tratamento de doenças, como o diabetes."
    )

    num_termos = st.slider("Número de termos a sugerir:", 1, 10, 5)

    if st.button("Gerar Termos"):
        with st.spinner('Gerando...'):
            termos_sugeridos_brutos = gerar_termos_llm(texto_proposicao, termo_dicionario_txt, num_termos)
            
            st.write("---")
            st.subheader("Resultado do Teste")
            
            if termos_sugeridos_brutos is None:
                st.error("Não foi possível gerar termos. Verifique o erro acima.")
            else:
                st.write(f"Termos sugeridos pela IA (brutos): **{termos_sugeridos_brutos}**")
                
                termos_finais = aplicar_logica_hierarquia(termos_sugeridos_brutos, mapa_hierarquia_txt)
                st.write(f"Termos finais após a lógica de hierarquia: **{termos_finais}**")
