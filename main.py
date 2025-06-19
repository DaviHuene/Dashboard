import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
from io import StringIO

# ========== CONFIG GERAL ==========
st.set_page_config("Dashboard Inventário", layout="wide")

# ========== MODO LIGHT / DARK ==========
# === MODO LIGHT / DARK COM MUDANÇA NO MENU E GRÁFICOS ===
modo = st.sidebar.radio("🌗 Tema", ["Claro", "Escuro"], horizontal=True)

if modo == "Claro":
    cor_menu = "#f0f0f0"
    cor_texto_menu = "#000000"
    cor_fundo = "#ffffff"
    cor_primaria = "#6C63FF"
else:
    cor_menu = "#1f1f2e"
    cor_texto_menu = "#ffffff"
    cor_fundo = "#121212"
    cor_primaria = "#bb86fc"

# Estilo CSS dinâmico com base no tema
# CSS customizado para modo claro/escuro completo
st.markdown(f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background: {cor_fundo};
        color: {cor_texto_menu};
    }}

    [data-testid="stSidebar"] {{
        background-color: {cor_menu};
        color: {cor_texto_menu};
        border-right: 3px solid {cor_primaria};
    }}

    [data-testid="stMarkdownContainer"] *,
    .stText, .stMarkdown, .stDataFrame,
    h1, h2, h3, h4, h5, h6, label, p, div, span, th, td {{
        color: {cor_texto_menu} !important;
    }}

    .stButton > button {{
        background-color: {cor_primaria};
        color: white;
        border: none;
        border-radius: 6px;
    }}

    .stSelectbox, .stMultiSelect, .stDateInput {{
        color: {cor_texto_menu} !important;
    }}

    .stTabs [role="tab"] {{
        color: {cor_texto_menu} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# ========== CARREGAR JSON ==========
try:
    with open("dados.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# ========== TRANSFORMAR ==========
registros = []
for lote in dados:
    for caixa in lote.get("caixas", []):
        for b in caixa.get("bipagem", []):
            registros.append({
                "lote_id": lote["id"],
                "status_lote": lote["status"].strip().lower(),
                "grupo": lote["group_user"],
                "caixa_id": caixa["id"],
                "nr_caixa": caixa["nr_caixa"],
                "identificador": caixa["identificador"],
                "unidade": b.get("unidade"),
                "modelo": b.get("modelo"),
                "patrimonio": b.get("patrimonio"),
                "data": b.get("data", "2024-01-01")
            })

df = pd.DataFrame(registros)
df["data"] = pd.to_datetime(df["data"])

# ========== FILTROS ==========
st.sidebar.title("🔍 Filtros")
grupo_op = sorted(df["grupo"].dropna().unique())
modelo_op = sorted(df["modelo"].dropna().unique())
unidade_op = sorted(df["unidade"].dropna().unique())
status_op = sorted(df["status_lote"].dropna().unique())

grupo_sel = st.sidebar.multiselect("Grupo", grupo_op, default=grupo_op)
modelo_sel = st.sidebar.multiselect("Modelo", modelo_op, default=modelo_op)
unidade_sel = st.sidebar.multiselect("Unidade", unidade_op, default=unidade_op)
status_sel = st.sidebar.multiselect("Status", status_op, default=status_op)
data_ini, data_fim = st.sidebar.date_input("Período", [df["data"].min(), df["data"].max()])

# ========== APLICAR FILTROS ==========
df_filt = df[
    df["grupo"].isin(grupo_sel) &
    df["modelo"].isin(modelo_sel) &
    df["unidade"].isin(unidade_sel) &
    df["status_lote"].isin(status_sel) &
    (df["data"] >= pd.to_datetime(data_ini)) &
    (df["data"] <= pd.to_datetime(data_fim))
].copy()

# ========== ABAS ==========
abas = st.tabs(["📊 Visão Geral", "📁 Grupos", "🏢 Unidades", "📅 Por Data", "📋 Tabela"])

# === VISÃO GERAL ===
with abas[0]:
    st.title("📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("Lotes únicos", df_filt["lote_id"].nunique())
    col2.metric("Seriais", df_filt.shape[0])
    col3.metric("Atualizado em", datetime.now().strftime("%d/%m/%Y %H:%M"))

# === POR GRUPO ===
with abas[1]:
    st.subheader("📁 Total de Seriais por Grupo")
    fig1 = px.histogram(df_filt, x="grupo", color="status_lote", barmode="group", title="Seriais por Grupo")
    fig1.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',        # fundo do gráfico
        paper_bgcolor='rgba(0,0,0,0)',       # fundo da área externa
        font=dict(color=cor_texto_menu),    # cor dos textos do gráfico
        legend=dict(font=dict(color=cor_texto_menu)),  # legenda
        xaxis=dict(
            color=cor_texto_menu,
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            color=cor_texto_menu,
            showgrid=True,
            gridcolor="#444" if modo == "Escuro" else "#ccc",
            zeroline=False
        )
    )

    st.plotly_chart(fig1, use_container_width=True)

# === POR UNIDADE ===
with abas[2]:
    st.subheader("🏢 Distribuição por Unidade")
    fig2 = px.histogram(df_filt, x="unidade", color="modelo", barmode="stack", title="Modelos por Unidade")
    fig2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',        # fundo do gráfico
        paper_bgcolor='rgba(0,0,0,0)',       # fundo da área externa
        font=dict(color=cor_texto_menu),    # cor dos textos do gráfico
        legend=dict(font=dict(color=cor_texto_menu)),  # legenda
        xaxis=dict(
            color=cor_texto_menu,
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            color=cor_texto_menu,
            showgrid=True,
            gridcolor="#444" if modo == "Escuro" else "#ccc",
            zeroline=False
        )
    )

    st.plotly_chart(fig2, use_container_width=True)

# === POR DATA ===
with abas[3]:
    st.subheader("📅 Evolução Temporal de Seriais")
    df_time = df_filt.groupby(df_filt["data"].dt.date).size().reset_index(name="qtd")
    fig3 = px.line(df_time, x="data", y="qtd", markers=True, title="Seriais ao Longo do Tempo")
    fig3.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',        # fundo do gráfico
        paper_bgcolor='rgba(0,0,0,0)',       # fundo da área externa
        font=dict(color=cor_texto_menu),    # cor dos textos do gráfico
        legend=dict(font=dict(color=cor_texto_menu)),  # legenda
        xaxis=dict(
            color=cor_texto_menu,
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            color=cor_texto_menu,
            showgrid=True,
            gridcolor="#444" if modo == "Escuro" else "#ccc",
            zeroline=False
        )
    )

    st.plotly_chart(fig3, use_container_width=True)
# === TABELA ===
with abas[4]:
    st.subheader("📋 Tabela Completa")
    st.dataframe(df_filt, use_container_width=True, height=500)

    csv = df_filt.to_csv(index=False, sep=";").encode("utf-8")
    st.download_button("⬇️ Baixar CSV", data=csv, file_name="seriais_filtrados.csv", mime="text/csv")
