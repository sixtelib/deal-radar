"""
Parseur des fiches de cession.

Les annonces Fusacq / Transentreprise / réseau CCI-CMA partagent un gabarit de
champs très stable ("Forme juridique", "Résumé général de l'activité",
"Raison principale de la cession", tableau "Eléments chiffrés", etc.), même si
le HTML change d'un site à l'autre. On travaille donc sur le texte visible de
la page plutôt que sur des sélecteurs CSS, qui cassent au moindre redesign.

⚠️ Ce parseur est volontairement tolérant (plusieurs variantes de libellés par
champ) mais reste une heuristique texte. Vérifie toujours les annonces
signalées comme pertinentes en ouvrant le lien d'origine.
"""
import re
from dataclasses import dataclass, field


@dataclass
class Listing:
    url: str = ""
    titre: str = ""
    forme_juridique: str = ""
    anciennete: str = ""
    localisation: str = ""
    activite: str = ""
    type_cession: str = ""
    raison_cession: str = ""
    apport_min_keur: float | None = None
    ca_par_annee: list[float] = field(default_factory=list)   # ordre chronologique croissant
    ebe_par_annee: list[float] = field(default_factory=list)
    rex_par_annee: list[float] = field(default_factory=list)
    rn_par_annee: list[float] = field(default_factory=list)
    raw_text: str = ""

    @property
    def ca_recent(self) -> float | None:
        return self.ca_par_annee[-1] if self.ca_par_annee else None

    @property
    def ca_evolution_pct(self) -> float | None:
        if len(self.ca_par_annee) >= 2 and self.ca_par_annee[-2]:
            return round(100 * (self.ca_par_annee[-1] - self.ca_par_annee[-2]) / self.ca_par_annee[-2], 1)
        return None

    @property
    def ebe_recent(self) -> float | None:
        return self.ebe_par_annee[-1] if self.ebe_par_annee else None

    @property
    def rn_recent(self) -> float | None:
        return self.rn_par_annee[-1] if self.rn_par_annee else None


def _search_first(text: str, labels: list[str]) -> str | None:
    """Cherche la première occurrence d'un des libellés et renvoie ce qui suit
    sur la même ligne (ou la ligne suivante si le libellé est seul sur sa ligne)."""
    for label in labels:
        # Cas "Label : valeur" ou "Label valeur" sur la même ligne
        m = re.search(re.escape(label) + r"\s*:?\s*(.+)", text, re.IGNORECASE)
        if m:
            value = m.group(1).strip()
            if value:
                return value
        # Cas où le libellé est seul sur sa ligne, valeur sur la ligne suivante
        m2 = re.search(re.escape(label) + r"\s*\n\s*(.+)", text, re.IGNORECASE)
        if m2:
            return m2.group(1).strip()
    return None


def _extract_numbers_on_label_line(text: str, labels: list[str]) -> list[float]:
    """Pour les lignes de tableau type 'CA 1100 900', renvoie la liste des
    nombres trouvés sur cette ligne (dans l'ordre où ils apparaissent, donc en
    principe du plus ancien au plus récent si le tableau est chronologique)."""
    for line in text.splitlines():
        stripped = line.strip()
        for label in labels:
            if re.match(re.escape(label) + r"\b", stripped, re.IGNORECASE):
                remainder = stripped[len(label):]
                # Chaque nombre est un token séparé par des espaces — on ne permet
                # PAS d'espace à l'intérieur d'un nombre (sinon "1100 900" fusionne
                # en un seul nombre au lieu de deux valeurs annuelles distinctes).
                tokens = re.findall(r"-?\d+(?:[.,]\d+)?", remainder)
                cleaned = []
                for n in tokens:
                    n = n.replace(",", ".")
                    try:
                        cleaned.append(float(n))
                    except ValueError:
                        continue
                if cleaned:
                    return cleaned
    return []


def _extract_keur(value_str: str | None) -> float | None:
    if not value_str:
        return None
    m = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)\s*k\s*€", value_str, re.IGNORECASE)
    if m:
        return float(m.group(1).replace(" ", "").replace(",", "."))
    m = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)\s*€", value_str)
    if m:
        # valeur en euros bruts -> conversion en k€
        return float(m.group(1).replace(" ", "").replace(",", ".")) / 1000
    return None


def parse_listing(html_text_or_plain: str, url: str = "", already_plain: bool = False) -> Listing:
    from scraper.common import visible_text

    text = html_text_or_plain if already_plain else visible_text(html_text_or_plain)

    listing = Listing(url=url, raw_text=text)

    listing.forme_juridique = _search_first(text, ["Forme juridique"]) or ""
    listing.anciennete = _search_first(text, ["Ancienneté de la société"]) or ""
    listing.localisation = _search_first(text, ["Localisation du siège"]) or ""
    listing.activite = _search_first(text, ["Résumé général de l'activité", "Résumé général de l’activité"]) or ""
    listing.type_cession = _search_first(text, ["Type de cession envisagée"]) or ""
    listing.raison_cession = _search_first(
        text, ["Raison principale de la cession", "Raison principale de cession"]
    ) or ""

    apport_str = _search_first(
        text,
        [
            "Apport en fonds propres minimum",
            "Apport personnel minimum",
            "Apport souhaité",
            "Apport minimum",
        ],
    )
    listing.apport_min_keur = _extract_keur(apport_str)

    listing.ca_par_annee = _extract_numbers_on_label_line(text, ["CA", "Chiffre d'Affaires", "Chiffre d’affaires"])
    listing.ebe_par_annee = _extract_numbers_on_label_line(text, ["EBE"])
    listing.rex_par_annee = _extract_numbers_on_label_line(text, ["REX", "Rés. Exp.", "Résultat d'Exploitation"])
    listing.rn_par_annee = _extract_numbers_on_label_line(text, ["RN", "Rés. Net", "Résultat Net"])

    # Titre : on utilise en priorité le résumé de l'activité (souvent la ligne la
    # plus parlante), sinon la première ligne qui ne fait pas partie du gabarit standard.
    if listing.activite:
        listing.titre = listing.activite.split(".")[0].strip()[:90]
    else:
        boilerplate = {
            "description générale", "eléments chiffrés", "portail d'affaires",
            "fiche d'identité de la société", "résumé général de l'activité",
            "a propos de la cession", "infos sur la cession",
        }
        for line in text.splitlines():
            if line.strip().lower() not in boilerplate and len(line.strip()) > 8:
                listing.titre = line.strip()
                break

    return listing
