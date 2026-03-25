import os
from dotenv import load_dotenv

load_dotenv()

# API keys and credentials
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

# LLM
MODEL_NAME = "llama-3.3-70b-versatile"
TEMPERATURE = 0

# Pipeline controls
SEVERITY_THRESHOLD = int(os.getenv("SEVERITY_THRESHOLD", "3"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", "150"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "24"))

# NewsAPI search terms
KEYWORDS = [
    "reinsurance",
    "nat-cat",
    "cyber risk",
    "liability insurance",
    "treaty reinsurance",
    "catastrophe loss",
    "underwriting",
    "insurance loss",
    "natural disaster insurance",
    "Munich Re",
    "Swiss Re",
    "Lloyd's",
    "combined ratio",
    "cedent",
]

# Email
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", GMAIL_USER or "")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "Daily Risk Intelligence Report")

# Paths
REPORTS_DIR = "reports"
RSS_FEEDS_PATH = "data/rss_feeds.json"
PROCESSED_URLS_PATH = "data/processed_urls.json"
REPORT_TEMPLATE_PATH = "report_template.html"
