import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import json
import os  # Ajouté pour lire les variables Railway

# --- 1. CONFIGURATION SUPABASE ---
# Cette modification permet de lire les clés sur Railway OU Streamlit Cloud
def get_config(key):
    # Cherche d'abord dans Railway (Environnement), puis dans Streamlit Secrets
    return os.environ.get(key) or st.secrets.get(key)

try:
    SUPABASE_URL = get_config("SUPABASE_URL")
    SUPABASE_KEY = get_config("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Clés manquantes")
        
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Erreur de configuration : Vérifiez les Variables Railway (SUPABASE_URL et SUPABASE_KEY).")
    st.stop()

# --- 2. CONFIGURATION STREAMLIT & DESIGN ---
st.set_page_config(page_title="HIKMA", layout="wide")

st.markdown("""
    <style>
    header[data-testid="stHeader"] {
        background-color: #075E54 !important;
    }
    .chat-header-custom {
        background-color: #075E54;
        color: white;
        padding: 12px;
        border-radius: 10px 10px 0 0;
        margin-bottom: 10px;
    }
    /* Bulles de messages plus fines */
    [data-testid="stChatMessage"] {
        border-radius: 12px !important;
        padding: 5px 12px !important;
        margin-bottom: 5px !important;
        max-width: 75% !important;
        font-size: 0.9rem !important;
    }
    /* Style pour les cartes de devoirs */
    .devoir-card {
        border-left: 5px solid #075E54;
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INITIALISATION DES ÉTATS ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 
        'user': None, 
        'role': None, 
        'user_id': None,
        'page': 'home' 
    })

# --- 4. DONNÉES SOURATES ---
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
    "Al-Qaria": (600, 600), "At-Talkathur": (600, 600), "Al-Asr": (601, 601), "Al-Humaza": (601, 601),
    "Al-Fil": (601, 601), "Quraish": (602, 602), "Al-Maun": (602, 602), "Al-Kawthar": (602, 602),
    "Al-Kafirun": (603, 603), "An-Nasr": (603, 603), "Al-Masad": (603, 603), "Al-Ikhlas": (604, 604),
    "Al-Falaq": (604, 604), "An-Nas": (604, 604)
}

# --- 5. FONCTIONS UTILES ---
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

# --- 6. AUTHENTIFICATION ---
if not st.session_state['logged_in']:
    st.title("📖 Hikma Bilan")
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
    # --- 7. SIDEBAR ---
    st.sidebar.title(f"👤 {st.session_state['user']}")
    
    if st.sidebar.button("🏠 Ma Progression", use_container_width=True):
        st.session_state['page'] = 'home'
        st.rerun()

    if st.sidebar.button("💬 Discussion", use_container_width=True):
        st.session_state['page'] = 'chat'
        st.rerun()

    if st.sidebar.button("📚 Devoir et Test", use_container_width=True):
        st.session_state['page'] = 'devoirs'
        st.rerun()

    st.sidebar.divider()
    
    # --- GESTION DES CONTACTS DANS LA SIDEBAR (Chat seulement) ---
    if st.session_state['page'] == 'chat':
        st.sidebar.subheader("📇 Mes Contacts")
        all_users = supabase.table("users").select("id", "username", "role").execute().data
        
        if st.session_state['role'] == 'admin':
            with st.sidebar.expander("➕ Créer un Groupe"):
                g_name = st.text_input("Nom du groupe")
                g_members = st.multiselect("Membres", [u['username'] for u in all_users if u['username'] != st.session_state['user']])
                if st.button("Créer"):
                    st.success(f"Groupe '{g_name}' créé !")
        
        contact_list = ["Groupe Global"] + [u['username'] for u in all_users if u['username'] != st.session_state['user']]
        selected_chat = st.sidebar.radio("Discuter avec :", contact_list)
        st.session_state['selected_chat'] = selected_chat

    # --- ADMINISTRATION TRADITIONNELLE ---
    if st.session_state['role'] == 'admin':
        with st.sidebar.expander("⚙️ Paramètres Admin"):
            membres_data = supabase.table("users").select("username").eq("role", "membre").execute().data
            liste_membres = [m['username'] for m in membres_data]
            if liste_membres:
                user_to_promote = st.selectbox("Promouvoir", liste_membres)
                if st.button("Rendre Administrateur"):
                    supabase.table("users").update({"role": "admin"}).eq("username", user_to_promote).execute()
                    st.success("Fait !"); st.rerun()

    if st.sidebar.button("Déconnexion", use_container_width=True): 
        st.session_state.clear()
        st.rerun()

    # --- 8. PAGE DISCUSSION (INTERFACE WHATSAPP) ---
    if st.session_state['page'] == 'chat':
        all_users = supabase.table("users").select("id", "username", "role").execute().data
        target_label = st.session_state.get('selected_chat', 'Groupe Global')
        
        st.markdown(f"""
            <div class="chat-header-custom">
                <strong>👤 {target_label}</strong><br>
                <small>{'Discussion de groupe' if target_label == 'Groupe Global' else 'Message privé'}</small>
            </div>
            """, unsafe_allow_html=True)

        group_tag = "GROUPE_MEMBRES" if target_label == "Groupe Global" else None
        target_id = None
        if not group_tag:
            target_user = next((u for u in all_users if u['username'] == target_label), None)
            target_id = target_user['id'] if target_user else None

        chat_container = st.container(height=500)
        with chat_container:
            query = supabase.table("messages").select("*").order("created_at", desc=False).execute()
            for m in query.data:
                if m.get('group_name') == "DEVOIR_SYSTEM": continue

                is_me = m['sender_id'] == st.session_state['user_id']
                sender_name = next((u['username'] for u in all_users if u['id'] == m['sender_id']), "Inconnu")
                
                show = False
                if group_tag and m['group_name'] == group_tag:
                    show = True
                elif not group_tag and m['group_name'] is None:
                    if (m['sender_id'] == st.session_state['user_id'] and m['receiver_id'] == target_id) or \
                       (m['sender_id'] == target_id and m['receiver_id'] == st.session_state['user_id']):
                        show = True
                
                if show:
                    with st.chat_message("user" if is_me else "assistant"):
                        if not is_me: st.markdown(f"**{sender_name}**")
                        st.write(m['content'])
                        st.caption(f"{m['created_at'][11:16]} {'✓✓' if is_me else ''}")

        prompt = st.chat_input(f"Envoyer à {target_label}...")
        if prompt:
            supabase.table("messages").insert({
                "sender_id": st.session_state['user_id'],
                "receiver_id": target_id,
                "group_name": group_tag,
                "content": prompt
            }).execute()
            st.rerun()

    # --- 10. PAGE DEVOIR ET TEST ---
    elif st.session_state['page'] == 'devoirs':
        st.title("📚 Devoirs et Tests")
        all_users = supabase.table("users").select("id", "username", "role").execute().data
        membres = [u for u in all_users if u['role'] == 'membre']

        if st.session_state['role'] == 'admin':
            with st.expander("🆕 Assigner un Devoir/Test", expanded=True):
                dest = st.selectbox("Pour qui ?", ["Tous"] + [u['username'] for u in membres])
                sujet = st.text_input("Sujet du test / devoir")
                c1, c2 = st.columns(2)
                with c1:
                    nb_p = st.number_input("Nombre de pages", 0, 604, 10)
                with c2:
                    nb_h = st.number_input("Nombre de Hizb", 0, 60, 1)
                
                instructions = st.text_area("Précisions (ex: Portera sur les 10 premières pages de Al-Baqara)")
                
                if st.button("Publier l'annonce"):
                    t_id = None if dest == "Tous" else next(u['id'] for u in membres if u['username'] == dest)
                    payload = {
                        "sujet": sujet,
                        "pages": nb_p,
                        "hizb": nb_h,
                        "text": instructions,
                        "date": str(date.today())
                    }
                    supabase.table("messages").insert({
                        "sender_id": st.session_state['user_id'],
                        "receiver_id": t_id,
                        "group_name": "DEVOIR_SYSTEM",
                        "content": json.dumps(payload)
                    }).execute()
                    st.success("Annonce publiée !"); st.rerun()

        st.divider()
        res_dev = supabase.table("messages").select("*").eq("group_name", "DEVOIR_SYSTEM").order("created_at", desc=True).execute()
        
        for d in res_dev.data:
            if d['receiver_id'] is None or d['receiver_id'] == st.session_state['user_id'] or st.session_state['role'] == 'admin':
                try:
                    info = json.loads(d['content'])
                    with st.container():
                        st.markdown(f"""
                        <div class="devoir-card">
                            <h4>📝 {info['sujet']}</h4>
                            <p><b>Cible :</b> {info['pages']} pages | {info['hizb']} Hizb</p>
                            <p><i>{info['text']}</i></p>
                            <small>Publié le {info['date']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.session_state['role'] == 'admin':
                            if st.button("Supprimer", key=f"del_dev_{d['id']}"):
                                supabase.table("messages").delete().eq("id", d['id']).execute()
                                st.rerun()
                except: continue

    # --- 9. PAGE PROGRESSION (HOME) ---
    else:
        if st.session_state['role'] != 'admin':
            u_data = supabase.table("users").select("*").eq("id", st.session_state['user_id']).execute().data[0]
            p_rest, j_rest, r_auto, d_est, d_cib, p_cib = calculer_metrics(u_data['page_actuelle'], u_data['obj_hizb'], u_data['rythme_fixe'], u_data['date_cible'])
            
            st.title("🚀 Ma Progression")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pages restantes", p_rest)
            if float(u_data['rythme_fixe']) > 0:
                c2.metric("Fin estimée", str(d_est))
                c3.metric("Rythme", f"{u_data['rythme_fixe']} p/s")
            else:
                c2.metric("Jours restants", j_rest)
                c3.metric("Conseillé", f"{r_auto} p/s")

            total_pages_objectif = 604 - p_cib
            perc = min(100, max(0, int(((total_pages_objectif - p_rest) / total_pages_objectif) * 100))) if total_pages_objectif > 0 else 100
            st.progress(perc / 100)
            st.write(f"**{perc}%** atteint")

            st.divider()
            colA, colB = st.columns(2)
            with colA:
                st.subheader("🎯 Objectifs")
                n_hizb = st.number_input("Hizb visé", 0, 60, int(u_data['obj_hizb']))
                n_date = st.date_input("Date cible", d_cib)
                n_rythme = st.number_input("Pages/semaine", 0.0, 100.0, float(u_data['rythme_fixe']))
            with colB:
                st.subheader("📖 Mon étude")
                s_list = list(DATA_CORAN.keys())
                curr_s = u_data.get('sourate') or "An-Nas"
                n_s = st.selectbox("Dernière sourate", s_list, index=s_list.index(curr_s))
                p_deb, p_fin = DATA_CORAN[n_s]
                p_dans_s = st.number_input(f"Page dans {n_s}", 1, (p_fin-p_deb+1), 1)
                n_p_reelle = p_fin - (p_dans_s - 1)

            if st.button("💾 Sauvegarder", use_container_width=True):
                upd = {"page_actuelle": n_p_reelle, "sourate": n_s, "obj_hizb": n_hizb, "date_cible": str(n_date), "rythme_fixe": n_rythme}
                supabase.table("users").update(upd).eq("id", st.session_state['user_id']).execute()
                st.success("Mis à jour !"); st.rerun()
        else:
            st.title("🛠️ Administration")
            res_all = supabase.table("users").select("*").execute()
            all_users_admin = res_all.data
            if all_users_admin:
                df_all = pd.DataFrame(all_users_admin)
                st.subheader("🚨 Données Maître")
                edited_master = st.data_editor(df_all, hide_index=True, use_container_width=True, disabled=["id"])
                if st.button("🔥 SAUVEGARDER"):
                    for _, row in edited_master.iterrows():
                        payload = row.to_dict(); uid = payload.pop('id')
                        supabase.table("users").update(payload).eq("id", uid).execute()
                    st.success("Base à jour !"); st.rerun()

                st.divider()
                st.subheader("🔍 Focus par membre")
                users_focus = [u for u in all_users_admin if u['username'] != 'admin']
                for user in users_focus:
                    with st.expander(f"👤 {user['username'].upper()}"):
                        p_rest, j_rest, r_auto, d_est, d_cib, p_cib = calculer_metrics(user['page_actuelle'], user['obj_hizb'], user['rythme_fixe'], user['date_cible'])
                        st.write(f"Reste : {p_rest} pages | Idéal : {r_auto} p/sem")

                st.divider()
                st.subheader("🗑️ Supprimer un membre")
                u_to_del = st.selectbox("Choisir", [u['username'] for u in users_focus], key="del_box")
                if st.button("SUPPRIMER DÉFINITIVEMENT", type="primary"):
                    supabase.table("users").delete().eq("username", u_to_del).execute()
                    st.rerun()
