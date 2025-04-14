# ✅ Logique Kelly avec affichage moderne & traitement complet des paris

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import psycopg2

# --- Connexion BDD ---
DATABASE_URL = "postgresql://postgres:jDDqfaqpspVDBBwsqxuaiSDNXjTxjMmP@shortline.proxy.rlwy.net:36536/railway"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Forcer le bon schéma
cursor.execute("SET search_path TO public")

# --- Bankroll helper ---
def get_bankroll():
    cursor.execute("SELECT solde FROM bankroll ORDER BY id DESC LIMIT 1")
    res = cursor.fetchone()
    return res[0] if res else 50.0

def init_bankroll():
    cursor.execute("SELECT COUNT(*) FROM bankroll")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO bankroll (solde) VALUES (50.0)")
        conn.commit()

def update_bankroll(delta):
    solde = float(get_bankroll() + delta)
    cursor.execute("UPDATE bankroll SET solde = %s WHERE id = (SELECT id FROM bankroll ORDER BY id DESC LIMIT 1)", (solde,))
    conn.commit()
    return solde

init_bankroll()

# --- Fonctions de calcul ---
def kelly(bankroll, p, c):
    if c <= 1 or not 0 < p < 1:
        return 0.0
    edge = (c * p - 1)
    return bankroll * edge / (c - 1) if edge > 0 else 0.0

def proba_estimee(c):
    implicite = 1 / c
    return max(0.01, min(0.99, implicite * 1.08))

# --- Interface Streamlit ---
st.set_page_config(page_title="Bankroll - Paris Sportifs", layout="centered")
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        padding: 0.25rem 0.75rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Gestion de Bankroll - Paris Sportifs")

# --- Navigation via onglets ---
tab1, tab2 = st.tabs(["🎯 Gestion des paris", "📊 Dashboard avancé"])

