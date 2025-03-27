# -*- coding: utf-8 -*-
"""RecupMatchs.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1G7K70fXhKwbOc0-FLdrxbVrAsrpZNxOo

## **Vide les tables**
"""

import requests
import psycopg2
from datetime import datetime, timedelta


# 🔑 Clé API SportsData.io
API_KEY = "f5dfafaf901b41b0898c6277c72300ea"

today = datetime.today().date()
yesterday = today - timedelta(days=1)

# 🏆 Liste des compétitions à récupérer
COMPETITIONS = {
    "Premier League": "1",
    "Bundesliga": "2",
    "La Liga": "4",
    "Serie A": "6",
    "Ligue 1": "13",
    "UEFA Champions League": "3",
    "UEFA Europa League": "9",
    "UEFA Europa Conference League": "55",
    "Eredivisie": "7",
    "2. Bundesliga": "74",
    "Saudi Professional League": "50"
}

# 🔌 Connexion PostgreSQL Railway
DATABASE_URL = "postgresql://postgres:jDDqfaqpspVDBBwsqxuaiSDNXjTxjMmP@shortline.proxy.rlwy.net:36536/railway"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

def to_float(x):
    try:
        return float(x)
    except:
        return 0.0

print("Fin de la défintion de variables")

"""# **📌 1️⃣ Récupération des Matchs**"""

def recuperer_matchs(date, API_KEY):
  # Récupère les matchs du jour et les insère dans la table 'matchs'.
  for competition_name, competition_id in COMPETITIONS.items():
      #print(f"🔍 Récupération des matchs pour {competition_name} ({competition_id})...")

      # 🔗 URL API pour récupérer les matchs
      url = f"https://api.sportsdata.io/v4/soccer/scores/json/GamesByDate/{competition_id}/{date}?key={API_KEY}"
      response = requests.get(url)

      if response.status_code == 200:
          data = response.json()

          if not data:  # Vérifier si la liste est vide
              #print(f"⚠️ Aucun match trouvé pour {competition_name} ({competition_id})")
              continue

          for match in data:
              game_id = match["GameId"]
              saison = datetime.strptime(match["DateTime"], "%Y-%m-%dT%H:%M:%S").year
              date_match = match["DateTime"]
              statut = match["Status"]
              equipe_domicile = match["HomeTeamName"]
              equipe_exterieur = match["AwayTeamName"]
              competition = competition_name

              # 🏆 Insérer dans la table matchs
              cursor.execute("""
                  INSERT INTO matchs (game_id, saison, date, statut, equipe_domicile, equipe_exterieur, competition)
                  VALUES (%s, %s, %s, %s, %s, %s, %s)
                  ON CONFLICT (game_id) DO NOTHING
              """, (game_id, saison, date_match, statut, equipe_domicile, equipe_exterieur, competition))

      else:
          print(f"❌ Erreur API pour {competition_name} ({competition_id}) : {response.status_code}")

  # ✅ Confirmer l'insertion
  conn.commit()
  print("✅ Données des matchs insérées avec succès !")

"""# **📌 2️⃣ Récupération des Statistiques des Matchs**"""

# Fonction de conversion sécurisée
import math

def convert_to_int(value):
    """Convertit une valeur en int, arrondie à l'entier inférieur sauf si cela tombe en dessous de 0."""
    try:
        x = float(value)
        return max(math.floor(x), 0)  # Arrondi en bas, mais pas en dessous de 0
    except (ValueError, TypeError):
        return 0  # Retourne 0 si la donnée est invalide

