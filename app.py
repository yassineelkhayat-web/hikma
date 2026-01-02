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
    # Création de la table si elle n'existe pas
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                  role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT)''')
    
    # --- AJOUT/MISE À JOUR DE L'ADMIN ---
    # On utilise REPLACE pour être sûr que les identifiants sont bien ceux-là
    c.execute("""
        INSERT OR REPLACE INTO users (id, username, password, role) 
        VALUES ((SELECT id FROM users WHERE username='admin'), 'admin', 'admin123', 'admin')
    """)
    
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

# --- INTERFACE DE CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Connexion au Suivi Coran")
    
    with st.container():
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        
        col1, col2 = st.columns(2)
        if col1.button("Se connecter", use_container_width=True):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
            res = c.fetchone()
            if res:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res[0]})
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
                st.info("Note : L'admin par défaut est 'admin' avec le mot de passe 'admin123'")
        
        if col2.button("S'inscrire comme Membre", use_container_width=True):
            if u and p:
                try:
                    conn = get_connection()
                    conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',1)", (u,p))
                    conn.commit()
                    st.success("Compte créé ! Connectez-vous.")
                except:
                    st.error("Ce pseudo existe déjà.")
            else:
                st.warning("Veuillez remplir les champs.")

# --- APP PRINCIPALE ---
else:
    # Sidebar
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

    # --- PAGE ACCUEIL ---
    if st.session_state['page'] == "Accueil":
        st.title("🏠 Accueil")
        
        # Section pour modifier son propre bilan
        st.subheader("📝 Mettre à jour mon bilan")
        c = conn.cursor()
        c.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (st.session_state['user'],))
        data = c.fetchone()
        
        # On s'assure que data n'est pas None (cas rare)
        current_p = data[0] if data and data[0] else 1
        current_s = data[1] if data and data[1] else ""
        current_h = data[2] if data and data[2] else 1
        
        with st.form("update_form"):
            c1, c2 = st.columns(2)
            p_act = c1.number_input("Page actuelle", value=int(current_p), min_value=1, max_value=604)
            sou = c1.text_input("Sourate actuelle", value=current_s)
            obj = c2.number_input("Objectif Hizb", value=int(current_h))
            dt = c2.date_input("Date cible")
            if st.form_submit_button("Enregistrer mes progrès"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_act, sou, obj, str(dt), st.session_state['user']))
                conn.commit()
                st.success("Progrès enregistrés !")

        # Affichage du tableau pour l'Admin
        if st.session_state['role'] == 'admin':
            st.markdown("---")
            st.subheader("📊 Tableau de bord de tous les membres")
            all_users = pd.read_sql_query("SELECT username, page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE role='membre'", conn)
            st.dataframe(all_users, use_container_width=True)

    # --- PAGE PARAMÈTRES ---
    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Paramètres")
        
        if st.session_state['role'] == 'admin':
            # Promotion
            st.subheader("👥 Gestion des rôles")
            u_list = pd.read_sql_query("SELECT username FROM users WHERE role='membre'", conn)
            if not u_list.empty:
                u_to_change = st.selectbox("Choisir un membre à promouvoir", u_list['username'])
                if st.button("Nommer Admin"):
                    conn.execute("UPDATE users SET role='admin' WHERE username=?", (u_to_change,))
                    conn.commit()
                    st.success(f"{u_to_change} est maintenant Admin")
                    st.rerun()
            
            st.markdown("---")
            
            # Suppression
            st.subheader("🗑️ Supprimer des membres")
            all_u = pd.read_sql_query("SELECT id, username FROM users WHERE role='membre'", conn)
            if not all_u.empty:
                for _, row in all_u.iterrows():
                    col_u, col_btn = st.columns([3, 1])
                    col_u.write(f"Utilisateur : **{row['username']}**")
                    if col_btn.button("Supprimer", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM users WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
                
                if st.button("TOUT SUPPRIMER", type="primary"):
                    conn.execute("DELETE FROM users WHERE role='membre'")
                    conn.commit()
                    st.rerun()
            else:
                st.info("Aucun membre enregistré.")
        else:
            st.info("Espace réservé à l'administrateur.")

    conn.close()
