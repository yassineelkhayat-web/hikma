import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran", layout="wide")

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                  role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT)''')
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- GESTION SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['user'] = None
    st.session_state['role'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = "Accueil"

# --- CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Connexion")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    
    col1, col2 = st.columns(2)
    if col1.button("Se connecter"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
        res = c.fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0]})
            st.rerun()
        else: st.error("Erreur d'identifiants")
        
    if col2.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',1)", (u,p))
            conn.commit()
            st.success("Compte créé !")
        except: st.error("Pseudo déjà pris")

# --- APP PRINCIPALE ---
else:
    # --- BARRE LATÉRALE (MENU) ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Accueil", use_container_width=True):
        st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Paramètres", use_container_width=True):
        st.session_state['page'] = "Paramètres"
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- LOGIQUE DES PAGES ---
    if st.session_state['page'] == "Accueil":
        st.title("🏠 Accueil")
        
        # Section Membre (Toujours visible pour soi-même)
        st.subheader("Mon Bilan")
        conn = get_connection()
        user_data = pd.read_sql_query("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", 
                                      conn, params=(st.session_state['user'],)).iloc[0]
        
        with st.form("update_form"):
            c1, c2 = st.columns(2)
            p_act = c1.number_input("Page actuelle", value=int(user_data['page_actuelle'] or 1))
            sou = c1.text_input("Sourate actuelle", value=user_data['sourate'] or "")
            obj = c2.number_input("Objectif Hizb", value=int(user_data['obj_hizb'] or 1))
            dt = c2.date_input("Date cible")
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_act, sou, obj, str(dt), st.session_state['user']))
                conn.commit()
                st.success("Mis à jour !")
        
        # Section Admin (Vue globale)
        if st.session_state['role'] == 'admin':
            st.markdown("---")
            st.subheader("📊 Vue d'ensemble (Admin)")
            all_users = pd.read_sql_query("SELECT username, page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE role='membre'", conn)
            st.table(all_users)
        conn.close()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Paramètres")
        
        if st.session_state['role'] == 'admin':
            st.subheader("Gestion des Membres")
            conn = get_connection()
            users_df = pd.read_sql_query("SELECT username, role FROM users", conn)
            u_to_change = st.selectbox("Choisir un utilisateur", users_df['username'])
            new_role = st.radio("Rôle", ["membre", "admin"])
            
            if st.button("Modifier le rôle"):
                conn.execute("UPDATE users SET role=? WHERE username=?", (new_role, u_to_change))
                conn.commit()
                st.success(f"{u_to_change} est maintenant {new_role}")
            conn.close()
        else:
            st.info("Seul un administrateur peut modifier les paramètres globaux.")
            st.write("Ici tu pourras bientôt changer ton mot de passe.")
