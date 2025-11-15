import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import sample_colorscale
from typing import Tuple

# -------------------- Config e meta --------------------
st.set_page_config(page_title="Dashboard: Marketing", layout="wide")

# -------------------- Utilitários e caches --------------------
@st.cache_data
def aggregate_by_month(df: pd.DataFrame):
    df2 = df.copy()
    if "Data_Campanha" not in df2.columns:
        df2["Data_Campanha"] = pd.NaT
    df2["Mes"] = pd.to_datetime(df2["Data_Campanha"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    inv = df2.groupby("Mes", as_index=False)["Investimento"].sum()
    rev = df2.groupby("Mes", as_index=False)["Receita_Gerada"].sum().rename(columns={"Receita_Gerada": "Receita_Bruta"})
    merged = pd.merge(inv, rev, on="Mes", how="outer").fillna(0).sort_values("Mes")
    return merged


def pearson_r_squared(x, y):
    try:
        if len(x) < 2:
            return np.nan
        mask = (~np.isnan(x)) & (~np.isnan(y))
        if mask.sum() < 2:
            return np.nan
        r = np.corrcoef(x[mask], y[mask])[0, 1]
        return float(r ** 2)
    except Exception:
        return np.nan


def _safe_to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0)


def _ensure_datecol(df: pd.DataFrame, col_name: str = "Data_Campanha") -> pd.DataFrame:
    if col_name not in df.columns:
        df[col_name] = pd.NaT
    else:
        df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
    return df


def _get_month_col(df: pd.DataFrame, col_name: str = "Mes") -> pd.DataFrame:
    if "Mês" in df.columns and "Mes" not in df.columns:
        df = df.rename(columns={"Mês": "Mes"})
    if "Mes" in df.columns:
        df["Mes"] = pd.to_datetime(df["Mes"], errors="coerce").dt.to_period("M").dt.to_timestamp()
    return df

# -------------------- Funções de formatação --------------------

def fmt_money(v):
    return f"R$ {v:,.2f}" if pd.notna(v) and np.isfinite(v) else "—"


def fmt_mult(v):
    return f"{v:.2f}x" if pd.notna(v) and np.isfinite(v) else "—"

# -------------------- App principal --------------------

def app(df_marketing: pd.DataFrame = None, df_financeiro: pd.DataFrame = None):
    st.title("📊 Dashboard: Marketing")

    # --- Preparação dos dados (defensiva) ---
    df_marketing = df_marketing.copy() if df_marketing is not None else pd.DataFrame()
    df_financeiro = df_financeiro.copy() if df_financeiro is not None else pd.DataFrame()

    # normalize expected columns
    for col in ["Investimento", "Receita_Gerada"]:
        if col not in df_marketing.columns:
            df_marketing[col] = 0

    # ensure textual identifier columns exist to avoid KeyErrors in UI
    if "Campanha" not in df_marketing.columns:
        df_marketing["Campanha"] = df_marketing.index.astype(str)
    if "Tipo_Midia" not in df_marketing.columns:
        df_marketing["Tipo_Midia"] = "Desconhecido"

    # numeric conversions
    df_marketing["Investimento"] = _safe_to_numeric(df_marketing["Investimento"])
    df_marketing["Receita_Gerada"] = _safe_to_numeric(df_marketing["Receita_Gerada"])

    # dates
    df_marketing = _ensure_datecol(df_marketing, "Data_Campanha")
    df_marketing["Ano"] = df_marketing["Data_Campanha"].dt.year
    df_marketing["Mes"] = df_marketing["Data_Campanha"].dt.to_period("M").dt.to_timestamp()
    df_marketing["Trimestre"] = df_marketing["Data_Campanha"].dt.quarter

    # computed metrics (safe)
    def safe_roas(row):
        inv = row["Investimento"]
        rev = row["Receita_Gerada"]
        if pd.isna(inv) or inv == 0:
            return np.nan
        return rev / inv

    def safe_cprg(row):
        inv = row["Investimento"]
        rev = row["Receita_Gerada"]
        if pd.isna(rev) or rev == 0:
            return np.nan
        return inv / rev

    df_marketing["ROAS"] = df_marketing.apply(safe_roas, axis=1)
    df_marketing["Lucro"] = df_marketing["Receita_Gerada"] - df_marketing["Investimento"]
    df_marketing["CPRG"] = df_marketing.apply(safe_cprg, axis=1)

    # classification
    df_marketing["Desempenho"] = df_marketing["ROAS"].apply(
        lambda x: "Excelente" if pd.notna(x) and x >= 3 else ("Bom" if pd.notna(x) and x >= 2 else "Ruim")
    )

    # ---------- Sidebar / UI ----------
    st.sidebar.markdown("## Preferências do Gráfico")

    color_mode = st.sidebar.radio(
        "Modo de cor — ROAS por Tipo de Mídia",
        options=["Cor única (limpa)", "Destacar melhor (amarelo)"],
        index=0
    )
    base_color = st.sidebar.color_picker("Cor base (para barras)", "#2ECC71")
    highlight_color = st.sidebar.color_picker("Cor de destaque (melhor mídia)", "#FFD700")

    uniform_scales = st.sidebar.checkbox("Small multiples — Escala uniforme entre facetas", value=True)
    show_regression = st.sidebar.checkbox("Mostrar regressão no scatter (R²)", value=True)
    use_scattergl_threshold = st.sidebar.number_input("Usar ScatterGL se pontos >", min_value=500, max_value=100000, value=2000)

    # ---------- KPIs ----------
    st.subheader("📌 Indicadores Gerais")
    total_invest = df_marketing["Investimento"].sum()
    total_receita = df_marketing["Receita_Gerada"].sum()

    # ROAS agregado (peso correto) vs ROAS médio por campanha (informativo)
    roas_agregado = (total_receita / total_invest) if total_invest > 0 else np.nan
    roas_medio_por_campanha = df_marketing["ROAS"].mean() if not df_marketing.empty else np.nan

    k1, k2, k3 = st.columns(3)
    k4, k5, k6 = st.columns(3)

    k1.metric("Investimento Total", fmt_money(total_invest))
    k2.metric("Receita Total", fmt_money(total_receita))
    k3.metric("ROAS (agregado)", fmt_mult(roas_agregado))
    k4.metric("ROAS médio (por campanha)", fmt_mult(roas_medio_por_campanha))
    k5.metric("Melhor ROAS", fmt_mult(df_marketing['ROAS'].max() if df_marketing['ROAS'].notna().any() else np.nan))
    k6.metric("Pior ROAS", fmt_mult(df_marketing['ROAS'].min() if df_marketing['ROAS'].notna().any() else np.nan))

    if not df_marketing.empty:
        pct_lucrativas = (df_marketing["Lucro"] > 0).sum() / len(df_marketing) * 100
        st.write(f"Campanhas lucrativas: {pct_lucrativas:.1f}%")
    else:
        st.write("Campanhas lucrativas: —")

    st.markdown("---")

    # ---------- Investimento x Receita por Tipo de Mídia (barras) ----------
    st.markdown("### 💸 Investimento e Receita por Tipo de Mídia")
    inv_mid = df_marketing.groupby("Tipo_Midia", as_index=False)[["Investimento", "Receita_Gerada"]].sum().fillna(0)
    if inv_mid.empty:
        st.info("Sem dados de Investimento x Receita por Tipo de Mídia.")
    else:
        inv_mid = inv_mid.sort_values("Investimento", ascending=False)
        fig_midia = go.Figure()
        fig_midia.add_trace(go.Bar(x=inv_mid["Tipo_Midia"], y=inv_mid["Investimento"], name="Investimento", marker=dict(color=base_color)))
        fig_midia.add_trace(go.Bar(x=inv_mid["Tipo_Midia"], y=inv_mid["Receita_Gerada"], name="Receita", marker=dict(color=highlight_color)))
        fig_midia.update_layout(
            barmode="group",
            title="Investimento x Receita por Tipo de Mídia",
            xaxis_title="Tipo de Mídia",
            yaxis_title="Valor (R$)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_midia, use_container_width=True)

    st.markdown("---")

    # ---------- ROAS Médio por Tipo de Mídia ----------
    st.markdown("### 📈 ROAS Médio por Tipo de Mídia (ordenado)")
    roas_midia = (df_marketing.groupby("Tipo_Midia", as_index=False)["ROAS"]
                  .mean()
                  .sort_values("ROAS", ascending=False)
                  .reset_index(drop=True))

    if roas_midia.empty:
        st.info("Sem dados para ROAS médio por Tipo de Mídia.")
    else:
        ordered_midia = roas_midia["Tipo_Midia"].tolist()
        if color_mode == "Cor única (limpa)":
            colors = [base_color] * len(roas_midia)
        else:
            top_media = roas_midia.loc[0, "Tipo_Midia"] if len(roas_midia) > 0 else None
            colors = [highlight_color if m == top_media else "#BDBDBD" for m in roas_midia["Tipo_Midia"]]

        fig_roas_midia = go.Figure()
        fig_roas_midia.add_trace(go.Bar(
            x=roas_midia["ROAS"],
            y=pd.Categorical(roas_midia["Tipo_Midia"], categories=ordered_midia, ordered=True),
            orientation="h",
            marker=dict(color=colors),
            hovertemplate="<b>%{y}</b><br>ROAS: %{x:.2f}x<extra></extra>"
        ))
        fig_roas_midia.update_layout(
            title="ROAS Médio por Tipo de Mídia (ordenado do maior para o menor)",
            xaxis_title="ROAS (Receita / Investimento)",
            yaxis_title="Tipo de Mídia",
            margin=dict(l=150),
            height=420
        )
        fig_roas_midia.update_traces(text=roas_midia["ROAS"].apply(lambda v: f"{v:.2f}x"), textposition="outside")
        st.plotly_chart(fig_roas_midia, use_container_width=True)

    st.markdown("---")

    # ---------- Ranking por Campanha ----------
    st.markdown("### 🏷️ Ranking de Campanhas — ROAS e Lucro")
    if df_marketing.empty:
        st.info("Sem dados de campanhas.")
    else:
        df_rank = df_marketing.copy()
        df_rank_sorted = df_rank.sort_values("ROAS", ascending=False, na_position="last").reset_index(drop=True)
        campaign_color = base_color
        fig_rank = go.Figure()
        fig_rank.add_trace(go.Bar(
            x=df_rank_sorted["ROAS"].fillna(0),
            y=pd.Categorical(df_rank_sorted["Campanha"], categories=df_rank_sorted["Campanha"].tolist()[::-1], ordered=True),
            orientation="h",
            marker=dict(color=campaign_color),
            hovertemplate="<b>%{y}</b><br>ROAS: %{x:.2f}x<br>Lucro: %{customdata}<extra></extra>",
            customdata=df_rank_sorted["Lucro"].apply(lambda v: f"R$ {v:,.2f}")
        ))
        fig_rank.update_traces(text=df_rank_sorted["Lucro"].apply(lambda v: f"R$ {v:,.0f}"), textposition="outside")
        fig_rank.update_layout(title="ROAS por Campanha (ordenado)", margin=dict(l=300), height=600, xaxis_title="ROAS")
        st.plotly_chart(fig_rank, use_container_width=True)

        st.markdown("**Top 3 Campanhas (por ROAS)** / **Bottom 3 Campanhas (por ROAS)**")
        df_roas_valid = df_marketing.dropna(subset=["ROAS"]) if not df_marketing.empty else pd.DataFrame()
        if not df_roas_valid.empty:
            top3 = df_roas_valid.nlargest(3, "ROAS")[["Campanha", "Tipo_Midia", "Investimento", "Receita_Gerada", "ROAS", "Lucro"]]
            bot3 = df_roas_valid.nsmallest(3, "ROAS")[["Campanha", "Tipo_Midia", "Investimento", "Receita_Gerada", "ROAS", "Lucro"]]
        else:
            top3 = pd.DataFrame(columns=["Campanha", "Tipo_Midia", "Investimento", "Receita_Gerada", "ROAS", "Lucro"])
            bot3 = top3.copy()

        c1, c2 = st.columns(2)
        c1.table(top3.reset_index(drop=True))
        c2.table(bot3.reset_index(drop=True))

    st.markdown("---")

    # ---------- Evolução Temporal: linha + média móvel ----------
    st.markdown("### 📅 Evolução Temporal — Investimento vs Receita (mensal)")
    df_merged_monthly = aggregate_by_month(df_marketing)

    if df_merged_monthly.empty:
        st.info("Sem dados mensais.")
    else:
        df_merged_monthly = df_merged_monthly.sort_values("Mes")
        df_merged_monthly["Investimento_MA3"] = df_merged_monthly["Investimento"].rolling(3, min_periods=1).mean()
        df_merged_monthly["Receita_MA3"] = df_merged_monthly["Receita_Bruta"].rolling(3, min_periods=1).mean()

        fig_time = go.Figure()
        fig_time.add_trace(go.Scatter(x=df_merged_monthly["Mes"], y=df_merged_monthly["Investimento"], mode="lines+markers", name="Investimento (mensal)"))
        fig_time.add_trace(go.Scatter(x=df_merged_monthly["Mes"], y=df_merged_monthly["Receita_Bruta"], mode="lines+markers", name="Receita (mensal)"))
        fig_time.add_trace(go.Scatter(x=df_merged_monthly["Mes"], y=df_merged_monthly["Investimento_MA3"], mode="lines", name="Investimento • MA(3)", line=dict(dash="dash")))
        fig_time.add_trace(go.Scatter(x=df_merged_monthly["Mes"], y=df_merged_monthly["Receita_MA3"], mode="lines", name="Receita • MA(3)", line=dict(dash="dash")))

        fig_time.update_layout(title="Investimento vs Receita Mensal (linhas) — com Médias Móveis", xaxis_title="Mês", yaxis_title="Valor (R$)")
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # ---------- Scatter geral + Equilíbrio + Regressão (se habilitado) ----------
    st.markdown("### 🔎 Investimento vs Receita — Visão Geral (limpa)")
    if df_marketing.empty:
        st.info("Sem dados para o gráfico de dispersão.")
    else:
        df_sc = df_marketing.dropna(subset=["Investimento", "Receita_Gerada"]).copy()
        x = df_sc["Investimento"].values
        y = df_sc["Receita_Gerada"].values

        # regressão linear
        slope = intercept = r2 = None
        y_pred = None
        trend_text = ""
        if show_regression:
            try:
                if len(x) >= 2 and np.nanstd(x) > 0:
                    slope, intercept = np.polyfit(x, y, 1)
                    y_pred = slope * x + intercept
                    r2 = pearson_r_squared(x, y)
                    trend_text = f"y = {slope:.2f}x + {intercept:.2f} • R²={r2:.3f}"
                else:
                    trend_text = "Insuficientes dados para regressão"
            except Exception:
                trend_text = "Erro ao calcular regressão"

        use_gl = len(df_sc) > use_scattergl_threshold
        scatter_trace_type = go.Scattergl if use_gl else go.Scatter

        fig_scatter = go.Figure()
        fig_scatter.add_trace(
            scatter_trace_type(
                x=df_sc["Investimento"],
                y=df_sc["Receita_Gerada"],
                mode="markers",
                marker=dict(size=8, opacity=0.7),
                text=df_sc["Campanha"],
                hovertemplate="<b>%{text}</b><br>Investimento: R$ %{x:.2f}<br>Receita: R$ %{y:.2f}<br>ROAS: %{customdata:.2f}x<extra></extra>",
                customdata=df_sc["ROAS"].fillna(-1)
            )
        )

        max_val = max(
            df_marketing["Investimento"].max(skipna=True) if not df_marketing["Investimento"].isna().all() else 0,
            df_marketing["Receita_Gerada"].max(skipna=True) if not df_marketing["Receita_Gerada"].isna().all() else 0
        ) * 1.05
        max_val = max_val if max_val > 0 else 1

        # linha de equilíbrio
        fig_scatter.add_trace(go.Scatter(x=[0, max_val], y=[0, max_val], mode="lines", name="Equilíbrio", line=dict(dash="dash", color="black")))

        # linha de regressão
        if y_pred is not None and slope is not None:
            xs = np.array([0, max_val])
            ys = slope * xs + intercept
            fig_scatter.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="firebrick", width=2), name=f"Regressão • R²={r2:.3f}"))

        fig_scatter.update_layout(height=520, title=f"Investimento vs Receita (com regressão) — {trend_text}")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### Small Multiples — Investimento vs Receita por Tipo de Mídia")
    # ---------- Small multiples: reconstruir manualmente para garantir a linha de equilíbrio em cada facet ----------
    medias = df_marketing["Tipo_Midia"].dropna().unique().tolist()
    if len(medias) == 0:
        st.info("Sem dados por Tipo de Mídia para small multiples.")
    else:
        try:
            media_order = df_marketing.groupby("Tipo_Midia")["ROAS"].mean().sort_values(ascending=False).index.tolist()
            medias = [m for m in media_order if m in medias]
        except Exception:
            pass

        stats = df_marketing.groupby("Tipo_Midia").agg(n=("Campanha", "count"), med_roas=("ROAS", lambda x: float(x.median(skipna=True)) if x.dropna().size > 0 else np.nan)).reindex(medias)
        subplot_titles = [f"{m} — n={int(stats.loc[m,'n'])} — med:{(stats.loc[m,'med_roas'] if not np.isnan(stats.loc[m,'med_roas']) else '—'):.2f}" if not np.isnan(stats.loc[m,'med_roas']) else f"{m} — n={int(stats.loc[m,'n'])} — med: —" for m in medias]

        cols = 3
        rows = math.ceil(len(medias) / cols)
        fig_facet = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles, horizontal_spacing=0.06, vertical_spacing=0.10, shared_xaxes=False, shared_yaxes=False)

        colorscale = px.colors.sequential.Viridis
        roas_min = df_marketing["ROAS"].min(skipna=True)
        roas_max = df_marketing["ROAS"].max(skipna=True)
        if pd.isna(roas_min) or pd.isna(roas_max) or roas_min == roas_max:
            roas_min, roas_max = 0.0, 1.0

        # global max quando uniform_scales=True
        global_max = max(
            df_marketing["Investimento"].max(skipna=True) if not df_marketing["Investimento"].isna().all() else 0,
            df_marketing["Receita_Gerada"].max(skipna=True) if not df_marketing["Receita_Gerada"].isna().all() else 0
        ) * 1.10
        global_max = global_max if global_max > 0 else 1

        i = 0
        for r in range(1, rows + 1):
            for c in range(1, cols + 1):
                if i >= len(medias):
                    fig_facet.add_trace(go.Scatter(x=[None], y=[None], showlegend=False, hoverinfo='none'), row=r, col=c)
                    i += 1
                    continue
                media = medias[i]
                sub = df_marketing[df_marketing["Tipo_Midia"] == media]

                local_max = max(
                    sub["Investimento"].max(skipna=True) if not sub["Investimento"].isna().all() else 0,
                    sub["Receita_Gerada"].max(skipna=True) if not sub["Receita_Gerada"].isna().all() else 0
                ) * 1.10
                local_max = local_max if local_max > 0 else 1

                sub_max = global_max if uniform_scales else local_max

                roas_vals = sub["ROAS"].fillna(roas_min).tolist()
                if len(roas_vals) == 0:
                    norm_vals = []
                else:
                    norm_vals = [0.0 if pd.isna(v) else float((v - roas_min) / (roas_max - roas_min)) if roas_max != roas_min else 0.5 for v in roas_vals]
                try:
                    marker_colors = sample_colorscale(colorscale, norm_vals)
                except Exception:
                    marker_colors = ["#636EFA"] * len(norm_vals)

                fig_facet.add_trace(
                    go.Scatter(mode="markers",
                               x=sub["Investimento"],
                               y=sub["Receita_Gerada"],
                               marker=dict(size=9, opacity=0.85, color=marker_colors),
                               name=str(media),
                               hovertemplate="<b>%{text}</b><br>Investimento: R$ %{x:.2f}<br>Receita: R$ %{y:.2f}<br>ROAS: %{customdata:.2f}x<extra></extra>",
                               text=sub.get("Campanha"),
                               customdata=sub["ROAS"].fillna(-1)),
                    row=r, col=c
                )

                # linha de equilíbrio local
                fig_facet.add_trace(
                    go.Scatter(x=[0, sub_max], y=[0, sub_max], mode="lines",
                               line=dict(dash="dash", color="black", width=1), showlegend=False, hoverinfo='none'),
                    row=r, col=c
                )

                try:
                    median_roas = sub["ROAS"].median(skipna=True)
                    med_text = f"n={len(sub)}\nmed: {median_roas:.2f}x" if pd.notna(median_roas) else f"n={len(sub)}\nmed: —"
                    fig_facet.add_trace(
                        go.Scatter(x=[sub_max * 0.05], y=[sub_max * 0.90], mode="text",
                                   text=[med_text],
                                   showlegend=False, hoverinfo='none'),
                        row=r, col=c
                    )
                except Exception:
                    fig_facet.add_trace(
                        go.Scatter(x=[sub_max * 0.05], y=[sub_max * 0.90], mode="text",
                                   text=[f"n={len(sub)}"],
                                   showlegend=False, hoverinfo='none'),
                        row=r, col=c
                    )

                fig_facet.update_xaxes(title_text="Investimento (R$)", range=[0, sub_max], row=r, col=c)
                fig_facet.update_yaxes(title_text="Receita (R$)", range=[0, sub_max], row=r, col=c)

                i += 1

        fig_facet.update_layout(height=350 * rows, title_text="Small Multiples: Investimento vs Receita por Tipo de Mídia", showlegend=False, margin=dict(t=120, l=60, r=20, b=60))
        for a in fig_facet.layout.annotations:
            a.font = dict(size=11)
            a.y = a.y + 0.02

        st.plotly_chart(fig_facet, use_container_width=True)

    st.markdown("---")

    # ---------- Boxplot de ROAS ----------
    st.markdown("### 📦 Distribuição de ROAS por Tipo de Mídia (Boxplot)")
    if df_marketing.empty:
        st.info("Sem dados para boxplot de ROAS.")
    else:
        fig_box = px.box(
            df_marketing,
            x="Tipo_Midia",
            y="ROAS",
            title="Variação de ROAS por Tipo de Mídia",
            points="outliers"
        )
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")

    # ---------- Heatmap ----------
    st.markdown("### 🔥 Heatmap: ROAS médio por Tipo de Mídia e Trimestre")
    if df_marketing["Trimestre"].isna().all() or df_marketing["Tipo_Midia"].isna().all():
        st.info("Dados insuficientes para heatmap (Trimestre x Tipo_Midia).")
    else:
        df_heat = df_marketing.groupby(["Tipo_Midia", "Trimestre"], as_index=False)["ROAS"].mean()
        pivot = df_heat.pivot(index="Tipo_Midia", columns="Trimestre", values="ROAS").fillna(0)
        pivot = pivot.reindex(columns=sorted(pivot.columns))
        fig_heat = px.imshow(
            pivot,
            labels=dict(x="Trimestre", y="Tipo de Mídia", color="ROAS"),
            x=pivot.columns.astype(str),
            y=pivot.index,
            title="ROAS médio (Tipo de Mídia x Trimestre)"
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")

    # ---------- Tabela detalhada + download ----------
    st.markdown("### 🗂️ Tabela Detalhada das Campanhas")
    cols_show = ["Campanha", "Tipo_Midia", "Investimento", "Receita_Gerada", "Lucro", "ROAS", "CPRG", "Desempenho", "Data_Campanha"]
    available = [c for c in cols_show if c in df_marketing.columns]
    if df_marketing.empty:
        st.info("Sem dados para tabela detalhada.")
    else:
        st.dataframe(df_marketing[available].sort_values("Data_Campanha", ascending=False).reset_index(drop=True))
        csv_bytes = df_marketing[available].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar tabela CSV", csv_bytes, file_name="campanhas_marketing.csv", mime="text/csv")

    st.markdown("---")

    # ---------- Insights automáticos e recomendações ----------
    st.markdown("## 🧠 Insights Automáticos")
    insights = []
    if not df_marketing.empty:
        try:
            melhor_midia = df_marketing.groupby("Tipo_Midia")["ROAS"].mean().idxmax()
            pior_midia = df_marketing.groupby("Tipo_Midia")["ROAS"].mean().idxmin()
        except Exception:
            melhor_midia = None
            pior_midia = None

        melhor_campanha = df_marketing.loc[df_marketing["Lucro"].idxmax()]["Campanha"] if df_marketing["Lucro"].notna().any() else None
        pior_campanha = df_marketing.loc[df_marketing["Lucro"].idxmin()]["Campanha"] if df_marketing["Lucro"].notna().any() else None

        insights.append(f"- ROAS agregado: **{roas_agregado:.2f}x**." if pd.notna(roas_agregado) else "- ROAS agregado: —")
        if melhor_midia:
            insights.append(f"- Mídia com melhor ROAS médio: **{melhor_midia}**.")
        if pior_midia:
            insights.append(f"- Mídia com pior ROAS médio: **{pior_midia}**.")
        if pd.notna(melhor_campanha):
            insights.append(f"- Campanha mais lucrativa: **{melhor_campanha}**.")
        if pd.notna(pior_campanha):
            insights.append(f"- Campanha com menor lucro: **{pior_campanha}**.")
        insights.append(f"- { (df_marketing['Lucro'] > 0).mean() * 100:.1f}% das campanhas geraram lucro.")
    else:
        insights.append("- Sem dados para gerar insights automáticos.")

    st.info("\n".join(["### Principais insights"] + insights))

    st.markdown("### ✅ Recomendações rápidas (automáticas)")
    recs = []
    if not roas_midia.empty and pd.notna(roas_agregado):
        medias_baixas = roas_midia[roas_midia["ROAS"] < roas_agregado]["Tipo_Midia"].tolist()
        if medias_baixas:
            recs.append(f"- Revisar estratégia para: {', '.join(medias_baixas)} (ROAS abaixo do agregado).")

    if not df_marketing.empty:
        candidates = df_marketing[(df_marketing["ROAS"] < 1) & (df_marketing["Investimento"] > df_marketing["Investimento"].median())]
        if not candidates.empty:
            recs.append(f"- Avaliar pausar/otimizar campanhas com ROAS < 1 e investimento alto (ex.: {', '.join(candidates['Campanha'].head(3).tolist())}).")

    if recs:
        for r in recs:
            st.write(r)
    else:
        st.write("- Nenhuma recomendação automática gerada (dados equilibrados).")


# -------------------- Ponto de entrada (para testes locais) --------------------
if __name__ == '__main__':
    # Exemplo mínimo para testar a interface localmente
    example = pd.DataFrame({
        'Campanha': ['Campanha_1','Campanha_2','Campanha_3','Campanha_4','Campanha_5'],
        'Tipo_Midia': ['Outdoor','Outdoor','TV','Rádio','Online'],
        'Investimento': [6612,16386,17955,8061,5000],
        'Receita_Gerada': [2332,29277,5327,16332,7000],
        'Data_Campanha': pd.to_datetime(['2022-05-19','2023-01-26','2023-10-19','2022-03-14','2023-06-01'])
    })
    app(example, None)
