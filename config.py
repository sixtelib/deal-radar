"""
Configuration du Deal Radar.
Modifie les valeurs ci-dessous pour ajuster tes critères sans toucher au reste du code.
"""
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # en production (Render/Railway), les variables d'env sont déjà injectées

# --------------------------------------------------------------------------
# 1. TES CRITÈRES D'ACQUISITION
# --------------------------------------------------------------------------

@dataclass
class Criteria:
    # Départements Île-de-France (codes INSEE) — utilisé pour repérer la région
    # même quand l'annonce ne dit pas explicitement "Île-de-France".
    idf_departements: tuple = ("75", "77", "78", "91", "92", "93", "94", "95")
    idf_keywords: tuple = ("ile-de-france", "île-de-france", "ile de france", "île de france")

    ca_min_keur: int = 500       # CA minimum, en k€
    ca_max_keur: int = 1000      # CA maximum, en k€

    raison_cession_keywords: tuple = ("retraite",)

    apport_max_keur: int = 150   # Apport en fonds propres maximum accepté, en k€

    # Si un champ est absent de l'annonce (souvent le cas pour l'apport ou le CA
    # sur les teasers), on ne rejette pas l'annonce : on la garde en "à vérifier"
    # plutôt que de risquer de rater une bonne opportunité par manque de données.


CRITERIA = Criteria()

# --------------------------------------------------------------------------
# 2. SOURCES À SURVEILLER
# --------------------------------------------------------------------------
# Renseigne ici les URLs de résultats de recherche DÉJÀ FILTRÉES sur le site
# (région + secteur si tu veux), copiées depuis ta barre d'adresse après avoir
# fait une recherche manuelle. Le scraper se contente ensuite d'ouvrir chaque
# annonce trouvée sur ces pages et d'appliquer le filtre financier.
#
# Ça évite de deviner l'API/les paramètres de recherche de chaque site, qui
# changent régulièrement.

SEARCH_SOURCES = [
    {
        "name": "fusacq",
        "search_urls": [
            # Exemple — remplace par tes propres résultats de recherche filtrés
            # "https://www.fusacq.com/acheter-une-entreprise/ile-de-france",
        ],
        "detail_link_pattern": r"/annonce[s]?[-/][a-z0-9-]+",
    },
    {
        "name": "transentreprise",
        "search_urls": [
            # "https://www.transentreprise.com/recherche?region=ile-de-france",
        ],
        "detail_link_pattern": r"/annonce[s]?/\d+",
    },
]

# --------------------------------------------------------------------------
# 3. NOTIFICATION EMAIL (variables d'environnement — ne rien mettre en dur ici)
# --------------------------------------------------------------------------

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ALERT_EMAIL_TO = os.environ.get("ALERT_EMAIL_TO", "")
ALERT_EMAIL_FROM = os.environ.get("ALERT_EMAIL_FROM", SMTP_USER)

# --------------------------------------------------------------------------
# 4. DIVERS
# --------------------------------------------------------------------------

REQUEST_DELAY_SECONDS = 3          # Pause entre deux requêtes (courtoisie / anti-blocage)
USER_AGENT = "Mozilla/5.0 (compatible; DealRadarPersonal/1.0; usage prive non-commercial)"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SEEN_STORE_PATH = os.path.join(DATA_DIR, "seen.json")
OUTPUT_HTML_PATH = os.path.join(os.path.dirname(__file__), "public", "index.html")
