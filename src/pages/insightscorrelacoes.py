import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def app(df_atendimento, df_financeiro, df_vendas, df_marketing):

    st.title("Dashboard: Insights & Correlações")

    # -----------------------------------------------------------
    # 🛠️ CORREÇÃO DA COLUNA "Margem (%)"
    # -----------------------------------------------------------
    if 'Margem (%)' in df_financeiro.columns:

        df_financeiro['Margem (%)'] = (
            df_financeiro['Margem (%)']
                .astype(str)
                .str.replace(',', '.', regex=False)
                .str.extract(r'([-]?\d*\.?\d+)')
        )

        df_financeiro['Margem (%)'] = pd.to_numeric(
            df_financeiro['Margem (%)'], 
            errors='coerce'
        )

    # -----------------------------------------------------------
    # 1) Receita mensal (vendas) × Lucro mensal (financeiro)
    # -----------------------------------------------------------

    st.markdown("### Receita Mensal (Vendas) vs. Lucro Mensal (Financeiro)")

    df_vendas['Mês'] = df_vendas['Data_Venda'].dt.to_period('M').dt.to_timestamp()
    receita_vendas_mensal = df_vendas.groupby('Mês')['Valor_Total'].sum().reset_index()

    df_financeiro['Mês'] = df_financeiro['Mês'].dt.to_period('M').dt.to_timestamp()
    lucro_financeiro_mensal = df_financeiro.groupby('Mês')['Lucro_Líquido'].sum().reset_index()

    df_merged_fin_vendas = pd.merge(
        receita_vendas_mensal,
        lucro_financeiro_mensal,
        on='Mês',
        how='outer'
    ).fillna(0)

    df_merged_fin_vendas.rename(columns={
        'Valor_Total': 'Receita_Vendas',
        'Lucro_Líquido': 'Lucro_Financeiro'
    }, inplace=True)

    fig_fin_vendas = go.Figure()
    fig_fin_vendas.add_trace(go.Scatter(
        x=df_merged_fin_vendas['Mês'],
        y=df_merged_fin_vendas['Receita_Vendas'],
        mode='lines+markers',
        name='Receita de Vendas',
        line_color='blue'
    ))
    fig_fin_vendas.add_trace(go.Scatter(
        x=df_merged_fin_vendas['Mês'],
        y=df_merged_fin_vendas['Lucro_Financeiro'],
        mode='lines+markers',
        name='Lucro Financeiro',
        line_color='green'
    ))

    fig_fin_vendas.update_layout(
        title='Receita de Vendas vs. Lucro Financeiro por Mês',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        hovermode="x unified"
    )
    st.plotly_chart(fig_fin_vendas, use_container_width=True)

    # -----------------------------------------------------------
    # 2) Investimento em marketing × Receita total do mês
    # -----------------------------------------------------------

    st.markdown("### Investimento em Marketing vs. Receita Total do Mês")

    df_marketing['Mês'] = df_marketing['Data_Campanha'].dt.to_period('M').dt.to_timestamp()
    investimento_mensal = df_marketing.groupby('Mês')['Investimento'].sum().reset_index()

    receita_total_mensal = df_financeiro.groupby('Mês')['Receita_Bruta'].sum().reset_index()

    df_merged_marketing_receita = pd.merge(
        investimento_mensal,
        receita_total_mensal,
        on='Mês',
        how='outer'
    ).fillna(0)

    df_merged_marketing_receita.rename(columns={
        'Receita_Bruta': 'Receita_Total'
    }, inplace=True)

    fig_marketing_receita = go.Figure()
    fig_marketing_receita.add_trace(go.Bar(
        x=df_merged_marketing_receita['Mês'],
        y=df_merged_marketing_receita['Investimento'],
        name='Investimento Marketing',
        marker_color='orange'
    ))
    fig_marketing_receita.add_trace(go.Scatter(
        x=df_merged_marketing_receita['Mês'],
        y=df_merged_marketing_receita['Receita_Total'],
        mode='lines+markers',
        name='Receita Total',
        line_color='purple',
        yaxis='y2'
    ))

    fig_marketing_receita.update_layout(
        title='Investimento em Marketing vs. Receita Total por Mês',
        xaxis_title='Mês',
        yaxis_title='Investimento (R$)',
        yaxis2=dict(
            title='Receita Total (R$)',
            overlaying='y',
            side='right'
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig_marketing_receita, use_container_width=True)

    # -----------------------------------------------------------
    # 3) Tickets por canal × Vendas por canal (AJUSTE DO EIXO X)
    # -----------------------------------------------------------

    st.markdown("### Tickets de Atendimento vs. Vendas por Canal")

    tickets_por_canal = df_atendimento.groupby('Canal').size().reset_index(name='Total_Tickets')

    vendas_por_canal = df_vendas.groupby('Canal_Venda')['Valor_Total'].sum().reset_index()
    vendas_por_canal.rename(columns={'Canal_Venda': 'Canal'}, inplace=True)

    df_merged_canal = pd.merge(
        tickets_por_canal,
        vendas_por_canal,
        on='Canal',
        how='outer'
    ).fillna(0)

    df_merged_canal['Tickets_Por_100_Vendas'] = (
        df_merged_canal['Total_Tickets'] / (df_merged_canal['Valor_Total'] / 100).replace(0, 1)
    )

    # Valor máximo real para ajustar o eixo
    max_vendas = df_merged_canal['Valor_Total'].max()

    fig_tickets_vendas_canal = px.scatter(
        df_merged_canal,
        x='Valor_Total',
        y='Total_Tickets',
        size='Tickets_Por_100_Vendas',
        color='Canal',
        hover_name='Canal',
        title='Tickets de Atendimento vs. Vendas por Canal',
        labels={
            'Valor_Total': 'Total de Vendas (R$)',
            'Total_Tickets': 'Total de Tickets'
        }
    )

    # 🔥 AQUI ESTÁ A CORREÇÃO DO GRÁFICO
    fig_tickets_vendas_canal.update_layout(
        xaxis=dict(
            range=[0, max_vendas * 1.1]  # deixa 10% de folga
        )
    )

    st.plotly_chart(fig_tickets_vendas_canal, use_container_width=True)
