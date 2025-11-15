import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def app(df_atendimento, df_clientes, df_financeiro, df_marketing, df_vendas):
    st.title("Dashboard: Visão Geral")

    # --- KPI Cards ---
    st.markdown("### Indicadores Chave de Performance")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # Calculate KPIs
    total_receita = df_financeiro['Receita_Bruta'].sum()
    total_lucro = df_financeiro['Lucro_Líquido'].sum()
    margem_percentual = (total_lucro / total_receita) * 100 if total_receita != 0 else 0
    total_vendas = df_vendas['Valor_Total'].sum()
    num_vendas = df_vendas.shape[0]
    ticket_medio = total_vendas / num_vendas if num_vendas != 0 else 0
    investimento_marketing = df_marketing['Investimento'].sum()

    with col1:
        st.metric(label="Receita Total", value=f"R$ {total_receita:,.2f}")
    with col2:
        st.metric(label="Lucro Total", value=f"R$ {total_lucro:,.2f}")
    with col3:
        st.metric(label="Margem (%)", value=f"{margem_percentual:,.2f}%")
    with col4:
        st.metric(label="Total de Vendas", value=f"R$ {total_vendas:,.2f}")
    with col5:
        st.metric(label="Ticket Médio Geral", value=f"R$ {ticket_medio:,.2f}")
    with col6:
        st.metric(label="Investimento Marketing", value=f"R$ {investimento_marketing:,.2f}")

    # --- Gráfico principal de tendência (Receita Bruta e Lucro Líquido Mensal) ---
    st.markdown("### Tendência Mensal: Receita Bruta vs. Lucro Líquido")
    df_financeiro_monthly = df_financeiro.set_index('Mês').resample('MS').agg({
        'Receita_Bruta': 'sum',
        'Lucro_Líquido': 'sum'
    }).reset_index()

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=df_financeiro_monthly['Mês'], y=df_financeiro_monthly['Receita_Bruta'], name='Receita Bruta', marker_color='blue'))
    fig_trend.add_trace(go.Scatter(x=df_financeiro_monthly['Mês'], y=df_financeiro_monthly['Lucro_Líquido'], name='Lucro Líquido', mode='lines+markers', marker_color='green', yaxis='y2'))

    fig_trend.update_layout(
        title_text='Receita Bruta e Lucro Líquido por Mês',
        xaxis_title='Mês',
        yaxis_title='Receita Bruta (R$)',
        yaxis2=dict(
            title='Lucro Líquido (R$)',
            overlaying='y',
            side='right'
        ),
        legend=dict(x=0.1, y=1.1, orientation="h"),
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Receita por Categoria ---
    st.markdown("### Receita por Categoria de Produto")
    receita_por_categoria = df_vendas.groupby('Categoria')['Valor_Total'].sum().reset_index()
    fig_categoria = go.Figure(data=[go.Pie(labels=receita_por_categoria['Categoria'], values=receita_por_categoria['Valor_Total'], hole=.3)])
    fig_categoria.update_layout(title_text='Distribuição da Receita por Categoria')
    st.plotly_chart(fig_categoria, use_container_width=True)

    # --- Margem por Mês (Sparklines - simplified as a line chart for clarity) ---
    st.markdown("### Margem Percentual Mensal")
    
    df_financeiro_monthly_margin = df_financeiro.set_index('Mês').resample('MS')['Margem (%)'].mean().reset_index()
    
    fig_margin = go.Figure(data=go.Scatter(x=df_financeiro_monthly_margin['Mês'], y=df_financeiro_monthly_margin['Margem (%)'], mode='lines+markers', name='Margem (%)', line_color='purple'))
    fig_margin.update_layout(
        title_text='Margem Percentual por Mês',
        xaxis_title='Mês',
        yaxis_title='Margem (%)',
        hovermode="x unified"
    )
    st.plotly_chart(fig_margin, use_container_width=True)