def recuperer_stats_matchs(date, API_KEY):
  # Récupère les statistiques des matchs et les insère dans la table 'stats_matchs'.
  for competition_name, competition_id in COMPETITIONS.items():
      #print(f"🔍 Récupération des statistiques pour {competition_name} ({competition_id})...")

      # 🔗 URL API pour récupérer les stats des matchs
      url = f"https://api.sportsdata.io/v4/soccer/stats/json/TeamGameStatsByDateFinal/{competition_id}/{date}?key={API_KEY}"
      response = requests.get(url)

      if response.status_code == 200:
          data = response.json()

          if not data:
              #print(f"⚠️ Aucune statistique trouvée pour {competition_name} ({competition_id})")
              continue

          match_stats = {}
          for stats in data:
              game_id = stats["GameId"]
              team_id = stats["TeamId"]

              if game_id not in match_stats:
                  match_stats[game_id] = {}
              match_stats[game_id][team_id] = stats

          for game_id, teams in match_stats.items():
              if len(teams) == 2:
                  team_ids = list(teams.keys())
                  stats_dom = teams[team_ids[0]]
                  stats_ext = teams[team_ids[1]]

                  # Création des valeurs avec conversion en int
                  values = (
                      convert_to_int(game_id),
                      convert_to_int(stats_dom.get("Possession")), convert_to_int(stats_ext.get("Possession")),
                      convert_to_int(stats_dom.get("Shots")), convert_to_int(stats_ext.get("Shots")),
                      convert_to_int(stats_dom.get("ShotsOnGoal")), convert_to_int(stats_ext.get("ShotsOnGoal")),
                      convert_to_int(stats_dom.get("Goals")), convert_to_int(stats_ext.get("Goals")),
                      convert_to_int(stats_dom.get("Passes")), convert_to_int(stats_ext.get("Passes")),
                      convert_to_int(stats_dom.get("PassesCompleted")), convert_to_int(stats_ext.get("PassesCompleted")),
                      convert_to_int(stats_dom.get("CornersWon")), convert_to_int(stats_ext.get("CornersWon")),
                      convert_to_int(stats_dom.get("Fouls")), convert_to_int(stats_ext.get("Fouls")),
                      convert_to_int(stats_dom.get("Offsides")), convert_to_int(stats_ext.get("Offsides")),
                      convert_to_int(stats_dom.get("YellowCards")), convert_to_int(stats_ext.get("YellowCards")),
                      convert_to_int(stats_dom.get("RedCards")), convert_to_int(stats_ext.get("RedCards")),
                      convert_to_int(stats_dom.get("Interceptions")), convert_to_int(stats_ext.get("Interceptions")),
                      convert_to_int(stats_dom.get("Tackles")), convert_to_int(stats_ext.get("Tackles"))
                  )

                  # Debugging: Affichage des valeurs AVANT insertion
                  #print(f"📝 Tentative d'insertion pour game_id {game_id}")
                  #print(f"📥 Values: {values}")
                  #print(f"📥 Values insérées: {values}")
                  #for i, v in enumerate(values):
                      #print(f"Index {i}: {v} (Type: {type(v)})")


                  # Requête SQL
                  query = """
                      INSERT INTO stats_matchs (
                                  game_id, possession_dom, possession_ext,
                                  tirs_dom, tirs_ext, tirs_cadres_dom, tirs_cadres_ext, buts_dom, buts_ext,
                                  passes_dom, passes_ext, passes_reussies_dom, passes_reussies_ext,
                                  corners_dom, corners_ext, fautes_dom, fautes_ext,
                                  hors_jeu_dom, hors_jeu_ext, cartons_jaunes_dom, cartons_jaunes_ext,
                                  cartons_rouges_dom, cartons_rouges_ext, interceptions_dom, interceptions_ext,
                                  tacles_dom, tacles_ext
                              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                              ON CONFLICT (game_id) DO NOTHING
                  """

                  try:
                      cursor.execute(query, values)
                  except Exception as e:
                      print(f"❌ Erreur lors de l'insertion des données pour game_id {game_id}: {e}")

  # ✅ Confirmer l'insertion
  conn.commit()
  print("✅ Données des statistiques insérées avec succès !")

"""# **📌 3️⃣ Récupération des Cotes**"""

