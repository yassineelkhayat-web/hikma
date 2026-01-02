import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURATION & BASE DE DONNÉES ---
st.set_page_config(page_title="Suivi Coran", layout="wide")

def init_db():
    conn = sqlite3.connect('coran_data.db')
    c = conn.cursor()
    # Table des utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                  role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT)''')
    # Ajout d'un admin par défaut si la table est vide
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect('coran_data.db')

# --- LOGIQUE DE SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None

# --- INTERFACE DE CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Connexion - Suivi Coran")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    
    col1, col2 = st.columns(2)
    if col1.button("Se connecter"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
        result = c.fetchone()
        if result:
            st.session_state['logged_in'] = True
            st.session_state['user'] = username
            st.session_state['role'] = result[0]
            st.rerun()
        else:
            st.error("Identifiants incorrects")
            
    if col2.button("S'inscrire (Membre)"):
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password, role, page_actuelle, sourate) VALUES (?, ?, 'membre', 1, 'Al-Baqara')", (username, password))
            conn.commit()
            st.success("Compte créé ! Connectez-vous.")
        except:
            st.error("Ce nom d'utilisateur existe déjà.")

# --- INTERFACE APRÈS CONNEXION ---
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    st.sidebar.write(f"Rôle: {st.session_state['role']}")
    if st.sidebar.button("Déconnexion"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- VUE ADMIN ---
    if st.session_state['role'] == 'admin':
        st.title("🛠 Panneau Administration")
        conn = get_connection()
        df = pd.read_sql_query("SELECT id, username, role, page_actuelle, sourate, obj_hizb, date_cible FROM users", conn)
        
        st.subheader("Liste des membres et progrès")
        st.dataframe(df, use_container_width=True)

        st.subheader("Gestion des rôles")
        user_to_promote = st.selectbox("Choisir un membre", df['username'])
        new_role = st.radio("Nouveau rôle", ["membre", "admin"])
        if st.button("Mettre à jour le rôle"):
            c = conn.cursor()
            c.execute("UPDATE users SET role=? WHERE username=?", (new_role, user_to_promote))
            conn.commit()
            st.success(f"{user_to_promote} est maintenant {new_role}")
            st.rerun()
        conn.close()

    # --- VUE MEMBRE ---
    st.title("📖 Mon Bilan Personnel")
    username = st.session_state['user']
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (username,))
    data = c.fetchone()

    with st.form("mon_bilan"):
        col1, col2 = st.columns(2)
        p_act = col1.number_input("Page actuelle", value=data[0] or 1)
        sou = col1.text_input("Sourate actuelle", value=data[1] or "")
        obj = col2.number_input("Objectif (Hizb)", value=data[2] or 1)
        date_c = col2.date_input("Pour le (date)")
        
        if st.form_submit_button("Enregistrer mes progrès"):
            c.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?", 
                      (p_act, sou, obj, str(date_c), username))
            conn.commit()
            st.success("Bilan mis à jour !")
    conn.close()
