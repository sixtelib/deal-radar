import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO, ALERT_EMAIL_FROM
from filters import Evaluation

logger = logging.getLogger("deal_radar")


def _format_evaluation_html(ev: Evaluation) -> str:
    l = ev.listing
    ok = "".join(f"<li style='color:#2f6d4f'>✓ {r}</li>" for r in ev.reasons_ok)
    watch = "".join(f"<li style='color:#a6453d'>⚠ {r}</li>" for r in ev.reasons_watch)
    unsure = "".join(f"<li style='color:#8a6d1f'>? {r}</li>" for r in ev.reasons_unsure)
    return f"""
    <div style="border:1px solid #ddd;border-radius:6px;padding:16px;margin-bottom:16px;font-family:sans-serif">
      <h3 style="margin:0 0 8px"><a href="{l.url}">{l.titre or l.url}</a></h3>
      <p style="color:#555;margin:0 0 10px">{l.activite[:280]}</p>
      <p style="margin:0 0 6px"><b>Score : {ev.score}/100</b></p>
      <ul style="margin:0;padding-left:18px">{ok}{watch}{unsure}</ul>
    </div>
    """


def send_alert_email(evaluations: list[Evaluation]) -> bool:
    if not evaluations:
        return False
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_TO]):
        logger.warning("Configuration SMTP incomplète — email non envoyé (voir .env)")
        return False

    subject = f"[Deal Radar] {len(evaluations)} nouvelle(s) annonce(s) pertinente(s)"
    body_html = "<h2>Nouvelles opportunités correspondant à tes critères</h2>"
    body_html += "".join(_format_evaluation_html(ev) for ev in evaluations)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = ALERT_EMAIL_FROM
    msg["To"] = ALERT_EMAIL_TO
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(ALERT_EMAIL_FROM, [ALERT_EMAIL_TO], msg.as_string())
        logger.info("Email d'alerte envoyé pour %d annonce(s)", len(evaluations))
        return True
    except Exception as exc:
        logger.error("Échec d'envoi de l'email d'alerte : %s", exc)
        return False