def recuperer_cotes(date, API_KEY):
    for competition_name, competition_id in COMPETITIONS.items():
        url = f"https://api.sportsdata.io/v4/soccer/odds/json/GameOddsByDate/{competition_id}/{date}?key={API_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            for match in data:
                game_id = match["GameId"]

                cursor.execute("SELECT game_id FROM matchs WHERE game_id = %s", (game_id,))
                match_row = cursor.fetchone()

                if match_row:
                    id_match = match_row[0]

                    cursor.execute("SELECT COUNT(*) FROM cotes WHERE game_id = %s", (game_id,))
                    cote_existante = cursor.fetchone()[0]

                    if cote_existante == 0:
                        for odd in match.get("PregameOdds", [])[:1]:

                            cote_domicile = 1 + (odd["HomeMoneyLine"] / 100) if odd["HomeMoneyLine"] and odd["HomeMoneyLine"] > 0 else 1 + (100 / abs(odd["HomeMoneyLine"])) if odd["HomeMoneyLine"] else None
                            cote_nul = 1 + (odd["DrawMoneyLine"] / 100) if odd["DrawMoneyLine"] and odd["DrawMoneyLine"] > 0 else 1 + (100 / abs(odd["DrawMoneyLine"])) if odd["DrawMoneyLine"] else None
                            cote_exterieur = 1 + (odd["AwayMoneyLine"] / 100) if odd["AwayMoneyLine"] and odd["AwayMoneyLine"] > 0 else 1 + (100 / abs(odd["AwayMoneyLine"])) if odd["AwayMoneyLine"] else None

                            cote_double_chance_1N = 1 / ((1 / cote_domicile) + (1 / cote_nul)) if cote_domicile and cote_nul else None
                            cote_double_chance_12 = 1 / ((1 / cote_domicile) + (1 / cote_exterieur)) if cote_domicile and cote_exterieur else None
                            cote_double_chance_X2 = 1 / ((1 / cote_exterieur) + (1 / cote_nul)) if cote_exterieur and cote_nul else None

                            over_under_ligne = odd.get("OverUnder")

                            cote_over = None
                            cote_under = None

                            if odd.get("OverPayout") is not None and odd["OverPayout"] != 0:
                                cote_over = 1 + (odd["OverPayout"] / 100) if odd["OverPayout"] > 0 else 1 + (100 / abs(odd["OverPayout"]))
                            else:
                                cote_over = None  # Ou définir une valeur par défaut

                            if odd.get("UnderPayout") is not None and odd["UnderPayout"] != 0:
                                cote_under = 1 + (odd["UnderPayout"] / 100) if odd["UnderPayout"] > 0 else 1 + (100 / abs(odd["UnderPayout"]))
                            else:
                                cote_under = None  # Ou définir une valeur par défaut


                            cursor.execute("""
                                INSERT INTO cotes (game_id, cote_domicile, cote_nul, cote_exterieur,
                                                  cote_double_chance_1N, cote_double_chance_12, cote_double_chance_X2,
                                                  over_under_ligne, cote_over, cote_under)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (game_id) DO NOTHING
                            """, (game_id, cote_domicile, cote_nul, cote_exterieur,
                                  cote_double_chance_1N, cote_double_chance_12, cote_double_chance_X2,
                                  over_under_ligne, cote_over, cote_under))

                            conn.commit()

                    else:
                        print(f"⚠️ Cotes déjà existantes pour le match {game_id} ({competition_name}). Aucune insertion.")

                else:
                    print(f"⚠️ Match {game_id} non trouvé dans la table matchs. Impossible d'insérer les cotes.")

        else:
            print(f"❌ Erreur API SportsData.io ({competition_name}) : {response.status_code}")

    print("✅ Intégration complète des cotes depuis SportsData.io terminée pour toutes les compétitions !")

