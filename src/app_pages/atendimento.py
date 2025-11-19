import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import math
from typing import List


@st.cache_data
def clean_and_engineer(df):
    """Normaliza colunas, converte tipos, preenche missing e cria features."""
    df = df.copy()

    df.columns = [c.strip() for c in df.columns]

    # Datas
    if 'Data_Abertura' in df.columns:
        df['Data_Abertura'] = pd.to_datetime(df['Data_Abertura'], errors='coerce')
    else:
        df['Data_Abertura'] = pd.NaT

    # Numéricos
    if 'Tempo_Resolucao' in df.columns:
        df['Tempo_Resolucao'] = pd.to_numeric(df['Tempo_Resolucao'], errors='coerce')
    else:
        df['Tempo_Resolucao'] = np.nan

    if 'Avaliacao_Cliente' in df.columns:
        df['Avaliacao_Cliente'] = pd.to_numeric(df['Avaliacao_Cliente'], errors='coerce')
    else:
        df['Avaliacao_Cliente'] = np.nan

    for col in ['Motivo', 'Status', 'Canal']:
        if col not in df.columns:
            df[col] = 'Desconhecido'
        else:
            df[col] = df[col].astype(str).str.strip().replace({'nan': 'Desconhecido'})

    if 'ID_Chamado' not in df.columns:
        df.insert(0, 'ID_Chamado', range(1, len(df) + 1))

    if 'Motivo' in df.columns:
        df['Tempo_Resolucao'] = df.groupby('Motivo')['Tempo_Resolucao'].transform(
            lambda x: x.fillna(x.median())
        )
    df['Tempo_Resolucao'] = df['Tempo_Resolucao'].fillna(df['Tempo_Resolucao'].median())

    if df['Avaliacao_Cliente'].isna().all():

        pass

    else:
        df['Avaliacao_Cliente'] = df['Avaliacao_Cliente'].fillna(df['Avaliacao_Cliente'].mean())

    df['Ano'] = df['Data_Abertura'].dt.year
    df['Mes'] = df['Data_Abertura'].dt.to_period('M').astype(str)
    df['Dia_Semana'] = df['Data_Abertura'].dt.day_name()

    def categorize_tempo(x):
        if pd.isna(x):
            return 'Desconhecido'
        if x <= 8:
            return 'Rápido (<=8h)'
        if x <= 48:
            return 'Médio (8-48h)'
        return 'Lento (>48h)'

    df['Tempo_Categoria'] = df['Tempo_Resolucao'].apply(categorize_tempo)

    df['Eh_Resolvido'] = df['Status'].astype(str).str.lower().isin(
        ['resolvido', 'resolved', 'closed', 'fechado', 'concluido', 'concluído']
    )

    return df

def _format_money_br(value: float) -> str:
    try:
        if pd.isna(value):
            return ""
        s = f"{float(value):,.2f}"
        s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {s}"
    except Exception:
        return str(value)


def _hours_to_hm(value: float) -> str:
    try:
        if pd.isna(value):
            return ""
        total_minutes = int(round(float(value) * 60))
        hours = total_minutes // 60
        minutes = total_minutes % 60
        if hours == 0 and minutes == 0:
            return "0h"
        if hours == 0:
            return f"{minutes}m"
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}m"
    except Exception:
        return str(value)


def _format_date_br(val):
    try:
        if pd.isna(val):
            return ""
        return pd.to_datetime(val).strftime("%d/%m/%Y")
    except Exception:
        return str(val)


def _is_money_column(col_name: str) -> bool:
    keywords = ['valor', 'preco', 'custo', 'price', 'amount', 'total', 'venda', 'receita', 'fatur']
    col = col_name.lower()
    return any(k in col for k in keywords)


def _is_percentage_column(col_name: str) -> bool:
    keywords = ['percent', 'porcent', 'percentual', '%']
    col = col_name.lower()
    return any(k in col for k in keywords)


def _is_time_column(col_name: str) -> bool:
    keywords = ['tempo', 'hora', 'duracao', 'duration']
    col = col_name.lower()
    return any(k in col for k in keywords)


def format_display_dataframe_for_view(df: pd.DataFrame) -> pd.DataFrame:

    disp = df.copy()

    for col in disp.columns:
        if np.issubdtype(disp[col].dtype, np.datetime64) or col.lower().startswith('data') or 'data' in col.lower():
            disp[col] = disp[col].apply(_format_date_br)

        elif _is_money_column(col):
            disp[col] = disp[col].apply(lambda x: _format_money_br(x) if not pd.isna(x) else "")

        elif _is_time_column(col):
            disp[col] = disp[col].apply(lambda x: _hours_to_hm(x) if not pd.isna(x) else "")

        elif _is_percentage_column(col):
            def fmt_pct(x):
                try:
                    if pd.isna(x):
                        return ""
                    return f"{float(x)*100:.1f}%"
                except Exception:
                    return str(x)
            disp[col] = disp[col].apply(fmt_pct)

        elif np.issubdtype(disp[col].dtype, np.number):
            disp[col] = disp[col].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if not pd.isna(x) else "")

        else:

            disp[col] = disp[col].astype(str)

    return disp