# Onglet 1 : Ton app actuelle
with tab1:
    # Tout ton code actuel ici (formulaires, historique, etc.)
    st.markdown("## 🎯 Interface principale")

    # --- Sidebar ---
    with st.sidebar:
        st.markdown("## ⚙️ Paramètres")
        if st.button("🔁 Réinitialiser la bankroll"):
            cursor.execute("UPDATE bankroll SET solde = 50.0")
            conn.commit()
            st.success("Bankroll réinitialisée à 50 €")
            st.rerun()
    
        st.markdown(f"### 💰 Bankroll actuelle : {get_bankroll():.2f} €")
    
        if st.button("🗑️ Réinitialiser l'historique des paris"):
            cursor.execute("DELETE FROM paris")
            conn.commit()
            st.success("Historique vidé")
            st.rerun()
    
        st.markdown("---")
        st.markdown("### 📈 Courbe Kelly vs Cote")
        cotes_range = np.linspace(1.01, 5.0, 60)
        probas = [proba_estimee(c) for c in cotes_range]
        kelly_vals = [kelly(100, p, c) for p, c in zip(probas, cotes_range)]
        fig, ax = plt.subplots(figsize=(3.5, 2.5))
        ax.plot(cotes_range, kelly_vals, color='blue', linewidth=2)
        ax.set_xlabel("Cote")
        ax.set_ylabel("Mise (€)")
        ax.set_title("Kelly vs Cote")
        ax.grid(True)
        st.pyplot(fig, clear_figure=True)
        st.caption("📌 Proba = (1 / cote) × 1.08")
    
    # --- Formulaire de pari ---
    st.markdown("### ➕ Ajouter un pari")
    type_pari_general = st.radio("Type de pari :", ["Pari simple", "Pari combiné"], horizontal=True)
    if type_pari_general == "Pari simple":
        with st.form("formulaire_pari"):
            match = st.text_input("Match")
            col1, col2 = st.columns(2)
            with col1:
                sport = st.selectbox("Sport", ["Football", "Basket", "Tennis"])
                type_pari = st.selectbox("Type", ["Vainqueur", "Over/Under", "Handicap", "Score exact", "Autre"])
            with col2:
                pari = st.text_input("Pari")
                cote = st.number_input("Cote", 1.01, step=0.01, format="%.2f")
    
            proba = proba_estimee(cote)
            bankroll = get_bankroll()
            mise_kelly = kelly(bankroll, proba, cote)
            strategie = st.radio("Stratégie", ["Kelly", "Demi-Kelly"], horizontal=True)
            mise_finale = mise_kelly if strategie == "Kelly" else mise_kelly / 2
            st.success(f"💸 Mise recommandée : {mise_finale:.2f} €")
    
            submitted = st.form_submit_button("✅ Enregistrer le pari")
            if submitted:
                update_bankroll(-mise_finale)
                cursor.execute("""
                    INSERT INTO paris (match, sport, type, pari, cote, mise, strategie, resultat, gain)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Non joué', 0)
                """, (match, sport, type_pari, pari, cote, round(mise_finale, 2), strategie))
                conn.commit()
                st.success("Pari enregistré et bankroll mise à jour ✅")
                st.rerun()
                
    elif type_pari_general == "Pari combiné":
        with st.form("formulaire_combine"):
            selections = []
            for i in range(1, 4):
                with st.expander(f"Sélection {i}"):
                    match_c = st.text_input(f"Match {i}", key=f"match_c_{i}")
                    pari_c = st.text_input(f"Pari {i}", key=f"pari_c_{i}")
                    cote_c = st.number_input(f"Cote {i}", 1.01, step=0.01, format="%.2f", key=f"cote_c_{i}")
                    if match_c and pari_c and cote_c > 1:
                        selections.append({"match": match_c, "pari": pari_c, "cote": cote_c})
    
            strategie = st.radio("Stratégie", ["Kelly", "Demi-Kelly"], horizontal=True, key="strat_c")
    
            if selections:
                cotes = [s["cote"] for s in selections]
                cote = np.prod(cotes)
                proba = proba_estimee(cote)
                bankroll = get_bankroll()
                mise_kelly = kelly(bankroll, proba, cote)
                mise_finale = mise_kelly if strategie == "Kelly" else mise_kelly / 2
    
                st.success(f"🎯 Cote combinée : {cote:.2f} | Mise recommandée : {mise_finale:.2f} €")
    
            submitted_c = st.form_submit_button("✅ Enregistrer le combiné")
            if submitted_c and selections:
                match = "Combiné"
                sport = "Multi"
                type_pari = "Combiné"
                pari = " + ".join([f"{s['match']} - {s['pari']}" for s in selections])
    
                update_bankroll(-float(mise_finale))
                cursor.execute("""
                    INSERT INTO paris (match, sport, type, pari, cote, mise, strategie, resultat, gain)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Non joué', 0)
                """, (match, sport, type_pari, pari, round(float(cote), 2), round(float(mise_finale), 2), strategie))
                conn.commit()
                st.success("Combiné enregistré ✅")
                st.rerun()
    
    
    
    # --- Traitement des paris non joués ---
    st.markdown("---")
    st.markdown("### 🔧 Traiter les paris non joués")
    cursor.execute("SELECT id, match, pari, cote, mise FROM paris WHERE resultat = 'Non joué' ORDER BY date DESC")
    non_joues = cursor.fetchall()
    
    if non_joues:
        for pid, m, p, c, mise in non_joues:
            st.markdown(f"➡️ **{m}** - {p} @ {c} | Mise : {mise:.2f} €")
            col1, col2, col3 = st.columns(3)
    
            with col1:
                if st.button("✅ Gagné", key=f"g{pid}"):
                    gain = round(mise * c, 2)
                    update_bankroll(gain)
                    cursor.execute("UPDATE paris SET resultat = 'Gagné', gain = %s WHERE id = %s", (gain, pid))
                    conn.commit()
                    st.success("Pari mis à jour comme Gagné")
                    st.rerun()
    
            with col2:
                if st.button("❌ Perdu", key=f"p{pid}"):
                    cursor.execute("UPDATE paris SET resultat = 'Perdu', gain = 0 WHERE id = %s", (pid,))
                    conn.commit()
                    st.error("Pari mis à jour comme Perdu")
                    st.rerun()
    
            with col3:
                if st.button("🗑️ Annuler", key=f"a{pid}"):
                    update_bankroll(mise)  # On rembourse la mise
                    cursor.execute("DELETE FROM paris WHERE id = %s", (pid,))
                    conn.commit()
                    st.warning("Pari annulé et mise remboursée")
                    st.rerun()
    else:
        st.info("Aucun pari à traiter.")
    
    # --- Top Gagnés ---
    st.markdown("---")
    st.markdown("### 🏆 Top 3 gains")
    cursor.execute("SELECT match, pari, gain FROM paris WHERE resultat = 'Gagné' ORDER BY gain DESC LIMIT 3")
    gagnes = cursor.fetchall()
    for m, p, g in gagnes:
        st.markdown(f"✅ **{m}** - {p} : **+{g:.2f} €**")
    
    # --- Top Pertes ---
    st.markdown("### ❌ Top 3 pertes")
    cursor.execute("SELECT match, pari, mise FROM paris WHERE resultat = 'Perdu' ORDER BY mise DESC LIMIT 3")
    perdus = cursor.fetchall()
    for m, p, m_ in perdus:
        st.markdown(f"❌ **{m}** - {p} : **-{m_:.2f} €**")

