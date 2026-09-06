"""
Point d'entrée du Deal Radar.

Usage :
    python main.py

Ce script :
1. parcourt les pages de résultats de recherche configurées dans config.py
2. ouvre chaque nouvelle annonce trouvée
3. la parse et l'évalue selon tes critères
4. envoie un email si de nouvelles annonces pertinentes apparaissent
5. régénère la landing page statique avec l'ensemble des annonces suivies

À planifier via un cron (voir README.md) — par exemple une fois par jour.
"""
import logging
import sys

from config import SEARCH_SOURCES, CRITERIA
from scraper.common import fetch_html, extract_links
from scraper.parser import parse_listing
from filters import evaluate
from storage import load_seen, save_seen, mark_seen
from notifier import send_alert_email
from render import render_landing_page

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("deal_radar")


def run() -> None:
    seen = load_seen()
    new_matches = []
    all_evaluations = []

    any_search_url_configured = any(source["search_urls"] for source in SEARCH_SOURCES)
    if not any_search_url_configured:
        logger.warning(
            "Aucune search_urls configurée dans config.py — voir README.md pour "
            "l'étape 'Configurer les recherches'. Rien à analyser pour l'instant."
        )

    for source in SEARCH_SOURCES:
        for search_url in source["search_urls"]:
            logger.info("[%s] Recherche : %s", source["name"], search_url)
            html = fetch_html(search_url)
            if not html:
                continue

            detail_links = extract_links(html, search_url, source["detail_link_pattern"])
            logger.info("[%s] %d annonce(s) trouvée(s) sur cette page", source["name"], len(detail_links))

            for link in detail_links:
                is_new = link not in seen
                detail_html = fetch_html(link)
                if not detail_html:
                    continue

                listing = parse_listing(detail_html, url=link)
                evaluation = evaluate(listing, CRITERIA)
                all_evaluations.append(evaluation)

                mark_seen(seen, link, evaluation.is_match, evaluation.score)

                if is_new and evaluation.is_match:
                    new_matches.append(evaluation)
                    logger.info("Nouvelle annonce pertinente : %s (score %d)", listing.titre, evaluation.score)

    save_seen(seen)

    if new_matches:
        send_alert_email(new_matches)
    else:
        logger.info("Aucune nouvelle annonce pertinente cette fois-ci.")

    output_path = render_landing_page(all_evaluations)
    logger.info("Landing page régénérée : %s", output_path)


if __name__ == "__main__":
    run()