def mettre_a_jour_stats_globales(date_reference):
    print("📊 Mise à jour des stats globales des équipes ayant joué le", date_reference)

    # Récupère les équipes concernées par des matchs hier
    cursor.execute("""
        SELECT DISTINCT m.saison, m.competition, m.equipe_domicile AS equipe
        FROM matchs m
        JOIN stats_matchs s ON m.game_id = s.game_id
        WHERE m.date::date = %s
        UNION
        SELECT DISTINCT m.saison, m.competition, m.equipe_exterieur AS equipe
        FROM matchs m
        JOIN stats_matchs s ON m.game_id = s.game_id
        WHERE m.date::date = %s
    """, (date_reference, date_reference))
    equipes = cursor.fetchall()

    for saison, competition, equipe in equipes:
        cursor.execute("""
            SELECT m.game_id, m.equipe_domicile, m.equipe_exterieur,
                   s.buts_dom, s.buts_ext, s.tirs_dom, s.tirs_ext, s.tirs_cadres_dom, s.tirs_cadres_ext,
                   s.possession_dom, s.possession_ext, s.passes_reussies_dom, s.passes_reussies_ext,
                   s.corners_dom, s.corners_ext, s.cartons_jaunes_dom, s.cartons_jaunes_ext,
                   s.cartons_rouges_dom, s.cartons_rouges_ext, s.interceptions_dom, s.interceptions_ext,
                   s.tacles_dom, s.tacles_ext, s.fautes_dom, s.fautes_ext, s.hors_jeu_dom, s.hors_jeu_ext
            FROM matchs m
            JOIN stats_matchs s ON m.game_id = s.game_id
            WHERE m.saison = %s AND m.competition = %s
              AND (m.equipe_domicile = %s OR m.equipe_exterieur = %s)
        """, (saison, competition, equipe, equipe))
        matchs = cursor.fetchall()

        if not matchs:
            continue

        total = {
            "matchs_joues": 0, "victoires": 0, "nuls": 0, "defaites": 0,
            "buts_marques": 0, "buts_encaisse": 0, "difference_buts": 0,
            "tirs": 0, "tirs_cadres": 0, "possession": 0, "passes_reussies": 0,
            "corners": 0, "cartons_jaunes": 0, "cartons_rouges": 0,
            "interceptions": 0, "tacles": 0, "fautes": 0, "hors_jeu": 0,
            "btts": 0, "over_2_5": 0, "over_1_5": 0, "clean_sheets": 0
        }

        for match in matchs:
            (
                game_id, dom, ext, bdom, bext, tirs_dom, tirs_ext, tirs_cadres_dom, tirs_cadres_ext,
                pos_dom, pos_ext, pass_dom, pass_ext,
                corners_dom, corners_ext, jaunes_dom, jaunes_ext,
                rouges_dom, rouges_ext, inter_dom, inter_ext,
                tacles_dom, tacles_ext, fautes_dom, fautes_ext, hj_dom, hj_ext
            ) = match

            est_domicile = (equipe == dom)

            buts_marques = bdom if est_domicile else bext
            buts_encaisse = bext if est_domicile else bdom

            total["matchs_joues"] += 1
            total["buts_marques"] += buts_marques
            total["buts_encaisse"] += buts_encaisse
            total["difference_buts"] += (buts_marques - buts_encaisse)

            total["victoires"] += int(buts_marques > buts_encaisse)
            total["nuls"] += int(buts_marques == buts_encaisse)
            total["defaites"] += int(buts_marques < buts_encaisse)

            total["tirs"] += tirs_dom if est_domicile else tirs_ext
            total["tirs_cadres"] += tirs_cadres_dom if est_domicile else tirs_cadres_ext
            total["possession"] += pos_dom if est_domicile else pos_ext
            total["passes_reussies"] += pass_dom if est_domicile else pass_ext
            total["corners"] += corners_dom if est_domicile else corners_ext
            total["cartons_jaunes"] += jaunes_dom if est_domicile else jaunes_ext
            total["cartons_rouges"] += rouges_dom if est_domicile else rouges_ext
            total["interceptions"] += inter_dom if est_domicile else inter_ext
            total["tacles"] += tacles_dom if est_domicile else tacles_ext
            total["fautes"] += fautes_dom if est_domicile else fautes_ext
            total["hors_jeu"] += hj_dom if est_domicile else hj_ext

            if bdom > 0 and bext > 0:
                total["btts"] += 1
            if (bdom + bext) > 2.5:
                total["over_2_5"] += 1
            if (bdom + bext) > 1.5:
                total["over_1_5"] += 1
            if buts_encaisse == 0:
                total["clean_sheets"] += 1

        def avg(val):
            return round(val / total["matchs_joues"], 2)

        insert_values = (
            equipe, competition, saison,
            total["matchs_joues"], total["victoires"], total["nuls"], total["defaites"],
            total["buts_marques"], total["buts_encaisse"], total["difference_buts"],
            total["tirs"], total["tirs_cadres"], avg(total["possession"]),
            avg(total["passes_reussies"]), total["corners"], total["cartons_jaunes"],
            total["cartons_rouges"], total["interceptions"], total["tacles"],
            total["fautes"], total["hors_jeu"],
            avg(total["buts_marques"]),
            round(100 * total["btts"] / total["matchs_joues"], 2),
            round(100 * total["over_2_5"] / total["matchs_joues"], 2),
            round(100 * total["over_1_5"] / total["matchs_joues"], 2),
            round(100 * total["clean_sheets"] / total["matchs_joues"], 2)
        )

        cursor.execute("""
            INSERT INTO stats_globales (
                equipe, competition, saison, matchs_joues, victoires, nuls, defaites,
                buts_marques, buts_encaisse, difference_buts, tirs, tirs_cadres, possession,
                passes_reussies, corners, cartons_jaunes, cartons_rouges, interceptions,
                tacles, fautes, hors_jeu, moyenne_buts, pourcentage_BTTS, pourcentage_over_2_5,
                pourcentage_over_1_5, pourcentage_clean_sheets
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (equipe, competition, saison)
            DO UPDATE SET
                matchs_joues = EXCLUDED.matchs_joues,
                victoires = EXCLUDED.victoires,
                nuls = EXCLUDED.nuls,
                defaites = EXCLUDED.defaites,
                buts_marques = EXCLUDED.buts_marques,
                buts_encaisse = EXCLUDED.buts_encaisse,
                difference_buts = EXCLUDED.difference_buts,
                tirs = EXCLUDED.tirs,
                tirs_cadres = EXCLUDED.tirs_cadres,
                possession = EXCLUDED.possession,
                passes_reussies = EXCLUDED.passes_reussies,
                corners = EXCLUDED.corners,
                cartons_jaunes = EXCLUDED.cartons_jaunes,
                cartons_rouges = EXCLUDED.cartons_rouges,
                interceptions = EXCLUDED.interceptions,
                tacles = EXCLUDED.tacles,
                fautes = EXCLUDED.fautes,
                hors_jeu = EXCLUDED.hors_jeu,
                moyenne_buts = EXCLUDED.moyenne_buts,
                pourcentage_BTTS = EXCLUDED.pourcentage_BTTS,
                pourcentage_over_2_5 = EXCLUDED.pourcentage_over_2_5,
                pourcentage_over_1_5 = EXCLUDED.pourcentage_over_1_5,
                pourcentage_clean_sheets = EXCLUDED.pourcentage_clean_sheets
        """, insert_values)

    conn.commit()
    print("✅ stats_globales mise à jour avec succès !")


