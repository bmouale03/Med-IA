import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import tempfile
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Inventaire Médicaments IA", layout="wide")

st.title("Pharma-IA-App")

# ---------- Chargement des données ----------
# Initialisation
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
        ],
        'prix_unitaire': [1.0, 1.5, 2.0, 0.8],
        'pays': ['Benin', 'Benin', 'Benin', 'Benin'],
        'ville': ['Cotonou', 'Parakou', 'Porto-Novo', 'Calavi'],
    }

# Ventes journalières historiques (pour dashboard)
if 'ventes_historique' not in st.session_state:
    if os.path.exists("historique_ventes.csv"):
        st.session_state.ventes_historique = pd.read_csv("historique_ventes.csv", parse_dates=['date'])
    else:
        st.session_state.ventes_historique = pd.DataFrame(columns=["date", "médicament", "ventes", "prix_unitaire", "pays", "ville"])

# ---------- Description du projet ----------
st.markdown("""
Bienvenue dans l'application **Inventaire Médicaments IA**
### Objectifs :
- Surveiller automatiquement les stocks par pays et ville
- Prédire la consommation à 3 jours
- Détecter les stocks critiques

### Fonctionnalités :
- Ajout de médicaments avec localisation
- Prédiction via IA
- Alerte intelligente
- Suivi des ventes et CA
""")

# ---------- Ajout Médicament ----------
with st.expander("➕ Ajouter un médicament"):
    with st.form("form_ajout"):
        nom = st.text_input("Nom du médicament")
        stock = st.number_input("Stock actuel", min_value=0, step=1)
        stock_min = st.number_input("Stock minimum", min_value=0, step=1)
        prix = st.number_input("Prix unitaire (€)", min_value=0.0, step=0.1)
        ventes_7j = st.text_input("Ventes des 7 derniers jours (séparées par virgules)")
        pays = st.text_input("Pays")
        ville = st.text_input("Ville")
        submit = st.form_submit_button("Ajouter")

        if submit:
            try:
                ventes = [int(x.strip()) for x in ventes_7j.split(',') if x.strip()]
                if len(ventes) != 7:
                    st.error("Veuillez entrer exactement 7 valeurs.")
                elif not pays or not ville:
                    st.error("Veuillez saisir Pays et Ville.")
                else:
                    st.session_state.data['médicament'].append(nom)
                    st.session_state.data['stock_actuel'].append(stock)
                    st.session_state.data['stock_minimum'].append(stock_min)
                    st.session_state.data['historique_ventes_7j'].append(ventes)
                    st.session_state.data['prix_unitaire'].append(prix)
                    st.session_state.data['pays'].append(pays)
                    st.session_state.data['ville'].append(ville)

                    # Historique journalier
                    dates = [datetime.today().date() - timedelta(days=6-i) for i in range(7)]
                    for i, d in enumerate(dates):
                        st.session_state.ventes_historique = pd.concat([
                            st.session_state.ventes_historique,
                            pd.DataFrame([{
                                "date": d,
                                "médicament": nom,
                                "ventes": ventes[i],
                                "prix_unitaire": prix,
                                "pays": pays,
                                "ville": ville
                            }])
                        ], ignore_index=True)

                    # Sauvegarde
                    st.session_state.ventes_historique.to_csv("historique_ventes.csv", index=False)
                    st.success(f"{nom} ajouté avec succès pour {ville}, {pays} !")
            except:
                st.error("Erreur dans les valeurs de ventes.")

# ---------- Prévisions ----------
def forecast_stock(historique):
    X = np.array(range(len(historique))).reshape(-1, 1)
    y = np.array(historique)
    model = LinearRegression().fit(X, y)
    return int(np.sum(model.predict(np.array([[7], [8], [9]]))))

df = pd.DataFrame(st.session_state.data)
df['prévision_3j'] = df['historique_ventes_7j'].apply(forecast_stock)
df['stock_final_prévu'] = df['stock_actuel'] - df['prévision_3j']
df['alerte'] = df.apply(lambda row: '⚠️ Critique' if row['stock_final_prévu'] < row['stock_minimum'] else '✅ OK', axis=1)
df['chiffre_affaires_7j'] = df.apply(lambda row: sum(row['historique_ventes_7j']) * row['prix_unitaire'], axis=1)

# ---------- Filtrage par Pays et Ville ----------
st.subheader("Filtrer l'inventaire par Pays et Ville")
pays_unique = ['Tous'] + sorted(df['pays'].unique().tolist())
selected_pays = st.selectbox("Choisissez un pays", pays_unique)

