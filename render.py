import os
import shutil
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from config import OUTPUT_HTML_PATH
from filters import Evaluation

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


def render_landing_page(evaluations: list[Evaluation]) -> str:
    retained = sorted([e for e in evaluations if e.is_match], key=lambda e: -e.score)
    unsure = sorted(
        [e for e in evaluations if not e.is_match and e.reasons_unsure and not e.reasons_ko],
        key=lambda e: -e.score,
    )

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("index.html")

    with open(os.path.join(STATIC_DIR, "style.css"), "r", encoding="utf-8") as f:
        css = f.read()

    html = template.render(
        retained=retained,
        unsure=unsure,
        total_checked=len(evaluations),
        last_run=datetime.now().strftime("%d/%m/%Y à %H:%M"),
        css=css,
    )

    os.makedirs(os.path.dirname(OUTPUT_HTML_PATH), exist_ok=True)
    with open(OUTPUT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    return OUTPUT_HTML_PATH
