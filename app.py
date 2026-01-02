import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Suivi Coran - Système Hiérarchique", layout="wide")

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
    # Création du Super Admin (ID 1)
    conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None, 'page': "Accueil"})

if not st.session_state['logged_in']:
    st.title("🌙 Connexion Groupe Coran")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        conn = get_connection()
        res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
            st.rerun()
        else: st.error("Identifiants incorrects.")
    if st.button("Créer un compte"):
        try:
            conn = get_connection()
            conn.execute("INSERT INTO users (username, password, role, page_actuelle, sourate) VALUES (?,?,'membre',604, 'An-Nas')", (u,p))
            conn.commit(); st.success("Compte créé !")
        except: st.error("Pseudo déjà utilisé.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    st.sidebar.write(f"Grade : **{st.session_state['role'].upper()}**")
    if st.sidebar.button("🏠 Mon Suivi", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.session_state['role'] == 'admin':
        if st.sidebar.button("⚙️ Administration", use_container_width=True): st.session_state['page'] = "Paramètres"
    st.sidebar.divider()
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi Personnel")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        p_act = row[0] or 604
        h_obj = row[2] or 0
        d_str = row[3] or str(date.today())
        p_sem_fixe = row[4] or 0.0

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

        with st.form("maj_perso"):
            s_list = list(SURATES_PAGES.keys())
            new_s = st.selectbox("Ma sourate actuelle", s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
            new_p = st.number_input("Ma page exacte", value=p_act)
            if st.form_submit_button("Enregistrer mes progrès"):
                conn.execute("UPDATE users SET page_actuelle=?, sourate=? WHERE id=?", (new_p, new_s, st.session_state['user_id']))
                conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                             (st.session_state['user'], str(date.today()), new_p, new_s))
                conn.commit(); st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Gestion du Groupe")
        
        # --- 1. GESTION DES MEMBRES ET RÔLES ---
        st.subheader("👥 Membres et Permissions")
        all_users = pd.read_sql_query("SELECT id, username, role, page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users", conn)
        
        for _, u_row in all_users.iterrows():
            if u_row['id'] == st.session_state['user_id']: continue # Ne pas s'auto-modifier
            
            with st.expander(f"👤 {u_row['username']} ({u_row['role']})"):
                with st.form(f"admin_form_{u_row['id']}"):
                    col_a, col_b = st.columns(2)
                    adm_p = col_a.number_input("Page", value=int(u_row['page_actuelle']), key=f"p_{u_row['id']}")
                    adm_s = col_b.selectbox("Sourate", list(SURATES_PAGES.keys()), index=list(SURATES_PAGES.keys()).index(u_row['sourate']) if u_row['sourate'] in SURATES_PAGES else 0, key=f"s_{u_row['id']}")
                    adm_h = col_a.number_input("Hizb Cible", value=int(u_row['obj_hizb'] or 0), key=f"h_{u_row['id']}")
                    adm_sem = col_b.number_input("Pages/Semaine Fixe", value=float(u_row['pages_par_semaine_fixe'] or 0.0), key=f"sem_{u_row['id']}")
                    
                    if st.form_submit_button("💾 Sauvegarder"):
                        conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, pages_par_semaine_fixe=? WHERE id=?", 
                                     (adm_p, adm_s, adm_h, adm_sem, u_row['id']))
                        conn.commit(); st.rerun()

                # --- BOUTONS DE RÔLES (LOGIQUE DE PERMISSION) ---
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                
                # Promotion en Admin (Tous les admins peuvent promouvoir)
                if u_row['role'] == 'membre':
                    if btn_col1.button(f"🔼 Promouvoir Admin", key=f"promo_{u_row['id']}"):
                        conn.execute("UPDATE users SET role='admin' WHERE id=?", (u_row['id'],))
                        conn.commit(); st.rerun()
                
                # Rétrogradation en Membre (Seul le Super Admin ID 1 peut le faire pour un admin)
                if u_row['role'] == 'admin':
                    if st.session_state['user_id'] == 1:
                        if btn_col1.button(f"🔽 Rendre Membre", key=f"retro_{u_row['id']}"):
                            conn.execute("UPDATE users SET role='membre' WHERE id=?", (u_row['id'],))
                            conn.commit(); st.rerun()
                    else:
                        btn_col1.info("Seul le créateur peut rétrograder un admin.")

                if btn_col3.button("🗑️ Supprimer", key=f"del_{u_row['id']}", type="primary"):
                    if u_row['id'] != 1: # On ne supprime pas le super admin
                        conn.execute("DELETE FROM users WHERE id=?", (u_row['id'],))
                        conn.commit(); st.rerun()

        st.divider()

        # --- 2. TABLEAU DES LOGS INTERACTIF ---
        st.subheader("📅 Historique des Logs (Tableau Interactif)")
        st.write("Tu peux modifier, trier ou supprimer des lignes directement dans le tableau ci-dessous.")
        
        hist_df = pd.read_sql_query("SELECT * FROM history", conn)
        
        # Éditeur de données interactif
        edited_df = st.data_editor(
            hist_df,
            num_rows="dynamic", # Permet de supprimer/ajouter des lignes
            use_container_width=True,
            key="log_editor",
            hide_index=True
        )
        
        if st.button("Enregistrer les modifications du tableau"):
            # On vide la table et on réinsère les données du tableau édité
            conn.execute("DELETE FROM history")
            edited_df.to_sql('history', conn, if_exists='append', index=False)
            conn.commit()
            st.success("Tableau des logs mis à jour !")

    conn.close()
