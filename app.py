import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran Pro", layout="wide")

# --- BASE DE DONNÉES ---
def get_connection():
    # Le fichier coran_data.db sera créé dans le dossier de l'app
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table des utilisateurs (Profil actuel)
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, 
                  role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT)''')
    
    # Table Historique (Pour voir les progrès à une date précise)
    c.execute('''CREATE TABLE IF NOT EXISTS history 
                 (id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, 
                  page_atteinte INT, sourate_atteinte TEXT)''')
    
    c.execute("INSERT OR REPLACE INTO users (id, username, password, role) VALUES ((SELECT id FROM users WHERE username='admin'), 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- LOGIQUE SOURATES ---
SURATES_PAGES = {"Al-Fatiha": 1, "Al-Baqara": 2, "Al-Imran": 50, "An-Nisa": 77, "Al-Maida": 106, "Al-Anam": 128, "Al-Araf": 151, "Al-Anfal": 177, "At-Tawba": 187, "Yunus": 208, "Hud": 221, "Yusuf": 235, "Ar-Rad": 249, "Ibrahim": 255, "Al-Hijr": 262, "An-Nahl": 267, "Al-Isra": 282, "Al-Kahf": 293, "Maryam": 305, "Taha": 312, "Al-Anbiya": 322, "Al-Hajj": 332, "Al-Muminun": 342, "An-Nur": 350, "Al-Furqan": 359, "Ash-Shuara": 367, "An-Naml": 377, "Al-Qasas": 385, "Al-Ankabut": 396, "Ar-Rum": 404, "Luqman": 411, "As-Sajda": 415, "Al-Ahzab": 418, "Saba": 428, "Fatir": 434, "Ya-Sin": 440, "As-Saffat": 446, "Sad": 453, "Az-Zumar": 458, "Ghafir": 467, "Fussilat": 477, "Ash-Shura": 483, "Az-Zukhruf": 489, "Ad-Dukhan": 496, "Al-Jathiya": 499, "Al-Ahqaf": 502, "Muhammad": 507, "Al-Fath": 511, "Al-Hujurat": 515, "Qaf": 518, "Adh-Dhariyat": 520, "At-Tur": 523, "An-Najm": 526, "Al-Qamar": 528, "Ar-Rahman": 531, "Al-Waqia": 534, "Al-Hadid": 537, "Al-Mujadila": 542, "Al-Hashr": 545, "Al-Mumtahina": 549, "As-Saff": 551, "Al-Jumua": 553, "Al-Munafiqun": 554, "At-Taghabun": 556, "At-Talaq": 558, "At-Tahrim": 560, "Al-Mulk": 562, "Al-Qalam": 564, "Al-Haqqa": 566, "Al-Maarij": 568, "Nuh": 570, "Al-Jinn": 572, "Al-Muzzammil": 574, "Al-Muddathir": 575, "Al-Qiyama": 577, "Al-Insan": 578, "Al-Mursalat": 580, "An-Naba": 582, "An-Naziat": 583, "Abasa": 585, "At-Takwir": 586, "Al-Infitar": 587, "Al-Mutaffifin": 588, "Al-Inshiqaq": 589, "Al-Buruj": 590, "At-Tariq": 591, "Al-Ala": 591, "Al-Ghashiya": 592, "Al-Fajr": 593, "Al-Balad": 594, "Ash-Shams": 595, "Al-Layl": 595, "Ad-Duha": 596, "Ash-Sharh": 596, "At-Tin": 597, "Al-Alaq": 597, "Al-Qadr": 598, "Al-Bayyina": 598, "Az-Zalzala": 599, "Al-Adiyat": 599, "Al-Qaria": 600, "At-Takathur": 600, "Al-Asr": 601, "Al-Humaza": 601, "Al-Fil": 601, "Quraish": 602, "Al-Maun": 602, "Al-Kawthar": 602, "Al-Kafirun": 603, "An-Nasr": 603, "Al-Masad": 603, "Al-Ikhlas": 604, "Al-Falaq": 604, "An-Nas": 604}

def get_page_from_surah(name):
    if not name: return None
    clean_n = re.sub(r'[^a-z]', '', name.lower())
    for s_name, page in SURATES_PAGES.items():
        if clean_n == re.sub(r'[^a-z]', '', s_name.lower()): return page
    return None

# --- SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

# --- LOGIN / SIGNUP ---
if not st.session_state['logged_in']:
    st.title("🌙 Connexion")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Se connecter"):
        conn = get_connection()
        res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0]})
            st.rerun()
        else: st.error("Identifiants incorrects.")
    if c2.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',1)", (u,p))
            conn.commit()
            st.success("Compte créé !")
        except: st.error("Pseudo déjà pris.")

else:
    # --- NAVIGATION ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Accueil"): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Paramètres"): st.session_state['page'] = "Paramètres"
    if st.sidebar.button("🚪 Déconnexion"): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi")
        
        # Récupération données
        data = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible FROM users WHERE username=?", (st.session_state['user'],)).fetchone()
        p_act = data[0] or 1
        h_obj = data[2] or 1
        d_str = data[3] or str(date.today())
        
        # --- CALCULS CORRIGÉS ---
        p_cible = (h_obj * 10) + 2
        p_restantes = max(0, p_cible - p_act)
        
        try:
            d_cible = datetime.strptime(d_str, '%Y-%m-%d').date()
            jours = (d_cible - date.today()).days
        except:
            jours = 0
            
        p_par_jour = round(p_restantes / jours, 2) if jours > 0 else 0

        # Affichage
        m1, m2, m3 = st.columns(3)
        m1.metric("Pages restantes", p_restantes)
        m2.metric("Jours restants", jours)
        m3.metric("Objectif / Jour", f"{p_par_jour} p/j")

        with st.form("update"):
            st.subheader("Mettre à jour mon état")
            sourate_in = st.text_input("Sourate actuelle", value=data[1] or "")
            
            # Aide au remplissage
            page_sug = get_page_from_surah(sourate_in)
            if page_sug: st.info(f"Début suggéré : Page {page_sug}")
            
            p_in = st.number_input("Page exacte", value=p_act)
            h_in = st.number_input("Objectif (Hizb)", value=h_obj)
            d_in = st.date_input("Date cible", value=datetime.strptime(d_str, '%Y-%m-%d').date())
            
            if st.form_submit_button("Enregistrer"):
                # Mise à jour profil
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=? WHERE username=?",
                             (p_in, sourate_in, h_in, str(d_in), st.session_state['user']))
                # Enregistrement historique
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), p_in, sourate_in))
                conn.commit()
                st.success("Données sauvegardées !")
                st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration")
        if st.session_state['role'] == 'admin':
            
            # --- NOUVELLE FONCTION : HISTORIQUE PAR DATE ---
            st.subheader("🔍 Historique à une date précise")
            date_search = st.date_input("Choisir une date", value=date.today())
            
            hist_df = pd.read_sql_query("""
                SELECT username, page_atteinte, sourate_atteinte, date_enregistrement 
                FROM history WHERE date_enregistrement = ?
            """, conn, params=(str(date_search),))
            
            if not hist_df.empty:
                st.write(f"Progrès enregistrés le {date_search} :")
                st.table(hist_df)
            else:
                st.warning("Aucune donnée enregistrée par les membres à cette date.")

            st.divider()
            
            # --- GESTION SUPPRESSION ---
            st.subheader("🗑️ Gestion des membres")
            all_u = pd.read_sql_query("SELECT id, username FROM users WHERE role='membre'", conn)
            for _, row in all_u.iterrows():
                c_u, c_b = st.columns([3,1])
                c_u.write(row['username'])
                if c_b.button("Supprimer", key=f"del_{row['id']}"):
                    conn.execute("DELETE FROM users WHERE id=?", (row['id'],))
                    conn.execute("DELETE FROM history WHERE username=?", (row['username'],))
                    conn.commit()
                    st.rerun()

        else:
            st.info("Espace Admin.")
    conn.close()
