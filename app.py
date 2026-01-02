import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import re

# --- DONNÉES DU CORAN (Pages de début standard) ---
SURATES_PAGES = {
    "Al-Fatiha": 1, "Al-Baqara": 2, "Al-Imran": 50, "An-Nisa": 77, "Al-Maida": 106,
    "Al-Anam": 128, "Al-Araf": 151, "Al-Anfal": 177, "At-Tawba": 187, "Yunus": 208,
    "Hud": 221, "Yusuf": 235, "Ar-Rad": 249, "Ibrahim": 255, "Al-Hijr": 262,
    "An-Nahl": 267, "Al-Isra": 282, "Al-Kahf": 293, "Maryam": 305, "Taha": 312,
    "Al-Anbiya": 322, "Al-Hajj": 332, "Al-Muminun": 342, "An-Nur": 350, "Al-Furqan": 359,
    "Ash-Shuara": 367, "An-Naml": 377, "Al-Qasas": 385, "Al-Ankabut": 396, "Ar-Rum": 404,
    "Luqman": 411, "As-Sajda": 415, "Al-Ahzab": 418, "Saba": 428, "Fatir": 434,
    "Ya-Sin": 440, "As-Saffat": 446, "Sad": 453, "Az-Zumar": 458, "Ghafir": 467,
    "Fussilat": 477, "Ash-Shura": 483, "Az-Zukhruf": 489, "Ad-Dukhan": 496, "Al-Jathiya": 499,
    "Al-Ahqaf": 502, "Muhammad": 507, "Al-Fath": 511, "Al-Hujurat": 515, "Qaf": 518,
    "Adh-Dhariyat": 520, "At-Tur": 523, "An-Najm": 526, "Al-Qamar": 528, "Ar-Rahman": 531,
    "Al-Waqia": 534, "Al-Hadid": 537, "Al-Mujadila": 542, "Al-Hashr": 545, "Al-Mumtahina": 549,
    "As-Saff": 551, "Al-Jumua": 553, "Al-Munafiqun": 554, "At-Taghabun": 556, "At-Talaq": 558,
    "At-Tahrim": 560, "Al-Mulk": 562, "Al-Qalam": 564, "Al-Haqqa": 566, "Al-Maarij": 568,
    "Nuh": 570, "Al-Jinn": 572, "Al-Muzzammil": 574, "Al-Muddathir": 575, "Al-Qiyama": 577,
    "Al-Insan": 578, "Al-Mursalat": 580, "An-Naba": 582, "An-Naziat": 583, "Abasa": 585,
    "At-Takwir": 586, "Al-Infitar": 587, "Al-Mutaffifin": 588, "Al-Inshiqaq": 589, "Al-Buruj": 590,
    "At-Tariq": 591, "Al-Ala": 591, "Al-Ghashiya": 592, "Al-Fajr": 593, "Al-Balad": 594,
    "Ash-Shams": 595, "Al-Layl": 595, "Ad-Duha": 596, "Ash-Sharh": 596, "At-Tin": 597,
    "Al-Alaq": 597, "Al-Qadr": 598, "Al-Bayyina": 598, "Az-Zalzala": 599, "Al-Adiyat": 599,
    "Al-Qaria": 600, "At-Takathur": 600, "Al-Asr": 601, "Al-Humaza": 601, "Al-Fil": 601,
    "Quraish": 602, "Al-Maun": 602, "Al-Kawthar": 602, "Al-Kafirun": 603, "An-Nasr": 603,
    "Al-Masad": 603, "Al-Ikhlas": 604, "Al-Falaq": 604, "An-Nas": 604
}

