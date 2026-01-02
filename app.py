import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran - 114 Sourates", layout="wide")

# --- BASE DE DONNÉES COMPLÈTE DES 114 SOURATES (Page Début, Page Fin) ---
# Format : "Nom": (Page_Début, Page_Fin)
DATA_CORAN = {
    "Al-Fatiha": (1, 1), "Al-Baqara": (2, 49), "Al-Imran": (50, 76), "An-Nisa": (77, 106),
    "Al-Maida": (106, 127), "Al-Anam": (128, 150), "Al-Araf": (151, 176), "Al-Anfal": (177, 186),
    "At-Tawba": (187, 207), "Yunus": (208, 220), "Hud": (221, 235), "Yusuf": (235, 248),
    "Ar-Rad": (249, 255), "Ibrahim": (255, 261), "Al-Hijr": (262, 267), "An-Nahl": (267, 281),
    "Al-Isra": (282, 293), "Al-Kahf": (293, 304), "Maryam": (305, 312), "Taha": (312, 321),
    "Al-Anbiya": (322, 331), "Al-Hajj": (332, 341), "Al-Muminun": (342, 350), "An-Nur": (350, 359),
    "Al-Furqan": (359, 366), "Ash-Shuara": (367, 376), "An-Naml": (377, 385), "Al-Qasas": (385, 395),
    "Al-Ankabut": (396, 404), "Ar-Rum": (404, 410), "Luqman": (411, 414), "As-Sajda": (415, 417),
    "Al-Ahzab": (418, 427), "Saba": (428, 434), "Fatir": (434, 440), "Ya-Sin": (440, 445),
    "As-Saffat": (446, 452), "Sad": (453, 458), "Az-Zumar": (458, 467), "Ghafir": (467, 476),
    "Fussilat": (477, 482), "Ash-Shura": (483, 489), "Az-Zukhruf": (489, 495), "Ad-Dukhan": (496, 498),
    "Al-Jathiya": (499, 502), "Al-Ahqaf": (502, 506), "Muhammad": (507, 510), "Al-Fath": (511, 515),
    "Al-Hujurat": (515, 517), "Qaf": (518, 520), "Adh-Dhariyat": (520, 523), "At-Tur": (523, 525),
    "An-Najm": (526, 528), "Al-Qamar": (528, 531), "Ar-Rahman": (531, 534), "Al-Waqia": (534, 537),
    "Al-Hadid": (537, 541), "Al-Mujadila": (542, 545), "Al-Hashr": (545, 548), "Al-Mumtahina": (549, 552),
    "As-Saff": (551, 552), "Al-Jumua": (553, 554), "Al-Munafiqun": (554, 555), "At-Taghabun": (556, 557),
    "At-Talaq": (558, 559), "At-Tahrim": (560, 561), "Al-Mulk": (562, 564), "Al-Qalam": (564, 566),
    "Al-Haqqa": (566, 568), "Al-Maarij": (568, 569), "Nuh": (570, 571), "Al-Jinn": (572, 573),
    "Al-Muzzammil": (574, 575), "Al-Muddathir": (575, 577), "Al-Qiyama": (577, 578), "Al-Insan": (578, 580),
    "Al-Mursalat": (580, 581), "An-Naba": (582, 583), "An-Naziat": (583, 584), "Abasa": (585, 585),
    "At-Takwir": (586, 586), "Al-Infitar": (587, 587), "Al-Mutaffifin": (588, 589), "Al-Inshiqaq": (589, 589),
    "Al-Buruj": (590, 590), "At-Tariq": (591, 591), "Al-Ala": (591, 591), "Al-Ghashiya": (592, 592),
    "Al-Fajr": (593, 594), "Al-Balad": (594, 594), "Ash-Shams": (595, 595), "Al-Layl": (595, 596),
    "Ad-Duha": (596, 596), "Ash-Sharh": (596, 596), "At-Tin": (597, 597), "Al-Alaq": (597, 598),
    "Al-Qadr": (598, 598), "Al-Bayyina": (598, 599), "Az-Zalzala": (599, 599), "Al-Adiyat": (599, 600),
    "Al-Qaria": (600, 600), "At-Takathur": (600, 600), "Al-Asr": (601, 601), "Al-Humaza": (601, 601),
    "Al-Fil": (601, 601), "Quraish": (602, 602), "Al-Maun": (602, 602), "Al-Kawthar": (602, 602),
    "Al-Kafirun": (603, 603), "An-Nasr": (603, 603), "Al-Masad": (603, 603), "Al-Ikhlas": (604, 604),
    "Al-Falaq": (604, 604), "An-Nas": (604, 604)
}

# --- FONCTIONS BASE DE DONNÉES ---
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

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None, 'page': "Accueil"})

