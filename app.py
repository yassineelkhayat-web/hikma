import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran - Admin Pro", layout="wide")

# --- DONNÉES SOURATES ---
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

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, 
        page_actuelle INT DEFAULT 604, sourate TEXT DEFAULT 'An-Nas', 
        obj_hizb INT DEFAULT 0, date_cible TEXT, pages_par_semaine_fixe REAL DEFAULT 0.0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, 
        page_atteinte INT, sourate_atteinte TEXT)''')
    conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None})

# --- CONNEXION ---
if not st.session_state['logged_in']:
    st.title("📖 Suivi Coran Collectif")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Entrer", use_container_width=True):
        conn = get_connection()
        res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        conn.close()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
            st.rerun()
        else: st.error("Erreur d'accès")
else:
    # NAVIGATION
    st.sidebar.title(f"👤 {st.session_state['user']}")
    page = "Administration" if st.session_state['role'] == 'admin' else "Mon Suivi"
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    conn = get_connection()

    if page == "Mon Suivi":
        st.title("🚀 Ma Progression")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        # LOGIQUE DE CALCUL PAGE CIBLE
        p_act = row[0]
        h_obj = row[2]
        # On définit la page cible selon le Hizb (ex: Hizb 10 = page 514)
        # Formule : la fin du Hizb N est à la page (604 - (N * 10)) + 1 environ
        p_cible = 604 - (h_obj * 10)
        p_restantes = p_act - p_cible
        
        c1, c2 = st.columns(2)
        c1.metric("Pages à faire", max(0, p_restantes))
        c2.info(f"Objectif : Fin du Hizb {h_obj}")

        st.divider()
        choix_s = st.selectbox("Quelle sourate as-tu terminée ?", list(DATA_CORAN.keys()), index=list(DATA_CORAN.keys()).index(row[1]))
        p_deb, p_fin = DATA_CORAN[choix_s]
        nb_p = p_fin - p_deb + 1
        
        if nb_p > 1:
            num_p = st.number_input(f"Tu as fini la page n° combien de {choix_s} ?", 1, nb_p, 1)
            # Correction logique : Si je fini page 2 de Jumua (p 553), ma page actuelle est 553 - (2-1) = 552
            page_calculee = p_fin - (num_p - 1)
        else:
            page_calculee = p_deb

        if st.button("💾 Valider mes progrès", use_container_width=True):
            conn.execute("UPDATE users SET page_actuelle=?, sourate=? WHERE id=?", (page_calculee, choix_s, st.session_state['user_id']))
            conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                         (st.session_state['user'], str(date.today()), page_calculee, choix_s))
            conn.commit()
            st.success(f"Bravo ! Tu es à la page {page_calculee}")
            st.rerun()

    elif page == "Administration":
        st.title("🛠️ Panneau de Contrôle")
        
        # --- NOUVEAU : TABLEAU RÉCAPITULATIF ---
        st.subheader("📊 État des lieux des membres")
        query = """
            SELECT u.username as Pseudo, u.sourate as Sourate, u.page_actuelle as 'Page Coran', 
            MAX(h.date_enregistrement) as 'Dernière Activité'
            FROM users u
            LEFT JOIN history h ON u.username = h.username
            WHERE u.role != 'admin'
            GROUP BY u.username
        """
        df_membres = pd.read_sql_query(query, conn)
        st.dataframe(df_membres, use_container_width=True)

        st.divider()
        
        # --- GESTION INDIVIDUELLE ---
        all_users = conn.execute("SELECT * FROM users WHERE role != 'admin'").fetchall()
        for u_row in all_users:
            with st.expander(f"👤 Modifier {u_row[1]}"):
                with st.form(f"form_{u_row[0]}"):
                    new_h = st.number_input("Hizb Cible", value=u_row[6], key=f"h_{u_row[0]}")
                    new_s = st.selectbox("Sourate", list(DATA_CORAN.keys()), index=list(DATA_CORAN.keys()).index(u_row[5]), key=f"s_{u_row[0]}")
                    new_p = st.number_input("Page Coran Directe", value=u_row[4], key=f"p_{u_row[0]}")
                    
                    if st.form_submit_button("Sauvegarder"):
                        conn.execute("UPDATE users SET obj_hizb=?, sourate=?, page_actuelle=? WHERE id=?", 
                                     (new_h, new_s, new_p, u_row[0]))
                        conn.commit()
                        st.rerun()
                
                if st.button(f"🗑️ Supprimer {u_row[1]}", key=f"del_{u_row[0]}"):
                    conn.execute("DELETE FROM users WHERE id=?", (u_row[0],))
                    conn.commit()
                    st.rerun()

    conn.close()
