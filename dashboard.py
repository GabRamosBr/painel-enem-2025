import streamlit as st
import duckdb
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Painel ENEM 2025", layout="wide")

st.title("📊 Portal de Resultados ENEM 2025")
st.write("Consulta o ranking ou descobre a tua posição exata no Brasil, Estado e Cidade.")

# Caminho do ficheiro otimizado
FICHEIRO_PARQUET = "dados_enem_2025_part_*.parquet"

# ====================================================================
# CRIAÇÃO DAS ABAS NA INTERFACE
# ====================================================================
aba_busca, aba_ranking = st.tabs(["🔍 Descobrir Minha Posição", "🏆 Ranking Geral"])

# ====================================================================
# ABA 1: DESCOBRIR MINHA POSIÇÃO (Lógica para os teus amigos)
# ====================================================================
with aba_busca:
    st.subheader("Introduz as tuas informações para calcular a tua posição")
    st.write("Como a TRI gera notas muito específicas, a combinação da tua Cidade + Notas funciona como uma chave única.")
    
    # Carregar listas para os menus dinamicamente via SQL (rápido e leve)
    lista_ufs = duckdb.query(f"SELECT DISTINCT SG_UF_PROVA FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA IS NOT NULL ORDER BY SG_UF_PROVA").to_df()['SG_UF_PROVA'].tolist()
    
    col_uf, col_cidade = st.columns(2)
    with col_uf:
        uf_amigo = st.selectbox("Selecione o Estado (UF) onde fez a prova", lista_ufs, key="uf_amigo")
    with col_cidade:
        lista_cidades = duckdb.query(f"SELECT DISTINCT NO_MUNICIPIO_PROVA FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA = '{uf_amigo}' ORDER BY NO_MUNICIPIO_PROVA").to_df()['NO_MUNICIPIO_PROVA'].tolist()
        cidade_amigo = st.selectbox("Selecione a Cidade onde fez a prova", lista_cidades, key="cidade_amigo")
        
    st.write("---")
    st.write("**Insira as suas notas exatas (pode usar vírgula ou ponto):**")
    
    # Função para o Python aceitar a vírgula, trocar por ponto invisivelmente e converter para matemática
    def tratar_nota(valor_texto):
        if not valor_texto: # Se o amigo deixar em branco
            return 0.0
        try:
            return float(valor_texto.replace(",", "."))
        except ValueError:
            return 0.0 # Se o amigo digitar letras sem querer, o Python não quebra
            
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: nota_cn = tratar_nota(st.text_input("Ciências da Natureza", value="0"))
    with c2: nota_ch = tratar_nota(st.text_input("Ciências Humanas", value="0"))
    with c3: nota_lc = tratar_nota(st.text_input("Linguagens e Códigos", value="0"))
    with c4: nota_mt = tratar_nota(st.text_input("Matemática", value="0"))
    with c5: nota_red = tratar_nota(st.text_input("Redação", value="0"))
    if st.button("Calcular Minha Posição no Ranking", type="primary"):
        # Calcula a média simples do utilizador
        media_usuario = (nota_cn + nota_ch + nota_lc + nota_mt + nota_red) / 5
        
        with st.spinner("Cruzando dados com os milhões de participantes..."):
            # LÓGICA DA ARQUITETURA:
            # Contamos quantos candidatos têm a MEDIA_GERAL maior do que a do utilizador.
            # A posição dele será esse total + 1.
            
            # 1. Posição Nacional
            pos_nacional = duckdb.query(f"SELECT COUNT(*) FROM '{FICHEIRO_PARQUET}' WHERE MEDIA_GERAL > {media_usuario}").fetchone()[0] + 1
            total_nacional = duckdb.query(f"SELECT COUNT(*) FROM '{FICHEIRO_PARQUET}'").fetchone()[0]
            
            # 2. Posição Estadual
            pos_estadual = duckdb.query(f"SELECT COUNT(*) FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA = '{uf_amigo}' AND MEDIA_GERAL > {media_usuario}").fetchone()[0] + 1
            total_estadual = duckdb.query(f"SELECT COUNT(*) FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA = '{uf_amigo}'").fetchone()[0]
            
            # 3. Posição Municipal
            pos_municipal = duckdb.query(f"SELECT COUNT(*) FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA = '{uf_amigo}' AND NO_MUNICIPIO_PROVA = '{cidade_amigo}' AND MEDIA_GERAL > {media_usuario}").fetchone()[0] + 1
            total_municipal = duckdb.query(f"SELECT COUNT(*) FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA = '{uf_amigo}' AND NO_MUNICIPIO_PROVA = '{cidade_amigo}'").fetchone()[0]
            
        # Exibição dos resultados em painéis de métricas
        st.success(f"Calculado com sucesso! A tua Média Geral foi: **{media_usuario:.2f}**")
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="📍 Posição na tua Cidade", value=f"{pos_municipal}º", delta=f"de {total_municipal} alunos", delta_color="inverse")
        with m2:
            st.metric(label="🏢 Posição no teu Estado", value=f"{pos_estadual}º", delta=f"de {total_estadual} alunos", delta_color="inverse")
        with m3:
            st.metric(label="🇧🇷 Posição no Brasil", value=f"{pos_nacional}º", delta=f"de {total_nacional} alunos", delta_color="inverse")

