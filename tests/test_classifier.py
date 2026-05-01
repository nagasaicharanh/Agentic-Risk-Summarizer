import unittest

from agents.classifier import RiskClassifier
from schemas import RawArticle, RiskItem, RiskItemBatch


class _FakeStructuredLLM:
    def __init__(self, result_items):
        self._result_items = result_items

    def invoke(self, _payload):
        return RiskItemBatch(items=self._result_items)


class _FakePrompt:
    def __or__(self, other):
        return other


class TestClassifier(unittest.TestCase):
    def test_batching_and_severity_filter(self):
        items = [
            RawArticle(
                title=f"Article {idx}",
                url=f"https://example.com/{idx}",
                body="content",
                source="Test",
                published_at="2026-04-25T07:00:00Z",
            )
            for idx in range(12)
        ]

        classifier = RiskClassifier(llm=object())
        fake_results = [
            RiskItem(
                headline="High severity risk",
                source="Test",
                peril_type="cyber",
                severity=4,
                region="Global",
                summary="Material incident detected. Spillover risk remains elevated.",
                published_at="2026-04-25T07:00:00Z",
            ),
            RiskItem(
                headline="Low severity update",
                source="Test",
                peril_type="market",
                severity=2,
                region="US",
                summary="Routine news item. Limited insurance impact expected.",
                published_at="2026-04-25T07:00:00Z",
            ),
            RiskItem(
                headline="Regulatory changes in UK",
                source="Test",
                peril_type="regulatory",
                severity=3,
                region="UK",
                summary="New capital requirements for offshore reinsurance.",
                published_at="2026-04-25T07:00:00Z",
            ),
        ]

        # Override internals to keep this test fully offline and deterministic.
        classifier._get_structured_llm = lambda: _FakeStructuredLLM(fake_results)  # type: ignore[method-assign]

        from agents import classifier as classifier_module

        original_prompt_builder = classifier_module.ChatPromptTemplate.from_messages
        classifier_module.ChatPromptTemplate.from_messages = lambda *_args, **_kwargs: _FakePrompt()
        try:
            from agents import classifier as _classifier_config

            original_batch = _classifier_config.config.BATCH_SIZE
            original_threshold = _classifier_config.config.SEVERITY_THRESHOLD
            _classifier_config.config.BATCH_SIZE = 10
            _classifier_config.config.SEVERITY_THRESHOLD = 3
            try:
                result = classifier.classify(items)
            finally:
                _classifier_config.config.BATCH_SIZE = original_batch
                _classifier_config.config.SEVERITY_THRESHOLD = original_threshold
        finally:
            classifier_module.ChatPromptTemplate.from_messages = original_prompt_builder

        # 12 inputs with batch size 10 creates 2 batches, each returns two high-severity items (severity 4 and 3).
        self.assertEqual(len(result), 4)
        self.assertTrue(all(item.severity >= 3 for item in result))


if __name__ == "__main__":
    unittest.main()
