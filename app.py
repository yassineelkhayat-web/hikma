import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime, timedelta

# --- CONFIGURATION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    st.error("Erreur de Secrets Supabase.")
    st.stop()

st.set_page_config(page_title="HIKMA PRO", layout="wide")

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

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None})

# --- AUTH ---
if not st.session_state['logged_in']:
    st.title("📖 Hikma Cloud")
    t1, t2 = st.tabs(["Connexion", "Inscription"])
    with t1:
        u = st.text_input("Pseudo", key="l1")
        p = st.text_input("MDP", type="password", key="l2")
        if st.button("Se connecter"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res.data[0]['role'], 'user_id': res.data[0]['id']})
                st.rerun()
    with t2:
        nu, np = st.text_input("Pseudo", key="r1"), st.text_input("MDP", type="password", key="r2")
        if st.button("S'inscrire"):
            supabase.table("users").insert({"username": nu, "password": np}).execute()
            st.success("OK !")

else:
    # --- LOGIQUE DE CALCUL ---
    u_data = supabase.table("users").select("*").eq("id", st.session_state['user_id']).execute().data[0]
    
    p_actuelle = u_data.get('page_actuelle') or 604
    h_cible = u_data.get('obj_hizb') or 0
    rythme_f = u_data.get('rythme_fixe') or 0.0
    d_cible_str = u_data.get('date_cible') or str(date.today())
    d_cible = datetime.strptime(d_cible_str, '%Y-%m-%d').date()
    
    # Formules
    page_cible = 604 - (h_cible * 10)
    pages_a_lire = max(0, p_actuelle - page_cible)
    jours_restants = max(0, (d_cible - date.today()).days)
    
    if jours_restants > 0:
        rythme_auto = round((pages_a_lire / jours_restants) * 7, 1)
    else:
        rythme_auto = 0.0

    # --- INTERFACE ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("Déconnexion"): st.session_state.clear(); st.rerun()

    if st.session_state['role'] != 'admin':
        st.title("🚀 Mon Suivi")
        
        # Dashboard
        c1, c2, c3 = st.columns(3)
        c1.metric("Pages restantes", pages_a_lire)
        c2.metric("Jours restants", jours_restants)
        c3.metric("Rythme conseillé", f"{rythme_auto} p/sem")

        st.divider()
        
        # Modification Objectifs
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("🎯 Objectif")
            n_hizb = st.number_input("Hizb Cible (ex: 60 pour Coran entier)", 0, 60, h_cible)
            n_date = st.date_input("Date cible", d_cible)
            n_rythme = st.number_input("OU fixer pages/semaine", 0.0, 100.0, rythme_f)
            
        with col_b:
            st.subheader("📖 Ma Lecture")
            s_list = list(DATA_CORAN.keys())
            s_act = st.selectbox("Sourate finie", s_list, index=s_list.index(u_data.get('sourate') or "An-Nas"))
            p_deb, p_fin = DATA_CORAN[s_act]
            p_dans_s = st.number_input(f"Page lue dans {s_act}", 1, (p_fin - p_deb + 1), 1)
            p_reelle = p_fin - (p_dans_s - 1)

        if st.button("💾 Sauvegarder", use_container_width=True):
            upd = {
                "page_actuelle": p_reelle, "sourate": s_act, 
                "obj_hizb": n_hizb, "date_cible": str(n_date), "rythme_fixe": n_rythme
            }
            supabase.table("users").update(upd).eq("id", st.session_state['user_id']).execute()
            supabase.table("history").insert({
                "username": st.session_state['user'], "date_enregistrement": str(date.today()),
                "page_atteinte": p_reelle, "sourate_atteinte": s_act
            }).execute()
            st.success("Cloud à jour !"); st.rerun()

    else:
        # --- ADMIN ---
        st.title("🛠️ Admin")
        res = supabase.table("users").select("*").neq("username", "admin").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # Ajout des colonnes calculées pour l'admin
            df['Pages Restantes'] = df['page_actuelle'] - (604 - (df['obj_hizb'] * 10))
            st.data_editor(df[["id", "username", "sourate", "page_actuelle", "obj_hizb", "Pages Restantes"]], use_container_width=True)
            
            if st.button("Supprimer un membre"):
                target = st.selectbox("Qui supprimer ?", df['username'])
                if st.button("Confirmer suppression"):
                    supabase.table("users").delete().eq("username", target).execute()
                    st.rerun()