if not st.session_state['logged_in']:
    st.title("📖 Suivi Coran Collectif")
    tab_log, tab_reg = st.tabs(["Connexion", "S'inscrire"])
    with tab_log:
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            conn = get_connection()
            res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if res:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with tab_reg:
        nu = st.text_input("Nouveau Pseudo")
        np = st.text_input("Nouveau Mot de passe", type="password")
        if st.button("Créer mon compte", use_container_width=True):
            try:
                conn = get_connection()
                conn.execute("INSERT INTO users (username, password, role, page_actuelle, sourate) VALUES (?,?,'membre',604, 'An-Nas')", (nu, np))
                conn.commit()
                st.success("Compte créé ! Connecte-toi.")
            except: st.error("Pseudo indisponible.")
else:
    # Sidebar
    st.sidebar.header(f"✨ {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.session_state['role'] == 'admin':
        if st.sidebar.button("⚙️ Admin", use_container_width=True): st.session_state['page'] = "Paramètres"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🚀 Ma Progression")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        # Dashboard
        p_act = row[0] or 604
        h_obj = row[2] or 0
        d_str = row[3] or str(date.today())
        
        # Calcul objectif (Système inverse : Hizb 1 = Sabbih, Hizb 2 = Naba...)
        p_cible = 582 if h_obj == 2 else (604 - ((h_obj - 1) * 10) if h_obj > 0 else p_act)
        p_restantes = max(0, p_act - p_cible)
        
        try: jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
        except: jours = 0
        p_hebdo = round((p_restantes / max(1, jours)) * 7, 1) if jours > 0 else row[4] or 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages à remonter", p_restantes)
        c2.metric("Jours restants", max(0, jours))
        c3.metric("Rythme Hebdo", f"{p_hebdo} p.")

        st.divider()

        # FORMULAIRE DYNAMIQUE SOURATES
        s_list = list(DATA_CORAN.keys())
        # Inverser l'ordre pour que An-Nas soit en haut si tu travailles à l'envers
        choix_s = st.selectbox("Où en es-tu (Sourate) ?", s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
        
        p_deb, p_fin = DATA_CORAN[choix_s]
        nb_p = p_fin - p_deb + 1
        page_finale = p_deb
        
        if nb_p > 1:
            opts = [f"Page {i+1} de la sourate" for i in range(nb_p)]
            sel = st.radio(f"La sourate {choix_s} s'étale sur {nb_p} pages. Laquelle as-tu terminé ?", opts, horizontal=True)
            page_finale = p_deb + opts.index(sel)
        
        st.info(f"📍 Cela correspond à la **Page {page_finale}** du Coran.")

        with st.expander("🎯 Configurer mes objectifs"):
            new_h = st.number_input("Objectif Hizb (ex: 2 pour Naba)", value=int(h_obj))
            new_sem = st.number_input("Objectif Pages/Semaine (fixe)", value=float(row[4] or 0.0))
            new_d = st.date_input("Date limite", value=datetime.strptime(d_str, '%Y-%m-%d').date())

        if st.button("💾 Sauvegarder mes progrès", use_container_width=True):
            conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_semaine_fixe=? WHERE id=?", 
                         (page_finale, choix_s, new_h, str(new_d), new_sem, st.session_state['user_id']))
            conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                         (st.session_state['user'], str(date.today()), page_finale, choix_s))
            conn.commit()
            st.success("C'est enregistré ! Qu'Allah te facilite.")
            st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("🛠️ Espace Admin")
        all_u = pd.read_sql_query("SELECT id, username, role, page_actuelle, sourate FROM users", conn)
        for _, ur in all_u.iterrows():
            if ur['id'] == st.session_state['user_id']: continue
            with st.expander(f"👤 {ur['username']} - Grade: {ur['role']}"):
                c1, c2 = st.columns(2)
                if ur['role'] == 'membre' and c1.button("🔼 Promouvoir Admin", key=f"p{ur['id']}"):
                    conn.execute("UPDATE users SET role='admin' WHERE id=?", (ur['id'],)); conn.commit(); st.rerun()
                if ur['role'] == 'admin' and st.session_state['user_id'] == 1 and c1.button("🔽 Rétrograder", key=f"r{ur['id']}"):
                    conn.execute("UPDATE users SET role='membre' WHERE id=?", (ur['id'],)); conn.commit(); st.rerun()
                if c2.button("🗑️ Supprimer", key=f"d{ur['id']}", type="primary"):
                    conn.execute("DELETE FROM users WHERE id=?", (ur['id'],)); conn.commit(); st.rerun()

        st.divider()
        st.subheader("📊 Logs de tous les membres")
        logs = pd.read_sql_query("SELECT * FROM history ORDER BY date_enregistrement DESC", conn)
        ed_logs = st.data_editor(logs, num_rows="dynamic", use_container_width=True)
        if st.button("Sauvegarder les modifications des logs"):
            conn.execute("DELETE FROM history")
            ed_logs.to_sql('history', conn, if_exists='append', index=False)
            conn.commit(); st.success("Base de données mise à jour.")
    conn.close()
