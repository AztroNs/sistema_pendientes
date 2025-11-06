import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
import bcrypt
from datetime import datetime

# -----------------------------------------------------
# CONFIGURACIÓN INICIAL
# -----------------------------------------------------
st.set_page_config(page_title="Gestor de Pendientes", layout="wide")

# Aquí debes tener guardada tu conexión a Supabase (PostgreSQL)
DB_URL = st.secrets.get("DB_URL", "")  # Si estás en Streamlit Cloud, usa Secrets
engine = create_engine(DB_URL)

# -----------------------------------------------------
# FUNCIONES DE BASE DE DATOS
# -----------------------------------------------------
def crear_usuario(nombre, correo, contrasena, rol="vendedor"):
    hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO usuarios (nombre, correo, contrasena_hash, rol) VALUES (:n, :c, :h, :r)"),
            {"n": nombre, "c": correo, "h": hashed, "r": rol}
        )

def verificar_usuario(correo, contrasena):
    with engine.begin() as conn:
        user = conn.execute(text("SELECT * FROM usuarios WHERE correo=:c"), {"c": correo}).fetchone()
    if user and bcrypt.checkpw(contrasena.encode('utf-8'), user.contrasena_hash.encode('utf-8')):
        return dict(user)
    return None

def agregar_pendiente(data):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO pendientes (empresa, producto, cantidad, proveedor, estado, motivo, vendedor)
            VALUES (:empresa, :producto, :cantidad, :proveedor, :estado, :motivo, :vendedor)
        """), data)

def obtener_pendientes():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM pendientes ORDER BY fecha_creacion DESC"))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

# -----------------------------------------------------
# INTERFAZ DE USUARIO
# -----------------------------------------------------
st.title("📦 Sistema de Gestión de Pendientes")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# LOGIN / REGISTRO
if not st.session_state.usuario:
    tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "🧾 Registrarse"])

    with tab_login:
        correo = st.text_input("Correo")
        contrasena = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            user = verificar_usuario(correo, contrasena)
            if user:
                st.session_state.usuario = user
                st.success(f"Bienvenido, {user['nombre']} 👋")
                st.experimental_rerun()
            else:
                st.error("Correo o contraseña incorrectos.")

    with tab_registro:
        nombre = st.text_input("Nombre completo")
        correo_r = st.text_input("Correo nuevo")
        contrasena_r = st.text_input("Contraseña nueva", type="password")
        if st.button("Registrar"):
            if nombre and correo_r and contrasena_r:
                crear_usuario(nombre, correo_r, contrasena_r)
                st.success("Usuario registrado correctamente ✅")
            else:
                st.warning("Por favor completa todos los campos.")
else:
    user = st.session_state.usuario
    st.sidebar.success(f"Conectado como: {user['nombre']} ({user['rol']})")
    opcion = st.sidebar.selectbox("Menú", ["📋 Pendientes", "📊 Dashboard", "🚪 Cerrar sesión"])

    if opcion == "📋 Pendientes":
        st.subheader("Agregar nuevo pendiente")
        with st.form("nuevo_pendiente"):
            empresa = st.text_input("Empresa")
            producto = st.text_input("Producto")
            cantidad = st.number_input("Cantidad", min_value=1, step=1)
            proveedor = st.text_input("Proveedor")
            motivo = st.text_area("Motivo o comentario")
            if st.form_submit_button("Guardar"):
                agregar_pendiente({
                    "empresa": empresa,
                    "producto": producto,
                    "cantidad": cantidad,
                    "proveedor": proveedor,
                    "estado": "Pendiente",
                    "motivo": motivo,
                    "vendedor": user["nombre"]
                })
                st.success("Pendiente guardado correctamente ✅")

        st.subheader("Lista de pendientes actuales")
        df = obtener_pendientes()
        if df.empty:
            st.info("No hay pendientes registrados aún.")
        else:
            st.dataframe(df)

    elif opcion == "📊 Dashboard":
        df = obtener_pendientes()
        if df.empty:
            st.info("Aún no hay datos para mostrar.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(df.groupby("proveedor")["cantidad"].sum().reset_index(),
                             x="proveedor", y="cantidad", title="Cantidad pendiente por proveedor")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig2 = px.pie(df, names="estado", title="Distribución por estado")
                st.plotly_chart(fig2, use_container_width=True)

    elif opcion == "🚪 Cerrar sesión":
        st.session_state.usuario = None
        st.experimental_rerun()