def app(df_atendimento):

    st.title("Dashboard: Atendimento")

    if df_atendimento is None or df_atendimento.empty:
        st.info("DataFrame vazio ou não fornecido. Forneça `df_atendimento` ao chamar esta página.")
        return

    df = clean_and_engineer(df_atendimento)

    # ----------------- KPIs -----------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_tickets = len(df)
    percent_resolvidos = (df['Eh_Resolvido'].mean() * 100) if total_tickets > 0 else 0.0
    tempo_medio = df['Tempo_Resolucao'].mean()
    avaliacao_media = df['Avaliacao_Cliente'].mean()

    kpi1.metric("Total de Tickets", f"{total_tickets:,}".replace(',', '.')) 
    kpi2.metric("% Resolvidos", f"{percent_resolvidos:.1f}%")
    kpi3.metric(
        "Tempo Médio de Resolução",
        _hours_to_hm(tempo_medio) if not np.isnan(tempo_medio) else "N/A",
    )
    kpi4.metric(
        "Avaliação Média",
        f"{avaliacao_media:.2f}" if not np.isnan(avaliacao_media) else "N/A",
    )

    st.markdown("---")

    st.markdown("### Volume de Tickets por Motivo")
    if df.empty:
        st.info("Sem dados para este gráfico.")
    else:
        tickets_por_motivo = (
            df.groupby('Motivo').size().reset_index(name='Count').sort_values(by='Count', ascending=False)
        )
        fig_motivo = px.bar(
            tickets_por_motivo,
            x='Motivo',
            y='Count',
            title='Volume de Tickets por Motivo',
            labels={'Count': 'Número de Tickets'},
            color='Count',
            color_continuous_scale=px.colors.sequential.OrRd
        )
        fig_motivo.update_layout(xaxis_tickangle=-45)
        fig_motivo.update_traces(hovertemplate='<b>%{x}</b><br>Tickets: %{y:,}<extra></extra>')
        st.plotly_chart(fig_motivo, use_container_width=True)

    st.markdown("### Tempo Médio de Resolução por Canal")
    if df.empty:
        st.info("Sem dados para este gráfico.")
    else:
        tempo_resolucao_por_canal = (
            df.groupby('Canal')['Tempo_Resolucao'].mean().reset_index().sort_values(by='Tempo_Resolucao', ascending=False)
        )
        fig_tempo_canal = px.bar(
            tempo_resolucao_por_canal,
            x='Canal',
            y='Tempo_Resolucao',
            title='Tempo Médio de Resolução por Canal',
            labels={'Tempo_Resolucao': 'Tempo Médio (horas)'},
            color='Tempo_Resolucao',
            color_continuous_scale=px.colors.sequential.Plasma
        )
        hover_texts = tempo_resolucao_por_canal['Tempo_Resolucao'].apply(lambda x: _hours_to_hm(x))
        fig_tempo_canal.update_traces(hovertemplate='<b>%{x}</b><br>Tempo médio: %{customdata[0]}<extra></extra>',
                                      customdata=hover_texts.to_frame().values)
        st.plotly_chart(fig_tempo_canal, use_container_width=True)

    st.markdown("### Distribuição de Status dos Tickets")
    if df.empty:
        st.info("Sem dados para este gráfico.")
    else:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_status = px.pie(
            status_counts,
            values='Count',
            names='Status',
            title='Distribuição de Status dos Tickets',
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        fig_status.update_traces(hovertemplate='%{label}: %{value:,} (%{percent})'.replace(',', '.'))
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("### Tickets por Mês e Canal")
    if df['Data_Abertura'].notna().any():
        df['Mês'] = df['Data_Abertura'].dt.to_period('M').astype(str)
        tickets_heatmap = df.groupby(['Mês', 'Canal']).size().unstack(fill_value=0)

        try:
            idx = pd.PeriodIndex(tickets_heatmap.index, freq='M').to_timestamp()
            tickets_heatmap.index = idx
            tickets_heatmap = tickets_heatmap.sort_index()
            y_labels = tickets_heatmap.index.strftime('%Y-%m')
        except Exception:
            y_labels = tickets_heatmap.index.astype(str)

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=tickets_heatmap.values,
            x=tickets_heatmap.columns,
            y=y_labels,
            colorscale='YlOrRd',
            hovertemplate='Canal: %{x}<br>Mês: %{y}<br>Tickets: %{z:,}<extra></extra>'
        ))
        fig_heatmap.update_layout(title='Volume de Tickets por Mês e Canal', xaxis_title='Canal', yaxis_title='Mês')
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("Coluna Data_Abertura ausente ou sem valores válidos para calcular meses.")

    st.markdown("### Avaliação Média do Cliente ao Longo do Tempo")
    if df['Data_Abertura'].notna().any() and 'Avaliacao_Cliente' in df.columns:
        df['Data_Abertura_Month'] = df['Data_Abertura'].dt.to_period('M').dt.to_timestamp()
        avg_avaliacao_mensal = df.groupby('Data_Abertura_Month')['Avaliacao_Cliente'].mean().reset_index()
        fig_avaliacao = px.line(
            avg_avaliacao_mensal,
            x='Data_Abertura_Month',
            y='Avaliacao_Cliente',
            title='Avaliação Média do Cliente por Mês',
            labels={'Avaliacao_Cliente': 'Avaliação Média', 'Data_Abertura_Month': 'Mês'},
            markers=True
        )
        fig_avaliacao.update_traces(hovertemplate='Mês: %{x|%d/%m/%Y}<br>Avaliação média: %{y:.2f}<extra></extra>')
        st.plotly_chart(fig_avaliacao, use_container_width=True)
    else:
        st.info("Não há dados suficientes para plotar avaliação por mês.")

    st.markdown("### Distribuição do Tempo de Resolução")
    col1, col2 = st.columns(2)
    with col1:
        if df['Tempo_Resolucao'].notna().any():
            fig_hist = px.histogram(df, x='Tempo_Resolucao', nbins=30, title='Histograma do Tempo de Resolução (h)')
            fig_hist.update_traces(hovertemplate='Tempo (h): %{x}<br>Contagem: %{y}<extra></extra>')
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Sem valores de Tempo_Resolucao para histograma.")
    with col2:
        if df['Tempo_Resolucao'].notna().any():
            fig_box = px.box(df, x='Motivo', y='Tempo_Resolucao', title='Boxplot: Tempo de Resolução por Motivo')
            fig_box.update_layout(xaxis_tickangle=-45)
            fig_box.update_traces(hovertemplate='Motivo: %{x}<br>Tempo (h): %{y}<extra></extra>')
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("Sem valores de Tempo_Resolucao para boxplot.")

    st.markdown("### Tempo de Resolução (h) vs Avaliação do Cliente")
    if df['Tempo_Resolucao'].notna().any() and df['Avaliacao_Cliente'].notna().any():
        df['_Tempo_Formatado_Hover'] = df['Tempo_Resolucao'].apply(lambda x: _hours_to_hm(x))
        fig_scatter = px.scatter(
            df,
            x='Tempo_Resolucao',
            y='Avaliacao_Cliente',
            hover_data=['ID_Chamado', 'Motivo', 'Canal', '_Tempo_Formatado_Hover'],
            title='Tempo de Resolução vs Avaliação'
        )
        fig_scatter.update_traces(hovertemplate='<b>ID:</b> %{customdata[0]}<br><b>Motivo:</b> %{customdata[1]}<br><b>Canal:</b> %{customdata[2]}<br><b>Tempo:</b> %{customdata[3]}<br><b>Avaliação:</b> %{y:.2f}<extra></extra>')
        st.plotly_chart(fig_scatter, use_container_width=True)
        df.drop(columns=['_Tempo_Formatado_Hover'], inplace=True, errors='ignore')
    else:
        st.info("Dados insuficientes para scatter (Tempo_Resolucao ou Avaliacao_Cliente ausentes).")

    st.markdown("### Top 3 e Bottom 3 por Tempo de Resolução")
    if df['Tempo_Resolucao'].notna().any():
        top3 = df.sort_values('Tempo_Resolucao', ascending=False).head(3)[
            ['ID_Chamado', 'Data_Abertura', 'Motivo', 'Status', 'Tempo_Resolucao', 'Canal', 'Avaliacao_Cliente']
        ]
        bot3 = df.sort_values('Tempo_Resolucao', ascending=True).head(3)[
            ['ID_Chamado', 'Data_Abertura', 'Motivo', 'Status', 'Tempo_Resolucao', 'Canal', 'Avaliacao_Cliente']
        ]
        # Formatar para exibição
        top3_disp = format_display_dataframe_for_view(top3)
        bot3_disp = format_display_dataframe_for_view(bot3)

        col_top, col_bot = st.columns(2)
        with col_top:
            st.markdown("**Top 3 (maiores tempos)**")
            st.dataframe(top3_disp.reset_index(drop=True))
        with col_bot:
            st.markdown("**Bottom 3 (menores tempos)**")
            st.dataframe(bot3_disp.reset_index(drop=True))
    else:
        st.info("Sem valores de Tempo_Resolucao para calcular top/bottom.")

    st.markdown("---")
    st.subheader("Amostra dos Dados (após limpeza)")

    display_df = format_display_dataframe_for_view(df)
    st.dataframe(display_df.head(200))

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(label='Download do dataset limpo (CSV)', data=csv, file_name='dataset_limpo_atendimento.csv', mime='text/csv')
