"""Test de bout en bout SANS accès réseau : on simule le texte de 3 annonces
(dont celle de tes captures d'écran) pour vérifier parseur + scoring + rendu."""
from scraper.parser import parse_listing
from filters import evaluate
from config import CRITERIA
from render import render_landing_page

# Annonce 1 : celle de tes captures (carrelage, Seine-et-Marne) — CA en baisse, EBE=0
annonce_carrelage = """
Description générale
Fiche d'identité de la société
Forme juridique : SAS
Ancienneté de la société : Plus de 10 ans
Localisation du siège : Seine et Marne, Ile-de-France, France

Résumé général de l'activité
Revêtement de sols : carrelage et sols souples.

A propos de la cession
Type de cession envisagée : Minoritaire ou majoritaire
Raison principale de la cession : Départ à la retraite
Compléments : Départ à la retraite du dirigeant, détenteur de 60 % du capital, accompagné de la cession des 40 % restants par l'autre associé.

Eléments chiffrés
En k€ 2022 2023 2024
CA 1100 900
Marge
EBE 0
REX 0
RN 35 15
Nb 5 5

Apport en fonds propres minimum pour se positionner sur ce dossier : 120 k€
"""

# Annonce 2 : hors critères (province + CA trop élevé)
annonce_hors_critere = """
Fiche d'identité de la société
Forme juridique SARL
Localisation du siège Bouches du Rhône

Résumé général de l'activité
Distribution de carrelage haut de gamme.

Type de cession envisagée Majoritaire
Raison principale de cession Changement d'activité du dirigeant

Eléments chiffrés
En k€/année 2022 2023 2024
CA 2200 2500
EBE 100
Salariés 20

Apport en fonds propres minimum pour se positionner sur ce dossier 400 k€
"""

# Annonce 3 : bon profil, données financières incomplètes -> "à vérifier"
annonce_incomplete = """
Fiche d'identité de la société
Forme juridique SAS
Localisation du siège Yvelines, Ile-de-France

Résumé général de l'activité
Bureau d'études techniques en génie climatique.

Raison principale de la cession Départ à la retraite

Eléments chiffrés
En k€/année 2023 2024
CA 650 700
"""

samples = [
    ("carrelage_77 (tes captures)", annonce_carrelage, "https://example.com/annonce/carrelage-77"),
    ("hors_critere_13", annonce_hors_critere, "https://example.com/annonce/carrelage-13"),
    ("bet_78_incomplet", annonce_incomplete, "https://example.com/annonce/bet-78"),
]

evaluations = []
for name, text, url in samples:
    listing = parse_listing(text, url=url, already_plain=True)
    ev = evaluate(listing, CRITERIA)
    evaluations.append(ev)
    print(f"\n=== {name} ===")
    print(f"  Localisation   : {listing.localisation!r}")
    print(f"  CA par année   : {listing.ca_par_annee}")
    print(f"  EBE par année  : {listing.ebe_par_annee}")
    print(f"  RN par année   : {listing.rn_par_annee}")
    print(f"  Apport min k€  : {listing.apport_min_keur}")
    print(f"  Raison cession : {listing.raison_cession!r}")
    print(f"  --> is_match={ev.is_match}  score={ev.score}")
    print(f"      OK     : {ev.reasons_ok}")
    print(f"      KO     : {ev.reasons_ko}")
    print(f"      UNSURE : {ev.reasons_unsure}")

path = render_landing_page(evaluations)
print(f"\nLanding page générée : {path}")
