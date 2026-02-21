import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(page_title="PUBG Ranking Squad", layout="wide")

st.title("🏆 PUBG Ranking - Squad")

# ==============================
# CONEXÃO COM BANCO (SUPABASE)
# ==============================
def get_engine():
    return create_engine(st.secrets["DATABASE_URL"])

# ==============================
# BUSCAR DADOS ATUALIZADOS
# ==============================
def carregar_dados():
    try:
        engine = get_engine()

        query = """
        SELECT nick, score, partidas
        FROM ranking_squad
        ORDER BY score DESC
        """

        df = pd.read_sql(query, engine)

        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# ==============================
# ATUALIZAR PARTIDAS (TESTE)
# ==============================
def atualizar_partidas():
    try:
        engine = get_engine()

        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE ranking_squad
                SET partidas = partidas + 1
            """))

        st.success("✅ Partidas atualizadas com sucesso!")

    except Exception as e:
        st.error(f"Erro ao atualizar banco: {e}")

# ==============================
# BOTÃO DE ATUALIZAÇÃO
# ==============================
if st.button("🔄 Atualizar Banco"):
    atualizar_partidas()

# ==============================
# EXIBIR TABELA
# ==============================
df = carregar_dados()

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Nenhum dado encontrado na tabela ranking_squad.")