recuperer_matchs(today, API_KEY)
recuperer_stats_matchs(yesterday, API_KEY)
recuperer_cotes(today, API_KEY)
mettre_a_jour_stats_globales(yesterday)

conn.commit()

print("✅ Récupération des données terminée !")

"""## **Envoie de mail et execution des fonction de récupération de données**"""

import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, to_email):
    from_email = "lilian.pamphile.bts@gmail.com"
    password = "fifkktsenfxsqiob"  # mot de passe d'application

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
        print("📬 Email envoyé avec succès.")
    except Exception as e:
        print("❌ Erreur lors de l'envoi de l'email :", e)

import os
import requests
import pickle

# --- Téléchargement des fichiers modèle/scaler depuis GitHub ---
def telecharger_model_depuis_github():
    # Infos du repo
    REPO = "LilianPamphile/paris-sportifs"
    BRANCH = "main"
    TOKEN = "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"

    # Liste des fichiers à télécharger (avec chemin dans le repo GitHub)
    fichiers = {
        "model_files/model_over25.pkl": "model_files/model_over25.pkl",
        "model_files/scaler_over25.pkl": "model_files/scaler_over25.pkl"
    }

    for chemin_dist, chemin_local in fichiers.items():
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{chemin_dist}"
        headers = {"Authorization": f"token {TOKEN}"}

        # Crée le dossier local si besoin
        dossier = os.path.dirname(chemin_local)
        if not os.path.exists(dossier):
            os.makedirs(dossier)

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(chemin_local, "wb") as f:
                f.write(response.content)
            print(f"✅ Fichier téléchargé : {chemin_local}")
        else:
            print(f"❌ Échec du téléchargement de {chemin_local} ({response.status_code})")

