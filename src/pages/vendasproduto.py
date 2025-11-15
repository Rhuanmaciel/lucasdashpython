import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def app(df_vendas):
    st.title("Dashboard: Vendas & Produto")

    # --- Mapa por cidade (Heatmap) ---
    st.markdown("### Receita por Cidade")
    receita_por_cidade = df_vendas.groupby('Cidade')['Valor_Total'].sum().reset_index()
    
    # To display on a map, we'd ideally need geographical coordinates.
    # For now, a bar chart serves as a good proxy for "heatmap" by value.
    fig_cidade = px.bar(receita_por_cidade, x='Cidade', y='Valor_Total', 
                        title='Receita Total por Cidade',
                        labels={'Valor_Total': 'Receita Total (R$)'},
                        color='Valor_Total',
                        color_continuous_scale=px.colors.sequential.Plasma)
    st.plotly_chart(fig_cidade, use_container_width=True)

    # --- Receita por Canal de Venda ---
    st.markdown("### Receita por Canal de Venda")
    receita_por_canal = df_vendas.groupby('Canal_Venda')['Valor_Total'].sum().reset_index().sort_values(by='Valor_Total', ascending=False)
    fig_canal = px.bar(receita_por_canal, x='Canal_Venda', y='Valor_Total', 
                       title='Receita Total por Canal de Venda',
                       labels={'Valor_Total': 'Receita Total (R$)'},
                       color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_canal, use_container_width=True)

    # --- Receita por Categoria ---
    st.markdown("### Receita por Categoria de Produto")
    receita_por_categoria = df_vendas.groupby('Categoria')['Valor_Total'].sum().reset_index().sort_values(by='Valor_Total', ascending=False)
    fig_categoria = px.bar(receita_por_categoria, x='Categoria', y='Valor_Total', 
                           title='Receita Total por Categoria de Produto',
                           labels={'Valor_Total': 'Receita Total (R$)'},
                           color='Categoria') # Different colors for each category
    st.plotly_chart(fig_categoria, use_container_width=True)

    # --- Ticket médio por canal ---
    st.markdown("### Ticket Médio por Canal de Venda")
    ticket_medio_por_canal = df_vendas.groupby('Canal_Venda')['Valor_Total'].mean().reset_index().sort_values(by='Valor_Total', ascending=False)
    fig_ticket_canal = px.bar(ticket_medio_por_canal, x='Canal_Venda', y='Valor_Total', 
                              title='Ticket Médio por Canal de Venda',
                              labels={'Valor_Total': 'Ticket Médio (R$)'},
                              color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_ticket_canal, use_container_width=True)

    # --- Tabela "Top 10 vendas do mês" ---
    st.markdown("### Top 10 Vendas Recentes")
    # Ensure 'Data_Venda' is datetime and sort
    df_vendas['Data_Venda'] = pd.to_datetime(df_vendas['Data_Venda'])
    top_vendas = df_vendas.sort_values(by='Data_Venda', ascending=False).head(10)
    st.dataframe(top_vendas[['Data_Venda', 'Cidade', 'Categoria', 'Canal_Venda', 'Valor_Total']])
