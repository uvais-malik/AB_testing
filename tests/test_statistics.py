from math import sqrt

import pandas as pd
import pytest
from scipy.stats import norm

from ab_test_dashboard.statistics import analyze_experiment, calculate_sample_size


def experiment(control_conversions: int, treatment_conversions: int, n: int = 100):
    return pd.DataFrame(
        {
            "group": ["control"] * n + ["treatment"] * n,
            "converted": (
                [1] * control_conversions
                + [0] * (n - control_conversions)
                + [1] * treatment_conversions
                + [0] * (n - treatment_conversions)
            ),
        }
    )


def test_analysis_calculates_rates_uplift_test_and_interval() -> None:
    result = analyze_experiment(experiment(10, 20))

    pooled_rate = 30 / 200
    expected_z = 0.10 / sqrt(pooled_rate * (1 - pooled_rate) * (1 / 100 + 1 / 100))
    expected_p = 2 * norm.sf(abs(expected_z))
    expected_se = sqrt(0.10 * 0.90 / 100 + 0.20 * 0.80 / 100)

    assert result.control_sample_size == 100
    assert result.treatment_sample_size == 100
    assert result.control_conversions == 10
    assert result.treatment_conversions == 20
    assert result.control_rate == pytest.approx(0.10)
    assert result.treatment_rate == pytest.approx(0.20)
    assert result.absolute_uplift == pytest.approx(0.10)
    assert result.relative_uplift == pytest.approx(1.0)
    assert result.z_statistic == pytest.approx(expected_z)
    assert result.p_value == pytest.approx(expected_p)
    assert result.ci_lower == pytest.approx(0.10 - norm.ppf(0.975) * expected_se)
    assert result.ci_upper == pytest.approx(0.10 + norm.ppf(0.975) * expected_se)
    assert result.recommendation == "Treatment wins"


def test_significant_negative_difference_favors_control() -> None:
    result = analyze_experiment(experiment(25, 10))

    assert result.p_value < 0.05
    assert result.absolute_uplift < 0
    assert result.recommendation == "Control performs better"


def test_non_significant_difference_is_inconclusive() -> None:
    result = analyze_experiment(experiment(10, 11))

    assert result.p_value > 0.05
    assert result.recommendation == "Experiment is inconclusive and needs more data"


def test_zero_control_rate_has_undefined_relative_uplift() -> None:
    result = analyze_experiment(experiment(0, 4))

    assert result.relative_uplift is None


def test_degenerate_all_zero_experiment_is_handled() -> None:
    result = analyze_experiment(experiment(0, 0))

    assert result.z_statistic == 0
    assert result.p_value == 1
    assert result.ci_lower == 0
    assert result.ci_upper == 0


def test_sample_size_calculator_returns_stable_per_group_count() -> None:
    sample_size = calculate_sample_size(
        baseline_rate=0.10,
        minimum_detectable_effect=0.02,
        power=0.80,
        alpha=0.05,
    )

    assert sample_size == 3_835


@pytest.mark.parametrize(
    ("baseline", "effect", "power", "alpha"),
    [
        (0, 0.02, 0.8, 0.05),
        (0.1, 0, 0.8, 0.05),
        (0.99, 0.02, 0.8, 0.05),
        (0.1, 0.02, 1.0, 0.05),
        (0.1, 0.02, 0.8, 0),
    ],
)
def test_invalid_sample_size_inputs_are_rejected(
    baseline: float, effect: float, power: float, alpha: float
) -> None:
    with pytest.raises(ValueError):
        calculate_sample_size(baseline, effect, power, alpha)