################################################################

try:
    recuperer_matchs(today, API_KEY)
    recuperer_stats_matchs(yesterday, API_KEY)
    recuperer_cotes(today, API_KEY)

    telecharger_model_depuis_github()

    conn.commit()

    print("✅ Récupération des données terminée !")

       # === Chargement du modèle ML et scaler ===
    with open("model_files/model_over25.pkl", "rb") as f:
        model_ml = pickle.load(f)
    with open("model_files/scaler_over25.pkl", "rb") as f:
        scaler_ml = pickle.load(f)

    # === Fonction pour récupérer les matchs du jour ===
    def get_matchs_jour_for_prediction():
        cursor = conn.cursor()
        query = """
            SELECT 
                m.game_id,
                m.equipe_domicile, m.equipe_exterieur,
                sg1.moyenne_buts, sg1.pourcentage_over_2_5, sg1.pourcentage_BTTS,
                sg1.tirs_cadres, sg1.possession, sg1.corners, sg1.fautes, sg1.cartons_jaunes, sg1.cartons_rouges,
                sg2.moyenne_buts, sg2.pourcentage_over_2_5, sg2.pourcentage_BTTS,
                sg2.tirs_cadres, sg2.possession, sg2.corners, sg2.fautes, sg2.cartons_jaunes, sg2.cartons_rouges,
                c.cote_over
            FROM matchs m
            JOIN stats_globales sg1 ON m.equipe_domicile = sg1.equipe
            JOIN stats_globales sg2 ON m.equipe_exterieur = sg2.equipe
            JOIN cotes c ON m.game_id = c.game_id
            WHERE DATE(m.date) = %s AND c.cote_over IS NOT NULL
        """

        cursor.execute(query, (today,))
        rows = cursor.fetchall()
        matchs = []
        seen_game_ids = set()
    
        for row in rows:
            game_id = row[0]
            if game_id in seen_game_ids:
                continue
            seen_game_ids.add(game_id)
        
            (
                _,
                dom, ext,
                buts_dom, over25_dom, btts_dom, tirs_dom, poss_dom, corners_dom, fautes_dom, cj_dom, cr_dom,
                buts_ext, over25_ext, btts_ext, tirs_ext, poss_ext, corners_ext, fautes_ext, cj_ext, cr_ext,
                cote_over
            ) = row
    
            tirs_cadres = to_float(tirs_dom) + to_float(tirs_ext)
            possession = to_float(poss_dom) + to_float(poss_ext)
            corners_fautes = (
                to_float(corners_dom) + to_float(corners_ext) +
                to_float(fautes_dom) + to_float(fautes_ext)
            )
            cartons = (
                to_float(cj_dom) + to_float(cj_ext) +
                2 * to_float(cr_dom) + 2 * to_float(cr_ext)
            )
    
            score_heuristique = (
                0.20 * (to_float(buts_dom) + to_float(buts_ext)) +
                0.20 * (to_float(over25_dom) + to_float(over25_ext)) +
                0.15 * (to_float(btts_dom) + to_float(btts_ext)) +
                0.10 * tirs_cadres +
                0.15 * (2.5 / float(to_float(cote_over) or 2.5)) +
                0.05 * possession +
                0.05 * corners_fautes +
                0.05 * cartons
            )
    
            features = [
                to_float(buts_dom), to_float(buts_ext),
                to_float(over25_dom), to_float(over25_ext),
                to_float(btts_dom), to_float(btts_ext),
                tirs_cadres, possession, corners_fautes, cartons,
                to_float(cote_over), score_heuristique
            ]
    
            matchs.append({
                "match": f"{dom} vs {ext}",
                "features": features,
                "score_heuristique": round(score_heuristique, 2),
                "cote_over": to_float(cote_over)
            })
    
        cursor.close()
        return matchs

    # === Prédiction ML ===
    matchs_jour = get_matchs_jour_for_prediction()
    X_live = scaler_ml.transform([m["features"] for m in matchs_jour])
    probas = model_ml.predict_proba(X_live)[:, 1]

    # === Classement + Value Bet ===
    over_matches = []
    under_matches = []

    for i, match in enumerate(matchs_jour):
        proba_ml = probas[i]
        cote = match['cote_over']
        proba_cote = 1 / cote if cote else 0
        is_value_bet = proba_ml > proba_cote

        line = (
            f"- {match['match']} | Heuristique: {match['score_heuristique']} | "
            f"Proba ML: {round(proba_ml*100, 1)}% | Cote Over: {cote}"
        )
        if is_value_bet:
            line += " 💰 Value Bet"

        if proba_ml >= 0.5:
            over_matches.append((proba_ml, line))
        else:
            under_matches.append((proba_ml, line))

    # Trier & limiter à 5
    over_matches.sort(reverse=True)
    under_matches.sort()

    top_over = [line for _, line in over_matches[:5]]
    top_under = [line for _, line in under_matches[:5]]

    # === Construction contenu du mail ===
    mail_lines = ["📈 MATCHS À BUTS (Over 2.5 probables)\n"]
    
    if top_over:
        mail_lines.extend(top_over)
    else:
        mail_lines.append("Aucun match fort en buts aujourd’hui. ❄️")
    
    mail_lines.append("\n🔒 MATCHS FERMÉS (Under 2.5 probables)\n")
    
    if top_under:
        for line in top_under:
            # On récupère la proba ML depuis la ligne
            proba_str = line.split("Proba ML: ")[1].split("%")[0]
            proba_ml = float(proba_str.replace(",", ".")) / 100
            proba_under = round((1 - proba_ml) * 100, 1)
    
            # Ajout de l'indicateur visuel avec emojis
            if proba_ml >= 0.8:
                emoji_bar = "🔥⚽⚽⚽🔥"
            elif proba_ml >= 0.6:
                emoji_bar = "⚽⚽⚽"
            elif proba_ml >= 0.4:
                emoji_bar = "⚽⚽"
            elif proba_ml >= 0.2:
                emoji_bar = "⚽"
            else:
                emoji_bar = "⚪"
    
            # Nettoyer la ligne et ajouter la synthèse
            line_clean = line.split(" |")[0]  # Supprime tout après le nom du match
            new_line = f"{line_clean} | 🔻 {proba_under}% de chance d'être en dessous de 2.5 {emoji_bar}"
            mail_lines.append(new_line)
    else:
        mail_lines.append("Aucun match fermé détecté.")
    
    mail_content = "\n".join(mail_lines)
    
    send_email(
        subject="🔥 Analyse Matchs Over/Under - Score, Proba ML & Value Bets",
        body=f"Voici les prévisions du {today} :\n\n{mail_content}",
        to_email="lilian.pamphile.bts@gmail.com"
    )

except Exception as e:
    # Si une erreur survient à n’importe quelle cellule
    error_message = f"❌ Erreur durant l’exécution du script Match_historique du {today} :\n\n{str(e)}"
    send_email(
        subject="❌ Échec - Script Match_historique",
        body=error_message,
        to_email="lilian.pamphile.bts@gmail.com"
    )
