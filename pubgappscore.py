import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time

# =============================
# CONFIGURAÇÃO DA PÁGINA
# =============================
st.set_page_config(page_title="PUBG Squad Ranking", layout="wide", page_icon="🎮")

# =============================
# CONEXÃO DE EMERGÊNCIA (SEM CACHE)
# =============================
def get_data_absolute_fresh():
    try:
        # Pega a URL. Tente trocar a porta 6543 por 5432 na sua secret se possível.
        db_url = st.secrets["DATABASE_URL"]
        
        # Criamos o engine com 'isolation_level' para ler dados commitados na hora
        engine = create_engine(
            db_url, 
            isolation_level="READ COMMITTED",
            pool_pre_ping=True,
            pool_recycle=0
        )
        
        with engine.connect() as conn:
            # Forçamos o fechamento de qualquer transação pendente no banco
            conn.execute(text("COMMIT")) 
            
            # Query com cache buster (timestamp aleatório no comentário)
            query = text(f"SELECT * FROM ranking_squad -- refresh_{int(time.time())}")
            df = pd.read_sql(query, conn)
            
        return df
    except Exception as e:
        st.error(f"Erro na leitura: {e}")
        return pd.DataFrame()

# =============================
# LÓGICA DE INTERFACE
# =============================
st.title("🎮 PUBG Squad Ranking")

# Barra lateral para controle de dados
with st.sidebar:
    st.header("⚙️ Controles")
    if st.button("🔄 SINCRONIZAR BANCO AGORA"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    st.write(f"Última tentativa: {time.strftime('%H:%M:%S')}")

# Busca os dados
df_bruto = get_data_absolute_fresh()

if not df_bruto.empty:
    # Tratamento de erro: converte colunas para numérico (caso o banco envie strings)
    cols_para_fix = ['partidas', 'vitorias', 'kr', 'dano_medio', 'headshots', 'assists', 'revives']
    for col in cols_para_fix:
        if col in df_bruto.columns:
            df_bruto[col] = pd.to_numeric(df_bruto[col], errors='coerce').fillna(0)

    # Evita divisão por zero
    df_bruto['partidas'] = df_bruto['partidas'].replace(0, 1)

    # --- SISTEMA DE TABS ---
    tab1, tab2, tab3 = st.tabs(["🔥 PRO", "🤝 TEAM", "🎯 ELITE"])

    def processar_e_exibir(df_input, col_score, formula):
        df_input[col_score] = formula.round(2)
        # Ordenação REAL por score atualizado
        df_final = df_input.sort_values(by=col_score, ascending=False).reset_index(drop=True)
        
        # Gera posições e emojis baseados nos dados NOVOS
        total = len(df_final)
        labels = []
        nicks_formatados = []
        
        for i, row in df_final.iterrows():
            pos = i + 1
            nick = str(row['nick']).replace("💀", "").replace("💩", "").replace("👤", "").strip()
            
            if pos <= 3:
                labels.append("Elite Zone")
                nicks_formatados.append(f"💀 {nick}")
            elif pos > (total - 3) and total > 5:
                labels.append("Cocô Zone")
                nicks_formatados.append(f"💩 {nick}")
            else:
                labels.append("Medíocre Zone")
                nicks_formatados.append(f"👤 {nick}")
        
        df_final['Classificação'] = labels
        df_final['nick'] = nicks_formatados
        df_final['Pos'] = range(1, total + 1)

        # Exibição
        st.dataframe(
            df_final.style
            .apply(lambda r: ['background-color: #004d00' if r['Classificação'] == "Elite Zone" 
                              else 'background-color: #4d2600' if r['Classificação'] == "Cocô Zone" 
                              else '' for _ in r], axis=1)
            .background_gradient(cmap='YlGnBu', subset=[col_score]),
            use_container_width=True, height=500, hide_index=True
        )

    with tab1:
        f = (df_bruto['kr'] * 40) + (df_bruto['dano_medio'] / 8) + ((df_bruto['vitorias'] / df_bruto['partidas']) * 500)
        processar_e_exibir(df_bruto.copy(), 'Score_Pro', f)

    with tab2:
        f = ((df_bruto['vitorias'] / df_bruto['partidas']) * 1000) + ((df_bruto['revives'] / df_bruto['partidas']) * 50) + ((df_bruto['assists'] / df_bruto['partidas']) * 35)
        processar_e_exibir(df_bruto.copy(), 'Score_Team', f)

    with tab3:
        f = (df_bruto['kr'] * 50) + ((df_bruto['headshots'] / df_bruto['partidas']) * 60) + (df_bruto['dano_medio'] / 5)
        processar_e_exibir(df_bruto.copy(), 'Score_Elite', f)

else:
    st.info("Aguardando dados... Se você atualizou o banco agora, clique no botão de Sincronizar.")
