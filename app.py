import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="HIKMA - Administration Directe", layout="wide")

# --- DONNÉES SOURATES (114) ---
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

# --- AUTHENTIFICATION ---
if not st.session_state['logged_in']:
    st.title("📖 Système Hikma")
    t1, t2 = st.tabs(["🔐 Connexion", "📝 S'inscrire"])
    with t1:
        u = st.text_input("Pseudo", key="l_u")
        p = st.text_input("Mot de passe", type="password", key="l_p")
        if st.button("Se connecter", use_container_width=True):
            conn = get_connection()
            res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            conn.close()
            if res:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with t2:
        nu, np = st.text_input("Choisir un Pseudo", key="s_u"), st.text_input("Choisir un MDP", type="password", key="s_p")
        if st.button("S'inscrire", use_container_width=True):
            try:
                conn = get_connection()
                conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'membre')", (nu, np))
                conn.commit(); conn.close(); st.success("Compte créé ! Connectez-vous.")
            except: st.error("Pseudo déjà pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    
    # --- LOGIQUE DE RESTRICTION ---
    if st.session_state['role'] == 'admin':
        page = "Administration" # Forcé pour l'admin
    else:
        page = "Mon Suivi"

    if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.clear(); st.rerun()

    conn = get_connection()

    # --- MON SUIVI (MEMBRE UNIQUEMENT) ---
    if page == "Mon Suivi":
        st.title("🚀 Ma Progression")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        p_act = row[0] or 604
        h_obj = row[2] or 0
        d_str = row[3] or str(date.today())
        p_sem_fixe = row[4] or 0.0

        p_cible = 604 - (h_obj * 10)
        p_restantes = max(0, p_act - p_cible)
        
        try: jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
        except: jours = 0
        p_hebdo_dyn = round((p_restantes / max(1, jours)) * 7, 1) if jours > 0 else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages à lire", p_restantes)
        c2.metric("Jours restants", max(0, jours))
        c3.metric("Rythme (dyn)", f"{p_hebdo_dyn} p/sem")

        st.divider()
        s_list = list(DATA_CORAN.keys())
        choix_s = st.selectbox("Sourate terminée", s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
        p_deb, p_fin = DATA_CORAN[choix_s]
        nb_p_sourate = p_fin - p_deb + 1
        
        if nb_p_sourate > 1:
            num_p = st.number_input(f"Dernière page lue dans {choix_s}", 1, nb_p_sourate, 1)
            page_calculee = p_fin - (num_p - 1)
        else:
            page_calculee = p_deb

        if st.button("💾 Enregistrer mes progrès", use_container_width=True):
            conn.execute("UPDATE users SET page_actuelle=?, sourate=? WHERE id=?", (page_calculee, choix_s, st.session_state['user_id']))
            conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                         (st.session_state['user'], str(date.today()), page_calculee, choix_s))
            conn.commit(); st.success("Progression sauvegardée !"); st.rerun()

    # --- ADMINISTRATION (ADMIN UNIQUEMENT) ---
    elif page == "Administration":
        st.title("🛠️ Panneau de Contrôle Admin")
        t_dash, t_hist, t_users = st.tabs(["📊 Tableau de Bord (Éditeur)", "📅 Historique par Date", "⚙️ Gestion Individuelle"])

        with t_dash:
            st.subheader("Modifier directement les données des membres")
            # Charger les données éditables
            df_edit = pd.read_sql_query("""
                SELECT id, username as Pseudo, role as Grade, sourate as Sourate, 
                page_actuelle as Page, obj_hizb as 'Hizb Cible'
                FROM users WHERE role != 'admin'
            """, conn)
            
            # Utilisation de st.data_editor pour permettre la modification directe
            edited_df = st.data_editor(df_edit, key="main_editor", use_container_width=True, hide_index=True,
                                      disabled=["id", "Pseudo"]) # On ne change pas l'ID ni le Pseudo ici

            if st.button("💾 Sauvegarder toutes les modifications du tableau"):
                for index, row in edited_df.iterrows():
                    conn.execute("""UPDATE users SET role=?, sourate=?, page_actuelle=?, obj_hizb=? 
                                    WHERE id=?""", (row['Grade'], row['Sourate'], row['Page'], row['Hizb Cible'], row['id']))
                conn.commit()
                st.success("Toutes les données du tableau ont été mises à jour !")
                st.rerun()

            st.divider()
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger la sauvegarde CSV", csv, "hikma_backup.csv", "text/csv")

        with t_hist:
            st.subheader("Vérifier les positions à une date précise")
            d_recherche = st.date_input("Date à consulter", value=date.today())
            q_hist = f"""
                SELECT h.username as Pseudo, h.sourate_atteinte as Sourate, h.page_atteinte as Page, h.date_enregistrement as Date
                FROM history h
                INNER JOIN (
                    SELECT username, MAX(date_enregistrement) as MD FROM history
                    WHERE date_enregistrement <= '{d_recherche}' GROUP BY username
                ) latest ON h.username = latest.username AND h.date_enregistrement = latest.MD
            """
            df_h = pd.read_sql_query(q_hist, conn)
            if not df_h.empty:
                st.table(df_h)
            else:
                st.warning("Pas de logs à cette date.")

        with t_users:
            # On garde l'expander pour les réglages plus fins (dates cibles, suppression)
            all_users = conn.execute("SELECT * FROM users WHERE id != 1").fetchall()
            for u in all_users:
                with st.expander(f"👤 Paramètres avancés de {u[1]}"):
                    with st.form(f"f_adm_{u[0]}"):
                        c1, c2 = st.columns(2)
                        n_rate = c1.number_input("Rythme fixe p/sem", value=u[8] or 0.0)
                        try: n_date_val = datetime.strptime(u[7], '%Y-%m-%d').date() if u[7] else date.today()
                        except: n_date_val = date.today()
                        n_d_cible = c2.date_input("Date Cible", value=n_date_val)
                        if st.form_submit_button("Sauvegarder Rythme/Date"):
                            conn.execute("UPDATE users SET pages_par_semaine_fixe=?, date_cible=? WHERE id=?", (n_rate, str(n_d_cible), u[0]))
                            conn.commit(); st.rerun()
                    
                    if st.button(f"🗑️ Supprimer définitivement {u[1]}", key=f"del_u_{u[0]}", type="primary"):
                        conn.execute("DELETE FROM users WHERE id=?", (u[0],))
                        conn.commit(); st.rerun()

    conn.close()
