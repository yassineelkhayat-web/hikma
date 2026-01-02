import streamlit as st
from datetime import date

# Configuration de la page
st.set_page_config(page_title="Bilan Coran", page_icon="📖")

st.title("📖 Mon Suivi de Mémorisation")

# --- SIMULATION UTILISATEUR (En attendant la base de données) ---
nom_membre = "Utilisateur Test" 

st.subheader(f"Bienvenue, {nom_membre}")

# --- FORMULAIRE DE MISE À JOUR ---
with st.form("bilan_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        page_actuelle = st.number_input("Page actuelle (où tu en es)", min_value=1, max_value=604, value=1)
        sourate_actuelle = st.text_input("Sourate actuelle", placeholder="Ex: Al-Baqara")
    
    with col2:
        page_objectif_jour = st.number_input("Objectif de pages à étudier / jour", min_value=0.5, step=0.5)
        date_objectif = st.date_input("Date cible pour l'objectif", value=date(2024, 2, 2))
    
    hizb_cible = st.number_input("Objectif (ex: 10ème Hizb)", min_value=1, max_value=60)
    
    # Bouton de validation
    submit = st.form_submit_button("Mettre à jour mon bilan")

if submit:
    st.success(f"Bravo ! Tes progrès ont été enregistrés : Page {page_actuelle}, {sourate_actuelle}.")
    # Ici, on ajoutera plus tard le code pour enregistrer dans la base de données
