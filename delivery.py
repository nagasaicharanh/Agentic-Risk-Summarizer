import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config
from schemas import RiskSummaryReport


def render_report_html(report: RiskSummaryReport) -> str:
    template_dir = Path(config.REPORT_TEMPLATE_PATH).resolve().parent
    template_name = Path(config.REPORT_TEMPLATE_PATH).name
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template(template_name)
    return template.render(report=report)


def send_report_email(report_html: str, report_date: str) -> None:
    if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
        raise ValueError("Missing GMAIL_USER or GMAIL_APP_PASSWORD environment variables.")
    if not config.RECIPIENT_EMAIL:
        raise ValueError("Missing RECIPIENT_EMAIL (or fallback GMAIL_USER).")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{config.EMAIL_SUBJECT} — {report_date}"
    msg["From"] = config.GMAIL_USER
    msg["To"] = config.RECIPIENT_EMAIL
    msg.attach(MIMEText(report_html, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        server.sendmail(config.GMAIL_USER, [config.RECIPIENT_EMAIL], msg.as_string())

