import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import os


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
        background-color: #E6F0FA !important;
        color: #003366 !important;
    }}

    /* Gráficos Plotly */
    .js-plotly-plot .plotly {{
        background-color: {HIMAX_WHITE} !important;
    }}

    /* Asegurar que TODAS las tablas (incluidas del dashboard) sean blancas */
    div[data-testid="stTable"] table {{
        background-color: white !important;
        color: #222 !important;
        border-collapse: collapse !important;
    }}

    div[data-testid="stTable"] th {{
        background-color: #f4f6f9 !important;
        color: #003366 !important;
        font-weight: bold !important;
        border-bottom: 1px solid #ccc !important;
    }}

    div[data-testid="stTable"] td {{
        background-color: white !important;
        color: #222 !important;
        border-top: 1px solid #eee !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# LEER CLAVES DESDE SECRETS (en Streamlit Cloud) O DESDE VARIABLES DE ENTORNO (local)
APP_PASSWORD = st.secrets.get("APP_PASSWORD", os.getenv("APP_PASSWORD"))
DB_URL = st.secrets.get("NEON_DB_URL", os.getenv("NEON_DB_URL"))

if not DB_URL:
    st.error("❌ No se encontró NEON_DB_URL. Revisa los Secrets de Streamlit Cloud o tu archivo de entorno.")
    st.stop()

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
    ["Lista de pendientes", "Agregar pendiente", "Dashboard", "Qué comprar", "Eliminar de pendientes", "Entregas Completadas"]
)

# === FUNCIONES ===
def obtener_pendientes():
    with engine.begin() as conn:
        result = conn.execute(text("SELECT * FROM pendientes ORDER BY fecha_creacion DESC"))
        df = pd.DataFrame(result.fetchall(), columns=result.keys())

    # Nos aseguramos de que fecha_creacion sea tipo fecha
    if not df.empty and "fecha_creacion" in df.columns:
        df["fecha_creacion"] = pd.to_datetime(df["fecha_creacion"])

    return df

# === LISTA DE PENDIENTES ===
if opcion == "Lista de pendientes":
    st.title("📋 Lista de pendientes actuales")
    df = obtener_pendientes()

    if df.empty:
        st.info("No hay pendientes registrados aún.")
    else:
        # === CÁLCULO DE DÍAS EN PENDIENTE ===
        if "fecha_creacion" in df.columns:
            # Fecha de hoy (solo fecha, sin hora)
            hoy = pd.Timestamp.today().normalize()

            # Nos aseguramos de que sea tipo datetime
            df["fecha_creacion"] = pd.to_datetime(df["fecha_creacion"])

            # Columna con días que lleva pendiente
            df["dias_pendiente"] = (hoy - df["fecha_creacion"]).dt.days

            # Filtrar los que llevan 7 días o más y siguen en estado Pendiente
            if "estado" in df.columns:
                df_atrasados = df[
                    (df["dias_pendiente"] >= 7) &
                    (df["estado"].astype(str).str.lower() == "pendiente")
                ]

                if not df_atrasados.empty:
                    st.warning(
                        f"⚠️ Hay {len(df_atrasados)} pendientes con más de 7 días sin completar."
                    )
                    # Pequeña tabla con solo lo más importante
                    columnas_alerta = [c for c in [
                        "empresa", "producto", "sku", "cantidad",
                        "proveedor", "fecha_creacion", "dias_pendiente"
                    ] if c in df_atrasados.columns]

                    st.dataframe(
                        df_atrasados[columnas_alerta].rename(columns={
                            "empresa": "Empresa",
                            "producto": "Producto",
                            "sku": "SKU",
                            "cantidad": "Cantidad",
                            "proveedor": "Proveedor",
                            "fecha_creacion": "Fecha Creación",
                            "dias_pendiente": "Días en pendiente"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    st.divider()

        # === TABLA GENERAL DE PENDIENTES ===

        columnas_mostrar = [
            "empresa",
            "rut_empresa",
            "producto",
            "sku",
            "cantidad",
            "proveedor",
            "tipo_facturacion",
            "orden_compra",
            "fecha_nota_venta",
            "n_nota_venta",
            "fecha_entrega",
            "estado",
            "motivo",
            "vendedor",
            "fecha_creacion",
            "dias_pendiente",   # 👈 agregamos esta columna
        ]

        # Filtra columnas que existan (por compatibilidad con datos antiguos)
        columnas_existentes = [c for c in columnas_mostrar if c in df.columns]
        df = df[columnas_existentes]

        # Renombra columnas para visualización
        df = df.rename(columns={
            "empresa": "Empresa",
            "rut_empresa": "RUT Empresa",
            "producto": "Producto",
            "sku": "SKU",
            "cantidad": "Cantidad",
            "proveedor": "Proveedor",
            "tipo_facturacion": "Tipo de Facturación",
            "orden_compra": "Orden de Compra",
            "fecha_nota_venta": "Fecha Nota Venta",
            "n_nota_venta": "N° Nota Venta",
            "estado": "Estado",
            "motivo": "Motivo o Comentario",
            "vendedor": "Vendedor",
            "fecha_creacion": "Fecha Creación",
            "fecha_entrega": "Fecha de Entrega",
            "dias_pendiente": "Días en pendiente"
        })

        st.dataframe(df, use_container_width=True, hide_index=True)

# === AGREGAR PENDIENTE ===
elif opcion == "Agregar pendiente":
    st.title("➕ Agregar nuevo pendiente")

    with st.form("form_pendiente"):
        col1, col2 = st.columns(2)
        with col1:
            empresa = st.text_input("Empresa (cliente)")
            rut_empresa = st.text_input("RUT de la empresa")
            fecha_nota_venta = st.date_input("Fecha de Nota de Venta")
            fecha_entrega = st.date_input("Fecha de Entrega (opcional)", value=None)
        with col2:
            n_nota_venta = st.text_input("N° Nota de Venta")
            tipo_facturacion = st.selectbox(
                "Tipo de Facturación",
                ["Parcializada c/ constancia", "Completa"]
            )
            orden_compra = st.text_input("Número de Orden de Compra")

        st.divider()

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
                    INSERT INTO pendientes 
                    (empresa, rut_empresa, fecha_nota_venta, fecha_entrega, n_nota_venta, tipo_facturacion, orden_compra,
                     producto, cantidad, proveedor, estado, motivo, vendedor, sku)
                    VALUES 
                    (:empresa, :rut_empresa, :fecha_nota_venta, :fecha_entrega, :n_nota_venta, :tipo_facturacion, :orden_compra,
                     :producto, :cantidad, :proveedor, :estado, :motivo, :vendedor, :sku)
                """), {
                    "empresa": empresa,
                    "rut_empresa": rut_empresa,
                    "fecha_nota_venta": fecha_nota_venta,
                    "fecha_entrega": fecha_entrega,
                    "n_nota_venta": n_nota_venta,
                    "tipo_facturacion": tipo_facturacion,
                    "orden_compra": orden_compra,
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
            st.write(f"### Productos pendientes para: {empresa_sel}")
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

# === SECCIÓN DE COMPRAS / QUÉ COMPRAR ===
elif opcion == "Qué comprar":
    st.title("🛒 Sección de Compras - Qué productos hay que comprar")

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM pendientes", conn)

    if df.empty:
        st.info("No hay productos pendientes actualmente.")
    else:
        # --- FILTROS ---
        st.subheader("🔍 Filtros de búsqueda")

        col1, col2 = st.columns(2)
        with col1:
            empresas = sorted(df["empresa"].dropna().unique())
            empresa_sel = st.selectbox("Filtrar por empresa (opcional)", ["Todas"] + empresas)
        with col2:
            proveedores = sorted(df["proveedor"].dropna().unique())
            proveedor_sel = st.selectbox("Filtrar por proveedor", ["Todos"] + proveedores)

        # --- APLICAR FILTROS ---
        df_filtrado = df.copy()

        if empresa_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado["empresa"] == empresa_sel]

        if proveedor_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["proveedor"] == proveedor_sel]

        st.divider()

        if df_filtrado.empty:
            st.warning("No hay pendientes que coincidan con los filtros seleccionados.")
        else:
            st.subheader("📦 Productos pendientes de compra")
            tabla = df_filtrado.groupby(
                ["proveedor", "producto", "sku"]
            )["cantidad"].sum().reset_index()

            # Mostramos resumen en tabla
            st.dataframe(tabla, use_container_width=True)

            # Gráfico visual
            import plotly.express as px
            fig = px.bar(
                tabla,
                x="producto",
                y="cantidad",
                color="proveedor",
                text="cantidad",
                title="Productos pendientes por proveedor",
                labels={"cantidad": "Unidades", "producto": "Producto"},
            )
            st.plotly_chart(fig, use_container_width=True)

# === ELIMINAR O EDITAR PENDIENTES ===
elif opcion == "Eliminar de pendientes":
    st.title("🗑️ Eliminar o Editar Pendientes Existentes")

    # Cargar datos
    df = obtener_pendientes()

    if df.empty:
        st.info("No hay pendientes registrados aún.")
        st.stop()

    # Filtros de búsqueda
    st.subheader("🔍 Buscar pendiente")
    col1, col2 = st.columns(2)
    with col1:
        filtro_empresa = st.text_input("Buscar por empresa")
    with col2:
        filtro_producto = st.text_input("Buscar por producto")

    df_filtrado = df.copy()
    if filtro_empresa:
        df_filtrado = df_filtrado[df_filtrado["empresa"].str.contains(filtro_empresa, case=False, na=False)]
    if filtro_producto:
        df_filtrado = df_filtrado[df_filtrado["producto"].str.contains(filtro_producto, case=False, na=False)]

    st.write("### Resultados de búsqueda")
    if df_filtrado.empty:
        st.warning("No se encontraron resultados.")
        st.stop()

    # Mostrar resultados
    st.dataframe(df_filtrado, use_container_width=True)

    # Seleccionar un pendiente
    ids = df_filtrado["id"].tolist()
    id_sel = st.selectbox("Selecciona el ID del pendiente a editar o eliminar:", ids)

    pendiente_sel = df[df["id"] == id_sel].iloc[0]

    st.subheader(f"✏️ Editar pendiente ID {id_sel}")

    with st.form("form_editar"):
        empresa = st.text_input("Empresa", pendiente_sel["empresa"])
        rut_empresa = st.text_input("RUT Empresa", pendiente_sel.get("rut_empresa", ""))
        fecha_nota_venta = st.date_input("Fecha Nota Venta", pendiente_sel.get("fecha_nota_venta"))
        n_nota_venta = st.text_input("N° Nota de Venta", pendiente_sel.get("n_nota_venta", ""))
        tipo_facturacion = st.selectbox(
            "Tipo de Facturación",
            ["Parcializada c/ constancia", "Completa"],
            index=0 if pendiente_sel.get("tipo_facturacion") == "Parcializada c/ constancia" else 1
        )
        orden_compra = st.text_input("Número de Orden de Compra", pendiente_sel.get("orden_compra", ""))
        producto = st.text_input("Producto", pendiente_sel["producto"])
        sku = st.text_input("Código SKU", pendiente_sel.get("sku", ""))
        cantidad = st.number_input("Cantidad", min_value=1, step=1, value=int(pendiente_sel["cantidad"]))
        proveedor = st.text_input("Proveedor", pendiente_sel.get("proveedor", ""))
        estado = st.selectbox("Estado", ["Pendiente", "Completado"], index=0 if pendiente_sel["estado"] == "Pendiente" else 1)
        motivo = st.text_area("Motivo o comentario", pendiente_sel.get("motivo", ""))
        vendedor = st.text_input("Vendedor", pendiente_sel.get("vendedor", ""))

        col1, col2 = st.columns(2)
        with col1:
            guardar = st.form_submit_button("💾 Guardar cambios")
        with col2:
            eliminar = st.form_submit_button("🗑️ Eliminar pendiente")

        if guardar:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE pendientes
                    SET empresa=:empresa, rut_empresa=:rut_empresa, fecha_nota_venta=:fecha_nota_venta,
                        n_nota_venta=:n_nota_venta, tipo_facturacion=:tipo_facturacion, orden_compra=:orden_compra,
                        producto=:producto, sku=:sku, cantidad=:cantidad, proveedor=:proveedor,
                        estado=:estado, motivo=:motivo, vendedor=:vendedor
                    WHERE id=:id
                """), {
                    "id": id_sel,
                    "empresa": empresa,
                    "rut_empresa": rut_empresa,
                    "fecha_nota_venta": fecha_nota_venta,
                    "n_nota_venta": n_nota_venta,
                    "tipo_facturacion": tipo_facturacion,
                    "orden_compra": orden_compra,
                    "producto": producto,
                    "sku": sku,
                    "cantidad": cantidad,
                    "proveedor": proveedor,
                    "estado": estado,
                    "motivo": motivo,
                    "vendedor": vendedor
                })
            st.success("✅ Pendiente actualizado correctamente.")
            st.rerun()

        if eliminar:
            # Confirmación antes de eliminar
            st.warning(f"⚠️ Estás a punto de eliminar el pendiente ID {id_sel} de la empresa '{pendiente_sel['empresa']}'")
            confirmar = st.checkbox("Confirmo que deseo eliminar este pendiente definitivamente")

            if confirmar:
                # Antes de eliminar, mover a la tabla de entregas_completadas
                with engine.begin() as conn:
                    # Obtener el pendiente completo
                    pendiente = conn.execute(
                        text("SELECT * FROM pendientes WHERE id = :id"),
                        {"id": id_sel}
                    ).mappings().first()

                    if pendiente:
                        # Insertar en tabla de entregas completadas
                        conn.execute(text("""
                            INSERT INTO entregas_completadas
                            (empresa, rut_empresa, producto, sku, cantidad, proveedor, tipo_facturacion,
                             orden_compra, fecha_nota_venta, n_nota_venta, estado, motivo, vendedor, fecha_creacion)
                            VALUES
                            (:empresa, :rut_empresa, :producto, :sku, :cantidad, :proveedor, :tipo_facturacion,
                             :orden_compra, :fecha_nota_venta, :n_nota_venta, :estado, :motivo, :vendedor, :fecha_creacion)
                        """), pendiente)

                        # Ahora sí, eliminarlo de pendientes
                        conn.execute(text("DELETE FROM pendientes WHERE id = :id"), {"id": id_sel})

                st.success("✅ Pendiente eliminado y movido a 'Entregas Completadas'.")
                st.rerun()

            else:
                st.info("El pendiente no ha sido eliminado. Marca la casilla para confirmar.")

# === ENTREGAS COMPLETADAS ===
elif opcion == "Entregas Completadas":
    st.title("📦 Entregas Completadas - Historial de productos entregados")

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM entregas_completadas ORDER BY fecha_entrega DESC", conn)

    if df.empty:
        st.info("Aún no hay entregas completadas registradas.")
    else:
        st.subheader("Historial de entregas registradas")

        # Opcional: filtros de búsqueda
        col1, col2 = st.columns(2)
        with col1:
            filtro_empresa = st.text_input("Buscar por empresa")
        with col2:
            filtro_proveedor = st.text_input("Buscar por proveedor")

        df_filtrado = df.copy()
        if filtro_empresa:
            df_filtrado = df_filtrado[df_filtrado["empresa"].str.contains(filtro_empresa, case=False, na=False)]
        if filtro_proveedor:
            df_filtrado = df_filtrado[df_filtrado["proveedor"].str.contains(filtro_proveedor, case=False, na=False)]

        # Reordenar columnas y mostrar
        columnas = [
            "empresa", "rut_empresa", "producto", "sku", "cantidad", "proveedor",
            "tipo_facturacion", "orden_compra", "fecha_nota_venta", "n_nota_venta",
            "motivo", "vendedor", "fecha_entrega"
        ]
        df_filtrado = df_filtrado[[c for c in columnas if c in df_filtrado.columns]]

        # Renombrar para visualización
        df_filtrado = df_filtrado.rename(columns={
            "empresa": "Empresa",
            "rut_empresa": "RUT Empresa",
            "producto": "Producto",
            "sku": "SKU",
            "cantidad": "Cantidad",
            "proveedor": "Proveedor",
            "tipo_facturacion": "Tipo de Facturación",
            "orden_compra": "Orden de Compra",
            "fecha_nota_venta": "Fecha Nota Venta",
            "n_nota_venta": "N° Nota Venta",
            "motivo": "Motivo o Comentario",
            "vendedor": "Vendedor",
            "fecha_entrega": "Fecha Entrega"
        })

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)












