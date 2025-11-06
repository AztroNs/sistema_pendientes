import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# 🔐 Contraseña única para ingresar
APP_PASSWORD = "Himax"

# 🌐 Conexión a la base de datos Neon.tech
DB_URL = "postgresql+psycopg2://neondb_owner:npg_XU4IAbaent7p@ep-twilight-credit-acc6aiu0-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DB_URL)

# --- Login simple ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
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

# --- Menú lateral ---
st.sidebar.title("Menú")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["Lista de pendientes", "Agregar pendiente", "Dashboard"]
)

# --- Función para obtener datos ---
def obtener_pendientes():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM pendientes ORDER BY fecha_creacion DESC"))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    return df

# --- Lista de pendientes ---
if opcion == "Lista de pendientes":
    st.title("📋 Lista de pendientes actuales")

    df = obtener_pendientes()
    if df.empty:
        st.info("No hay pendientes registrados aún.")
    else:
        st.dataframe(df, use_container_width=True)

# --- Agregar pendiente ---
elif opcion == "Agregar pendiente":
    st.title("➕ Agregar nuevo pendiente")

    with st.form("form_pendiente"):
        empresa = st.text_input("Empresa (cliente)")
        producto = st.text_input("Producto")
        sku = st.text_input("Código SKU (opcional)")
        cantidad = st.number_input("Cantidad", min_value=1, step=1)
        proveedor = st.text_input("Proveedor")
        estado = st.selectbox("Estado", ["Pendiente", "En Proceso", "Completado"])
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

# --- Dashboard ---
elif opcion == "Dashboard":
    st.title("📊 Dashboard de Productos Pendientes")

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM pendientes", conn)

    if df.empty:
        st.info("No hay datos registrados todavía.")
    else:
        st.subheader("📦 Resumen general por proveedor")

        resumen_proveedor = df.groupby("proveedor")["cantidad"].sum().reset_index()
        st.bar_chart(resumen_proveedor.set_index("proveedor"))

        st.divider()
        st.subheader("🏢 Detalle por empresa")

        empresas = sorted(df["empresa"].dropna().unique())
        empresa_sel = st.selectbox("Selecciona una empresa", empresas)

        df_empresa = df[df["empresa"] == empresa_sel]

        if not df_empresa.empty:
            st.write("### Productos pendientes para:", empresa_sel)

            tabla = df_empresa.groupby(["producto", "sku", "proveedor"])["cantidad"].sum().reset_index()
            st.dataframe(tabla, use_container_width=True)

            st.write("### Cantidad de productos pendientes")
            fig = px.bar(
                tabla,
                x="producto",
                y="cantidad",
                color="proveedor",
                text="cantidad",
                title=f"Pendientes por producto - {empresa_sel}",
                labels={"cantidad": "Unidades", "producto": "Producto"},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Esta empresa no tiene productos pendientes.")


