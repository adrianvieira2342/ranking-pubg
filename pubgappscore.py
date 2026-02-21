import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(
    page_title="PUBG Squad Ranking",
    layout="wide",
    page_icon="🎮"
)

# =============================
# FUNÇÃO DE BUSCA REAL NO BANCO
# =============================
def get_data_fresh():
    try:
        # Pega a URL dos Secrets
        db_url = st.secrets["DATABASE_URL"]
        
        # Criamos o motor de conexão configurado para NÃO guardar cache
        # isolation_level="AUTOCOMMIT" garante que ele leia dados commitados AGORA
        engine = create_engine(
            db_url, 
            pool_pre_ping=True,
            pool_recycle=0,
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )
        
        with engine.connect() as conn:
            # O Segredo: Comentário dinâmico na query impede o cache do Supabase
            query = text(f"SELECT * FROM ranking_squad -- refresh_{int(time.time())}")
            df = pd.read_sql(query, conn)
            return df
    except Exception as e:
        st.error(f"Erro ao buscar dados reais: {e}")
        return pd.DataFrame()

# =============================
# INTERFACE E PROCESSAMENTO
# =============================
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.markdown("# 🎮 Ranking Squad - Season 40")
with col2:
    # Botão que limpa o cache do Streamlit e força o rerun
    if st.button("🔄 Sincronizar Agora"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

st.markdown("---")

# Busca os dados atuais diretamente do banco
df_bruto = get_data_fresh()

if not df_bruto.empty:
    # Garante que as colunas numéricas sejam tratadas
    df_bruto['partidas'] = pd.to_numeric(df_bruto['partidas'], errors='coerce').fillna(1).replace(0, 1)

    # --- ABAIXO SEGUE SEU LAYOUT ORIGINAL ---
    tab1, tab2, tab3 = st.tabs(["🔥 PRO", "🤝 TEAM", "🎯 ELITE"])

    def renderizar_ranking(df_local, col_score, formula):
        df_local[col_score] = formula.round(2)
        ranking_ordenado = df_local.sort_values(col_score, ascending=False).reset_index(drop=True)
        
        # Lógica de medalhas e tabela (Mantenha sua lógica original aqui...)
        st.dataframe(ranking_ordenado, use_container_width=True) 

    # Chamadas das abas com as suas fórmulas...
    with tab1:
        f_pro = (df_bruto['kr'] * 40) + (df_bruto['dano_medio'] / 8) + ((df_bruto['vitorias'] / df_bruto['partidas']) * 500)
        # renderizar_ranking(...) 
else:
    st.warning("O banco de dados está vazio ou não pôde ser acessado.")
