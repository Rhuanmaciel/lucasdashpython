import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

def app(df_atendimento, df_clientes, df_financeiro, df_marketing, df_vendas):
    st.title("Dashboard: Visão Geral")

    # ==========================================================================================
    #  1. TRATAMENTO E NORMALIZAÇÃO DO DATAFRAME FINANCEIRO (PARA EVITAR DUPLICAÇÕES)
    # ==========================================================================================

    df_financeiro['Receita_Bruta'] = pd.to_numeric(df_financeiro['Receita_Bruta'], errors='coerce').fillna(0)
    df_financeiro['Lucro_Líquido'] = pd.to_numeric(df_financeiro['Lucro_Líquido'], errors='coerce').fillna(0)
    df_financeiro['Despesas_Operacionais'] = pd.to_numeric(df_financeiro['Despesas_Operacionais'], errors='coerce').fillna(0)
    df_financeiro['Margem (%)'] = pd.to_numeric(df_financeiro['Margem (%)'], errors='coerce').fillna(0)

    df_financeiro['Mês'] = pd.to_datetime(df_financeiro['Mês'], errors='coerce')
    df_financeiro['Mês'] = df_financeiro['Mês'].dt.to_period('M').dt.to_timestamp()

    df_financeiro_mensal = df_financeiro.groupby('Mês', as_index=False).agg({
        'Receita_Bruta': 'sum',
        'Despesas_Operacionais': 'sum',
        'Lucro_Líquido': 'sum',
        'Margem (%)': 'mean'
    })

    # ==========================================================================================
    #  2. TRATAMENTO DE OUTRAS TABELAS
    # ==========================================================================================
    df_marketing['Investimento'] = pd.to_numeric(df_marketing['Investimento'], errors='coerce').fillna(0)
    df_vendas['Valor_Total'] = pd.to_numeric(df_vendas['Valor_Total'], errors='coerce').fillna(0)

    # ==========================================================================================
    # 3. KPI CARDS
    # ==========================================================================================
    st.markdown("### Indicadores Chave de Performance")
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_receita = df_financeiro_mensal['Receita_Bruta'].sum()
    total_lucro = df_financeiro_mensal['Lucro_Líquido'].sum()
    margem_percentual = (total_lucro / total_receita * 100) if total_receita > 0 else 0

    total_vendas = df_vendas['Valor_Total'].sum()
    num_vendas = len(df_vendas)
    ticket_medio = total_vendas / num_vendas if num_vendas > 0 else 0

    investimento_marketing = df_marketing['Investimento'].sum()

    with col1:
        st.metric("Receita Total", f"R$ {total_receita:,.2f}")
    with col2:
        st.metric("Lucro Total", f"R$ {total_lucro:,.2f}")
    with col3:
        st.metric("Margem (%)", f"{margem_percentual:,.2f}%")
    with col4:
        st.metric("Total de Vendas", f"R$ {total_vendas:,.2f}")
    with col5:
        st.metric("Ticket Médio Geral", f"R$ {ticket_medio:,.2f}")
    with col6:
        st.metric("Investimento Marketing", f"R$ {investimento_marketing:,.2f}")

    # ==========================================================================================
    # 4. GRÁFICO PRINCIPAL – RECEITA VS LUCRO POR MÊS
    # ==========================================================================================
    st.markdown("### Tendência Mensal: Receita Bruta vs. Lucro Líquido")

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(
        x=df_financeiro_mensal['Mês'],
        y=df_financeiro_mensal['Receita_Bruta'],
        name='Receita Bruta',
        marker_color='blue'
    ))

    fig_trend.add_trace(go.Scatter(
        x=df_financeiro_mensal['Mês'],
        y=df_financeiro_mensal['Lucro_Líquido'],
        name='Lucro Líquido',
        mode='lines+markers',
        marker_color='green',
        yaxis='y2'
    ))

    fig_trend.update_layout(
        title_text="Receita Bruta e Lucro Líquido por Mês",
        xaxis_title="Mês",
        yaxis_title="Receita Bruta (R$)",
        yaxis2=dict(
            title="Lucro Líquido (R$)",
            overlaying="y",
            side="right"
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    # ==========================================================================================
    # 5. RECEITA POR CATEGORIA
    # ==========================================================================================
    st.markdown("### Receita por Categoria de Produto")

    receita_por_categoria = df_vendas.groupby('Categoria')['Valor_Total'].sum().reset_index()

    fig_categoria = go.Figure(data=[
        go.Pie(labels=receita_por_categoria['Categoria'], values=receita_por_categoria['Valor_Total'], hole=.3)
    ])

    fig_categoria.update_layout(title_text="Distribuição da Receita por Categoria")
    st.plotly_chart(fig_categoria, use_container_width=True)

    # ==========================================================================================
    # 6. MARGEM MENSAL
    # ==========================================================================================
    st.markdown("### Margem Percentual Mensal")

    fig_margin = go.Figure(
        data=go.Scatter(
            x=df_financeiro_mensal['Mês'],
            y=df_financeiro_mensal['Margem (%)'],
            mode='lines+markers',
            line_color='purple',
            name='Margem (%)'
        )
    )

    fig_margin.update_layout(
        title_text="Margem Percentual por Mês",
        xaxis_title="Mês",
        yaxis_title="Margem (%)",
        hovermode="x unified"
    )

    st.plotly_chart(fig_margin, use_container_width=True)
