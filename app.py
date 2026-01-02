import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import re

# --- DONNÉES INVERSÉES (Hizb 1 = Fin du Coran) ---
# Ce dictionnaire définit la sourate de FIN de l'objectif selon ton système
HIZB_INVERSE_TO_SURAH = {
    1: "Al-A'la", 2: "An-Naba", 3: "Al-Mulk", 4: "Al-Mujadila", 5: "Adh-Dhariyat",
    # On peut continuer la liste, voici la logique :
    60: "Al-Baqara" 
}

# Pour le calcul des pages (Début de sourate)
SURATES_PAGES = {"Al-Baqara": 2, "Al-Imran": 50, "An-Nisa": 77, "Al-Maida": 106, "Al-Anam": 128, "Al-Araf": 151, "Al-Anfal": 177, "At-Tawba": 187, "Yunus": 208, "Hud": 221, "Yusuf": 235, "Ar-Rad": 249, "Ibrahim": 255, "Al-Hijr": 262, "An-Nahl": 267, "Al-Isra": 282, "Al-Kahf": 293, "Maryam": 305, "Taha": 312, "Al-Anbiya": 322, "Al-Hajj": 332, "Al-Muminun": 342, "An-Nur": 350, "Al-Furqan": 359, "Ash-Shuara": 367, "An-Naml": 377, "Al-Qasas": 385, "Al-Ankabut": 396, "Ar-Rum": 404, "Luqman": 411, "As-Sajda": 415, "Al-Ahzab": 418, "Saba": 428, "Fatir": 434, "Ya-Sin": 440, "As-Saffat": 446, "Sad": 453, "Az-Zumar": 458, "Ghafir": 467, "Fussilat": 477, "Ash-Shura": 483, "Az-Zukhruf": 489, "Ad-Dukhan": 496, "Al-Jathiya": 499, "Al-Ahqaf": 502, "Muhammad": 507, "Al-Fath": 511, "Al-Hujurat": 515, "Qaf": 518, "Adh-Dhariyat": 520, "At-Tur": 523, "An-Najm": 526, "Al-Qamar": 528, "Ar-Rahman": 531, "Al-Waqia": 534, "Al-Hadid": 537, "Al-Mujadila": 542, "Al-Hashr": 545, "Al-Mumtahina": 549, "As-Saff": 551, "Al-Jumua": 553, "Al-Munafiqun": 554, "At-Taghabun": 556, "At-Talaq": 558, "At-Tahrim": 560, "Al-Mulk": 562, "Al-Qalam": 564, "Al-Haqqa": 566, "Al-Maarij": 568, "Nuh": 570, "Al-Jinn": 572, "Al-Muzzammil": 574, "Al-Muddathir": 575, "Al-Qiyama": 577, "Al-Insan": 578, "Al-Mursalat": 580, "An-Naba": 582, "An-Naziat": 583, "Abasa": 585, "At-Takwir": 586, "Al-Infitar": 587, "Al-Mutaffifin": 588, "Al-Inshiqaq": 589, "Al-Buruj": 590, "At-Tariq": 591, "Al-Ala": 591, "Al-Ghashiya": 592, "Al-Fajr": 593, "Al-Balad": 594, "Ash-Shams": 595, "Al-Layl": 595, "Ad-Duha": 596, "Ash-Sharh": 596, "At-Tin": 597, "Al-Alaq": 597, "Al-Qadr": 598, "Al-Bayyina": 598, "Az-Zalzala": 599, "Al-Adiyat": 599, "Al-Qaria": 600, "At-Takathur": 600, "Al-Asr": 601, "Al-Humaza": 601, "Al-Fil": 601, "Quraish": 602, "Al-Maun": 602, "Al-Kawthar": 602, "Al-Kafirun": 603, "An-Nasr": 603, "Al-Masad": 603, "Al-Ikhlas": 604, "Al-Falaq": 604, "An-Nas": 604}

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

# --- LOGIQUE NAVIGATION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

# --- INTERFACE CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Connexion (Système Inversé)")
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
            st.success("Compte créé !")
        except: st.error("Pseudo déjà pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Accueil", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Paramètres", use_container_width=True): st.session_state['page'] = "Paramètres"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi (De la fin vers le début)")
        data = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (st.session_state['user'],)).fetchone()
        
        p_act = data[0] or 604
        h_obj_inv = data[2] or 1 # Hizb 1 = Sabbih
        d_str = data[3] or str(date.today())

        # --- CALCULS SYSTÈME INVERSÉ ---
        # Si Hizb 1 = Fin (page 604), alors Hizb 2 = Page 594, etc.
        p_cible = 604 - ((h_obj_inv - 1) * 10) 
        p_restantes = max(0, p_act - p_cible) # On soustrait car on remonte les pages
        
        try:
            d_cible = datetime.strptime(d_str, '%Y-%m-%d').date()
            jours = (d_cible - date.today()).days
        except: jours = 0
        p_par_jour = round(p_restantes / jours, 2) if jours > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Pages à remonter", p_restantes)
        col2.metric("Jours restants", jours)
        col3.metric("Rythme / Jour", f"{p_par_jour} p.")

        with st.form("bilan"):
            st.subheader("Mise à jour")
            h_inv_in = st.number_input("Objectif (Hizb 1=Sabbih, 2=3ama...)", value=int(h_obj_inv), min_value=1, max_value=60)
            
            # Affichage de l'aide pour le membre
            st.info(f"🚩 Ton objectif est d'arriver à la page **{604 - ((h_inv_in - 1) * 10)}**")
            
            p_in = st.number_input("Page actuelle (où tu es)", value=int(p_act))
            s_in = st.text_input("Sourate actuelle", value=data[1] or "")
            d_in = st.date_input("Date cible", value=datetime.strptime(d_str, '%Y-%m-%d').date())
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_in, s_in, h_inv_in, str(d_in), st.session_state['user']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), p_in, s_in))
                conn.commit()
                st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration")
        if st.session_state['role'] == 'admin':
            
            # ADMIN GÈRE LES OBJECTIFS
            st.subheader("🎯 Fixer des objectifs (Hizb 1 = Sabbih)")
            u_list = pd.read_sql_query("SELECT username FROM users WHERE role='membre'", conn)
            if not u_list.empty:
                u_sel = st.selectbox("Membre", u_list['username'])
                col_a, col_b = st.columns(2)
                h_fix = col_a.number_input("Hizb imposé", 1, 60)
                d_fix = col_b.date_input("Date imposée")
                if st.button("Valider l'objectif"):
                    conn.execute("UPDATE users SET obj_hizb=?, date_cible=? WHERE username=?", (h_fix, str(d_fix), u_sel))
                    conn.commit(); st.success("Objectif envoyé !")
            
            st.divider()
            
            # VUE HISTORIQUE
            st.subheader("📅 Historique des membres")
            d_search = st.date_input("Choisir une date", value=date.today())
            hist = pd.read_sql_query("SELECT username, page_atteinte, sourate_atteinte FROM history WHERE date_enregistrement=?", conn, params=(str(d_search),))
            st.table(hist) if not hist.empty else st.info("Aucun log à cette date.")

            st.divider()
            
            # SUPPRESSION
            st.subheader("🗑️ Supprimer un membre")
            for _, row in u_list.iterrows():
                c1, c2 = st.columns([3,1])
                c1.write(row['username'])
                if c2.button("Supprimer", key=f"del_{row['username']}"):
                    conn.execute("DELETE FROM users WHERE username=?", (row['username'],))
                    conn.commit(); st.rerun()
    conn.close()
