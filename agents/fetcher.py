import hashlib
import json
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable

import feedparser
from newsapi import NewsApiClient

import config
from schemas import RawArticle


def _to_utc_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass

    try:
        dt = parsedate_to_datetime(value)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _hash_url(url: str) -> str:
    return hashlib.md5(url.strip().encode("utf-8")).hexdigest()


class RiskSignalFetcher:
    def __init__(self) -> None:
        self.news_client = NewsApiClient(api_key=config.NEWS_API_KEY) if config.NEWS_API_KEY else None
        self.processed_urls_path = Path(config.PROCESSED_URLS_PATH)
        self.processed_urls_path.parent.mkdir(parents=True, exist_ok=True)

    def fetch_recent_articles(self) -> list[RawArticle]:
        processed_hashes = self._load_processed_hashes()
        candidates = [
            *self._fetch_newsapi_articles(),
            *self._fetch_rss_articles(),
        ]

        cutoff = datetime.now(timezone.utc) - timedelta(hours=config.LOOKBACK_HOURS)
        unique_articles: list[RawArticle] = []
        run_hashes: set[str] = set()

        for article in candidates:
            parsed = _to_utc_datetime(article.published_at)
            if not parsed or parsed < cutoff:
                continue

            url_hash = _hash_url(article.url)
            if url_hash in processed_hashes or url_hash in run_hashes:
                continue

            run_hashes.add(url_hash)
            unique_articles.append(article)

            if len(unique_articles) >= config.MAX_ARTICLES:
                break

        self._save_processed_hashes(processed_hashes | run_hashes)
        return unique_articles

    def _fetch_newsapi_articles(self) -> list[RawArticle]:
        if not self.news_client:
            return []

        query = " OR ".join(config.KEYWORDS)
        response = self.news_client.get_everything(
            q=query,
            language="en",
            sort_by="publishedAt",
            page_size=min(config.MAX_ARTICLES, 100),
        )
        raw_articles = response.get("articles", [])
        return list(self._normalize_newsapi_articles(raw_articles))

    def _fetch_rss_articles(self) -> list[RawArticle]:
        feeds_path = Path(config.RSS_FEEDS_PATH)
        if not feeds_path.exists():
            return []

        feeds = json.loads(feeds_path.read_text(encoding="utf-8"))
        normalized: list[RawArticle] = []
        for feed in feeds:
            parsed_feed = feedparser.parse(feed["url"])
            normalized.extend(self._normalize_rss_entries(feed["name"], parsed_feed.entries))
        return normalized

    @staticmethod
    def _normalize_newsapi_articles(articles: Iterable[dict]) -> Iterable[RawArticle]:
        for article in articles:
            url = (article.get("url") or "").strip()
            title = (article.get("title") or "").strip()
            if not url or not title:
                continue

            body = (article.get("content") or article.get("description") or "").strip()
            source = (article.get("source") or {}).get("name", "NewsAPI")
            published_at = article.get("publishedAt") or ""
            yield RawArticle(
                title=title,
                url=url,
                body=body,
                source=source,
                published_at=published_at,
            )

    @staticmethod
    def _normalize_rss_entries(feed_name: str, entries: Iterable[dict]) -> list[RawArticle]:
        normalized: list[RawArticle] = []
        for entry in entries:
            url = (entry.get("link") or "").strip()
            title = (entry.get("title") or "").strip()
            if not url or not title:
                continue

            body = (entry.get("summary") or entry.get("description") or "").strip()
            published_at = (
                entry.get("published")
                or entry.get("updated")
                or entry.get("pubDate")
                or ""
            )
            normalized.append(
                RawArticle(
                    title=title,
                    url=url,
                    body=body,
                    source=feed_name,
                    published_at=published_at,
                )
            )
        return normalized

    def _load_processed_hashes(self) -> set[str]:
        if not self.processed_urls_path.exists():
            return set()

        try:
            payload = json.loads(self.processed_urls_path.read_text(encoding="utf-8"))
            return set(payload.get("hashes", []))
        except json.JSONDecodeError:
            return set()

    def _save_processed_hashes(self, hashes: set[str]) -> None:
        payload = {"hashes": sorted(hashes)}
        self.processed_urls_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