if selected_pays != 'Tous':
    villes_unique = ['Toutes'] + sorted(df[df['pays'] == selected_pays]['ville'].unique().tolist())
else:
    villes_unique = ['Toutes'] + sorted(df['ville'].unique().tolist())

selected_ville = st.selectbox("Choisissez une ville", villes_unique)

# Filtrer le dataframe
df_filtre = df.copy()
if selected_pays != 'Tous':
    df_filtre = df_filtre[df_filtre['pays'] == selected_pays]
if selected_ville != 'Toutes':
    df_filtre = df_filtre[df_filtre['ville'] == selected_ville]

# ---------- Affichage tableau principal ----------
st.subheader("Inventaire actuel")
st.dataframe(df_filtre[['médicament', 'pays', 'ville', 'stock_actuel', 'stock_minimum', 'stock_final_prévu', 'alerte', 'prix_unitaire', 'chiffre_affaires_7j']], use_container_width=True)

# ---------- Graphique de consommation ----------
st.subheader("Historique de consommation (7 jours)")

# Pour le selectbox, limiter aux médicaments filtrés
selected_med = st.selectbox("Choisissez un médicament", df_filtre['médicament'].unique())
row = df_filtre[df_filtre['médicament'] == selected_med].iloc[0]
fig, ax = plt.subplots()
ax.plot(range(1, 8), row['historique_ventes_7j'], marker='o')
ax.set_title(f"Consommation - {selected_med} ({row['ville']}, {row['pays']})")
ax.set_xlabel("Jour")
ax.set_ylabel("Ventes")
st.pyplot(fig)

# ---------- Alerte globale ----------
if any(df_filtre['alerte'] == '⚠️ Critique'):
    st.warning("⚠️ Certains stocks sont critiques dans la sélection !")
else:
    st.success("✅ Tous les stocks sont suffisants dans la sélection.")

# ---------- Dashboard Statistiques Ventes ----------
st.subheader("Tableau de bord des ventes")

df_hist = st.session_state.ventes_historique.copy()
#df_hist['date'] = pd.to_datetime(df_hist['date'])
df_hist['date'] = pd.to_datetime(df_hist['date'], errors='coerce', format='%Y-%m-%d')


# Filtrer ventes historique selon pays et ville
if selected_pays != 'Tous':
    df_hist = df_hist[df_hist['pays'] == selected_pays]
if selected_ville != 'Toutes':
    df_hist = df_hist[df_hist['ville'] == selected_ville]

df_last7 = df_hist[df_hist['date'] >= datetime.today() - timedelta(days=7)]

if not df_last7.empty:
    top_med = df_last7.groupby('médicament')['ventes'].sum().idxmax()
    top_rev = df_last7.groupby('médicament').apply(lambda x: (x['ventes'] * x['prix_unitaire']).sum()).idxmax()
    st.metric("Médicament le plus vendu", top_med)
    st.metric("Médicament le plus rentable", top_rev)
    st.metric("CA total (7j)", f"{(df_last7['ventes'] * df_last7['prix_unitaire']).sum():.2f} €")

    # Graphique barres
    ventes_par_med = df_last7.groupby('médicament')['ventes'].sum()
    fig2, ax2 = plt.subplots()
    ventes_par_med.plot(kind='bar', color='skyblue', ax=ax2)
    ax2.set_title(f"Ventes totales par médicament (7j) - {selected_ville}, {selected_pays}")
    ax2.set_ylabel("Unités vendues")
    st.pyplot(fig2)
else:
    st.info("Aucune donnée de vente enregistrée pour les 7 derniers jours dans la sélection.")

# ---------- Export HTML ----------
if st.button("🌐 Exporter en HTML"):
    html_content = f"""
    <html>
    <head><meta charset="utf-8"><title>Inventaire Médicaments</title></head>
    <body>
        <h1>Inventaire Médicaments IA</h1>
        <p>Rapport de stock généré le {datetime.today().strftime('%d/%m/%Y')}</p>
        {df_filtre[['médicament', 'pays', 'ville', 'stock_actuel', 'stock_minimum', 'stock_final_prévu', 'alerte', 'prix_unitaire']].to_html(index=False)}
    </body>
    </html>
    """
    st.download_button("⬇️ Télécharger en HTML", data=html_content, file_name="rapport_medicaments.html", mime="text/html")

# ---------- Pied de page ----------
st.markdown("---")
st.caption("© 2025 - IA développée par Dr. MOUALE")
