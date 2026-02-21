import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(page_title="DEBUG PUBG Ranking", layout="wide")

def get_data_diagnostic():
    try:
        # Recomendo fortemente usar a porta 5432 na URL do segredo
        db_url = st.secrets["DATABASE_URL"]
        engine = create_engine(db_url, pool_pre_ping=True)
        
        with engine.connect() as conn:
            # Força o banco a liberar dados novos
            conn.execute(text("COMMIT"))
            
            # Query com timestamp para matar qualquer cache no provedor
            query = f"SELECT * FROM ranking_squad -- {time.time()}"
            df = pd.read_sql(text(query), conn)
            
            # Pega o horário da última atualização do próprio banco (se a coluna existir)
            # Ou apenas conta as linhas
            count_rows = len(df)
            
        return df, count_rows
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame(), 0

# =============================
# INTERFACE DE DIAGNÓSTICO
# =============================
st.title("🎮 PUBG Squad - Verificação de Dados")

df_bruto, total_linhas = get_data_diagnostic()

# Painel de Controle lateral
with st.sidebar:
    st.header("🔍 Diagnóstico")
    st.write(f"**Total de linhas no banco:** {total_linhas}")
    st.write(f"**Última leitura:** {time.strftime('%H:%M:%S')}")
    
    if st.button("♻️ Limpar Tudo e Recarregar"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

if not df_bruto.empty:
    # --- AQUI ESTÁ O TRUQUE PARA SABER SE ESTÁ ATUALIZADO ---
    st.subheader("👀 Visualização Bruta (Primeiras 5 linhas)")
    # Mostramos o DF sem cálculos para ver se o número de partidas bate com o banco
    st.table(df_bruto[['nick', 'partidas', 'vitorias', 'kr']].head(5))
    
    st.markdown("---")

    # Tratamento de dados
    df_bruto['partidas'] = pd.to_numeric(df_bruto['partidas'], errors='coerce').fillna(1).replace(0, 1)
    
    tab1, tab2, tab3 = st.tabs(["🔥 PRO", "🤝 TEAM", "🎯 ELITE"])

    def mostrar_ranking(df_temp, formula, col_nome):
        df_temp[col_nome] = formula.round(2)
        # Ordenação agressiva: o maior score vai para o topo
        df_temp = df_temp.sort_values(by=col_nome, ascending=False).reset_index(drop=True)
        
        # Recalcula as zonas baseado na nova ordem
        total = len(df_temp)
        def definir_zona(i):
            if i < 3: return "Elite Zone"
            if i >= total - 3: return "Cocô Zone"
            return "Medíocre Zone"
        
        df_temp['Classificação'] = [definir_zona(i) for i in range(total)]
        
        st.dataframe(
            df_temp[['nick', 'partidas', 'vitorias', 'kr', col_nome, 'Classificação']].style
            .background_gradient(cmap='YlGn', subset=[col_nome])
            .apply(lambda x: ['background-color: #004d00' if x.Classificação == "Elite Zone" 
                              else 'background-color: #4d2600' if x.Classificação == "Cocô Zone" 
                              else '' for _ in x], axis=1),
            use_container_width=True
        )

    with tab1:
        f_pro = (df_bruto['kr'] * 40) + (df_bruto['dano_medio'] / 8) + ((df_bruto['vitorias'] / df_bruto['partidas']) * 500)
        mostrar_ranking(df_bruto.copy(), f_pro, "Score_Pro")

    with tab2:
        f_team = ((df_bruto['vitorias'] / df_bruto['partidas']) * 1000) + ((df_bruto['revives'] / df_bruto['partidas']) * 50)
        mostrar_ranking(df_bruto.copy(), f_team, "Score_Team")

    with tab3:
        f_elite = (df_bruto['kr'] * 50) + (df_bruto['dano_medio'] / 5)
        mostrar_ranking(df_bruto.copy(), f_elite, "Score_Elite")

else:
    st.warning("O DataFrame está vindo vazio. Verifique se o nome da tabela é 'ranking_squad' no schema 'public'.")
