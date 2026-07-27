from ab_test_dashboard.reporting import explain_result, results_summary
from ab_test_dashboard.statistics import analyze_experiment
from ab_test_dashboard.sample_data import make_sample_data
from ab_test_dashboard.validation import validate_experiment_data


def test_summary_contains_computed_result_and_source() -> None:
    result = analyze_experiment(validate_experiment_data(make_sample_data()))

    summary = results_summary(result, "Synthetic sample")

    assert len(summary) == 1
    assert summary.loc[0, "data_source"] == "Synthetic sample"
    assert summary.loc[0, "p_value"] == result.p_value
    assert summary.loc[0, "recommendation"] == result.recommendation


def test_plain_english_explanation_mentions_p_value_and_interval() -> None:
    result = analyze_experiment(validate_experiment_data(make_sample_data()))

    explanation = explain_result(result)

    assert f"{result.p_value:.4f}" in explanation
    assert "confidence interval" in explanation

