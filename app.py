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
    st.error("Erreur de configuration : Vérifiez les Secrets Streamlit.")
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

# --- FONCTION DE CALCUL ---
def calculer_metrics(p_actuelle, h_cible, rythme_f, d_cible_str):
    try:
        d_cible = datetime.strptime(d_cible_str, '%Y-%m-%d').date()
    except:
        d_cible = date.today()
    
    p_cible = 604 - (int(h_cible) * 10)
    p_restantes = max(0, int(p_actuelle) - p_cible)
    j_restants = max(0, (d_cible - date.today()).days)
    rythme_auto = round((p_restantes / j_restants) * 7, 1) if j_restants > 0 else 0.0
    
    d_estimee = d_cible
    if float(rythme_f) > 0:
        semaines_besoin = p_restantes / float(rythme_f)
        d_estimee = date.today() + timedelta(weeks=semaines_besoin)
    
    return p_restantes, j_restants, rythme_auto, d_estimee, d_cible, p_cible

# --- AUTHENTIFICATION ---
if not st.session_state['logged_in']:
    st.title("📖 Hikma Cloud")
    t1, t2 = st.tabs(["Connexion", "Inscription"])
    with t1:
        u = st.text_input("Pseudo", key="l1")
        p = st.text_input("MDP", type="password", key="l2")
        if st.button("Se connecter", use_container_width=True):
            res = supabase.table("users").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.update({'logged_in': True, 'user': u, 'role': res.data[0]['role'], 'user_id': res.data[0]['id']})
                st.rerun()
            else: st.error("Identifiants incorrects.")
    with t2:
        nu, np = st.text_input("Pseudo", key="r1"), st.text_input("MDP", type="password", key="r2")
        if st.button("S'inscrire"):
            try:
                supabase.table("users").insert({"username": nu, "password": np, "role": "membre"}).execute()
                st.success("Compte créé ! Connectez-vous.")
            except: st.error("Pseudo déjà utilisé.")

