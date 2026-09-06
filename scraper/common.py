import re
import time
import logging
from urllib.parse import urljoin, urlparse

import requests

from config import USER_AGENT, REQUEST_DELAY_SECONDS

logger = logging.getLogger("deal_radar")

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT})


def fetch_html(url: str, timeout: int = 20) -> str | None:
    """Récupère le HTML d'une page, avec une pause de courtoisie avant chaque requête."""
    time.sleep(REQUEST_DELAY_SECONDS)
    try:
        resp = _session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        logger.warning("Échec de récupération de %s : %s", url, exc)
        return None


def extract_links(html: str, base_url: str, pattern: str) -> list[str]:
    """Extrait les liens d'une page de résultats qui correspondent au pattern des fiches détail."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    found = set()
    regex = re.compile(pattern, re.IGNORECASE)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if regex.search(href):
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                found.add(full_url)
    return sorted(found)


def visible_text(html: str) -> str:
    """Convertit le HTML en texte brut lisible, en conservant les sauts de ligne
    entre blocs (utile pour le parsing par label ensuite)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
