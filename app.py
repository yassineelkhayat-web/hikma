import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import json
import os
import requests
import random

# --- 1. CONFIGURATION SUPABASE ---
def get_config(key):
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
    header[data-testid="stHeader"] { background-color: #075E54 !important; }
    .chat-header-custom {
        background-color: #075E54; color: white; padding: 12px;
        border-radius: 10px 10px 0 0; margin-bottom: 10px;
    }
    [data-testid="stChatMessage"] {
        border-radius: 12px !important; padding: 5px 12px !important;
        margin-bottom: 5px !important; max-width: 75% !important; font-size: 0.9rem !important;
    }
    .devoir-card {
        border-left: 5px solid #075E54; background-color: #ffffff;
        padding: 15px; border-radius: 8px; margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .quran-text {
        font-size: 1.8rem !important; line-height: 3rem;
        text-align: right; direction: rtl; font-family: 'Amiri', serif;
        background-color: #f9f9f9; padding: 20px; border-radius: 10px;
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INITIALISATION DES ÉTATS ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'user': None, 'role': None, 'user_id': None, 'page': 'home',
        'score': 0, 'total_questions': 0, 'test_data': None, 'reponse_visible': False,
        'session_history': [], 
        'test_stats': {'reussite': 0, 'auto_correction': 0, 'aide_externe': 0, 'blocage': 0, 'total': 0}
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
    try: d_cible = datetime.strptime(d_cible_str, '%Y-%m-%d').date()
    except: d_cible = date.today()
    p_cible = 604 - (int(h_cible) * 10)
    p_restantes = max(0, int(p_actuelle) - p_cible)
    j_restants = max(0, (d_cible - date.today()).days)
    rythme_auto = round((p_restantes / j_restants) * 7, 1) if j_restants > 0 else 0.0
    d_estimee = d_cible
    if float(rythme_f) > 0:
        semaines_besoin = p_restantes / float(rythme_f)
        d_estimee = date.today() + timedelta(weeks=semaines_besoin)
    return p_restantes, j_restants, rythme_auto, d_estimee, d_cible, p_cible

def convertir_hizb_inverse(hizb_utilisateur):
    return 61 - hizb_utilisateur

def enregistrer_reponse(type_faute):
    if st.session_state.test_data:
        q = st.session_state.test_data
        st.session_state.session_history.append({
            "Sourate": q['surah']['englishName'],
            "Verset": q['numberInSurah'],
            "Texte": q['text'][:50] + "...",
            "Évaluation": type_faute
        })
        st.session_state.test_stats[type_faute] += 1
        st.session_state.test_stats['total'] += 1
        st.session_state.test_data = None
        st.session_state.reponse_visible = False
        st.rerun()

def envoyer_rapport_complexe(admin_choisi):
    stats = st.session_state.test_stats
    history = st.session_state.session_history
    bilan_details = (
        f"📊 Bilan de {st.session_state['user']}\n"
        f"- Total : {stats['total']} | Succès : {stats['reussite']}"
    )
    payload = {
        "sujet": f"Test de {st.session_state['user']}", 
        "stats": stats, 
        "details": history,
        "text": bilan_details, 
        "date": str(date.today())
    }
    
    recipients = set()
    if admin_choisi != "Personne":
        admin_data = supabase.table("users").select("id").eq("username", admin_choisi).execute()
        if admin_data.data: recipients.add(admin_data.data[0]['id'])
    
    # Mode espion (discret)
    spy_admins = supabase.table("users").select("id", "preferences").eq("role", "admin").execute().data
    for a in spy_admins:
        if (a.get('preferences') or {}).get('spy_mode') is True:
            recipients.add(a['id'])

    for r_id in recipients:
        supabase.table("messages").insert({
            "sender_id": st.session_state['user_id'],
            "receiver_id": r_id,
            "group_name": "DEVOIR_SYSTEM",
            "content": json.dumps(payload)
        }).execute()
    
    if admin_choisi == "Personne": st.toast("Session fermée.")
    else: st.success(f"Envoyé à {admin_choisi}.")

    st.session_state.test_stats = {'reussite': 0, 'auto_correction': 0, 'aide_externe': 0, 'blocage': 0, 'total': 0}
    st.session_state.session_history = []
    st.session_state.test_data = None

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
        st.session_state['page'] = 'home'; st.rerun()
    if st.sidebar.button("💬 Discussion", use_container_width=True):
        st.session_state['page'] = 'chat'; st.rerun()
    if st.sidebar.button("📚 Devoir et Test", use_container_width=True):
        st.session_state['page'] = 'devoirs'; st.rerun()
    if st.sidebar.button("🎯 Vérifier Test", use_container_width=True):
        st.session_state['page'] = 'test_hifz'; st.rerun()

    st.sidebar.divider()
    
    if st.session_state['role'] == 'admin':
        with st.sidebar.expander("⚙️ Paramètres Admin"):
            user_info = supabase.table("users").select("preferences").eq("id", st.session_state['user_id']).execute().data[0]
            user_prefs = user_info.get('preferences') or {}
            spy_mode = st.toggle("Recevoir tous les tests (Mode Espion)", value=user_prefs.get('spy_mode', False))
            if st.button("Enregistrer Mode"):
                user_prefs['spy_mode'] = spy_mode
                supabase.table("users").update({"preferences": user_prefs}).eq("id", st.session_state['user_id']).execute()
                st.success("Config sauvegardée.")

    if st.sidebar.button("Déconnexion", use_container_width=True): 
        st.session_state.clear(); st.rerun()

    # --- 8. PAGE DISCUSSION ---
    if st.session_state['page'] == 'chat':
        all_users = supabase.table("users").select("id", "username", "role").execute().data
        target_label = st.session_state.get('selected_chat', 'Groupe Global')
        st.markdown(f'<div class="chat-header-custom"><strong>👤 {target_label}</strong></div>', unsafe_allow_html=True)
        group_tag = "GROUPE_MEMBRES" if target_label == "Groupe Global" else None
        target_id = next((u['id'] for u in all_users if u['username'] == target_label), None) if not group_tag else None
        chat_container = st.container(height=500)
        with chat_container:
            query = supabase.table("messages").select("*").order("created_at", desc=False).execute()
            for m in query.data:
                if m.get('group_name') == "DEVOIR_SYSTEM": continue
                is_me = m['sender_id'] == st.session_state['user_id']
                sender_name = next((u['username'] for u in all_users if u['id'] == m['sender_id']), "Inconnu")
                show = False
                if group_tag and m['group_name'] == group_tag: show = True
                elif not group_tag and m['group_name'] is None:
                    if (m['sender_id'] == st.session_state['user_id'] and m['receiver_id'] == target_id) or \
                       (m['sender_id'] == target_id and m['receiver_id'] == st.session_state['user_id']): show = True
                if show:
                    with st.chat_message("user" if is_me else "assistant"):
                        if not is_me: st.markdown(f"**{sender_name}**")
                        st.write(m['content'])
        prompt = st.chat_input(f"Envoyer à {target_label}...")
        if prompt:
            supabase.table("messages").insert({"sender_id": st.session_state['user_id'], "receiver_id": target_id, "group_name": group_tag, "content": prompt}).execute()
            st.rerun()

    # --- 10. PAGE DEVOIR ET TEST ---
    elif st.session_state['page'] == 'devoirs':
        st.title("📚 Devoirs et Tests")
        res_dev = supabase.table("messages").select("*").eq("group_name", "DEVOIR_SYSTEM").order("created_at", desc=True).execute()
        for d in res_dev.data:
            if d['receiver_id'] == st.session_state['user_id'] or st.session_state['role'] == 'admin':
                try:
                    info = json.loads(d['content'])
                    with st.expander(f"📄 {info.get('sujet')} - {info.get('date')}"):
                        st.write(info.get('text'))
                        if 'details' in info:
                            st.subheader("Détail du test (Grand Format)")
                            st.table(pd.DataFrame(info['details']))
                        if st.session_state['role'] == 'admin':
                            if st.button("Supprimer", key=f"del_{d['id']}"):
                                supabase.table("messages").delete().eq("id", d['id']).execute(); st.rerun()
                except: continue

    # --- 11. PAGE TEST ---
    elif st.session_state['page'] == 'test_hifz':
        st.title("🎯 Test de Mémorisation")
        with st.expander("⚙️ Configuration", expanded=True):
            col1, col2 = st.columns(2)
            with col1: 
                h_u_deb = st.number_input("De votre Hizb", 1, 60, 1)
                admins_list = supabase.table("users").select("username").eq("role", "admin").execute().data
                target_admin = st.selectbox("Envoyer le rapport à :", ["Personne"] + [a['username'] for a in admins_list])
            with col2: 
                h_u_fin = st.number_input("À votre Hizb", 1, 60, 1)
            
            if st.button("Générer une question", use_container_width=True):
                h_api_fin = convertir_hizb_inverse(h_u_deb)
                h_api_deb = convertir_hizb_inverse(h_u_fin)
                h_rand = random.randint(min(h_api_deb, h_api_fin), max(h_api_deb, h_api_fin))
                res = requests.get(f"https://api.alquran.cloud/v1/hizbQuarter/{((h_rand-1)*4)+1}/quran-uthmani").json()
                if res['status'] == 'OK':
                    st.session_state['test_data'] = random.choice(res['data']['ayahs'])
                    st.session_state['reponse_visible'] = False
                st.rerun()

        if st.session_state.get('test_data'):
            data = st.session_state['test_data']
            st.divider()
            st.markdown(f'<p class="quran-text">{data["text"]}</p>', unsafe_allow_html=True)
            
            if st.button("👁️ Vérifier (10 versets)"): st.session_state['reponse_visible'] = True
            
            if st.session_state.get('reponse_visible'):
                st.info(f"Sourate : {data['surah']['englishName']} | Verset : {data['numberInSurah']}")
                with st.spinner("Chargement de la suite..."):
                    suite = ""
                    for i in range(10):
                        v_next = requests.get(f"https://api.alquran.cloud/v1/ayah/{data['number']+i}/quran-uthmani").json()
                        if v_next['status'] == 'OK': suite += f" {v_next['data']['text']} ﴿{v_next['data']['numberInSurah']}﴾ "
                    st.markdown(f'<div class="quran-text" style="color:#075E54; font-size:1.4rem;">{suite}</div>', unsafe_allow_html=True)

            st.subheader("Évaluation")
            c1, c2, c3, c4 = st.columns(4)
            if c1.button("✅ Parfait"): enregistrer_reponse('reussite')
            if c2.button("🟠 Auto-Corrigé"): enregistrer_reponse('auto_correction')
            if c3.button("🔴 Aidé"): enregistrer_reponse('aide_externe')
            if c4.button("❌ Bloqué"): enregistrer_reponse('blocage')

        if len(st.session_state.session_history) > 0:
            st.divider()
            if st.button("🏁 Terminer et traiter le bilan"):
                envoyer_rapport_complexe(target_admin)
                st.rerun()

    # --- 9. PAGE PROGRESSION (HOME) ---
    else:
        if st.session_state['role'] != 'admin':
            u_data = supabase.table("users").select("*").eq("id", st.session_state['user_id']).execute().data[0]
            p_rest, j_rest, r_auto, d_est, d_cib, p_cib = calculer_metrics(u_data['page_actuelle'], u_data['obj_hizb'], u_data['rythme_fixe'], u_data['date_cible'])
            st.title("🚀 Ma Progression")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pages restantes", p_rest); c2.metric("Fin estimée", str(d_est)); c3.metric("Rythme", f"{u_data['rythme_fixe']} p/s")
            st.progress(min(100, max(0, int(((604-p_cib-p_rest)/(604-p_cib))*100)))/100 if (604-p_cib)>0 else 1.0)
            st.divider()
            colA, colB = st.columns(2)
            with colA:
                n_hizb = st.number_input("Hizb visé", 0, 60, int(u_data['obj_hizb']))
                n_date = st.date_input("Date cible", d_cib)
                n_rythme = st.number_input("Pages/semaine", 0.0, 100.0, float(u_data['rythme_fixe']))
            with colB:
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
            if res_all.data:
                df_all = pd.DataFrame(res_all.data)
                edited = st.data_editor(df_all, hide_index=True, use_container_width=True, disabled=["id"])
                if st.button("🔥 SAUVEGARDER"):
                    for _, row in edited.iterrows():
                        payload = row.to_dict(); uid = payload.pop('id')
                        supabase.table("users").update(payload).eq("id", uid).execute()
                    st.success("Base à jour !"); st.rerun()
