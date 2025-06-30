
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

st.set_page_config(page_title="Inventaire Médicaments IA", layout="wide")

st.title("💊 Application IA – Gestion d'Inventaire de Médicaments")
st.markdown("Cette application prédit la consommation des médicaments et signale les stocks critiques.")

# Session state to store dynamic data
if 'data' not in st.session_state:
    st.session_state.data = {
        'médicament': ['Paracétamol', 'Ibuprofène', 'Amoxicilline', 'Doliprane'],
        'stock_actuel': [150, 80, 40, 20],
        'stock_minimum': [50, 30, 20, 15],
        'historique_ventes_7j': [
            [30, 32, 29, 28, 31, 33, 35],
            [10, 12, 11, 9, 13, 15, 14],
            [5, 6, 5, 4, 6, 7, 8],
            [3, 2, 2, 1, 2, 3, 4]
        ]
    }

# Convert to DataFrame
df = pd.DataFrame(st.session_state.data)

# --- Formulaire d'ajout ---
with st.expander("➕ Ajouter un médicament"):
    with st.form("form_ajout"):
        nom = st.text_input("Nom du médicament")
        stock = st.number_input("Stock actuel", min_value=0, step=1)
        stock_min = st.number_input("Stock minimum", min_value=0, step=1)
        ventes_7j = st.text_input("Ventes des 7 derniers jours (séparées par des virgules)")
        submit = st.form_submit_button("Ajouter")

        if submit:
            try:
                ventes = [int(x.strip()) for x in ventes_7j.split(',') if x.strip() != '']
                if len(ventes) != 7:
                    st.error("Veuillez entrer exactement 7 valeurs.")
                else:
                    st.session_state.data['médicament'].append(nom)
                    st.session_state.data['stock_actuel'].append(stock)
                    st.session_state.data['stock_minimum'].append(stock_min)
                    st.session_state.data['historique_ventes_7j'].append(ventes)
                    st.success(f"{nom} ajouté avec succès !")
            except:
                st.error("Erreur dans les valeurs des ventes. Assurez-vous d'utiliser uniquement des nombres séparés par des virgules.")

# --- Fonction de prévision ---
def forecast_stock(historique):
    X = np.array(range(len(historique))).reshape(-1, 1)
    y = np.array(historique)
    model = LinearRegression().fit(X, y)
    future_days = np.array([[7], [8], [9]])
    prediction = model.predict(future_days)
    return int(np.sum(prediction))

df['prévision_3j'] = df['historique_ventes_7j'].apply(forecast_stock)
df['stock_final_prévu'] = df['stock_actuel'] - df['prévision_3j']
df['alerte'] = df.apply(lambda row: '⚠️ Critique' if row['stock_final_prévu'] < row['stock_minimum'] else '✅ OK', axis=1)

# --- Affichage tableau ---
st.subheader("📋 Inventaire actuel")
st.dataframe(df[['médicament', 'stock_actuel', 'stock_minimum', 'stock_final_prévu', 'alerte']], use_container_width=True)

# --- Affichage graphique ---
st.subheader("📈 Graphique de consommation (7 derniers jours)")
selected_med = st.selectbox("Choisissez un médicament", df['médicament'])

selected_row = df[df['médicament'] == selected_med].iloc[0]
historique = selected_row['historique_ventes_7j']

fig, ax = plt.subplots()
ax.plot(range(1, 8), historique, marker='o', color='blue')
ax.set_title(f'Historique de consommation - {selected_med}')
ax.set_xlabel("Jour")
ax.set_ylabel("Ventes")
st.pyplot(fig)

# --- Message final ---
if any(df['alerte'] == '⚠️ Critique'):
    st.warning("Attention : certains stocks sont critiques !")
else:
    st.success("Tous les stocks sont dans les seuils normaux.")
