"""Statistical calculations for binary A/B experiments."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil, sqrt

import pandas as pd
from scipy.stats import norm
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize


@dataclass(frozen=True)
class AnalysisResult:
    """Complete statistical summary for a two-group conversion experiment."""

    control_sample_size: int
    treatment_sample_size: int
    control_conversions: int
    treatment_conversions: int
    control_rate: float
    treatment_rate: float
    absolute_uplift: float
    relative_uplift: float | None
    z_statistic: float
    p_value: float
    ci_lower: float
    ci_upper: float
    confidence_level: float
    alpha: float
    recommendation: str

    def to_dict(self) -> dict[str, int | float | str | None]:
        return asdict(self)


def analyze_experiment(data: pd.DataFrame, alpha: float = 0.05) -> AnalysisResult:
    """Run a two-sided pooled two-proportion z-test and unpooled Wald CI."""

    if not 0 < alpha < 1:
        raise ValueError("Alpha must be between 0 and 1.")

    control = data.loc[data["group"].eq("control"), "converted"]
    treatment = data.loc[data["group"].eq("treatment"), "converted"]
    n_control = int(control.size)
    n_treatment = int(treatment.size)
    if n_control == 0 or n_treatment == 0:
        raise ValueError("Both control and treatment must contain at least one observation.")

    conversions_control = int(control.sum())
    conversions_treatment = int(treatment.sum())
    rate_control = conversions_control / n_control
    rate_treatment = conversions_treatment / n_treatment
    difference = rate_treatment - rate_control

    pooled_rate = (conversions_control + conversions_treatment) / (n_control + n_treatment)
    pooled_se = sqrt(
        pooled_rate * (1 - pooled_rate) * (1 / n_control + 1 / n_treatment)
    )
    if pooled_se == 0:
        z_statistic = 0.0
        p_value = 1.0
    else:
        z_statistic = difference / pooled_se
        p_value = float(2 * norm.sf(abs(z_statistic)))

    difference_se = sqrt(
        rate_control * (1 - rate_control) / n_control
        + rate_treatment * (1 - rate_treatment) / n_treatment
    )
    confidence_level = 1 - alpha
    critical_value = float(norm.ppf(1 - alpha / 2))
    ci_lower = difference - critical_value * difference_se
    ci_upper = difference + critical_value * difference_se

    relative_uplift = difference / rate_control if rate_control > 0 else None
    if p_value < alpha and difference > 0:
        recommendation = "Treatment wins"
    elif p_value < alpha and difference < 0:
        recommendation = "Control performs better"
    else:
        recommendation = "Experiment is inconclusive and needs more data"

    return AnalysisResult(
        control_sample_size=n_control,
        treatment_sample_size=n_treatment,
        control_conversions=conversions_control,
        treatment_conversions=conversions_treatment,
        control_rate=rate_control,
        treatment_rate=rate_treatment,
        absolute_uplift=difference,
        relative_uplift=relative_uplift,
        z_statistic=z_statistic,
        p_value=p_value,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        confidence_level=confidence_level,
        alpha=alpha,
        recommendation=recommendation,
    )


def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    power: float = 0.80,
    alpha: float = 0.05,
) -> int:
    """Calculate the required observations per group for equal-sized groups.

    The minimum detectable effect is an absolute increase in conversion rate.
    A two-sided independent-proportions z-test is assumed.
    """

    if not 0 < baseline_rate < 1:
        raise ValueError("Baseline conversion rate must be between 0 and 1.")
    if not 0 < minimum_detectable_effect < 1:
        raise ValueError("Minimum detectable effect must be between 0 and 1.")
    treatment_rate = baseline_rate + minimum_detectable_effect
    if treatment_rate >= 1:
        raise ValueError("Baseline rate plus the detectable effect must be below 100%.")
    if not 0 < power < 1:
        raise ValueError("Power must be between 0 and 1.")
    if not 0 < alpha < 1:
        raise ValueError("Significance level must be between 0 and 1.")

    effect_size = abs(proportion_effectsize(treatment_rate, baseline_rate))
    observations = NormalIndPower().solve_power(
        effect_size=effect_size,
        power=power,
        alpha=alpha,
        ratio=1.0,
        alternative="two-sided",
    )
    return ceil(float(observations))

