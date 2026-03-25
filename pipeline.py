from datetime import datetime, timezone

import config
from agents.classifier import RiskClassifier
from agents.fetcher import RiskSignalFetcher
from agents.summarizer import RiskSummarizer
from delivery import render_report_html, send_report_email


def _ensure_required_runtime_config() -> None:
    missing = []
    if not config.GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not config.NEWS_API_KEY:
        missing.append("NEWS_API_KEY")
    if not config.GMAIL_USER:
        missing.append("GMAIL_USER")
    if not config.GMAIL_APP_PASSWORD:
        missing.append("GMAIL_APP_PASSWORD")

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def run_pipeline() -> None:
    started_at = datetime.now(timezone.utc).isoformat()
    print(f"[pipeline] Start: {started_at}")
    _ensure_required_runtime_config()

    fetcher = RiskSignalFetcher()
    classifier = RiskClassifier()
    summarizer = RiskSummarizer()

    print("[pipeline] Fetching articles...")
    articles = fetcher.fetch_recent_articles()
    print(f"[pipeline] Fetched {len(articles)} normalized articles.")

    print("[pipeline] Classifying risks...")
    top_risks = classifier.classify(articles)
    print(f"[pipeline] Retained {len(top_risks)} items at severity >= {config.SEVERITY_THRESHOLD}.")

    print("[pipeline] Building summary report...")
    report = summarizer.build_report(top_risks=top_risks, total_signals=len(articles))

    print("[pipeline] Rendering and sending email...")
    html = render_report_html(report)
    send_report_email(report_html=html, report_date=report.date)
    print("[pipeline] Completed successfully.")


if __name__ == "__main__":
    run_pipeline()

