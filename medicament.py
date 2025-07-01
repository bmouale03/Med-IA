import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import tempfile
import pdfkit

import os


st.set_page_config(page_title="Inventaire Médicaments IA", layout="wide")

st.title("Pharma-IA-App")

# Description complète du projet
st.markdown("""
Bienvenue dans l'application **Inventaire Médicaments IA** 

Cette solution intelligente est conçue pour aider les établissements de santé, les pharmacies et les gestionnaires de stocks médicaux à **surveiller en temps réel les niveaux de médicaments**, **anticiper les consommations futures**, et **prévenir les ruptures de stock critiques**.

### Objectifs :
- Automatiser la surveillance des stocks de médicaments.
- Prédire la consommation des 3 prochains jours grâce à un modèle de régression linéaire.
- Détecter les situations à risque où les stocks peuvent passer en dessous du seuil minimum.

### Fonctionnalités principales :
- **Ajout dynamique de nouveaux médicaments** avec leurs stocks et ventes récentes.
- **Prévision de la consommation** sur 3 jours basée sur les 7 derniers jours de ventes.
- **Tableau de bord en temps réel** avec statut d'alerte automatique.
- **Visualisation graphique** des tendances de consommation hebdomadaire.

### Alertes intelligentes :
Chaque médicament est automatiquement marqué :
- ✅ **OK** si les prévisions indiquent un stock suffisant.
- ⚠️ **Critique** si une rupture est anticipée.
""")

# Session state
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

df = pd.DataFrame(st.session_state.data)

# Ajout médicament
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

# Prévision
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

# Affichage du tableau
st.subheader(" Inventaire actuel")
st.dataframe(df[['médicament', 'stock_actuel', 'stock_minimum', 'stock_final_prévu', 'alerte']], use_container_width=True)

# Affichage graphique
st.subheader(" Graphique de consommation (7 derniers jours)")
selected_med = st.selectbox("Choisissez un médicament", df['médicament'])

selected_row = df[df['médicament'] == selected_med].iloc[0]
historique = selected_row['historique_ventes_7j']

fig, ax = plt.subplots()
ax.plot(range(1, 8), historique, marker='o', color='blue')
ax.set_title(f'Historique de consommation - {selected_med}')
ax.set_xlabel("Jour")
ax.set_ylabel("Ventes")
st.pyplot(fig)

# Message final
if any(df['alerte'] == '⚠️ Critique'):
    st.warning("Attention : certains stocks sont critiques !")
else:
    st.success("Tous les stocks sont dans les seuils normaux.")

# Export HTML
if st.button("🌐 Exporter en HTML"):
    html_content = f"""
    <html>
    <head><meta charset="utf-8"><title>Inventaire Médicaments</title></head>
    <body>
        <h1>Inventaire Médicaments IA</h1>
        <p>Bienvenue dans l'application <strong>Inventaire Médicaments IA</strong> </p>
        <p>Cette solution intelligente est conçue pour surveiller les niveaux de médicaments, anticiper la consommation et prévenir les ruptures de stock.</p>
        <h2>Inventaire actuel</h2>
        {df[['médicament', 'stock_actuel', 'stock_minimum', 'stock_final_prévu', 'alerte']].to_html(index=False)}
    </body>
    </html>
    """
    st.download_button("⬇️ Télécharger en HTML", data=html_content, file_name="rapport_medicaments.html", mime="text/html")

# Export PDF (nécessite wkhtmltopdf installé)
if st.button("📄 Exporter en PDF"):
    try:
        html_content = f"""
        <h1>Inventaire Médicaments IA</h1>
        <p>Bienvenue dans l'application <strong>Inventaire Médicaments IA</strong></p>
        <p>Cette solution intelligente est conçue pour surveiller les niveaux de médicaments, anticiper la consommation et prévenir les ruptures de stock.</p>
        <h2>Inventaire actuel</h2>
        {df[['médicament', 'stock_actuel', 'stock_minimum', 'stock_final_prévu', 'alerte']].to_html(index=False)}
        """

        # Spécifier le chemin exact vers wkhtmltopdf.exe
        config = pdfkit.configuration(wkhtmltopdf="C:\Program Files\wkhtmltopdf\bin\wkhtmltox-0.12.6-1.msvc2015-win32.exe")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            pdfkit.from_string(html_content, tmp_file.name, configuration=config)
            with open(tmp_file.name, "rb") as f:
                st.download_button("⬇️ Télécharger le rapport PDF", f, file_name="rapport_medicaments.pdf")
            os.remove(tmp_file.name)
    except Exception as e:
        st.error(f"Erreur lors de l’export PDF : {e}")


# --- PIED DE PAGE ---
st.markdown("---")
st.caption("© 2025 - IA développée par Dr. MOUALE")