import streamlit as st
import pandas as pd
import plotly.express as px

def app(df_clientes):
    st.title("Análise de Clientes")
    # Garantias finais (apenas segurança)
    df_clientes["Renda"] = pd.to_numeric(df_clientes["Renda"], errors="coerce")
    df_clientes["Data_Cadastro"] = pd.to_datetime(df_clientes["Data_Cadastro"], errors="coerce")

    # ================================================================
    # 1. Perfil Demográfico
    # ================================================================
    st.header("1. Análise de Perfil Demográfico")

    # PF vs PJ
    st.subheader("Distribuição de Clientes por Tipo (PF vs. PJ)")
    type_counts = df_clientes['Tipo'].value_counts().reset_index()
    type_counts.columns = ['Tipo', 'Contagem']
    fig_type = px.pie(
        type_counts, values='Contagem', names='Tipo',
        title='Proporção de Clientes PF vs. PJ', hole=0.3
    )
    st.plotly_chart(fig_type)

    # Distribuição por gênero
    st.subheader("Distribuição de Clientes por Gênero")
    gender_counts = df_clientes['Gênero'].value_counts().reset_index()
    gender_counts.columns = ['Gênero', 'Contagem']
    fig_gender = px.bar(
        gender_counts, x='Gênero', y='Contagem',
        title='Distribuição de Clientes por Gênero'
    )
    fig_gender.update_layout(yaxis_tickformat=",")
    fig_gender.update_traces(
        hovertemplate='Gênero: %{x}<br>Contagem: %{y:,}<extra></extra>'
    )
    st.plotly_chart(fig_gender)

    # Faixa etária
    st.subheader("Distribuição de Clientes por Faixa Etária")
    fig_age = px.histogram(
        df_clientes, x='Idade', nbins=10,
        title='Distribuição de Idade dos Clientes'
    )
    fig_age.update_layout(xaxis_tickformat=",", yaxis_tickformat=",")
    fig_age.update_traces(
        hovertemplate='Idade: %{x}<br>Contagem: %{y:,}<extra></extra>'
    )
    st.plotly_chart(fig_age)

    # ================================================================
    # 2. Análise Financeira
    # ================================================================
    st.header("2. Análise Financeira (Renda)")

    # Renda média por cidade
    st.subheader("Renda Média por Cidade")
    avg_income_city = (
        df_clientes.groupby('Cidade')['Renda']
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_income_city = px.bar(
        avg_income_city, x='Renda', y='Cidade',
        orientation='h', title='Renda Média por Cidade'
    )
    fig_income_city.update_layout(
        xaxis_tickprefix="R$ ", 
        xaxis_tickformat=",.2f"
    )
    fig_income_city.update_traces(
        hovertemplate='Cidade: %{y}<br>Renda = R$ %{x:,.2f}<extra></extra>'
    )
    st.plotly_chart(fig_income_city)

    # Renda por tipo
    st.subheader("Renda Média por Tipo de Cliente (PF vs. PJ)")
    avg_income_type = df_clientes.groupby('Tipo')['Renda'].mean().reset_index()
    fig_income_type = px.bar(
        avg_income_type, x='Tipo', y='Renda',
        title='Renda Média por Tipo de Cliente'
    )
    fig_income_type.update_layout(
        yaxis_tickprefix="R$ ", 
        yaxis_tickformat=",.2f"
    )
    fig_income_type.update_traces(
        hovertemplate='Tipo: %{x}<br>Renda média = R$ %{y:,.2f}<extra></extra>'
    )
    st.plotly_chart(fig_income_type)

    # Boxplot renda
    st.subheader("Dispersão da Renda dos Clientes")
    fig_boxplot_income = px.box(
        df_clientes, y='Renda',
        title='Boxplot da Renda dos Clientes'
    )
    fig_boxplot_income.update_layout(
        yaxis_tickprefix="R$ ", 
        yaxis_tickformat=",.2f"
    )
    fig_boxplot_income.update_traces(
        hovertemplate='Renda: R$ %{y:,.2f}<extra></extra>'
    )
    st.plotly_chart(fig_boxplot_income)

    # ================================================================
    # 3. Análise Temporal
    # ================================================================
    st.header("3. Análise Temporal (Evolução)")

    df_clientes['Ano_Mes_Cadastro'] = df_clientes['Data_Cadastro'].dt.to_period('M').astype(str)

    # Cadastros por mês
    st.subheader("Novos Cadastros por Mês/Ano")
    monthly = df_clientes.groupby('Ano_Mes_Cadastro').size().reset_index(name='Contagem')
    fig_monthly = px.line(
        monthly, x='Ano_Mes_Cadastro', y='Contagem',
        title='Novos Cadastros por Mês/Ano', markers=True
    )
    fig_monthly.update_layout(yaxis_tickformat=",")
    fig_monthly.update_traces(
        hovertemplate='Período: %{x}<br>Cadastros: %{y:,}<extra></extra>'
    )
    st.plotly_chart(fig_monthly)

    # Renda por mês
    st.subheader("Evolução da Renda Média dos Novos Entrantes")
    avg_income_month = (
        df_clientes.groupby('Ano_Mes_Cadastro')['Renda']
        .mean().reset_index()
    )
    fig_avg_income = px.line(
        avg_income_month, x='Ano_Mes_Cadastro', y='Renda',
        title='Renda Média dos Novos Entrantes por Mês/Ano', markers=True
    )
    fig_avg_income.update_layout(
        yaxis_tickprefix="R$ ",
        yaxis_tickformat=",.2f"
    )
    fig_avg_income.update_traces(
        hovertemplate='Período: %{x}<br>Renda média: R$ %{y:,.2f}<extra></extra>'
    )
    st.plotly_chart(fig_avg_income)

    # ================================================================
    # 4. Correlação
    # ================================================================
    st.header("4. Análise de Correlação (Multivariada)")

    st.subheader("Idade vs. Renda")
    fig_scatter = px.scatter(
        df_clientes,
        x='Idade',
        y='Renda',
        color='Tipo',
        hover_data=['Cidade'],
        title='Idade vs. Renda (Colorido por Tipo de Cliente)'
    )
    fig_scatter.update_layout(
        yaxis_tickprefix="R$ ",
        yaxis_tickformat=",.2f"
    )
    fig_scatter.update_traces(
        hovertemplate='Idade: %{x}<br>Renda: R$ %{y:,.2f}<br>Tipo: %{trace.name}<br>Cidade: %{customdata[0]}<extra></extra>'
    )
    st.plotly_chart(fig_scatter)
