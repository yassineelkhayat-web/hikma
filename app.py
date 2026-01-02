import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime, timedelta

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Ajout de la colonne pages_par_jour_fixe pour l'objectif alternatif
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, 
                  page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT, pages_par_jour_fixe FLOAT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, page_atteinte INT, sourate_atteinte TEXT)''')
    c.execute("INSERT OR REPLACE INTO users (id, username, password, role) VALUES ((SELECT id FROM users WHERE username='admin'), 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

# --- CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Suivi Coran Inversé")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        conn = get_connection()
        res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0]})
            st.rerun()
        else: st.error("Identifiants incorrects.")
    if st.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',604)", (u,p))
            conn.commit()
            st.success("Compte créé ! Connectez-vous.")
        except: st.error("Pseudo déjà pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi"): st.session_state['page'] = "Accueil"
    if st.session_state['role'] == 'admin':
        if st.sidebar.button("🛡️ Panel Admin"): st.session_state['page'] = "Admin"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()

    conn = get_connection()

    # --- PAGE UTILISATEUR ---
    if st.session_state['page'] == "Accueil":
        st.title("📖 Mon Progrès")
        data = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_jour_fixe FROM users WHERE username=?", (st.session_state['user'],)).fetchone()
        p_act, s_act, h_obj, d_str, p_fixe = data[0] or 604, data[1] or "", data[2], data[3], data[4]

        # Calcul des stats
        if h_obj and d_str:
            p_cible = 604 - ((h_obj - 1) * 10)
            p_restantes = max(0, p_act - p_cible)
            jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
            rythme = round(p_restantes / jours, 2) if jours > 0 else 0
            methode = "Objectif Hizb"
        elif p_fixe and p_fixe > 0:
            p_restantes = p_act - 1 # Jusqu'au début du Coran
            jours = round(p_restantes / p_fixe)
            d_estimee = date.today() + timedelta(days=jours)
            rythme = p_fixe
            methode = f"Rythme fixe ({p_fixe} p/j)"
        else:
            p_restantes, jours, rythme, methode = 0, 0, 0, "Aucun objectif"

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages restantes", p_restantes)
        c2.metric("Jours", jours)
        c3.metric("Pages/Jour", rythme)
        st.caption(f"Méthode actuelle : {methode}")

        with st.form("update_user"):
            st.subheader("Mettre à jour mon état")
            new_p = st.number_input("Page actuelle", value=p_act)
            new_s = st.text_input("Sourate actuelle", value=s_act)
            st.divider()
            st.write("Modifier mon objectif (Hizb OU Pages/Jour)")
            new_h = st.number_input("Hizb Cible (Laissez 0 pour utiliser pages/jour)", value=h_obj or 0)
            new_d = st.date_input("Date Cible", value=datetime.strptime(d_str, '%Y-%m-%d').date() if d_str else date.today())
            new_p_f = st.number_input("OU Pages par jour (si pas d'objectif Hizb)", value=p_fixe or 0.0)
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_jour_fixe=? WHERE username=?",
                             (new_p, new_s, new_h if new_h > 0 else None, str(new_d), new_p_f if new_h <= 0 else 0, st.session_state['user']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), new_p, new_s))
                conn.commit()
                st.rerun()

    # --- PAGE ADMIN ---
    elif st.session_state['page'] == "Admin":
        st.title("🛡️ Gestion des Membres")
        
        users_df = pd.read_sql_query("SELECT * FROM users WHERE role='membre'", conn)
        
        if users_df.empty:
            st.info("Aucun membre inscrit.")
        else:
            for index, row in users_df.iterrows():
                with st.expander(f"👤 {row['username']} (Page: {row['page_actuelle']})"):
                    with st.form(f"admin_edit_{row['username']}"):
                        col1, col2 = st.columns(2)
                        edit_p = col1.number_input("Page Actuelle", value=row['page_actuelle'], key=f"p_{index}")
                        edit_s = col2.text_input("Sourate", value=row['sourate'], key=f"s_{index}")
                        edit_h = col1.number_input("Objectif Hizb", value=int(row['obj_hizb'] or 0), key=f"h_{index}")
                        edit_d = col2.date_input("Date Cible", value=datetime.strptime(row['date_cible'], '%Y-%m-%d').date() if row['date_cible'] else date.today(), key=f"d_{index}")
                        edit_pf = col1.number_input("Pages/Jour fixe", value=float(row['pages_par_jour_fixe'] or 0), key=f"pf_{index}")
                        
                        btn_col1, btn_col2 = st.columns(2)
                        if btn_col1.form_submit_button("💾 Sauvegarder"):
                            conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_jour_fixe=? WHERE username=?",
                                         (edit_p, edit_s, edit_h if edit_h > 0 else None, str(edit_d), edit_pf, row['username']))
                            conn.commit()
                            st.success("Modifié !")
                            st.rerun()
                        
                        if btn_col2.form_submit_button("🗑️ Supprimer le membre"):
                            conn.execute("DELETE FROM users WHERE username=?", (row['username'],))
                            conn.commit()
                            st.rerun()

            st.divider()
            st.subheader("📊 Historique global (Aujourd'hui)")
            hist_today = pd.read_sql_query("SELECT * FROM history WHERE date_enregistrement=?", conn, params=(str(date.today()),))
            st.dataframe(hist_today)

    conn.close()
