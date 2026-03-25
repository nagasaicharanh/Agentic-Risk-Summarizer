import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

import config
from schemas import RiskItem, RiskSummaryReport


class RiskSummarizer:
    def __init__(self, llm=None) -> None:
        self._llm = llm
        Path(config.REPORTS_DIR).mkdir(parents=True, exist_ok=True)

    def build_report(self, top_risks: list[RiskItem], total_signals: int) -> RiskSummaryReport:
        peril_breakdown = dict(Counter(item.peril_type for item in top_risks))
        executive_summary = self._build_executive_summary(top_risks)

        report = RiskSummaryReport(
            date=datetime.now(timezone.utc).date().isoformat(),
            total_signals=total_signals,
            high_severity_count=len(top_risks),
            peril_breakdown=peril_breakdown,
            executive_summary=executive_summary,
            top_risks=top_risks,
        )
        self._save_report(report)
        return report

    def _build_executive_summary(self, top_risks: list[RiskItem]) -> str:
        if not top_risks:
            return "No high-severity insurance risk signals were identified in the last 24 hours."

        grouped: dict[str, list[str]] = {}
        for item in top_risks:
            grouped.setdefault(item.peril_type, []).append(item.summary)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a reinsurance risk editor. Write a single executive summary under 150 words.",
                ),
                (
                    "human",
                    "Summaries grouped by peril type:\n{grouped_summaries}\n\n"
                    "Output only the summary paragraph.",
                ),
            ]
        )

        llm = self._llm or ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
        )
        chain = prompt | llm
        output = chain.invoke(
            {"grouped_summaries": json.dumps(grouped, ensure_ascii=False, indent=2)}
        ).content.strip()
        return output[:1000]

    @staticmethod
    def _save_report(report: RiskSummaryReport) -> None:
        report_path = Path(config.REPORTS_DIR) / f"{report.date}.json"
        report_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

