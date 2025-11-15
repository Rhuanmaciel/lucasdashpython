import streamlit as st
from data_handler import load_data
from pages import visaogeral
from pages import vendasproduto
from pages import marketing
from pages import atendimento
from pages import insightscorrelacoes

st.set_page_config(layout="wide")

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
        "Insights & Correlações",
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
elif page == "Insights & Correlações":
    insightscorrelacoes.app(df_atendimento, df_financeiro, df_vendas, df_marketing)