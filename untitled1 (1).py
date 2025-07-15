import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random

st.set_page_config(page_title="P.A.N.D.A. PE", layout="wide")

# --- Simular usuarios permitidos ---
USUARIOS = {"admin": "1234", "gustavo": "panda2025"}

# --- Control de sesión ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# --- Login ---
if not st.session_state.logueado:
    st.title("🔐 Iniciar Sesión - P.A.N.D.A. PE")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if user in USUARIOS and USUARIOS[user] == password:
            st.session_state.logueado = True
            st.session_state.usuario = user
            st.success(f"¡Bienvenido, {user}!")
            st.rerun()
        else:
            st.error("Credenciales incorrectas.")
    st.stop()

# --- Menú lateral ---
st.sidebar.title("📊 Menú")
opcion = st.sidebar.selectbox("Selecciona una opción:", [
    "🏠 Volver al inicio",
    "🧪 Iniciar nuevo proyecto",
    "📁 Cargar proyecto guardado",
    "❌ Salir"
])

if opcion == "❌ Salir":
    st.session_state.logueado = False
    st.session_state.usuario = ""
    st.success("Sesión finalizada.")
    st.rerun()

# --- Inicio ---
if opcion == "🏠 Volver al inicio":
    st.title("🐼 P.A.N.D.A. PE - Dashboard de Conservación")
    st.markdown("Bienvenido al sistema de reproducción asistida de especies en peligro. Selecciona una opción del menú para comenzar.")
    st.image("https://cdn-icons-png.flaticon.com/512/616/616408.png", width=150)

# --- Iniciar nuevo proyecto ---
elif opcion == "🧪 Iniciar nuevo proyecto":
    st.title("🧬 Nuevo Proyecto de Emparejamiento Genético")

    archivo = st.file_uploader("📥 Sube tu archivo CSV de animales saludables", type=["csv"])

    if archivo:
        df = pd.read_csv(archivo)
        st.success("¡Archivo cargado correctamente!")
        st.dataframe(df.head())

        saludables = df[df['Salud'] == 'Saludable']
        machos = saludables[saludables['Sexo'] == 'Macho']
        hembras = saludables[saludables['Sexo'] == 'Hembra']

        if len(machos) == 0 or len(hembras) == 0:
            st.error("No hay machos o hembras saludables suficientes.")
            st.stop()

        G = nx.Graph()
        for _, row in machos.iterrows():
            G.add_node(f"M_{row['ID']}", **row.to_dict())
        for _, row in hembras.iterrows():
            G.add_node(f"H_{row['ID']}", **row.to_dict())

        def calcular_peso(macho, hembra):
            try:
                pg = 1 - ((macho['Valor_Genetico'] + hembra['Valor_Genetico']) / 2)
                pdist = 1 - abs(macho['Distancia'] - hembra['Distancia']) / max(macho['Distancia'], hembra['Distancia'], 1)
                pcost = 1 - abs(macho['Costo_Movilidad'] - hembra['Costo_Movilidad']) / max(macho['Costo_Movilidad'], hembra['Costo_Movilidad'], 1)
                clima = 1 if macho['Clima'] == hembra['Clima'] else 0
                antecedentes = 1 if macho['Antecedentes'] == hembra['Antecedentes'] else 0
                return (pg + pdist + pcost + clima + antecedentes) / 5
            except:
                return 0.0

        for _, m in machos.iterrows():
            for _, h in hembras.iterrows():
                if m['Especie'] == h['Especie']:
                    peso = calcular_peso(m, h)
                    G.add_edge(f"M_{m['ID']}", f"H_{h['ID']}", weight=peso)

        matching = nx.algorithms.matching.min_weight_matching(G, weight="weight")
        parejas = [(m, h) if m.startswith("M_") else (h, m) for m, h in matching]

        st.subheader("🐾 Parejas Seleccionadas")
        st.write(f"Se emparejaron {len(parejas)} parejas.")
        if st.checkbox("Mostrar parejas"):
            for macho, hembra in parejas:
                st.write(f"{macho} - {hembra}")

        st.header("🍼 Simulación de Crías")
        prob_salud = st.slider("Probabilidad de salud", 0.5, 1.0, 0.95)
        if st.button("Simular crías"):
            random.seed(42)
            np.random.seed(42)
            crias = []
            for macho_id, hembra_id in parejas:
                macho_row = machos[machos['ID'] == int(macho_id[2:])].iloc[0]
                hembra_row = hembras[hembras['ID'] == int(hembra_id[2:])].iloc[0]
                for _ in range(random.randint(1, 3)):
                    base = (macho_row['Valor_Genetico'] + hembra_row['Valor_Genetico']) / 2
                    variacion = np.random.normal(0, 0.05)
                    valor = min(max(base + variacion, 0), 1)
                    salud = "Saludable" if random.random() < prob_salud else "Enfermo"
                    crias.append({
                        "Especie": macho_row['Especie'],
                        "Valor_Genetico": valor,
                        "Salud": salud
                    })

            df_crias = pd.DataFrame(crias)
            st.success(f"{len(df_crias)} crías generadas.")
            st.dataframe(df_crias.head())

            tabs = st.tabs(["📊 Histograma Genético", "🧬 Pie Chart Salud", "📈 Boxplot Comparativo"])
            with tabs[0]:
                fig, ax = plt.subplots()
                ax.hist(df_crias["Valor_Genetico"], bins=20, color='skyblue', edgecolor='black')
                ax.set_title("Distribución del Valor Genético de Crías")
                st.pyplot(fig)

            with tabs[1]:
                fig, ax = plt.subplots()
                df_crias["Salud"].value_counts().plot.pie(autopct='%1.1f%%', colors=['green', 'red'], ax=ax)
                ax.set_ylabel("")
                ax.set_title("Salud de Crías")
                st.pyplot(fig)

            with tabs[2]:
                comparar = pd.concat([
                    pd.DataFrame({"Grupo": "Originales", "Valor_Genetico": saludables["Valor_Genetico"]}),
                    pd.DataFrame({"Grupo": "Crías", "Valor_Genetico": df_crias["Valor_Genetico"]})
                ])
                fig, ax = plt.subplots()
                comparar.boxplot(column='Valor_Genetico', by='Grupo', ax=ax)
                plt.suptitle("")
                ax.set_title("Comparación de Valor Genético")
                st.pyplot(fig)

# --- Opción futura: cargar proyecto guardado ---
elif opcion == "📁 Cargar proyecto guardado":
    st.info("📦 Esta función se implementará próximamente para cargar archivos CSV anteriores.")