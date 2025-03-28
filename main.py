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
import math
import smtplib
from email.mime.text import MIMEText

# 🔑 Clé API SportsData.io
API_KEY = "f5dfafaf901b41b0898c6277c72300ea"

# 📅 Dates utiles
today = datetime.today().date()
yesterday = today - timedelta(days=1)

# 🏆 Liste des compétitions
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

# 🔌 Connexion PostgreSQL
DATABASE_URL = "postgresql://postgres:jDDqfaqpspVDBBwsqxuaiSDNXjTxjMmP@shortline.proxy.rlwy.net:36536/railway"
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("Fin de la défintion de variables")

# === Récupération des matchs ===
def recuperer_matchs(date, API_KEY):
    for competition_name, competition_id in COMPETITIONS.items():
        url = f"https://api.sportsdata.io/v4/soccer/scores/json/GamesByDate/{competition_id}/{date}?key={API_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if not data:
                continue

            for match in data:
                game_id = match["GameId"]
                saison = datetime.strptime(match["DateTime"], "%Y-%m-%dT%H:%M:%S").year
                date_match = match["DateTime"]
                statut = match["Status"]
                equipe_domicile = match["HomeTeamName"]
                equipe_exterieur = match["AwayTeamName"]
                competition = competition_name

                cursor.execute("""
                    INSERT INTO matchs (game_id, saison, date, statut, equipe_domicile, equipe_exterieur, competition)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (game_id) DO NOTHING
                """, (game_id, saison, date_match, statut, equipe_domicile, equipe_exterieur, competition))
        else:
            print(f"❌ Erreur API pour {competition_name} ({competition_id}) : {response.status_code}")

    conn.commit()
    print("✅ Données des matchs insérées avec succès !")

# === Récupération des stats ===
def convert_to_int(value):
    try:
        x = float(value)
        return max(math.floor(x), 0)
    except (ValueError, TypeError):
        return 0

def recuperer_stats_matchs(date, API_KEY):
    for competition_name, competition_id in COMPETITIONS.items():
        url = f"https://api.sportsdata.io/v4/soccer/stats/json/TeamGameStatsByDateFinal/{competition_id}/{date}?key={API_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if not data:
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
                        print(f"❌ Erreur pour game_id {game_id}: {e}")

    conn.commit()
    print("✅ Données des statistiques insérées avec succès !")

# === Envoi Email ===
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

# === Main execution ===
try:
    recuperer_matchs(today, API_KEY)
    recuperer_stats_matchs(yesterday, API_KEY)

    conn.commit()
    print("✅ Récupération des données terminée !")

    send_email(
        subject="✅ Succès - Script de récupération des matchs",
        body=f"Le script s'est exécuté avec succès le {today}.",
        to_email="lilian.pamphile.bts@gmail.com"
    )

except Exception as e:
    error_message = f"❌ Erreur durant l’exécution du script Match_historique du {today} :\n\n{str(e)}"
    send_email(
        subject="❌ Échec - Script Match_historique",
        body=error_message,
        to_email="lilian.pamphile.bts@gmail.com"
    )
