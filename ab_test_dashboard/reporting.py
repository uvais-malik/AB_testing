"""Human-readable and downloadable summaries."""

from __future__ import annotations

import pandas as pd

from .statistics import AnalysisResult


def explain_result(result: AnalysisResult) -> str:
    """Translate the statistical result into plain English for any audience."""

    direction = "higher" if result.absolute_uplift >= 0 else "lower"
    difference = abs(result.absolute_uplift)

    if result.recommendation == "Treatment wins":
        return (
            f"✅ **The new version is working.** It converts {difference:.2%} more users "
            f"than the original — and we're confident this is a real improvement, not a fluke "
            f"(statistical confidence: {result.confidence_level:.0%}). "
            f"**Recommendation: ship the new version.** "
            f"Always double-check that no guardrail metrics (e.g. revenue per user, "
            f"support tickets) moved in the wrong direction before going live."
        )
    if result.recommendation == "Control performs better":
        return (
            f"⚠️ **The new version is underperforming.** It converts {difference:.2%} fewer "
            f"users than the original — and we're confident this drop is real "
            f"(statistical confidence: {result.confidence_level:.0%}). "
            f"**Recommendation: keep the original.** "
            f"Revisit the design or hypothesis before running another test."
        )
    return (
        f"🔄 **The result is not conclusive yet.** The new version converts "
        f"{difference:.2%} {direction} than the original, but the difference "
        f"could still be due to random chance (p-value: {result.p_value:.4f}). "
        f"**Recommendation: keep collecting data.** "
        f"Use the sample-size calculator below to check how many more users you need."
    )


def results_summary(result: AnalysisResult, data_source: str) -> pd.DataFrame:
    """Create a one-row, analysis-ready export."""

    values = result.to_dict()
    values["data_source"] = data_source
    values["absolute_uplift_percentage_points"] = result.absolute_uplift * 100
    values["relative_uplift_percent"] = (
        result.relative_uplift * 100 if result.relative_uplift is not None else None
    )
    return pd.DataFrame([values])
