import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from datetime import datetime

# -----------------------------------------------------
# CONFIGURACIÓN INICIAL
# -----------------------------------------------------
st.set_page_config(page_title="Gestor de Pendientes", layout="wide")

# Conexión a la base de datos (debe estar configurada en Streamlit Secrets)
DB_URL = st.secrets.get("DB_URL", "")
if not DB_URL:
    st.error("❌ No se encontró la conexión a la base de datos. Configura DB_URL en Streamlit Secrets.")
engine = create_engine(DB_URL)

# -----------------------------------------------------
# FUNCIONES DE BASE DE DATOS
# -----------------------------------------------------
def agregar_pendiente(data):
    """Inserta un nuevo pendiente en la base de datos"""
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pendientes (empresa, producto, cantidad, proveedor, estado, motivo, vendedor)
            VALUES (:empresa, :producto, :cantidad, :proveedor, :estado, :motivo, :vendedor)
        """), data)

def obtener_pendientes():
    """Obtiene todos los pendientes"""
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM pendientes ORDER BY fecha_creacion DESC"))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# -----------------------------------------------------
# LOGIN CON UNA SOLA CONTRASEÑA GLOBAL
# -----------------------------------------------------
PASSWORD_GLOBAL = "Himax"  # 🔒 Cambia esta contraseña a la que quieras

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    clave = st.text_input("Ingresa la contraseña:", type="password")
    if st.button("Entrar"):
        if clave == PASSWORD_GLOBAL:
            st.session_state.autenticado = True
            st.success("✅ Acceso concedido. Bienvenido al sistema.")
            st.rerun()

        else:
            st.error("❌ Contraseña incorrecta.")

# -----------------------------------------------------
# INTERFAZ PRINCIPAL (solo si el usuario está autenticado)
# -----------------------------------------------------
if st.session_state.autenticado:
    st.sidebar.success("🔐 Acceso autorizado")
    opcion = st.sidebar.selectbox("Menú", ["📋 Pendientes", "📊 Dashboard", "🚪 Cerrar sesión"])

    # -------------------------------
    # SECCIÓN: AGREGAR / VER PENDIENTES
    # -------------------------------
    if opcion == "📋 Pendientes":
        st.header("📋 Gestión de Pendientes")

        st.subheader("Agregar nuevo pendiente")
        with st.form("nuevo_pendiente"):
            empresa = st.text_input("Empresa")
            producto = st.text_input("Producto")
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            proveedor = st.text_input("Proveedor")
            motivo = st.text_area("Motivo o comentario")

            if st.form_submit_button("Guardar"):
                if empresa and producto:
                    agregar_pendiente({
                        "empresa": empresa,
                        "producto": producto,
                        "cantidad": cantidad,
                        "proveedor": proveedor,
                        "estado": "Pendiente",
                        "motivo": motivo,
                        "vendedor": "Usuario General"
                    })
                    st.success("✅ Pendiente guardado correctamente.")
                else:
                    st.warning("Por favor completa al menos Empresa y Producto.")

        st.subheader("Lista de pendientes actuales")
        df = obtener_pendientes()
        if df.empty:
            st.info("No hay pendientes registrados aún.")
        else:
            st.dataframe(df, use_container_width=True)

    # -------------------------------
    # SECCIÓN: DASHBOARD
    # -------------------------------
    elif opcion == "Dashboard":
    st.title("📊 Dashboard de Productos Pendientes")

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM pendientes", conn)

    if df.empty:
        st.info("No hay datos registrados todavía.")
    else:
        st.subheader("Resumen general")

        # Resumen total por proveedor
        resumen_proveedor = df.groupby("proveedor")["cantidad"].sum().reset_index()
        st.bar_chart(resumen_proveedor.set_index("proveedor"))

        st.divider()
        st.subheader("Detalle por empresa")

        empresas = sorted(df["empresa"].dropna().unique())
        empresa_sel = st.selectbox("Selecciona una empresa", empresas)

        df_empresa = df[df["empresa"] == empresa_sel]

        if not df_empresa.empty:
            st.write("### Productos pendientes para:", empresa_sel)

            # Tabla resumen
            tabla = df_empresa.groupby(["producto", "sku", "proveedor"])["cantidad"].sum().reset_index()
            st.dataframe(tabla, use_container_width=True)

            # Gráfico de barras por producto
            st.write("### Cantidad de productos pendientes")
            import plotly.express as px
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


    # -------------------------------
    # SECCIÓN: CERRAR SESIÓN
    # -------------------------------
    elif opcion == "🚪 Cerrar sesión":
        st.session_state.autenticado = False
        st.success("Sesión cerrada correctamente.")
        st.rerun()



