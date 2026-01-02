import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import re

# --- DONNÉES DU CORAN (Dernière sourate de chaque Hizb) ---
HIZB_TO_SURAH = {
    1: "Al-Baqara", 2: "Al-Baqara", 3: "Al-Baqara", 4: "Al-Baqara", 5: "Al-Imran",
    6: "Al-Imran", 7: "An-Nisa", 8: "An-Nisa", 9: "An-Nisa", 10: "Al-Maida",
    11: "Al-Maida", 12: "Al-Anam", 13: "Al-Anam", 14: "Al-Araf", 15: "Al-Araf",
    16: "Al-Anfal", 17: "At-Tawba", 18: "Yunus", 19: "Hud", 20: "Yusuf",
    21: "Ar-Rad", 22: "Al-Hijr", 23: "An-Nahl", 24: "Al-Isra", 25: "Al-Kahf",
    26: "Maryam", 27: "Taha", 28: "Al-Anbiya", 29: "Al-Hajj", 30: "Al-Muminun",
    31: "An-Nur", 32: "Al-Furqan", 33: "Ash-Shuara", 34: "An-Naml", 35: "Al-Qasas",
    36: "Al-Ankabut", 37: "Ar-Rum", 38: "Al-Ahzab", 39: "Saba", 40: "Ya-Sin",
    41: "As-Saffat", 42: "Sad", 43: "Az-Zumar", 44: "Ghafir", 45: "Fussilat",
    46: "Ash-Shura", 47: "Az-Zukhruf", 48: "Al-Ahqaf", 49: "Muhammad", 50: "Al-Fath",
    51: "Adh-Dhariyat", 52: "At-Tur", 53: "An-Najm", 54: "Al-Qamar", 55: "Ar-Rahman",
    56: "Al-Waqia", 57: "Al-Hadid", 58: "Al-Mujadila", 59: "Al-Hashr", 60: "An-Nas"
}