else:
    st.sidebar.title(f"👤 {st.session_state['user']}")
    if st.sidebar.button("Déconnexion"): st.session_state.clear(); st.rerun()

    # --- INTERFACE MEMBRE ---
    if st.session_state['role'] != 'admin':
        u_data = supabase.table("users").select("*").eq("id", st.session_state['user_id']).execute().data[0]
        p_rest, j_rest, r_auto, d_est, d_cib, p_cib = calculer_metrics(u_data['page_actuelle'], u_data['obj_hizb'], u_data['rythme_fixe'], u_data['date_cible'])
        
        st.title("🚀 Ma Progression")
        c1, c2, c3 = st.columns(3)
        c1.metric("Pages restantes", p_rest)
        if float(u_data['rythme_fixe']) > 0:
            c2.metric("Date fin estimée", str(d_est))
            c3.metric("Rythme fixé", f"{u_data['rythme_fixe']} p/sem")
        else:
            c2.metric("Jours restants", j_rest)
            c3.metric("Rythme conseillé", f"{r_auto} p/sem")

        # --- BARRE DE PROGRESSION VISUELLE ---
        st.subheader("📊 Progression vers l'objectif")
        total_pages_objectif = 604 - p_cib
        if total_pages_objectif > 0:
            pages_faites = total_pages_objectif - p_rest
            pourcentage = min(100, max(0, int((pages_faites / total_pages_objectif) * 100)))
        else:
            pourcentage = 100
        st.progress(pourcentage / 100)
        st.write(f"**{pourcentage}%** de ton objectif atteint !")
        if pourcentage >= 100: st.balloons()

        st.divider()
        colA, colB = st.columns(2)
        with colA:
            st.subheader("🎯 Objectifs")
            n_hizb = st.number_input("Hizb visé (0-60)", 0, 60, int(u_data['obj_hizb']))
            n_date = st.date_input("Date cible", d_cib)
            n_rythme = st.number_input("OU Pages/semaine", 0.0, 100.0, float(u_data['rythme_fixe']))
        with colB:
            st.subheader("📖 Ma Lecture")
            s_list = list(DATA_CORAN.keys())
            curr_s = u_data.get('sourate') or "An-Nas"
            n_s = st.selectbox("Dernière sourate finie", s_list, index=s_list.index(curr_s))
            p_deb, p_fin = DATA_CORAN[n_s]
            p_dans_s = st.number_input(f"Page lue dans {n_s}", 1, (p_fin-p_deb+1), 1)
            n_p_reelle = p_fin - (p_dans_s - 1)

        if st.button("💾 Sauvegarder", use_container_width=True):
            upd = {"page_actuelle": n_p_reelle, "sourate": n_s, "obj_hizb": n_hizb, "date_cible": str(n_date), "rythme_fixe": n_rythme}
            supabase.table("users").update(upd).eq("id", st.session_state['user_id']).execute()
            st.success("Synchronisé !"); st.rerun()

    # --- INTERFACE ADMIN ---
    else:
        st.title("🛠️ Panneau Administrateur")
        users = supabase.table("users").select("*").neq("username", "admin").execute().data
        
        if users:
            df = pd.DataFrame(users)
            st.subheader("📊 Vue d'ensemble")
            edited_df = st.data_editor(
                df[["id", "username", "role", "sourate", "page_actuelle", "obj_hizb", "rythme_fixe", "date_cible"]], 
                hide_index=True, use_container_width=True, disabled=["id", "username"]
            )
            if st.button("💾 Sauvegarder les modifications du tableau"):
                for _, row in edited_df.iterrows():
                    supabase.table("users").update({
                        "role": row['role'], "sourate": row['sourate'], 
                        "page_actuelle": int(row['page_actuelle']), "obj_hizb": int(row['obj_hizb']), 
                        "rythme_fixe": float(row['rythme_fixe']), "date_cible": str(row['date_cible'])
                    }).eq("id", row['id']).execute()
                st.success("Modifications appliquées !"); st.rerun()

            st.divider()
            st.subheader("🔍 Focus par membre")
            for user in users:
                with st.expander(f"👤 {user['username'].upper()} - Gestion détaillée"):
                    p_rest, j_rest, r_auto, d_est, d_cib, p_cib = calculer_metrics(
                        user['page_actuelle'], user['obj_hizb'], user['rythme_fixe'], user['date_cible']
                    )
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Pages restantes", p_rest)
                    m2.metric("Jours restants", j_rest)
                    m3.metric("Rythme idéal", f"{r_auto} p/sem")

                    # Barre de progression pour l'admin aussi
                    total_p_obj = 604 - p_cib
                    perc = min(100, max(0, int(((total_p_obj - p_rest) / total_p_obj) * 100))) if total_p_obj > 0 else 100
                    st.progress(perc / 100)
                    st.caption(f"Progression : {perc}%")
                    
                    c_adm1, c_adm2 = st.columns(2)
                    with c_adm1:
                        st.write("**🎯 Objectifs**")
                        adm_h = st.number_input("Hizb cible", 0, 60, int(user['obj_hizb']), key=f"h_{user['id']}")
                        adm_d = st.date_input("Date cible", d_cib, key=f"d_{user['id']}")
                        adm_r = st.number_input("Rythme fixe (p/sem)", 0.0, 100.0, float(user['rythme_fixe']), key=f"r_{user['id']}")
                    with c_adm2:
                        st.write("**📖 Lecture**")
                        s_list = list(DATA_CORAN.keys())
                        u_s = user['sourate'] if user['sourate'] in s_list else "An-Nas"
                        adm_s = st.selectbox("Sourate", s_list, index=s_list.index(u_s), key=f"s_{user['id']}")
                        p_deb, p_fin = DATA_CORAN[adm_s]
                        adm_p_s = st.number_input(f"Page dans {adm_s}", 1, (p_fin-p_deb+1), 1, key=f"ps_{user['id']}")
                        adm_p_reelle = p_fin - (adm_p_s - 1)
                    
                    if st.button(f"Mettre à jour {user['username']}", key=f"btn_{user['id']}", use_container_width=True):
                        upd_indiv = {"page_actuelle": adm_p_reelle, "sourate": adm_s, "obj_hizb": adm_h, "date_cible": str(adm_d), "rythme_fixe": adm_r}
                        supabase.table("users").update(upd_indiv).eq("id", user['id']).execute()
                        st.success("Mis à jour !"); st.rerun()

            st.divider()
            st.subheader("🗑️ Zone de danger")
            u_to_del = st.selectbox("Choisir le compte à supprimer", [u['username'] for u in users])
            if st.button("CONFIRMER LA SUPPRESSION", type="primary"):
                supabase.table("users").delete().eq("username", u_to_del).execute()
                st.rerun()
