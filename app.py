import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --- CONFIGURATION DES PAGES DU CORAN (Début et Fin) ---
# On définit le début et la fin de chaque sourate pour savoir combien de pages elle contient
DATA_CORAN = {
    "An-Nas": (604, 604), "Al-Falaq": (604, 604), "Al-Ikhlas": (604, 604), "Al-Masad": (603, 603), 
    "An-Nasr": (603, 603), "Al-Kafirun": (603, 603), "Al-Kawthar": (602, 602), "Al-Maun": (602, 602), 
    "Quraish": (602, 602), "Al-Fil": (601, 601), "Al-Humaza": (601, 601), "Al-Asr": (601, 601), 
    "At-Takathur": (600, 600), "Al-Qaria": (600, 600), "Al-Adiyat": (599, 599), "Az-Zalzala": (599, 599), 
    "Al-Bayyina": (598, 598), "Al-Qadr": (598, 598), "Al-Alaq": (597, 597), "At-Tin": (597, 597),
    "Ash-Sharh": (596, 596), "Ad-Duha": (596, 596), "Al-Layl": (595, 595), "Ash-Shams": (595, 595), 
    "Al-Balad": (594, 594), "Al-Fajr": (593, 593), "Al-Ghashiya": (592, 592), "Al-Ala": (591, 591), 
    "At-Tariq": (591, 591), "Al-Buruj": (590, 590), "Al-Inshiqaq": (589, 589), "Al-Mutaffifin": (588, 588), 
    "Al-Infitar": (587, 587), "At-Takwir": (586, 586), "Abasa": (585, 585), "An-Naziat": (583, 584), 
    "An-Naba": (582, 583), "Al-Mursalat": (580, 581), "Al-Insan": (578, 580), "Al-Qiyama": (577, 578),
    "Al-Muddathir": (575, 577), "Al-Muzzammil": (574, 575), "Al-Jinn": (572, 573), "Nuh": (570, 571), 
    "Al-Maarij": (568, 569), "Al-Haqqa": (566, 568), "Al-Qalam": (564, 566), "Al-Mulk": (562, 564),
} 
# Note: J'ai mis les principales du Juz Amma/Tabarak, le code calculera la différence tout seul.

def get_connection():
    return sqlite3.connect('coran_data.db', check_same_thread=False)