# (Dictionnaire des pages de début gardé en mémoire pour les calculs)
SURATES_PAGES = {"Al-Fatiha": 1, "Al-Baqara": 2, "Al-Imran": 50, "An-Nisa": 77, "Al-Maida": 106, "Al-Anam": 128, "Al-Araf": 151, "Al-Anfal": 177, "At-Tawba": 187, "Yunus": 208, "Hud": 221, "Yusuf": 235, "Ar-Rad": 249, "Ibrahim": 255, "Al-Hijr": 262, "An-Nahl": 267, "Al-Isra": 282, "Al-Kahf": 293, "Maryam": 305, "Taha": 312, "Al-Anbiya": 322, "Al-Hajj": 332, "Al-Muminun": 342, "An-Nur": 350, "Al-Furqan": 359, "Ash-Shuara": 367, "An-Naml": 377, "Al-Qasas": 385, "Al-Ankabut": 396, "Ar-Rum": 404, "Luqman": 411, "As-Sajda": 415, "Al-Ahzab": 418, "Saba": 428, "Fatir": 434, "Ya-Sin": 440, "As-Saffat": 446, "Sad": 453, "Az-Zumar": 458, "Ghafir": 467, "Fussilat": 477, "Ash-Shura": 483, "Az-Zukhruf": 489, "Ad-Dukhan": 496, "Al-Jathiya": 499, "Al-Ahqaf": 502, "Muhammad": 507, "Al-Fath": 511, "Al-Hujurat": 515, "Qaf": 518, "Adh-Dhariyat": 520, "At-Tur": 523, "An-Najm": 526, "Al-Qamar": 528, "Ar-Rahman": 531, "Al-Waqia": 534, "Al-Hadid": 537, "Al-Mujadila": 542, "Al-Hashr": 545, "Al-Mumtahina": 549, "As-Saff": 551, "Al-Jumua": 553, "Al-Munafiqun": 554, "At-Taghabun": 556, "At-Talaq": 558, "At-Tahrim": 560, "Al-Mulk": 562, "Al-Qalam": 564, "Al-Haqqa": 566, "Al-Maarij": 568, "Nuh": 570, "Al-Jinn": 572, "Al-Muzzammil": 574, "Al-Muddathir": 575, "Al-Qiyama": 577, "Al-Insan": 578, "Al-Mursalat": 580, "An-Naba": 582, "An-Naziat": 583, "Abasa": 585, "At-Takwir": 586, "Al-Infitar": 587, "Al-Mutaffifin": 588, "Al-Inshiqaq": 589, "Al-Buruj": 590, "At-Tariq": 591, "Al-Ala": 591, "Al-Ghashiya": 592, "Al-Fajr": 593, "Al-Balad": 594, "Ash-Shams": 595, "Al-Layl": 595, "Ad-Duha": 596, "Ash-Sharh": 596, "At-Tin": 597, "Al-Alaq": 597, "Al-Qadr": 598, "Al-Bayyina": 598, "Az-Zalzala": 599, "Al-Adiyat": 599, "Al-Qaria": 600, "At-Takathur": 600, "Al-Asr": 601, "Al-Humaza": 601, "Al-Fil": 601, "Quraish": 602, "Al-Maun": 602, "Al-Kawthar": 602, "Al-Kafirun": 603, "An-Nasr": 603, "Al-Masad": 603, "Al-Ikhlas": 604, "Al-Falaq": 604, "An-Nas": 604}

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, page_atteinte INT, sourate_atteinte TEXT)''')
    c.execute("INSERT OR REPLACE INTO users (id, username, password, role) VALUES ((SELECT id FROM users WHERE username='admin'), 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- APP ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

if not st.session_state['logged_in']:
    st.title("🌙 Connexion")
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
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',1)", (u,p))
            conn.commit()
            st.success("Compte créé !")
        except: st.error("Pseudo déjà pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Accueil"): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Paramètres"): st.session_state['page'] = "Paramètres"
    if st.sidebar.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi")
        data = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (st.session_state['user'],)).fetchone()
        
        p_act = data[0] or 1
        h_obj = data[2] or 1
        d_str = data[3] or str(date.today())

        # --- CALCULS ---
        p_cible = (h_obj * 10) + 2
        p_restantes = max(0, p_cible - p_act)
        try:
            d_cible = datetime.strptime(d_str, '%Y-%m-%d').date()
            jours = (d_cible - date.today()).days
        except: jours = 0
        p_par_jour = round(p_restantes / jours, 2) if jours > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Pages à faire", p_restantes)
        col2.metric("Jours restants", jours)
        col3.metric("Rythme / Jour", f"{p_par_jour} p.")

        # --- FORMULAIRE MEMBRE ---
        with st.form("bilan"):
            st.subheader("Mise à jour")
            h_in = st.number_input("Objectif final (Hizb)", value=int(h_obj), min_value=1, max_value=60)
            
            # AUTOMATISATION : Trouver la sourate correspondant au Hizb
            sourate_cible_automatique = HIZB_TO_SURAH.get(h_in, "Inconnue")
            st.info(f"🚩 Pour atteindre le Hizb {h_in}, tu dois arriver à la sourate : **{sourate_cible_automatique}**")
            
            p_in = st.number_input("Page où tu es actuellement", value=int(p_act))
            s_in = st.text_input("Sourate où tu es actuellement", value=data[1] or "")
            d_in = st.date_input("Date cible de l'objectif", value=datetime.strptime(d_str, '%Y-%m-%d').date())
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_in, s_in, h_in, str(d_in), st.session_state['user']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), p_in, s_in))
                conn.commit()
                st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration")
        if st.session_state['role'] == 'admin':
            
            # --- GESTION DES OBJECTIFS PAR L'ADMIN ---
            st.subheader("🎯 Fixer des objectifs aux membres")
            u_list = pd.read_sql_query("SELECT username, obj_hizb, date_cible FROM users WHERE role='membre'", conn)
            if not u_list.empty:
                u_select = st.selectbox("Choisir un membre", u_list['username'])
                col_a, col_b = st.columns(2)
                new_h = col_a.number_input("Hizb imposé", min_value=1, max_value=60)
                new_d = col_b.date_input("Date imposée")
                
                if st.button("Attribuer l'objectif"):
                    conn.execute("UPDATE users SET obj_hizb=?, date_cible=? WHERE username=?", (new_h, str(new_d), u_select))
                    conn.commit()
                    st.success(f"Objectif mis à jour pour {u_select} !")
            
            st.divider()
            
            # --- HISTORIQUE PAR DATE ---
            st.subheader("📅 Voir les progrès à une date")
            d_search = st.date_input("Date", value=date.today())
            hist = pd.read_sql_query("SELECT username, page_atteinte, sourate_atteinte FROM history WHERE date_enregistrement=?", conn, params=(str(d_search),))
            st.table(hist) if not hist.empty else st.info("Rien à cette date.")

            st.divider()
            
            # --- SUPPRESSION ---
            st.subheader("🗑️ Supprimer un membre")
            for _, row in u_list.iterrows():
                c_u, c_b = st.columns([3,1])
                c_u.write(row['username'])
                if c_b.button("Supprimer", key=f"del_{row['username']}"):
                    conn.execute("DELETE FROM users WHERE username=?", (row['username'],))
                    conn.commit(); st.rerun()
        else:
            st.info("Espace Admin uniquement.")
    conn.close()
