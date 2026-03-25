import unittest

from pydantic import ValidationError

from schemas import RiskItem


class TestSchemas(unittest.TestCase):
    def test_risk_item_valid(self):
        item = RiskItem(
            headline="Severe flooding causes insurer losses",
            source="Reuters",
            peril_type="nat-cat",
            severity=4,
            region="EMEA",
            summary="Flooding events continue to escalate. Insurers may face material claims pressure.",
            published_at="2026-04-25T07:00:00Z",
        )
        self.assertEqual(item.severity, 4)

    def test_risk_item_invalid_severity(self):
        with self.assertRaises(ValidationError):
            RiskItem(
                headline="Minor note",
                source="Reuters",
                peril_type="market",
                severity=6,
                region="Global",
                summary="Invalid severity.",
                published_at="2026-04-25T07:00:00Z",
            )

    def test_risk_item_invalid_peril(self):
        with self.assertRaises(ValidationError):
            RiskItem(
                headline="Wrong peril",
                source="Reuters",
                peril_type="credit",  # type: ignore[arg-type]
                severity=2,
                region="Global",
                summary="Invalid peril taxonomy.",
                published_at="2026-04-25T07:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