# --- DB SETUP ---
def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT, pages_par_jour_fixe REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, page_atteinte INT, sourate_atteinte TEXT)''')
    c.execute("INSERT OR REPLACE INTO users (id, username, password, role) VALUES ((SELECT id FROM users WHERE username='admin'), 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- APP ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

# --- CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Suivi Coran")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        conn = get_connection()
        res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0]})
            st.rerun()
        else: st.error("Erreur.")
    if st.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',604)", (u,p))
            conn.commit(); st.success("Compte créé !")
        except: st.error("Pseudo pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi"): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Administration"): st.session_state['page'] = "Paramètres"
    if st.sidebar.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi")
        # On récupère toutes les colonnes
        data = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_jour_fixe FROM users WHERE username=?", (st.session_state['user'],)).fetchone()
        
        p_act = data[0] or 604
        h_obj_inv = data[2] # Peut être None
        d_str = data[3] or str(date.today())
        p_jour_fixe = data[4] or 0.0

        # --- CALCULS ---
        try:
            jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
        except: jours = 0

        # Si objectif par Hizb (Système Inversé)
        if h_obj_inv and h_obj_inv > 0:
            p_cible = 604 - ((h_obj_inv - 1) * 10)
            p_restantes = max(0, p_act - p_cible)
            p_par_jour = round(p_restantes / jours, 2) if jours > 0 else 0
        # Sinon si objectif pages/jour fixe
        elif p_jour_fixe > 0:
            p_restantes = "N/A"
            p_par_jour = p_jour_fixe
        else:
            p_restantes = 0
            p_par_jour = 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Pages restantes", p_restantes)
        col2.metric("Jours restants", jours)
        col3.metric("Rythme / Jour", f"{p_par_jour} p.")

        with st.form("maj"):
            st.subheader("Mise à jour de mes progrès")
            
            # --- BOUTON DE DEPLOIEMENT (Menu déroulant des sourates) ---
            liste_sourates = list(SURATES_PAGES.keys())[::-1] # Inversé pour commencer par la fin
            sourate_choisie = st.selectbox("À quelle sourate es-tu arrivé ?", options=liste_sourates)
            
            # Mise à jour automatique de la page
            page_auto = SURATES_PAGES[sourate_choisie]
            
            p_in = st.number_input("Ou entre la page exacte", value=int(page_auto))
            h_in = st.number_input("Objectif Hizb (1=Sabbih...)", value=int(h_obj_inv or 0))
            p_f_in = st.number_input("OU Objectif pages/jour fixe", value=float(p_jour_fixe))
            d_in = st.date_input("Date cible", value=datetime.strptime(d_str, '%Y-%m-%d').date())
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_jour_fixe=? WHERE username=?",
                             (p_in, sourate_choisie, h_in, str(d_in), p_f_in, st.session_state['user']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), p_in, sourate_choisie))
                conn.commit(); st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Panneau Admin")
        if st.session_state['role'] == 'admin':
            
            # 1. VOIR ET MODIFIER TOUT LE MONDE
            st.subheader("👥 Liste et Modification des membres")
            all_users = pd.read_sql_query("SELECT * FROM users WHERE role='membre'", conn)
            
            for index, row in all_users.iterrows():
                with st.expander(f"Modifier : {row['username']}"):
                    col_a, col_b = st.columns(2)
                    new_p = col_a.number_input("Page actuelle", value=int(row['page_actuelle']), key=f"p_{row['id']}")
                    new_h = col_b.number_input("Hizb cible", value=int(row['obj_hizb'] or 0), key=f"h_{row['id']}")
                    new_pj = col_a.number_input("Pages/jour fixe", value=float(row['pages_par_jour_fixe'] or 0), key=f"pj_{row['id']}")
                    
                    if st.button(f"Sauvegarder {row['username']}", key=f"btn_{row['id']}"):
                        conn.execute("UPDATE users SET page_actuelle=?, obj_hizb=?, pages_par_jour_fixe=? WHERE id=?", 
                                     (new_p, new_h, new_pj, row['id']))
                        conn.commit(); st.success("Modifié !"); st.rerun()
                    
                    if st.button(f"SUPPRIMER {row['username']}", type="primary", key=f"del_{row['id']}"):
                        conn.execute("DELETE FROM users WHERE id=?", (row['id'],))
                        conn.commit(); st.rerun()

            st.divider()
            
            # 2. HISTORIQUE PAR DATE
            st.subheader("📅 Historique par date")
            d_s = st.date_input("Date", value=date.today())
            hist = pd.read_sql_query("SELECT username, page_atteinte, sourate_atteinte FROM history WHERE date_enregistrement=?", conn, params=(str(d_s),))
            st.table(hist) if not hist.empty else st.info("Aucun log.")

        else:
            st.info("Réservé à l'admin.")
    conn.close()
