import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran - Complet", layout="wide")

SURATES_PAGES = {
    "An-Nas": 604, "Al-Falaq": 604, "Al-Ikhlas": 604, "Al-Masad": 603, "An-Nasr": 603,
    "Al-Kafirun": 603, "Al-Kawthar": 602, "Al-Maun": 602, "Quraish": 602, "Al-Fil": 601,
    "Al-Humaza": 601, "Al-Asr": 601, "At-Takathur": 600, "Al-Qaria": 600, "Al-Adiyat": 599,
    "Az-Zalzala": 599, "Al-Bayyina": 598, "Al-Qadr": 598, "Al-Alaq": 597, "At-Tin": 597,
    "Ash-Sharh": 596, "Ad-Duha": 596, "Al-Layl": 595, "Ash-Shams": 595, "Al-Balad": 594,
    "Al-Fajr": 593, "Al-Ghashiya": 592, "Al-Ala": 591, "At-Tariq": 591, "Al-Buruj": 590,
    "Al-Inshiqaq": 589, "Al-Mutaffifin": 588, "Al-Infitar": 587, "At-Takwir": 586, "Abasa": 585,
    "An-Naziat": 583, "An-Naba": 582, "Al-Mursalat": 580, "Al-Insan": 578, "Al-Qiyama": 577,
    "Al-Muddathir": 575, "Al-Muzzammil": 574, "Al-Jinn": 572, "Nuh": 570, "Al-Maarij": 568,
    "Al-Haqqa": 566, "Al-Qalam": 564, "Al-Mulk": 562, "At-Tahrim": 560, "At-Talaq": 558,
    "At-Taghabun": 556, "Al-Munafiqun": 554, "Al-Jumua": 553, "As-Saff": 551, "Al-Mumtahina": 549,
    "Al-Hashr": 545, "Al-Mujadila": 542, "Al-Hadid": 537, "Al-Waqia": 534, "Ar-Rahman": 531,
    "Al-Qamar": 528, "An-Najm": 526, "At-Tur": 523, "Adh-Dhariyat": 520, "Qaf": 518,
    "Al-Hujurat": 515, "Al-Fath": 511, "Muhammad": 507, "Al-Ahqaf": 502, "Al-Jathiya": 499,
    "Ad-Dukhan": 496, "Az-Zukhruf": 489, "Ash-Shura": 483, "Fussilat": 477, "Ghafir": 467,
    "Az-Zumar": 458, "Sad": 453, "As-Saffat": 446, "Ya-Sin": 440, "Fatir": 434,
    "Saba": 428, "Al-Ahzab": 418, "As-Sajda": 415, "Luqman": 411, "Ar-Rum": 404,
    "Al-Ankabut": 396, "Al-Qasas": 385, "An-Naml": 377, "Ash-Shuara": 367, "Al-Furqan": 359,
    "An-Nur": 350, "Al-Muminun": 342, "Al-Hajj": 332, "Al-Anbiya": 322, "Taha": 312,
    "Maryam": 305, "Al-Kahf": 293, "Al-Isra": 282, "An-Nahl": 267, "Al-Hijr": 262,
    "Ibrahim": 255, "Ar-Rad": 249, "Yusuf": 235, "Hud": 221, "Yunus": 208,
    "At-Tawba": 187, "Al-Anfal": 177, "Al-Araf": 151, "Al-Anam": 128, "Al-Maida": 106,
    "An-Nisa": 77, "Al-Imran": 50, "Al-Baqara": 2, "Al-Fatiha": 1
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

# --- CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Mon Suivi Coran")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        conn = get_connection()
        res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
            st.rerun()
        else: st.error("Identifiants incorrects.")
    if st.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle, sourate) VALUES (?,?,'membre',604, 'An-Nas')", (u,p))
            conn.commit(); st.success("Compte créé !")
        except: st.error("Pseudo déjà pris.")

