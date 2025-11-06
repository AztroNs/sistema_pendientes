import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(
    page_title="Sistema de Pendientes - Himax",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === COLORES CORPORATIVOS HIMAX ===
HIMAX_PRIMARY = "#007BFF"
HIMAX_DARK = "#003366"
HIMAX_LIGHT = "#E6F0FA"
HIMAX_ACCENT = "#00AEEF"
HIMAX_WHITE = "#FFFFFF"
HIMAX_TEXT = "#222222"

# === ESTILO PERSONALIZADO ===
st.markdown(
    f"""
    <style>
    /* Fondo general */
    .stApp {{
        background-color: {HIMAX_LIGHT};
    }}

    /* Títulos */
    h1, h2, h3, h4, h5, h6, label {{
        color: {HIMAX_DARK} !important;
        font-family: 'Segoe UI', sans-serif;
    }}

    /* Texto general */
    p, span, div {{
        color: {HIMAX_TEXT} !important;
        font-family: 'Segoe UI', sans-serif;
    }}

    /* Formularios */
    input, textarea, select {{
        color: {HIMAX_TEXT} !important;
        background-color: {HIMAX_WHITE} !important;
        border-radius: 6px !important;
        border: 1px solid #CCC !important;
    }}

    /* Placeholders */
    input::placeholder, textarea::placeholder {{
        color: #777 !important;
    }}

    /* Botones */
    .stButton>button {{
        background-color: {HIMAX_PRIMARY};
        color: white;
        border-radius: 6px;
        height: 2.5em;
        font-weight: bold;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {HIMAX_ACCENT};
        color: white;
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {HIMAX_WHITE};
        border-right: 2px solid {HIMAX_ACCENT};
    }}
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] span {{
        color: {HIMAX_DARK} !important;
        font-weight: 500;
    }}

    /* DataFrame (tabla fondo blanco) */
    div[data-testid="stDataFrame"] div[role="gridcell"],
    div[data-testid="stDataFrame"] div[role="columnheader"] {{
        background-color: {HIMAX_WHITE} !important;
        color: {HIMAX_TEXT} !important;
        border-color: #ddd !important;
    }}

    /* Cabecera de tabla */
    div[data-testid="stDataFrame"] div[role="columnheader"] {{
        font-weight: bold !important;
        background-color: #f4f6f9 !important;
    }}

    /* Selectbox */
    div[data-baseweb="select"] > div {{
        background-color: {HIMAX_WHITE} !important;
        color: {HIMAX_TEXT} !important;
    }}

    /* --- FIX: menú desplegable oscuro --- */
    div[data-baseweb="popover"] {{
        background-color: white !important;
        color: #222 !important;
        border: 1px solid #ccc !important;
    }}
    div[data-baseweb="popover"] div {{
        background-color: white !important;
        color: #222 !important;
    }}
    div[data-baseweb="option"] {{
        background-color: white !important;
        color: #222 !important;
    }}
    div[data-baseweb="option"]:hover {{
        background-color: #E6F0FA !important;  /* tono celeste Himax */
        color: #003366 !important;
    }}

    /* Gráficos Plotly */
    .js-plotly-plot .plotly {{
        background-color: {HIMAX_WHITE} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# === LOGIN SIMPLE ===
APP_PASSWORD = "Familia2025"
DB_URL = "postgresql+psycopg2://neondb_owner:npg_XU4IAbaent7p@ep-twilight-credit-acc6aiu0-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DB_URL)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.image("Logotipo Himax COLOR.png", width=220)
    st.title("🔒 Acceso al Sistema de Pendientes")
    password = st.text_input("Contraseña:", type="password")
    if st.button("Entrar"):
        if password == APP_PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Acceso concedido. Bienvenido al sistema.")
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta.")
    st.stop()

# === MENÚ LATERAL ===
st.sidebar.image("Logotipo Himax COLOR.png", width=180)
st.sidebar.title("Menú")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["Lista de pendientes", "Agregar pendiente", "Dashboard"]
)

# === FUNCIONES ===
def obtener_pendientes():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM pendientes ORDER BY fecha_creacion DESC"))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df

# === LISTA DE PENDIENTES ===
if opcion == "Lista de pendientes":
    st.title("📋 Lista de pendientes actuales")
    df = obtener_pendientes()

    if df.empty:
        st.info("No hay pendientes registrados aún.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

# === AGREGAR PENDIENTE ===
elif opcion == "Agregar pendiente":
    st.title("➕ Agregar nuevo pendiente")

    with st.form("form_pendiente"):
        empresa = st.text_input("Empresa (cliente)")
        producto = st.text_input("Producto")
        sku = st.text_input("Código SKU (opcional)")
        cantidad = st.number_input("Cantidad", min_value=1, step=1)
        proveedor = st.text_input("Proveedor")
        estado = "Pendiente"
        motivo = st.text_area("Motivo o comentario")
        vendedor = st.text_input("Vendedor")

        enviado = st.form_submit_button("Guardar")

        if enviado:
            with engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO pendientes (empresa, producto, cantidad, proveedor, estado, motivo, vendedor, sku)
                    VALUES (:empresa, :producto, :cantidad, :proveedor, :estado, :motivo, :vendedor, :sku)
                """), {
                    "empresa": empresa,
                    "producto": producto,
                    "cantidad": cantidad,
                    "proveedor": proveedor,
                    "estado": estado,
                    "motivo": motivo,
                    "vendedor": vendedor,
                    "sku": sku
                })
            st.success("✅ Pendiente agregado exitosamente.")

# === DASHBOARD ===
elif opcion == "Dashboard":
    st.title("📊 Dashboard de Productos Pendientes")

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM pendientes", conn)

    if df.empty:
        st.info("No hay datos registrados todavía.")
    else:
        st.subheader("📦 Resumen general por proveedor")

        resumen_proveedor = df.groupby("proveedor")["cantidad"].sum().reset_index()
        fig1 = px.bar(
            resumen_proveedor,
            x="proveedor",
            y="cantidad",
            text="cantidad",
            title="Cantidad total de productos pendientes por proveedor",
            color_discrete_sequence=[HIMAX_PRIMARY]
        )
        fig1.update_layout(
            plot_bgcolor=HIMAX_WHITE,
            paper_bgcolor=HIMAX_WHITE,
            font_color=HIMAX_DARK
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.divider()
        st.subheader("🏢 Detalle por empresa")

        empresas = sorted(df["empresa"].dropna().unique())
        empresa_sel = st.selectbox("Selecciona una empresa", empresas)

        df_empresa = df[df["empresa"] == empresa_sel]

        if not df_empresa.empty:
            st.write("### Productos pendientes para:", empresa_sel)
            tabla = df_empresa.groupby(["producto", "sku", "proveedor"])["cantidad"].sum().reset_index()
            st.dataframe(tabla, use_container_width=True)

            fig2 = px.bar(
                tabla,
                x="producto",
                y="cantidad",
                color="proveedor",
                text="cantidad",
                title=f"Pendientes por producto - {empresa_sel}",
                color_discrete_sequence=[HIMAX_PRIMARY, HIMAX_ACCENT, HIMAX_DARK]
            )
            fig2.update_layout(
                plot_bgcolor=HIMAX_WHITE,
                paper_bgcolor=HIMAX_WHITE,
                font_color=HIMAX_DARK
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Esta empresa no tiene productos pendientes.")
