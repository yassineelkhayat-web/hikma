import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime, timedelta

# --- CONFIGURATION SUPABASE ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Erreur de configuration : Vérifie les Secrets dans Streamlit.")
    st.stop()

# --- CONFIGURATION STREAMLIT ---
st.set_page_config(page_title="HIKMA - Suivi Coran", layout="wide")

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

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user': None, 'role': None, 'user_id': None})

# --- CONNEXION / INSCRIPTION ---
if not st.session_state['logged_in']:
    st.title("📖 Hikma - Suivi Collectif")
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
    with t1:
        u = st.text_input("Pseudo", key="l_u")
        p = st.text_input("Mot de passe", type="password", key="l_p")
        if st.button("Entrer", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res.data[0]['role'], 'user_id': res.data[0]['id']})
                st.rerun()
            else: st.error("Erreur d'accès.")
    with t2:
        nu, np = st.text_input("Nouveau Pseudo", key="r_u"), st.text_input("Nouveau Mot de passe", type="password", key="r_p")
        if st.button("Créer mon compte"):
            try:
                supabase.table("users").insert({"username": nu, "password": np}).execute()
                st.success("Compte créé !")
            except: st.error("Pseudo déjà pris.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("Déconnexion"):
        st.session_state.clear(); st.rerun()

    # --- MODE MEMBRE ---
    if st.session_state['role'] != 'admin':
        st.title("🚀 Mon Suivi Personnel")
        u_data = supabase.table("users").select("*").eq("id", st.session_state['user_id']).execute().data[0]
        
        # 1. PARAMÈTRES D'OBJECTIF
        st.subheader("🎯 Mon Objectif")
        col_obj1, col_obj2 = st.columns(2)
        
        mode = col_obj1.radio("Calculer par :", ["Hizb cible", "Pages par semaine"])
        
        if mode == "Hizb cible":
            h_obj = col_obj2.number_input("Hizb à atteindre (ex: 60)", 0, 60, int(u_data.get('obj_hizb') or 60))
            d_cible = st.date_input("Pour quelle date ?", value=datetime.strptime(u_data.get('date_cible') or str(date.today()), '%Y-%m-%d').date())
            rythme = 0.0
        else:
            rythme = col_obj2.number_input("Pages par semaine", 0.1, 70.0, float(u_data.get('rythme_fixe') or 5.0))
            h_obj = int(u_data.get('obj_hizb') or 60)
            d_cible = date.today() # Sera ignoré car calculé par le rythme

        st.divider()

        # 2. DERNIÈRE LECTURE
        st.subheader("📖 Ma Progression Actuelle")
        c1, c2 = st.columns(2)
        s_list = list(DATA_CORAN.keys())
        s_act = c1.selectbox("Dernière Sourate finie", s_list, index=s_list.index(u_data.get('sourate') or "An-Nas"))
        
        p_deb, p_fin = DATA_CORAN[s_act]
        p_dans_s = c2.number_input(f"Page lue dans {s_act}", 1, (p_fin - p_deb + 1), 1)
        p_reelle = p_fin - (p_dans_s - 1)

        if st.button("💾 Enregistrer mes modifications", use_container_width=True):
            upd = {
                "page_actuelle": p_reelle, 
                "sourate": s_act, 
                "obj_hizb": h_obj, 
                "date_cible": str(d_cible),
                "rythme_fixe": rythme
            }
            supabase.table("users").update(upd).eq("id", st.session_state['user_id']).execute()
            supabase.table("history").insert({"username": st.session_state['user'], "date_enregistrement": str(date.today()), "page_atteinte": p_reelle, "sourate_atteinte": s_act}).execute()
            st.success("Données sauvegardées !"); st.rerun()

    # --- MODE ADMIN ---
    else:
        st.title("🛠️ Gestion du Groupe")
        res = supabase.table("users").select("*").neq("username", "admin").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            # On permet à l'admin de tout modifier via le tableau
            st.write("Modifiez les valeurs directement dans le tableau :")
            edited_df = st.data_editor(df[["id", "username", "sourate", "page_actuelle", "obj_hizb", "rythme_fixe", "date_cible"]], hide_index=True, use_container_width=True)
            
            if st.button("💾 Sauvegarder les changements globaux"):
                for _, row in edited_df.iterrows():
                    supabase.table("users").update({
                        "sourate": row['sourate'],
                        "page_actuelle": row['page_actuelle'],
                        "obj_hizb": row['obj_hizb'],
                        "rythme_fixe": row['rythme_fixe'],
                        "date_cible": str(row['date_cible'])
                    }).eq("id", row['id']).execute()
                st.success("Base de données mise à jour !"); st.rerun()