# ====================================================================
# ABA 2: RANKING GERAL (O painel que já tinhas construído)
# ====================================================================
with aba_ranking:
    st.subheader("Filtros do Ranking")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_uf = st.selectbox("Filtrar por UF", ["Todos"] + lista_ufs)
    with col_f2:
        if filtro_uf != "Todos":
            lista_cidades_filtro = duckdb.query(f"SELECT DISTINCT NO_MUNICIPIO_PROVA FROM '{FICHEIRO_PARQUET}' WHERE SG_UF_PROVA = '{filtro_uf}' ORDER BY NO_MUNICIPIO_PROVA").to_df()['NO_MUNICIPIO_PROVA'].tolist()
        else:
            lista_cidades_filtro = duckdb.query(f"SELECT DISTINCT NO_MUNICIPIO_PROVA FROM '{FICHEIRO_PARQUET}' ORDER BY NO_MUNICIPIO_PROVA").to_df()['NO_MUNICIPIO_PROVA'].tolist()
        filtro_cidade = st.selectbox("Filtrar por Cidade", ["Todas"] + lista_cidades_filtro)
    with col_f3:
        filtro_escola = st.text_input("Código da Escola (Opcional)", placeholder="Ex: 41355644")

    # Construção da Query SQL Dinâmica baseada nos filtros selecionados
    query_base = f"SELECT CO_ESCOLA, NO_MUNICIPIO_PROVA, SG_UF_PROVA, NU_NOTA_CN, NU_NOTA_CH, NU_NOTA_LC, NU_NOTA_MT, NU_NOTA_REDACAO, MEDIA_GERAL FROM '{FICHEIRO_PARQUET}' WHERE 1=1"
    
    if filtro_uf != "Todos":
        query_base += f" AND SG_UF_PROVA = '{filtro_uf}'"
    if filtro_cidade != "Todas":
        query_base += f" AND NO_MUNICIPIO_PROVA = '{filtro_cidade}'"
    if filtro_escola:
        try:
            cod_esc = float(filtro_escola)
            query_base += f" AND CO_ESCOLA = {cod_esc}"
        except ValueError:
            st.error("Insira um código de escola válido.")

    # Ordena e limita às 1.000 maiores notas diretamente no SQL (máxima eficiência)
    query_base += " ORDER BY MEDIA_GERAL DESC LIMIT 2000"
    
    with st.spinner("A atualizar ranking..."):
        df_ranking = duckdb.query(query_base).to_df()
    
    # Cria a coluna de posição para o bloco filtrado
    df_ranking.insert(0, 'POSIÇÃO', range(1, len(df_ranking) + 1))
    
    st.write(f"**Total de alunos encontrados neste filtro:** {len(df_ranking)}")
    st.dataframe(df_ranking, use_container_width=True, hide_index=True)
