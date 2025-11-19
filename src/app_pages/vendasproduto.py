import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def app(df_vendas):
    st.title("Dashboard: Vendas & Produto")

    df_vendas['Valor_Total'] = pd.to_numeric(df_vendas['Valor_Total'], errors='coerce')
    df_vendas['Data_Venda'] = pd.to_datetime(df_vendas['Data_Venda'], errors='coerce')

    # ==========================================================
    # 1) RECEITA POR CIDADE
    # ==========================================================
    st.markdown("### Receita por Cidade")

    receita_por_cidade = df_vendas.groupby('Cidade')['Valor_Total'].sum().reset_index()

    fig_cidade = px.bar(
        receita_por_cidade,
        x='Cidade',
        y='Valor_Total',
        title='Receita Total por Cidade',
        labels={'Valor_Total': 'Receita Total (R$)'},
        color='Valor_Total',
        color_continuous_scale=px.colors.sequential.Plasma
    )

    # Formatação BR no hover
    fig_cidade.update_traces(
        hovertemplate="<b>Cidade=%{x}</b><br>Receita Total: R$ %{y:,.2f}<extra></extra>"
    )
    fig_cidade.update_yaxes(tickformat=",.2f")

    st.plotly_chart(fig_cidade, use_container_width=True)

    # ==========================================================
    # 2) RECEITA POR CANAL
    # ==========================================================
    st.markdown("### Receita por Canal de Venda")

    receita_por_canal = (
        df_vendas.groupby('Canal_Venda')['Valor_Total']
        .sum()
        .reset_index()
        .sort_values(by='Valor_Total', ascending=False)
    )

    fig_canal = px.bar(
        receita_por_canal,
        x='Canal_Venda',
        y='Valor_Total',
        title='Receita Total por Canal de Venda',
        labels={'Valor_Total': 'Receita Total (R$)'},
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig_canal.update_traces(
        hovertemplate="<b>%{x}</b><br>Receita Total: R$ %{y:,.2f}<extra></extra>"
    )
    fig_canal.update_yaxes(tickformat=",.2f")

    st.plotly_chart(fig_canal, use_container_width=True)

    # ==========================================================
    # 3) RECEITA POR CATEGORIA
    # ==========================================================
    st.markdown("### Receita por Categoria de Produto")

    receita_por_categoria = (
        df_vendas.groupby('Categoria')['Valor_Total']
        .sum()
        .reset_index()
        .sort_values(by='Valor_Total', ascending=False)
    )

    fig_categoria = px.bar(
        receita_por_categoria,
        x='Categoria',
        y='Valor_Total',
        title='Receita Total por Categoria de Produto',
        labels={'Valor_Total': 'Receita Total (R$)'},
        color='Categoria'
    )

    fig_categoria.update_traces(
        hovertemplate="<b>%{x}</b><br>Receita Total: R$ %{y:,.2f}<extra></extra>"
    )
    fig_categoria.update_yaxes(tickformat=",.2f")

    st.plotly_chart(fig_categoria, use_container_width=True)

    # ==========================================================
    # 4) TICKET MÉDIO POR CANAL
    # ==========================================================
    st.markdown("### Ticket Médio por Canal de Venda")

    ticket_medio_por_canal = (
        df_vendas.groupby('Canal_Venda')['Valor_Total']
        .mean()
        .reset_index()
        .sort_values(by='Valor_Total', ascending=False)
    )

    fig_ticket_canal = px.bar(
        ticket_medio_por_canal,
        x='Canal_Venda',
        y='Valor_Total',
        title='Ticket Médio por Canal de Venda',
        labels={'Valor_Total': 'Ticket Médio (R$)'},
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_ticket_canal.update_traces(
        hovertemplate="<b>%{x}</b><br>Ticket Médio: R$ %{y:,.2f}<extra></extra>"
    )
    fig_ticket_canal.update_yaxes(tickformat=",.2f")

    st.plotly_chart(fig_ticket_canal, use_container_width=True)

    # ==========================================================
    # 5) TOP 10 VENDAS RECENTES
    # ==========================================================
    st.markdown("### Top 10 Vendas Recentes")

    top_vendas = df_vendas.sort_values(
        by='Data_Venda',
        ascending=False
    ).head(10)

    # Aplicar formatação
    top_vendas_display = top_vendas.copy()
    top_vendas_display['Valor_Total'] = top_vendas_display['Valor_Total'].apply(formatar_moeda)
    top_vendas_display['Data_Venda'] = top_vendas_display['Data_Venda'].dt.strftime("%d/%m/%Y")

    st.dataframe(
        top_vendas_display[['Data_Venda', 'Cidade', 'Categoria', 'Canal_Venda', 'Valor_Total']],
        use_container_width=True
    )
