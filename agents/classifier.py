import json
from collections.abc import Iterable

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

import config
from schemas import RawArticle, RiskItem, RiskItemBatch


SYSTEM_PROMPT = """You are a reinsurance risk analyst at a leading reinsurer.
Classify each article into exactly one peril type and assign a severity score.

Peril types: nat-cat, cyber, liability, market, operational
Severity scale:
1 = Informational / industry news
2 = Minor event, limited market impact
3 = Moderate event, regional significance
4 = Major event, material financial impact
5 = Critical / catastrophic event

Requirements:
- Return an item for every input article.
- Keep summary concise (maximum 2 sentences).
- Preserve each article's source and published_at fields.
- If an article is not related to insurance risk, assign severity = 1.
"""


class RiskClassifier:
    def __init__(self, llm=None) -> None:
        self._llm = llm

    def classify(self, articles: list[RawArticle]) -> list[RiskItem]:
        if not articles:
            return []

        high_severity: list[RiskItem] = []
        for batch in self._batch_items(articles, config.BATCH_SIZE):
            batch_result = self._classify_batch(batch)
            high_severity.extend(
                item for item in batch_result if item.severity >= config.SEVERITY_THRESHOLD
            )
        return high_severity

    def _classify_batch(self, batch: list[RawArticle]) -> list[RiskItem]:
        formatted_articles = [
            {
                "headline": article.title,
                "source": article.source,
                "published_at": article.published_at,
                "url": article.url,
                "body": article.body,
            }
            for article in batch
        ]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "Classify these articles:\n{articles_json}"),
            ]
        )
        chain = prompt | self._get_structured_llm()
        result: RiskItemBatch = chain.invoke(
            {"articles_json": json.dumps(formatted_articles, ensure_ascii=False)}
        )
        return result.items

    def _get_structured_llm(self):
        llm = self._llm or ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
        )
        return llm.with_structured_output(RiskItemBatch)

    @staticmethod
    def _batch_items(items: list[RawArticle], batch_size: int) -> Iterable[list[RawArticle]]:
        for idx in range(0, len(items), batch_size):
            yield items[idx : idx + batch_size]