else:
    # --- NAVIGATION ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.session_state['role'] == 'admin':
        if st.sidebar.button("⚙️ Administration", use_container_width=True): st.session_state['page'] = "Paramètres"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    # --- PAGE ACCUEIL ---
    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi Personnel")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        p_act = row[0] or 604
        h_obj = row[2] or 0
        d_str = row[3] or str(date.today())
        p_sem_fixe = row[4] or 0.0

        # Calculs
        p_cible = 604 - ((h_obj - 1) * 10) if h_obj > 0 else p_act
        if h_obj == 2: p_cible = 582
        p_restantes = max(0, p_act - p_cible)
        
        try: jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
        except: jours = 0
        p_semaine = round((p_restantes / max(1, jours)) * 7, 1) if jours > 0 else p_sem_fixe

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages restantes", p_restantes)
        c2.metric("Jours restants", max(0, jours))
        c3.metric("Objectif Hebdo", f"{p_semaine} p.")

        with st.form("maj_complete"):
            st.subheader("Mettre à jour ma progression")
            col1, col2 = st.columns(2)
            
            s_list = list(SURATES_PAGES.keys())
            new_s = col1.selectbox("Sourate actuelle", s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
            new_p = col2.number_input("Page exacte", value=p_act)
            
            st.divider()
            st.write("🎯 **Mes Objectifs**")
            new_h = col1.number_input("Objectif Hizb (1=Sabbih, 2=Naba...)", value=int(h_obj))
            new_sem = col2.number_input("OU Pages/Semaine fixe", value=float(p_sem_fixe))
            
            # Affichage de la sourate cible auto
            if new_h > 0:
                calc_p = 582 if new_h == 2 else (604 - ((new_h - 1) * 10))
                st.info(f"Ton objectif est d'atteindre la page **{calc_p}**")

            new_date = st.date_input("Date cible finale", value=datetime.strptime(d_str, '%Y-%m-%d').date())
            
            if st.form_submit_button("Sauvegarder tout"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_semaine_fixe=? WHERE id=?", 
                             (new_p, new_s, new_h, str(new_date), new_sem, st.session_state['user_id']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), new_p, new_s))
                conn.commit(); st.rerun()

    # --- PAGE ADMIN ---
    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration")
        
        st.subheader("👥 Membres")
        all_u = pd.read_sql_query("SELECT * FROM users", conn)
        
        for _, u_row in all_u.iterrows():
            if u_row['id'] == st.session_state['user_id']: continue
            
            with st.expander(f"👤 {u_row['username']} ({u_row['role']})"):
                with st.form(f"adm_{u_row['id']}"):
                    ca, cb = st.columns(2)
                    ap = ca.number_input("Page", value=int(u_row['page_actuelle']), key=f"ap_{u_row['id']}")
                    ah = cb.number_input("Hizb", value=int(u_row['obj_hizb'] or 0), key=f"ah_{u_row['id']}")
                    as_ = ca.selectbox("Sourate", list(SURATES_PAGES.keys()), index=list(SURATES_PAGES.keys()).index(u_row['sourate']) if u_row['sourate'] in SURATES_PAGES else 0, key=f"as_{u_row['id']}")
                    asem = cb.number_input("Pages/Sem", value=float(u_row['pages_par_semaine_fixe'] or 0), key=f"asem_{u_row['id']}")
                    ad = st.date_input("Date Cible", value=datetime.strptime(u_row['date_cible'], '%Y-%m-%d').date() if u_row['date_cible'] else date.today(), key=f"ad_{u_row['id']}")
                    
                    if st.form_submit_button("Enregistrer modifications"):
                        conn.execute("UPDATE users SET page_actuelle=?, obj_hizb=?, sourate=?, pages_par_semaine_fixe=?, date_cible=? WHERE id=?", (ap, ah, as_, asem, str(ad), u_row['id']))
                        conn.commit(); st.rerun()

                # --- BOUTONS DE RÔLES ---
                c_role1, c_role2, c_role3 = st.columns(3)
                if u_row['role'] == 'membre':
                    if c_role1.button("🔼 Promouvoir Admin", key=f"prm_{u_row['id']}"):
                        conn.execute("UPDATE users SET role='admin' WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()
                elif u_row['role'] == 'admin' and st.session_state['user_id'] == 1:
                    if c_role1.button("🔽 Rendre Membre", key=f"rtr_{u_row['id']}"):
                        conn.execute("UPDATE users SET role='membre' WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()
                
                if c_role3.button("🗑️ Supprimer", key=f"del_{u_row['id']}", type="primary"):
                    conn.execute("DELETE FROM users WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()

        st.divider()
        st.subheader("📅 Historique (Modifiable)")
        h_df = pd.read_sql_query("SELECT * FROM history", conn)
        edited_h = st.data_editor(h_df, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("Sauvegarder modifications tableau"):
            conn.execute("DELETE FROM history")
            edited_h.to_sql('history', conn, if_exists='append', index=False)
            conn.commit(); st.success("Logs mis à jour")

    conn.close()
