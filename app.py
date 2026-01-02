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
    # Force la création/mise à jour de l'admin au démarrage
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
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
        else: st.error("Erreur d'identifiants (Rappel : admin / admin123)")
        
    if col2.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',1)", (u,p))
            conn.commit()
            st.success("Compte créé ! Connectez-vous.")
        except: st.error("Pseudo déjà pris")

# --- APP PRINCIPALE ---
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Accueil", use_container_width=True):
        st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Paramètres", use_container_width=True):
        st.session_state['page'] = "Paramètres"
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Accueil")
        
        # Section Membre
        st.subheader("📝 Mettre à jour mon bilan")
        c = conn.cursor()
        c.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (st.session_state['user'],))
        data = c.fetchone()
        
        with st.form("update_form"):
            c1, c2 = st.columns(2)
            p_act = c1.number_input("Page actuelle", value=int(data[0] or 1), min_value=1, max_value=604)
            sou = c1.text_input("Sourate actuelle", value=data[1] or "")
            obj = c2.number_input("Objectif Hizb", value=int(data[2] or 1))
            dt = c2.date_input("Date cible")
            if st.form_submit_button("Enregistrer mes progrès"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_act, sou, obj, str(dt), st.session_state['user']))
                conn.commit()
                st.success("Progrès enregistrés !")

        # Vue Admin sur l'accueil
        if st.session_state['role'] == 'admin':
            st.markdown("---")
            st.subheader("📊 Tableau de bord global")
            all_users = pd.read_sql_query("SELECT username, page_actuelle, sourate, obj_hizb, date_cible FROM users", conn)
            st.dataframe(all_users, use_container_width=True)

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Paramètres")
        
        if st.session_state['role'] == 'admin':
            st.subheader("👥 Gestion des comptes")
            
            # 1. Promouvoir un membre
            st.write("**Promouvoir un membre en Admin**")
            u_list = pd.read_sql_query("SELECT username FROM users WHERE role='membre'", conn)
            if not u_list.empty:
                u_to_change = st.selectbox("Choisir un membre", u_list['username'])
                if st.button("Nommer Admin"):
                    conn.execute("UPDATE users SET role='admin' WHERE username=?", (u_to_change,))
                    conn.commit()
                    st.success(f"{u_to_change} est maintenant Admin")
                    st.rerun()
            else:
                st.info("Aucun membre à promouvoir.")

            st.markdown("---")
            
            # 2. Supprimer des membres
            st.write("**Supprimer des utilisateurs**")
            all_u = pd.read_sql_query("SELECT id, username, role FROM users WHERE username != 'admin'", conn)
            for index, row in all_u.iterrows():
                col_u, col_btn = st.columns([3, 1])
                col_u.write(f"{row['username']} ({row['role']})")
                if col_btn.button("Supprimer", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM users WHERE id=?", (row['id'],))
                    conn.commit()
                    st.warning(f"Utilisateur {row['username']} supprimé.")
                    st.rerun()

            st.markdown("---")
            
            # 3. Supprimer TOUT LE MONDE
            st.write("⚠️ **Zone de danger**")
            if st.button("SUPPRIMER TOUS LES MEMBRES", type="primary"):
                conn.execute("DELETE FROM users WHERE role='membre'")
                conn.commit()
                st.error("Tous les membres ont été supprimés.")
                st.rerun()
        else:
            st.info("Vous n'avez pas les droits pour modifier les paramètres.")

    conn.close()
