import streamlit as st
import os
import re

# Função para carregar o dicionário de termos de um arquivo de texto
@st.cache_data
def carregar_dicionario_termos(nome_arquivo):
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

# Função para aplicar a lógica de hierarquia nos termos sugeridos
def aplicar_logica_hierarquia(termos_sugeridos, mapa_hierarquia):
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

# Mock da função que gera termos, para simular a resposta da IA
def gerar_termos_llm_mock(texto_original, termos_dicionario, num_termos):
    st.info(f"Simulando sugestão de termos para o texto: '{texto_original[:40]}...'")
    if "diabetes" in texto_original.lower():
        return ["Saúde", "Doença", "Diabetes"]
    if "recursos hídricos" in texto_original.lower():
        return ["Recursos Hídricos"]
    if "ensino superior" in texto_original.lower():
        return ["Educação", "Ensino Superior"]
    return ["Política Pública"]

# --- Bloco de código para o Streamlit ---
st.title("Teste de Carregamento de Dicionário TXT")

# 1. Carrega o dicionário
arquivo_txt = "dicionario_termos.txt"
termo_dicionario_txt, mapa_hierarquia_txt = carregar_dicionario_termos(arquivo_txt)

if not termo_dicionario_txt:
    st.warning("Teste não pode continuar: Dicionário não foi carregado.")
else:
    st.success(f"Dicionário TXT carregado com {len(termo_dicionario_txt)} termos.")
    
    st.subheader("Termos carregados do TXT:")
    st.write(termo_dicionario_txt)
    
    st.subheader("Mapa de hierarquia criado:")
    st.write(mapa_hierarquia_txt)

    # Simulação do fluxo de trabalho
    st.markdown("---")
    st.subheader("Testar a Sugestão de Termos")

    texto_proposicao = st.text_area(
        "Digite um texto para testar a sugestão de termos:",
        "Esta lei visa tratar sobre a saúde e o tratamento de doenças, como o diabetes."
    )

    num_termos = st.slider("Número de termos a sugerir:", 1, 10, 5)

    if st.button("Gerar Termos"):
        with st.spinner('Gerando...'):
            termos_sugeridos_brutos = gerar_termos_llm_mock(texto_proposicao, termo_dicionario_txt, num_termos)
            
            st.write("---")
            st.subheader("Resultado do Teste")
            st.write(f"Termos sugeridos pela IA (brutos): **{termos_sugeridos_brutos}**")
            
            termos_finais = aplicar_logica_hierarquia(termos_sugeridos_brutos, mapa_hierarquia_txt)
            st.write(f"Termos finais após a lógica de hierarquia: **{termos_finais}**")
