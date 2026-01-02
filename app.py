import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import re

# --- DONNÉES DU CORAN (Pages de début par sourate) ---
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

def clean_text(text):
    """Nettoie le texte pour la comparaison (minuscule, sans tirets/espaces spéciaux)"""
    return re.sub(r'[^a-z]', '', text.lower())

def get_page_from_surah(name):
    clean_name = clean_text(name)
    for s_name, page in SURATES_PAGES.items():
        if clean_name == clean_text(s_name):
            return page
    return None

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="Suivi Coran", layout="wide")

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                  role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT)''')
    c.execute("INSERT OR REPLACE INTO users (id, username, password, role) VALUES ((SELECT id FROM users WHERE username='admin'), 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

# --- CONNEXION ---
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

# --- APP PRINCIPALE ---
else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Accueil"): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Paramètres"): st.session_state['page'] = "Paramètres"
    if st.sidebar.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Bilan Coran")
        
        c = conn.cursor()
        c.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (st.session_state['user'],))
        data = c.fetchone()
        
        # --- CALCULS ---
        p_act = data[0] or 1
        hizb_cible = data[2] or 1
        page_cible = (hizb_cible * 10) + 2 # Approximation : 1 Hizb = 10 pages environ
        
        # Calcul jours restants
        try:
            date_fin = datetime.strptime(data[3], '%Y-%m-%d').date()
            jours_restants = (date_fin - date.today()).days
        except:
            jours_restants = 0
            date_fin = date.today()

        # Pages à faire
        pages_restantes = max(0, page_cible - p_act)
        pages_par_jour = round(pages_restantes / jours_restants, 2) if jours_restants > 0 else 0

        # Affichage Stats
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Pages restantes", pages_restantes)
        col_s2.metric("Jours restants", jours_restants)
        col_s3.metric("Objectif / Jour", f"{pages_par_jour} pgs")

        # --- FORMULAIRE ---
        with st.form("bilan_form"):
            st.subheader("Mettre à jour")
            nom_sourate = st.text_input("Nom de la sourate (ex: Al Baqara)", value=data[1] or "")
            
            # Auto-calcul de la page si sourate changée
            auto_page = get_page_from_surah(nom_sourate)
            if auto_page:
                st.info(f"Sourate reconnue ! Page de début : {auto_page}")
                p_input = st.number_input("Page exacte actuelle", value=max(p_act, auto_page))
            else:
                p_input = st.number_input("Page exacte actuelle", value=p_act)
                
            c1, c2 = st.columns(2)
            obj_h = c1.number_input("Objectif final (en Hizb)", value=hizb_cible)
            dt_c = c2.date_input("Date cible pour cet objectif", value=date_fin)
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_input, nom_sourate, obj_h, str(dt_c), st.session_state['user']))
                conn.commit()
                st.rerun()

        # Vue Admin
        if st.session_state['role'] == 'admin':
            st.divider()
            st.subheader("📊 Vue globale des membres")
            df = pd.read_sql_query("SELECT username, page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE role='membre'", conn)
            st.dataframe(df, use_container_width=True)

    elif st.session_state['page'] == "Paramètres":
        # (Le code des paramètres reste le même que précédemment...)
        st.title("⚙️ Paramètres")
        if st.session_state['role'] == 'admin':
            st.write("Gestion des membres...")
            # ... (Copier la logique de suppression du message précédent ici)
        else:
            st.info("Espace admin uniquement.")

    conn.close()