with tab2:
    st.markdown("## 📊 Dashboard avancé – Aide à la décision")
    st.caption("Analyse complète pour comprendre et améliorer ta stratégie de paris 🔍")

    # LIGNE 1 : Analyse par SPORT
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown("**ROI par sport**")
        st.caption("Permet de mesurer la rentabilité de chaque sport. ROI = ((Gains - Mises) / Mises) × 100")
        cursor.execute("""
            SELECT sport, SUM(mise) AS mises, SUM(gain) AS gains
            FROM paris
            GROUP BY sport
        """)
        df_roi_sport = pd.DataFrame(cursor.fetchall(), columns=["Sport", "Mises (€)", "Gains (€)"])
        df_roi_sport["ROI (%)"] = ((df_roi_sport["Gains (€)"] - df_roi_sport["Mises (€)"]) / df_roi_sport["Mises (€)"]) * 100
        cols = st.columns(len(df_roi_sport))
        for i, row in df_roi_sport.iterrows():
            roi = row["ROI (%)"]
            color = "green" if roi >= 0 else "red"
            sign = "+" if roi >= 0 else ""
            cols[i].metric(row["Sport"], f"{sign}{roi:.1f} %")
    
    with col2:
        st.markdown("**Taux de réussite par sport**")
        st.caption("Pourcentage de paris gagnés sur l’ensemble des paris effectués par sport.")
        cursor.execute("""
            SELECT sport, COUNT(*) AS nb, 
                   SUM(CASE WHEN resultat = 'Gagné' THEN 1 ELSE 0 END) AS gagnes
            FROM paris
            GROUP BY sport
        """)
        rows = cursor.fetchall()
        df_taux_sport = pd.DataFrame(rows, columns=["Sport", "Nb Paris", "Gagnés"])
        df_taux_sport["Taux de réussite (%)"] = (df_taux_sport["Gagnés"] / df_taux_sport["Nb Paris"]) * 100
        df_taux_sport = df_taux_sport.sort_values(by="Taux de réussite (%)", ascending=False)
    
        fig2, ax2 = plt.subplots()
        bars = ax2.bar(df_taux_sport["Sport"], df_taux_sport["Taux de réussite (%)"], color="mediumseagreen")
        ax2.set_ylabel("Taux de réussite (%)")
        ax2.set_title("Taux de réussite par sport")
        ax2.bar_label(bars, fmt="%.1f%%", padding=3)
        fig2.tight_layout()
        st.pyplot(fig2)
    
    # LIGNE 2 : Analyse par TYPE
    col3, col4 = st.columns([1.2, 1])
    
    with col3:
        st.markdown("**ROI par type de pari**")
        st.caption("Permet de mesurer la rentabilité par type de pari joué.")
        cursor.execute("""
            SELECT type, SUM(mise) AS mises, SUM(gain) AS gains
            FROM paris
            GROUP BY type
        """)
        df_roi_type = pd.DataFrame(cursor.fetchall(), columns=["Type", "Mises (€)", "Gains (€)"])
        df_roi_type["ROI (%)"] = ((df_roi_type["Gains (€)"] - df_roi_type["Mises (€)"]) / df_roi_type["Mises (€)"]) * 100
    
        for _, row in df_roi_type.iterrows():
            roi = row["ROI (%)"]
            sign = "+" if roi >= 0 else ""
            color = "inverse" if roi > 0 else "off" if roi < 0 else "normal"
            st.metric(label=row["Type"], value=f"{sign}{roi:.1f} %", delta=None, delta_color=color)

    with col4:
        st.markdown("**Taux de réussite par type de pari**")
        st.caption("Part des paris gagnés selon leur typologie (ex : Over/Under, Vainqueur, etc.).")
        cursor.execute("""
            SELECT type, COUNT(*) AS nb,
                   SUM(CASE WHEN resultat = 'Gagné' THEN 1 ELSE 0 END) AS gagnes
            FROM paris
            GROUP BY type
        """)
        rows = cursor.fetchall()
        df_taux_type = pd.DataFrame(rows, columns=["Type", "Nb Paris", "Gagnés"])
        df_taux_type["Taux de réussite (%)"] = (df_taux_type["Gagnés"] / df_taux_type["Nb Paris"]) * 100
        df_taux_type = df_taux_type.sort_values(by="Taux de réussite (%)", ascending=False)
    
        fig4, ax4 = plt.subplots()
        bars = ax4.bar(df_taux_type["Type"], df_taux_type["Taux de réussite (%)"], color="mediumpurple")
        ax4.set_ylabel("Taux de réussite (%)")
        ax4.set_title("Taux de réussite par type de pari")
        ax4.bar_label(bars, fmt="%.1f%%", padding=3)
        fig4.tight_layout()
        st.pyplot(fig4)


    # LIGNE 3 : Risque (Cotes & Combinés)
    col5, col6 = st.columns([1.2, 1])
    
    with col5:
        st.markdown("**% de réussite par tranche de cote**")
        st.caption("Évalue ta performance selon les cotes jouées pour repérer ta zone de confort.")
        cursor.execute("SELECT cote, resultat FROM paris WHERE resultat IN ('Gagné', 'Perdu')")
        rows = cursor.fetchall()
        tranches = {
            "1.01–1.49": {"total": 0, "gagnés": 0},
            "1.50–1.99": {"total": 0, "gagnés": 0},
            "2.00–2.49": {"total": 0, "gagnés": 0},
            "2.50–2.99": {"total": 0, "gagnés": 0},
            "3.00+": {"total": 0, "gagnés": 0}
        }
        for cote, res in rows:
            if cote < 1.50:
                key = "1.01–1.49"
            elif cote < 2.00:
                key = "1.50–1.99"
            elif cote < 2.50:
                key = "2.00–2.49"
            elif cote < 3.00:
                key = "2.50–2.99"
            else:
                key = "3.00+"
            tranches[key]["total"] += 1
            if res == "Gagné":
                tranches[key]["gagnés"] += 1
    
        df_tranches = pd.DataFrame([
            [k, v["total"], v["gagnés"], (v["gagnés"] / v["total"]) * 100 if v["total"] else 0]
            for k, v in tranches.items()
        ], columns=["Tranche de cote", "Nb Paris", "Gagnés", "Taux de réussite (%)"])
    
        fig, ax = plt.subplots()
        bars = ax.bar(df_tranches["Tranche de cote"], df_tranches["Taux de réussite (%)"], color="cornflowerblue")
        ax.set_title("Taux de réussite par tranche de cote")
        ax.set_ylabel("% de réussite")
        ax.bar_label(bars, fmt="%.1f%%", padding=3)
        fig.tight_layout()
        st.pyplot(fig)
    
    with col6:
        st.markdown("**Simples vs combinés**")
        st.caption("Compare la rentabilité et la précision entre les paris simples et les combinés.")
        cursor.execute("""
            SELECT 
                CASE WHEN type = 'Combiné' THEN 'Combiné' ELSE 'Simple' END AS categorie,
                COUNT(*) AS nb,
                SUM(mise) AS mises,
                SUM(gain) AS gains,
                SUM(CASE WHEN resultat = 'Gagné' THEN 1 ELSE 0 END) AS gagnes
            FROM paris
            GROUP BY categorie
        """)
        rows = cursor.fetchall()
        df_simple_combine = pd.DataFrame(rows, columns=["Type", "Nb Paris", "Mises (€)", "Gains (€)", "Gagnés"])
        df_simple_combine["ROI (%)"] = ((df_simple_combine["Gains (€)"] - df_simple_combine["Mises (€)"]) / df_simple_combine["Mises (€)"]) * 100
        df_simple_combine["Taux de réussite (%)"] = (df_simple_combine["Gagnés"] / df_simple_combine["Nb Paris"]) * 100
    
        fig2, ax2 = plt.subplots()
        colors = ["green" if x >= 0 else "red" for x in df_simple_combine["ROI (%)"]]
        bars = ax2.barh(df_simple_combine["Type"], df_simple_combine["ROI (%)"], color=colors)
        ax2.set_title("ROI par type (Simple vs Combiné)")
        ax2.set_xlabel("ROI (%)")
        ax2.axvline(0, color="black", linewidth=0.8)
        ax2.bar_label(bars, fmt="%.1f", padding=3)
        fig2.tight_layout()
        st.pyplot(fig2)
    
    # LIGNE 4 : Comportement / Value
    col7, col8 = st.columns([1.2, 1])
    
    with col7:
        st.markdown("**Cote moyenne gagnés / perdus**")
        st.caption("Analyse si tu gagnes grâce à des value bets (grosses cotes) ou en jouant safe. Évalue ta prise de risque.")
        cursor.execute("""
            SELECT resultat, AVG(cote)
            FROM paris
            WHERE resultat IN ('Gagné', 'Perdu')
            GROUP BY resultat
        """)
        df_cote_moyenne = pd.DataFrame(cursor.fetchall(), columns=["Résultat", "Cote moyenne"])
        colg, colp = st.columns(2)
        with colg:
            val = df_cote_moyenne[df_cote_moyenne["Résultat"] == "Gagné"]["Cote moyenne"].values
            if len(val):
                st.metric("Cote moyenne gagnée", f"{val[0]:.2f}")
        with colp:
            val = df_cote_moyenne[df_cote_moyenne["Résultat"] == "Perdu"]["Cote moyenne"].values
            if len(val):
                st.metric("Cote moyenne perdue", f"{val[0]:.2f}")
    
    with col8:
        st.markdown("**Taux de réussite par niveau de mise**")
        st.caption("Montre si tu es plus performant avec petites ou grosses mises. Aide à ajuster ta gestion de bankroll.")
        cursor.execute("""
            SELECT
                CASE
                    WHEN mise < 5 THEN '0–5'
                    WHEN mise < 10 THEN '5–10'
                    WHEN mise < 20 THEN '10–20'
                    ELSE '20+'
                END AS tranche,
                COUNT(*) AS nb,
                SUM(CASE WHEN resultat = 'Gagné' THEN 1 ELSE 0 END) AS gagnes
            FROM paris
            GROUP BY tranche
            ORDER BY tranche
        """)
        df_mises = pd.DataFrame(cursor.fetchall(), columns=["Tranche de mise (€)", "Nb Paris", "Gagnés"])
        df_mises["Taux de réussite (%)"] = (df_mises["Gagnés"] / df_mises["Nb Paris"]) * 100
    
        fig4, ax4 = plt.subplots()
        bars = ax4.bar(df_mises["Tranche de mise (€)"], df_mises["Taux de réussite (%)"], color="mediumslateblue")
        ax4.set_title("Taux de réussite par tranche de mise")
        ax4.set_ylabel("% de réussite")
        ax4.bar_label(bars, fmt="%.1f%%", padding=3)
        fig4.tight_layout()
        st.pyplot(fig4)
    
    # LIGNE 5 : Argent engagé
    col9, col10 = st.columns([1.2, 1])
    
    with col9:
        st.markdown("**Gain net par sport**")
        st.caption("Affiche le gain ou la perte en € pour chaque sport. Permet d’identifier ce qui rapporte réellement.")
        cursor.execute("""
            SELECT sport, SUM(mise) AS mises, SUM(gain) AS gains
            FROM paris
            GROUP BY sport
        """)
        df_gain_sport = pd.DataFrame(cursor.fetchall(), columns=["Sport", "Mises (€)", "Gains (€)"])
        df_gain_sport["Gain net (€)"] = df_gain_sport["Gains (€)"] - df_gain_sport["Mises (€)"]
    
        # Affichage avec couleur conditionnelle
        metrics = df_gain_sport.set_index("Sport")["Gain net (€)"].to_dict()
        cols = st.columns(len(metrics))
        for i, (sport, gain) in enumerate(metrics.items()):
            sign = "+" if gain >= 0 else ""
            color = "normal" if gain == 0 else "inverse" if gain > 0 else "off"
            cols[i].metric(label=sport, value=f"{sign}{gain:.0f} €", delta=None, delta_color=color)

    with col10:
        st.markdown("**Répartition des mises par type**")
        st.caption("Visualise où tu places ton argent selon les types de paris. Aide à aligner l’investissement avec les performances.")
        cursor.execute("""
            SELECT type AS "Type de pari", SUM(mise) AS "Total Mises (€)"
            FROM paris
            GROUP BY type
        """)
        df_repartition_mises = pd.DataFrame(cursor.fetchall(), columns=["Type de pari", "Total Mises (€)"])
    
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            df_repartition_mises["Total Mises (€)"],
            labels=df_repartition_mises["Type de pari"],
            autopct='%1.1f%%',
            startangle=140,
            wedgeprops=dict(width=0.4),
            textprops=dict(color="black")
        )
        ax.set_title("Répartition des mises par type")
        ax.axis("equal")
        st.pyplot(fig)



