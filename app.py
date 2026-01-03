import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime

# --- CONFIGURATION SUPABASE ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="HIKMA - Supabase Cloud", layout="wide")

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

# --- AUTHENTIFICATION ---
if not st.session_state['logged_in']:
    st.title("📖 Hikma - Cloud")
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    with t1:
        u = st.text_input("Pseudo")
        p = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                u_data = res.data[0]
                st.session_state.update({'logged_in': True, 'user': u, 'role': u_data['role'], 'user_id': u_data['id']})
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with t2:
        nu, np = st.text_input("Nouveau Pseudo"), st.text_input("Nouveau MDP", type="password")
        if st.button("S'inscrire", use_container_width=True):
            try:
                supabase.table("users").insert({"username": nu, "password": np, "role": "membre"}).execute()
                st.success("Compte créé sur le Cloud !")
            except: st.error("Pseudo déjà pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    page = "Admin" if st.session_state['role'] == 'admin' else "Suivi"
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state.clear(); st.rerun()

    # --- PAGE SUIVI ---
    if page == "Suivi":
        st.title("🚀 Ma Progression")
        res = supabase.table("users").select("*").eq("id", st.session_state['user_id']).execute()
        u_data = res.data[0]
        
        p_act = u_data.get('page_actuelle') or 604
        h_obj = u_data.get('obj_hizb') or 0
        d_str = u_data.get('date_cible') or str(date.today())
        
        p_cible = 604 - (h_obj * 10)
        p_restantes = max(0, p_act - p_cible)
        try: jours = (datetime.strptime(d_str, '%Y-%m-%d').date() - date.today()).days
        except: jours = 0
        p_hebdo = round((p_restantes / max(1, jours)) * 7, 1) if jours > 0 else 0.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Pages à lire", p_restantes)
        c2.metric("Jours restants", max(0, jours))
        c3.metric("Rythme idéal", f"{p_hebdo} p/sem")

        st.divider()
        col_s, col_h = st.columns(2)
        s_list = list(DATA_CORAN.keys())
        sourate_act = u_data.get('sourate') or "An-Nas"
        choix_s = col_s.selectbox("Sourate finie", s_list, index=s_list.index(sourate_act) if sourate_act in s_list else 0)
        n_hizb = col_h.number_input("Hizb Cible (Objectif)", 0, 60, h_obj)
        
        p_deb, p_fin = DATA_CORAN[choix_s]
        num_p = st.number_input(f"Dernière page lue dans {choix_s}", 1, (p_fin - p_deb + 1), 1)
        p_calc = p_fin - (num_p - 1)

        if st.button("💾 Sauvegarder Progrès & Objectif", use_container_width=True):
            supabase.table("users").update({"page_actuelle": p_calc, "sourate": choix_s, "obj_hizb": n_hizb}).eq("id", st.session_state['user_id']).execute()
            supabase.table("history").insert({"username": st.session_state['user'], "date_enregistrement": str(date.today()), "page_atteinte": p_calc, "sourate_atteinte": choix_s}).execute()
            st.success("Données synchronisées sur le Cloud !"); st.rerun()

    # --- PAGE ADMIN ---
    elif page == "Admin":
        st.title("🛠️ Administration Hikma")
        t1, t2, t3 = st.tabs(["📊 Éditeur Rapide", "📅 Historique", "⚙️ Paramètres"])

        with t1:
            res = supabase.table("users").select("id, username, role, sourate, page_actuelle, obj_hizb").neq("username", "admin").execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                df.columns = ["id", "Pseudo", "Grade", "Sourate", "Page", "Hizb Cible"]
                edited = st.data_editor(df, hide_index=True, disabled=["id", "Pseudo"], use_container_width=True)
                if st.button("Sauvegarder les modifications"):
                    for _, r in edited.iterrows():
                        supabase.table("users").update({"role": r['Grade'], "sourate": r['Sourate'], "page_actuelle": r['Page'], "obj_hizb": r['Hizb Cible']}).eq("id", r['id']).execute()
                    st.success("Base de données Cloud mise à jour !"); st.rerun()

        with t2:
            d_hist = st.date_input("Consulter l'historique au :")
            res_h = supabase.table("history").select("*").lte("date_enregistrement", str(d_hist)).order("date_enregistrement", desc=True).execute()
            if res_h.data:
                df_h = pd.DataFrame(res_h.data).drop_duplicates(subset=["username"])
                st.table(df_h[["username", "sourate_atteinte", "page_atteinte", "date_enregistrement"]])

        with t3:
            res_u = supabase.table("users").select("*").neq("username", "admin").execute()
            for u in res_u.data:
                with st.expander(f"👤 {u['username']}"):
                    with st.form(f"f_{u['id']}"):
                        is_adm = st.checkbox("Admin", value=(u['role'] == 'admin'))
                        n_date = st.date_input("Date Cible", value=datetime.strptime(u['date_cible'], '%Y-%m-%d').date() if u.get('date_cible') else date.today())
                        if st.form_submit_button("Valider"):
                            supabase.table("users").update({"role": "admin" if is_adm else "membre", "date_cible": str(n_date)}).eq("id", u['id']).execute()
                            st.rerun()
                    if st.button(f"🗑️ Supprimer {u['username']}", type="primary"):
                        supabase.table("users").delete().eq("id", u['id']).execute()
                        st.rerun()
