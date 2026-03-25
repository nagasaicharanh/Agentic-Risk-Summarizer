import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from agents.fetcher import RiskSignalFetcher
from schemas import RawArticle


class TestFetcher(unittest.TestCase):
    def test_dedupe_lookback_and_idempotency(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_path = Path(tmpdir) / "processed_urls.json"

            now = datetime.now(timezone.utc)
            recent = (now - timedelta(hours=1)).isoformat()
            old = (now - timedelta(hours=30)).isoformat()

            news_items = [
                RawArticle(
                    title="Recent duplicate",
                    url="https://example.com/a",
                    body="news",
                    source="NewsAPI",
                    published_at=recent,
                ),
                RawArticle(
                    title="Old article",
                    url="https://example.com/old",
                    body="old",
                    source="NewsAPI",
                    published_at=old,
                ),
            ]
            rss_items = [
                RawArticle(
                    title="Recent duplicate from RSS",
                    url="https://example.com/a",
                    body="rss",
                    source="RSS",
                    published_at=recent,
                ),
                RawArticle(
                    title="Recent unique",
                    url="https://example.com/b",
                    body="rss2",
                    source="RSS",
                    published_at=recent,
                ),
            ]

            with patch("agents.fetcher.config.PROCESSED_URLS_PATH", str(processed_path)), patch(
                "agents.fetcher.config.LOOKBACK_HOURS", 24
            ):
                fetcher = RiskSignalFetcher()
                with patch.object(fetcher, "_fetch_newsapi_articles", return_value=news_items), patch.object(
                    fetcher, "_fetch_rss_articles", return_value=rss_items
                ):
                    result = fetcher.fetch_recent_articles()

                self.assertEqual(len(result), 2)
                urls = {item.url for item in result}
                self.assertSetEqual(urls, {"https://example.com/a", "https://example.com/b"})

                stored = json.loads(processed_path.read_text(encoding="utf-8"))
                self.assertEqual(len(stored["hashes"]), 2)

                with patch.object(fetcher, "_fetch_newsapi_articles", return_value=news_items), patch.object(
                    fetcher, "_fetch_rss_articles", return_value=rss_items
                ):
                    second_run = fetcher.fetch_recent_articles()
                self.assertEqual(second_run, [])


if __name__ == "__main__":
    unittest.main()
