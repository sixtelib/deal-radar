"""
Applique tes critères à une annonce parsée et calcule un score de pertinence.

Principe : un critère explicitement en dehors des clous EXCLUT l'annonce.
Un critère absent de l'annonce ne l'exclut pas (on préfère un faux positif
« à vérifier » à un faux négatif qui te ferait rater une bonne affaire) —
mais il est signalé comme incertain.
"""
from dataclasses import dataclass, field

from config import Criteria
from scraper.parser import Listing


@dataclass
class Evaluation:
    listing: Listing
    is_match: bool
    score: int  # 0-100, indicatif, pour trier les annonces retenues
    reasons_ok: list = field(default_factory=list)
    reasons_ko: list = field(default_factory=list)       # motifs d'exclusion dure (annonce hors critères)
    reasons_unsure: list = field(default_factory=list)   # données manquantes, à vérifier
    reasons_watch: list = field(default_factory=list)    # signaux d'alerte visibles même sur une annonce retenue


def _is_idf(listing: Listing, criteria: Criteria) -> tuple[bool | None, str]:
    loc = listing.localisation.lower()
    if not loc:
        return None, "Localisation non précisée dans l'annonce"
    if any(kw in loc for kw in criteria.idf_keywords):
        return True, f"Localisation : {listing.localisation}"
    if any(dep in loc for dep in criteria.idf_departements):
        return True, f"Localisation : {listing.localisation}"
    return False, f"Localisation hors Île-de-France apparente : {listing.localisation}"


def _is_ca_in_range(listing: Listing, criteria: Criteria) -> tuple[bool | None, str]:
    ca = listing.ca_recent
    if ca is None:
        return None, "CA non trouvé dans l'annonce"
    if criteria.ca_min_keur <= ca <= criteria.ca_max_keur:
        return True, f"CA le plus récent : {ca:.0f} k€"
    return False, f"CA hors cible : {ca:.0f} k€ (cible {criteria.ca_min_keur}-{criteria.ca_max_keur} k€)"


def _is_retraite(listing: Listing, criteria: Criteria) -> tuple[bool | None, str]:
    raison = listing.raison_cession.lower()
    if not raison:
        return None, "Raison de cession non précisée"
    if any(kw in raison for kw in criteria.raison_cession_keywords):
        return True, f"Raison de cession : {listing.raison_cession}"
    return False, f"Raison de cession : {listing.raison_cession} (≠ départ à la retraite)"


def _is_apport_ok(listing: Listing, criteria: Criteria) -> tuple[bool | None, str]:
    if listing.apport_min_keur is None:
        return None, "Apport minimum non précisé dans l'annonce"
    if listing.apport_min_keur <= criteria.apport_max_keur:
        return True, f"Apport minimum demandé : {listing.apport_min_keur:.0f} k€"
    return False, f"Apport minimum trop élevé : {listing.apport_min_keur:.0f} k€ (max {criteria.apport_max_keur} k€)"


def evaluate(listing: Listing, criteria: Criteria) -> Evaluation:
    checks = [
        _is_idf(listing, criteria),
        _is_ca_in_range(listing, criteria),
        _is_retraite(listing, criteria),
        _is_apport_ok(listing, criteria),
    ]

    reasons_ok, reasons_ko, reasons_unsure, reasons_watch = [], [], [], []
    hard_fail = False

    for result, reason in checks:
        if result is True:
            reasons_ok.append(reason)
        elif result is False:
            reasons_ko.append(reason)
            hard_fail = True
        else:
            reasons_unsure.append(reason)

    is_match = not hard_fail

    # Score indicatif pour trier les annonces retenues entre elles
    score = 0
    score += 15 * len(reasons_ok)
    score -= 5 * len(reasons_unsure)

    if listing.ebe_recent is not None and listing.ebe_recent > 0:
        score += 15
        reasons_ok.append(f"EBE positif ({listing.ebe_recent:.0f} k€)")
    elif listing.ebe_recent == 0:
        score -= 10
        reasons_watch.append("EBE à 0 — l'activité ne dégage aucune rentabilité opérationnelle visible")

    evol = listing.ca_evolution_pct
    if evol is not None:
        if evol >= 0:
            score += 10
            reasons_ok.append(f"CA en croissance ({evol:+.1f} %)")
        elif evol <= -15:
            score -= 15
            reasons_watch.append(f"CA en forte baisse ({evol:+.1f} %) — à creuser avant toute offre")
        else:
            score -= 5
            reasons_watch.append(f"CA en légère baisse ({evol:+.1f} %)")

    score = max(0, min(100, score))

    return Evaluation(
        listing=listing,
        is_match=is_match,
        score=score,
        reasons_ok=reasons_ok,
        reasons_ko=reasons_ko,
        reasons_unsure=reasons_unsure,
        reasons_watch=reasons_watch,
    )
