import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran - Final", layout="wide")

# --- DONNÉES SOURATES (Début, Fin) ---
DATA_CORAN = {
    "An-Nas": (604, 604), "Al-Falaq": (604, 604), "Al-Ikhlas": (604, 604), "Al-Masad": (603, 603), 
    "An-Nasr": (603, 603), "Al-Kafirun": (603, 603), "Al-Kawthar": (602, 602), "Al-Maun": (602, 602), 
    "Quraish": (602, 602), "Al-Fil": (601, 601), "Al-Humaza": (601, 601), "Al-Asr": (601, 601), 
    "At-Takathur": (600, 600), "Al-Qaria": (600, 600), "Al-Adiyat": (599, 599), "Az-Zalzala": (599, 599), 
    "Al-Bayyina": (598, 598), "Al-Qadr": (598, 598), "Al-Alaq": (597, 597), "At-Tin": (597, 597),
    "Ash-Sharh": (596, 596), "Ad-Duha": (596, 596), "Al-Layl": (595, 595), "Ash-Shams": (595, 595), 
    "Al-Balad": (594, 594), "Al-Fajr": (593, 593), "Al-Ghashiya": (592, 592), "Al-Ala": (591, 591), 
    "At-Tariq": (591, 591), "Al-Buruj": (590, 590), "Al-Inshiqaq": (589, 589), "Al-Mutaffifin": (588, 588), 
    "Al-Infitar": (587, 587), "At-Takwir": (586, 586), "Abasa": (585, 585), "An-Naziat": (583, 584), 
    "An-Naba": (582, 583), "Al-Mursalat": (580, 581), "Al-Insan": (578, 580), "Al-Qiyama": (577, 578),
    "Al-Muddathir": (575, 577), "Al-Muzzammil": (574, 575), "Al-Jinn": (572, 573), "Nuh": (570, 571), 
    "Al-Maarij": (568, 569), "Al-Haqqa": (566, 568), "Al-Qalam": (564, 566), "Al-Mulk": (562, 564),
}

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT, pages_par_semaine_fixe REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, page_atteinte INT, sourate_atteinte TEXT)''')
    conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None, 'page': "Accueil"})

# --- ÉCRAN DE CONNEXION / INSCRIPTION ---
if not st.session_state['logged_in']:
    st.title("🌙 Suivi Coran")
    tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])
    
    with tab1:
        u = st.text_input("Pseudo", key="login_u")
        p = st.text_input("Mot de passe", type="password", key="login_p")
        if st.button("Se connecter", use_container_width=True):
            conn = get_connection()
            res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
                st.rerun()
            else: st.error("Identifiants incorrects.")

    with tab2:
        new_u = st.text_input("Choisir un Pseudo", key="reg_u")
        new_p = st.text_input("Choisir un Mot de passe", type="password", key="reg_p")
        if st.button("S'inscrire", use_container_width=True):
            if new_u and new_p:
                try:
                    conn = get_connection()
                    conn.execute("INSERT INTO users (username, password, role, page_actuelle, sourate) VALUES (?,?,'membre',604, 'An-Nas')", (new_u, new_p))
                    conn.commit()
                    st.success("Compte créé ! Connecte-toi maintenant.")
                except: st.error("Ce pseudo est déjà utilisé.")
            else: st.warning("Remplis tous les champs.")

else:
    # --- INTERFACE PRINCIPALE ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Admin", use_container_width=True) and st.session_state['role'] == 'admin': st.session_state['page'] = "Paramètres"
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        # Dashboard
        p_act, h_obj, d_str = row[0] or 604, row[2] or 0, row[3] or str(date.today())
        p_cible = 582 if h_obj == 2 else (604 - ((h_obj - 1) * 10) if h_obj > 0 else p_act)
        p_restantes = max(0, p_act - p_cible)
        try: jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
        except: jours = 0
        p_hebdo = round((p_restantes / max(1, jours)) * 7, 1) if jours > 0 else row[4] or 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages à faire", p_restantes)
        c2.metric("Jours restants", max(0, jours))
        c3.metric("Objectif Hebdo", f"{p_hebdo} p.")

        # Formulaire Dynamique
        s_list = list(DATA_CORAN.keys())
        choix_s = st.selectbox("Sourate actuelle", s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
        p_deb, p_fin = DATA_CORAN[choix_s]
        nb_p = p_fin - p_deb + 1
        page_detectee = p_deb
        
        if nb_p > 1:
            opts = [f"Page {i+1}" for i in range(nb_p)]
            sel_p = st.radio(f"{choix_s} ({nb_p} pages). Laquelle as-tu fini ?", opts, horizontal=True)
            page_detectee = p_deb + opts.index(sel_p)
        
        st.success(f"📍 Page actuelle enregistrée : **{page_detectee}**")

        with st.expander("🎯 Modifier mes objectifs"):
            new_h = st.number_input("Hizb Cible", value=int(h_obj))
            new_sem = st.number_input("Pages/Semaine fixe", value=float(row[4] or 0.0))
            new_d = st.date_input("Date limite", value=datetime.strptime(d_str, '%Y-%m-%d').date())

        if st.button("💾 Enregistrer mes progrès", use_container_width=True):
            conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_semaine_fixe=? WHERE id=?", 
                         (page_detectee, choix_s, new_h, str(new_d), new_sem, st.session_state['user_id']))
            conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                         (st.session_state['user'], str(date.today()), page_detectee, choix_s))
            conn.commit(); st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration")
        all_u = pd.read_sql_query("SELECT * FROM users", conn)
        for _, u_row in all_u.iterrows():
            if u_row['id'] == st.session_state['user_id']: continue
            with st.expander(f"👤 {u_row['username']} ({u_row['role']})"):
                c1, c2 = st.columns(2)
                if u_row['role'] == 'membre' and c1.button("🔼 Promouvoir", key=f"p{u_row['id']}"):
                    conn.execute("UPDATE users SET role='admin' WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()
                if u_row['role'] == 'admin' and st.session_state['user_id'] == 1 and c1.button("🔽 Rétrograder", key=f"r{u_row['id']}"):
                    conn.execute("UPDATE users SET role='membre' WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()
                if c2.button("🗑️ Supprimer", key=f"d{u_row['id']}", type="primary"):
                    conn.execute("DELETE FROM users WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()

        st.divider()
        st.subheader("📅 Logs de progression")
        h_df = pd.read_sql_query("SELECT * FROM history", conn)
        ed_df = st.data_editor(h_df, num_rows="dynamic", use_container_width=True)
        if st.button("Enregistrer modifications tableau"):
            conn.execute("DELETE FROM history")
            ed_df.to_sql('history', conn, if_exists='append', index=False)
            conn.commit(); st.success("Logs mis à jour")
    conn.close()