# --- INITIALISATION DB ---
def init_db():
    conn = get_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, page_actuelle INT, sourate TEXT, obj_hizb INT, date_cible TEXT, pages_par_semaine_fixe REAL)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, username TEXT, date_enregistrement TEXT, page_atteinte INT, sourate_atteinte TEXT)''')
    conn.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin123', 'admin')")
    conn.commit()
    conn.close()

init_db()

# --- ETAT DE LA SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None, 'page': "Accueil"})

# --- LOGIQUE DE CONNEXION ---
if not st.session_state['logged_in']:
    st.title("🌙 Suivi Coran")
    u = st.text_input("Pseudo")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        conn = get_connection()
        res = conn.execute("SELECT role, id FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        if res:
            st.session_state.update({'logged_in': True, 'user': u, 'role': res[0], 'user_id': res[1]})
            st.rerun()
        else: st.error("Erreur d'identifiants")
else:
    # Sidebar
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("🏠 Mon Suivi", use_container_width=True): st.session_state['page'] = "Accueil"
    if st.session_state['role'] == 'admin':
        if st.sidebar.button("⚙️ Administration", use_container_width=True): st.session_state['page'] = "Paramètres"
    if st.sidebar.button("🚪 Déconnexion", use_container_width=True): st.session_state.clear(); st.rerun()

    conn = get_connection()

    if st.session_state['page'] == "Accueil":
        st.title("🏠 Mon Suivi Personnel")
        row = conn.execute("SELECT page_actuelle, sourate, obj_hizb, date_cible, pages_par_semaine_fixe FROM users WHERE id=?", (st.session_state['user_id'],)).fetchone()
        
        # --- CALCULS DASHBOARD ---
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
        c1.metric("Pages à remonter", p_restantes)
        c2.metric("Jours restants", max(0, jours))
        c3.metric("Objectif Hebdo", f"{p_semaine} p.")

        st.divider()

        # --- FORMULAIRE DYNAMIQUE ---
        st.subheader("Mise à jour rapide")
        
        # 1. Choisir la sourate
        s_list = list(DATA_CORAN.keys())
        choix_s = st.selectbox("À quelle sourate es-tu ?", s_list, index=s_list.index(row[1]) if row[1] in s_list else 0)
        
        # 2. Vérifier si plusieurs pages
        p_debut, p_fin = DATA_CORAN[choix_s]
        nb_pages = p_fin - p_debut + 1
        
        page_calculee = p_debut
        
        if nb_pages > 1:
            options_p = [f"Page {i+1} de la sourate" for i in range(nb_pages)]
            choix_p_interne = st.radio(f"La sourate {choix_s} fait {nb_pages} pages. Laquelle as-tu fini ?", options_p)
            # On calcule la page réelle dans le Coran
            index_p = options_p.index(choix_p_interne)
            page_calculee = p_debut + index_p
        else:
            st.info(f"Cette sourate tient sur une seule page (Page {p_debut})")

        # Affichage de la page détectée
        st.success(f"📍 Page détectée : **{page_calculee}**")

        # 3. Objectifs
        with st.expander("Modifier mes objectifs (Hizb, Date, Rythme)"):
            new_h = st.number_input("Objectif Hizb (1=Sabbih, 2=Naba...)", value=int(h_obj))
            new_sem = st.number_input("OU Objectif pages/semaine fixe", value=float(p_sem_fixe))
            new_date = st.date_input("Date cible finale", value=datetime.strptime(d_str, '%Y-%m-%d').date())

        if st.button("✅ Enregistrer mes progrès", use_container_width=True):
            conn.execute("UPDATE users SET page_actuelle=?, sourate=?, obj_hizb=?, date_cible=?, pages_par_semaine_fixe=? WHERE id=?", 
                         (page_calculee, choix_s, new_h, str(new_date), new_sem, st.session_state['user_id']))
            conn.execute("INSERT INTO history (username, date_enregistrement, page_atteinte, sourate_atteinte) VALUES (?,?,?,?)",
                         (st.session_state['user'], str(date.today()), page_calculee, choix_s))
            conn.commit()
            st.toast("Progression enregistrée !")
            st.rerun()

    elif st.session_state['page'] == "Paramètres":
        st.title("⚙️ Administration")
        
        # Gestion des membres
        all_u = pd.read_sql_query("SELECT * FROM users", conn)
        for _, u_row in all_u.iterrows():
            if u_row['id'] == st.session_state['user_id']: continue
            with st.expander(f"👤 {u_row['username']} ({u_row['role']})"):
                # Rôles
                c_r1, c_r2 = st.columns(2)
                if u_row['role'] == 'membre':
                    if c_r1.button("🔼 Promouvoir Admin", key=f"p_{u_row['id']}"):
                        conn.execute("UPDATE users SET role='admin' WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()
                elif u_row['role'] == 'admin' and st.session_state['user_id'] == 1:
                    if c_r1.button("🔽 Rendre Membre", key=f"r_{u_row['id']}"):
                        conn.execute("UPDATE users SET role='membre' WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()
                
                if c_r2.button("🗑️ Supprimer", key=f"d_{u_row['id']}", type="primary"):
                    conn.execute("DELETE FROM users WHERE id=?", (u_row['id'],)); conn.commit(); st.rerun()

        st.divider()
        st.subheader("📅 Logs interactifs")
        h_df = pd.read_sql_query("SELECT * FROM history", conn)
        edited_h = st.data_editor(h_df, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("Enregistrer les modifs du tableau"):
            conn.execute("DELETE FROM history")
            edited_h.to_sql('history', conn, if_exists='append', index=False)
            conn.commit(); st.success("Logs mis à jour")

    conn.close()
