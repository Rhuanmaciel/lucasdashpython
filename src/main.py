import streamlit.web.bootstrap
streamlit.web.bootstrap._is_running_with_streamlit = lambda: False

import streamlit as st
from data_handler import load_data
from app_pages import visaogeral, vendasproduto, marketing, atendimento

# ==== TÍTULO DA ABA DO NAVEGADOR ====
st.set_page_config(
    page_title="EcoMov",   # <- Nome que aparece na aba do Google/Chrome
    layout="wide"
)

st.sidebar.title("Navegação")
st.sidebar.markdown("Selecione uma página abaixo:")

# Load data once
df_atendimento, df_clientes, df_financeiro, df_marketing, df_vendas = load_data()

page = st.sidebar.selectbox(
    "Escolha o Dashboard",
    [
        "Visão Geral",
        "Vendas & Produto",
        "Marketing",
        "Atendimento",
    ],
)

if page == "Visão Geral":
    visaogeral.app(df_atendimento, df_clientes, df_financeiro, df_marketing, df_vendas)
elif page == "Vendas & Produto":
    vendasproduto.app(df_vendas)
elif page == "Marketing":
    marketing.app(df_marketing, df_financeiro)
elif page == "Atendimento":
    atendimento.app(df_atendimento)
