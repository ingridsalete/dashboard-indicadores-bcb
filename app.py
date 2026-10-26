import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_bcb import load_all_indicators

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Painel de Indicadores Econômicos | BCB",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. ESTILIZAÇÃO CSS CUSTOMIZADA
st.markdown(
    """
    <style>
    /* Estilo do fundo principal */
    .stApp {
        background-color: #0E1117;
        color: #E0E6ED;
        font-family: 'Inter', sans-serif;
    }
    
    /* Cabeçalho Principal */
    .main-header {
        background: linear-gradient(90deg, #1E2640 0%, #0E1117 100%);
        padding: 24px 30px;
        border-radius: 12px;
        border-left: 5px solid #2962FF;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .main-header h1 {
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.8rem;
        margin: 0;
    }
    .main-header p {
        color: #8B949E;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Estilização dos Cards de Métricas (KPIs) */
    [data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #21262D;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #2962FF;
        transform: translateY(-2px);
    }
    [data-testid="stMetricLabel"] {
        color: #8B949E !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        color: #58A6FF !important;
        font-weight: 700 !important;
    }

    /* Abas/Tabs Estilizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #161B22;
        padding: 8px;
        border-radius: 10px;
        border: 1px solid #21262D;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8B949E;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2962FF !important;
        color: #FFFFFF !important;
        font-weight: 600;
    }

    /* Tabela */
    .stDataFrame {
        border: 1px solid #21262D;
        border-radius: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# 3. CABEÇALHO DO DASHBOARD
st.markdown(
    """
    <div class="main-header">
        <h1>Painel Executivo de Indicadores Econômicos</h1>
        <p>Análise de inteligência de mercado com dados oficiais em tempo real via API do Banco Central do Brasil (BCB).</p>
    </div>
""",
    unsafe_allow_html=True,
)


# 4. CARGA DE DADOS
@st.cache_data(ttl=3600)
def fetch_data():
    return load_all_indicators("01/01/2015", "31/12/2026")


df_full = fetch_data()

if df_full.empty:
    st.error("Falha ao comunicar com a API do Banco Central. Verifique a sua conexão.")
else:
    # 5. BARRA LATERAL (FILTROS)
    st.sidebar.markdown("### Painel de Controle")

    indicadores = sorted(df_full["indicador"].unique())
    selected_indicador = st.sidebar.selectbox("Indicador Macroeconômico", indicadores)

    df_indicador = df_full[df_full["indicador"] == selected_indicador].copy()

    anos_disponiveis = sorted(df_indicador["ano"].unique())
    min_ano, max_ano = min(anos_disponiveis), max(anos_disponiveis)

    selected_anos = st.sidebar.slider(
        "Período de Análise",
        min_value=min_ano,
        max_value=max_ano,
        value=(min_ano, max_ano),
    )

    if st.sidebar.button("Atualizar Base da API"):
        st.cache_data.clear()
        st.rerun()

    df_filtered = df_indicador[
        (df_indicador["ano"] >= selected_anos[0])
        & (df_indicador["ano"] <= selected_anos[1])
    ].sort_values("data")

    if not df_filtered.empty:
        # Recalcula a variação no intervalo filtrado
        df_filtered["variacao_pct"] = (
            df_filtered["valor"].pct_change() * 100
        ).fillna(0.0)

        # 6. MÉTRICAS EXECUTIVAS (KPIS)
        ultimo_valor = df_filtered.iloc[-1]["valor"]
        primeiro_valor = df_filtered.iloc[0]["valor"]
        variacao_total = (
            ((ultimo_valor - primeiro_valor) / primeiro_valor) * 100
            if primeiro_valor != 0
            else 0
        )

        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric(
            "Cotação / Taxa Atual",
            f"{ultimo_valor:.2f}",
            f"{variacao_total:+.2f}% no acumulado",
        )
        kpi2.metric("Média do Período", f"{df_filtered['valor'].mean():.2f}")
        kpi3.metric("Pico Máximo", f"{df_filtered['valor'].max():.2f}")
        kpi4.metric("Ponto Mínimo", f"{df_filtered['valor'].min():.2f}")
        kpi5.metric("Amostras Analisadas", f"{len(df_filtered):,}")

        st.markdown("---")

        # 7. SEÇÕES DE GRÁFICOS (TABS MULTIVISUALIZAÇÃO)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Tendência Temporal",
            "Média vs Máxima Anual",
            "Volatilidade & Dispersão",
            "Variabilidade (%)",
            "Tabela de Dados Completa",
        ])

        # TEMAS DE CORES PARA GRÁFICOS
        plotly_layout = dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#C9D1D9", family="Inter"),
            xaxis=dict(showgrid=True, gridcolor="#21262D"),
            yaxis=dict(showgrid=True, gridcolor="#21262D"),
            margin=dict(l=20, r=20, t=40, b=20),
        )

        # TAB 1: LINHA DE TENDÊNCIA
        with tab1:
            st.subheader(f"Evolução Histórica - {selected_indicador}")
            fig_line = px.line(
                df_filtered,
                x="data",
                y="valor",
                title=f"Série Temporal ({selected_anos[0]} - {selected_anos[1]})",
            )
            fig_line.update_traces(
                line_color="#2962FF", line_width=2.5, fill="tozeroy", fillcolor="rgba(41, 98, 255, 0.08)"
            )
            fig_line.update_layout(**plotly_layout)
            st.plotly_chart(fig_line, use_container_width=True)

        # TAB 2: MÉTRICA E PICO ANUAL
        with tab2:
            st.subheader("Comparativo de Desempenho Anual")
            df_grouped = (
                df_filtered.groupby("ano")["valor"]
                .agg(["mean", "max"])
                .reset_index()
            )
            df_grouped.columns = ["ano", "Média", "Máxima"]

            fig_bar_group = go.Figure()
            fig_bar_group.add_trace(
                go.Bar(
                    x=df_grouped["ano"],
                    y=df_grouped["Média"],
                    name="Média Anual",
                    marker_color="#2962FF",
                )
            )
            fig_bar_group.add_trace(
                go.Bar(
                    x=df_grouped["ano"],
                    y=df_grouped["Máxima"],
                    name="Pico Máximo",
                    marker_color="#00E5FF",
                )
            )

            fig_bar_group.update_layout(
                barmode="group", title="Média vs Máxima Histórica", **plotly_layout
            )
            st.plotly_chart(fig_bar_group, use_container_width=True)

        # TAB 3: BOXPLOT E FREQUÊNCIA
        with tab3:
            col_b1, col_b2 = st.columns(2)

            with col_b1:
                st.subheader("Dispersão e Outliers por Ano (Boxplot)")
                fig_box = px.box(
                    df_filtered,
                    x="ano",
                    y="valor",
                    color="ano",
                    title="Distribuição e Amplitude Anual",
                )
                fig_box.update_layout(**plotly_layout)
                st.plotly_chart(fig_box, use_container_width=True)

            with col_b2:
                st.subheader("Frequência da Distribuição (Histograma)")
                fig_hist = px.histogram(
                    df_filtered,
                    x="valor",
                    nbins=25,
                    title="Concentração das Cotações",
                    color_discrete_sequence=["#7C4DFF"],
                )
                fig_hist.update_layout(**plotly_layout)
                st.plotly_chart(fig_hist, use_container_width=True)

        # TAB 4: FLUTUAÇÃO PERCENTUAL
        with tab4:
            st.subheader("Flutuação de Curto Prazo (Variação %)")
            fig_var = px.area(
                df_filtered,
                x="data",
                y="variacao_pct",
                title="Variação Percentual Período a Período",
            )
            fig_var.update_traces(
                line_color="#00E676", fillcolor="rgba(0, 230, 118, 0.1)"
            )
            fig_var.update_layout(**plotly_layout)
            st.plotly_chart(fig_var, use_container_width=True)

        # TAB 5: TABELA DE DADOS COMPLETA
        with tab5:
            st.subheader("Registros Consolidados da API")
            st.markdown("Busca direta com os valores exatos retornados pelo Banco Central.")

            df_tabela = df_filtered[
                ["data", "valor", "ano", "variacao_pct"]
            ].copy()
            df_tabela["data"] = df_tabela["data"].dt.strftime("%d/%m/%Y")
            df_tabela.columns = [
                "Data de Registro",
                "Valor do Indicador",
                "Ano",
                "Variação (%)",
            ]

            st.dataframe(
                df_tabela.style.format(
                    {"Valor do Indicador": "{:.2f}", "Variação (%)": "{:+.2f}%"}
                ),
                use_container_width=True,
                height=450,
            )