import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran - Admin Pro", layout="wide")

# --- DONNÉES SOURATES ---
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
    conn.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'page': "Accueil"})

# --- LOGIN ---
if not st.session_state['logged_in']:
    st.title("🌙 Connexion")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True):
        conn = get_connection()
        res = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0]})
            st.rerun()
        else: st.error("Accès refusé.")
    if st.button("S'inscrire"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle) VALUES (?,?,'membre',604)", (u,p))
            conn.commit(); st.success("Compte créé !")
        except: st.error("Pseudo déjà utilisé.")

else:
    # --- BARRE LATÉRALE ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.sidebar.button("⚙️ Administration", use_container_width=True): st.session_state['page'] = "Paramètres"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    # --- PAGE ACCUEIL ---
    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi")
        
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE username=?", (st.session_state['user'],)).fetchone()
        p_act = row[0] or 604
        h_obj = row[2] or 0
        d_str = row[3] or str(date.today())
        p_sem_fixe = row[4] or 0.0

        # Calculs
        try:
            jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
            jours = max(0, jours)
        except: jours = 0

        if h_obj > 0:
            p_cible = 604 - ((h_obj - 1) * 10)
            p_restantes = max(0, p_act - p_cible)
            p_par_semaine = round((p_restantes / jours) * 7, 1) if jours > 0 else 0
        else:
            p_restantes = "N/A"
            p_par_semaine = p_sem_fixe

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages restantes", p_restantes)
        c2.metric("Jours restants", jours)
        c3.metric("Rythme / Semaine", f"{p_par_semaine} p.")

        with st.form("maj_form"):
            st.subheader("Mettre à jour mon état")
            s_list = list(SURATES_PAGES.keys())
            choix_s = st.selectbox("Sourate actuelle", options=s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
            p_final = st.number_input("Page exacte", value=SURATES_PAGES[choix_s])
            
            st.divider()
            h_in = st.number_input("Objectif Hizb (1=Sabbih...)", value=int(h_obj))
            if h_in > 0:
                p_cible_calc = 604 - ((h_in - 1) * 10)
                st.info(f"🎯 Objectif : Page {p_cible_calc}")
            
            p_sem_in = st.number_input("OU Pages/Semaine fixe", value=float(p_sem_fixe))
            d_in = st.date_input("Date cible", value=datetime.strptime(d_str, '%Y-%m-%d').date())
            
            if st.form_submit_button("Enregistrer"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_semaine_fixe=? WHERE username=?",
                             (p_final, choix_s, h_in, str(d_in), p_sem_in, st.session_state['user']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), p_final, choix_s))
                conn.commit(); st.rerun()

    # --- PAGE ADMIN ---
    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration (Accès Total)")
        if st.session_state['role'] == 'admin':
            
            # Récupérer tous les membres
            all_u = pd.read_sql_query("SELECT * FROM users WHERE role='membre'", conn)
            
            if all_u.empty:
                st.info("Aucun membre inscrit pour le moment.")
            else:
                for _, u_row in all_u.iterrows():
                    with st.expander(f"👤 Gérer : {u_row['username']}"):
                        # On crée un mini formulaire pour chaque membre
                        with st.form(f"form_admin_{u_row['id']}"):
                            col1, col2 = st.columns(2)
                            
                            # Modification de la progression actuelle
                            adm_page = col1.number_input("Page Actuelle", value=int(u_row['page_actuelle']), key=f"ap_{u_row['id']}")
                            adm_sourate = col2.selectbox("Sourate Actuelle", options=list(SURATES_PAGES.keys()), 
                                                       index=list(SURATES_PAGES.keys()).index(u_row['sourate']) if u_row['sourate'] in SURATES_PAGES else 0,
                                                       key=f"as_{u_row['id']}")
                            
                            # Modification des objectifs
                            adm_hizb = col1.number_input("Hizb Cible", value=int(u_row['obj_h_inv'] if 'obj_h_inv' in u_row else u_row['obj_hizb'] or 0), key=f"ah_{u_row['id']}")
                            adm_sem = col2.number_input("Pages/Semaine Fixe", value=float(u_row['pages_par_semaine_fixe'] or 0.0), key=f"aps_{u_row['id']}")
                            
                            # Date cible
                            current_dt = datetime.strptime(u_row['date_cible'], '%Y-%m-%d').date() if u_row['date_cible'] else date.today()
                            adm_date = st.date_input("Date Cible", value=current_dt, key=f"ad_{u_row['id']}")
                            
                            # Boutons d'action
                            btn_save, btn_del = st.columns(2)
                            if btn_save.form_submit_button("✅ Enregistrer les modifications", use_container_width=True):
                                conn.execute("""UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, pages_par_semaine_fixe=?, date_cible=? 
                                             WHERE id=?""", (adm_page, adm_sourate, adm_hizb, adm_sem, str(adm_date), u_row['id']))
                                conn.commit()
                                st.success(f"Données de {u_row['username']} mises à jour !")
                                st.rerun()
                                
                            if btn_del.form_submit_button("🗑️ Supprimer définitivement", use_container_width=True):
                                conn.execute("DELETE FROM users WHERE id=?", (u_row['id'],))
                                conn.commit()
                                st.rerun()

            st.divider()
            st.subheader("📅 Historique des enregistrements")
            d_hist = st.date_input("Consulter une date précise :", value=date.today())
            hist_df = pd.read_sql_query("SELECT username, page_atteinte, sourate_atteinte FROM history WHERE date_enregistrement=?", conn, params=(str(d_hist),))
            if not hist_df.empty:
                st.dataframe(hist_df, use_container_width=True)
            else:
                st.info("Aucun log trouvé pour cette date.")
        else:
            st.warning("Accès réservé à l'administrateur.")

    conn.close()
