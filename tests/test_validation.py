import pandas as pd
import pytest

from ab_test_dashboard.validation import DataValidationError, validate_experiment_data


def valid_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": ["u1", "u2", "u3", "u4"],
            "group": ["control", "control", "treatment", "treatment"],
            "converted": [0, 1, 0, 1],
        }
    )


def test_valid_data_is_normalized() -> None:
    data = valid_data()
    data["group"] = [" Control ", "CONTROL", "Treatment", " treatment "]

    clean = validate_experiment_data(data)

    assert clean["group"].tolist() == ["control", "control", "treatment", "treatment"]
    assert clean["converted"].dtype.name == "int8"


def test_missing_required_column_is_rejected() -> None:
    with pytest.raises(DataValidationError, match="Missing required columns: converted"):
        validate_experiment_data(valid_data().drop(columns="converted"))


def test_missing_values_are_rejected() -> None:
    data = valid_data()
    data.loc[0, "user_id"] = None

    with pytest.raises(DataValidationError, match="Missing values"):
        validate_experiment_data(data)


def test_duplicate_user_ids_are_rejected() -> None:
    data = valid_data()
    data.loc[1, "user_id"] = "u1"

    with pytest.raises(DataValidationError, match="Duplicate user IDs"):
        validate_experiment_data(data)


@pytest.mark.parametrize(
    "groups",
    [
        ["control", "control", "control", "control"],
        ["a", "a", "b", "b"],
        ["control", "treatment", "holdout", "holdout"],
    ],
)
def test_exact_expected_groups_are_required(groups: list[str]) -> None:
    data = valid_data()
    data["group"] = groups

    with pytest.raises(DataValidationError, match="exactly two groups"):
        validate_experiment_data(data)


@pytest.mark.parametrize("invalid_value", [2, -1, "yes", 0.5])
def test_non_binary_outcomes_are_rejected(invalid_value: object) -> None:
    data = valid_data()
    data["converted"] = data["converted"].astype(object)
    data.loc[0, "converted"] = invalid_value

    with pytest.raises(DataValidationError, match="only 0 or 1"):
        validate_experiment_data(data)


def test_multiple_issues_are_reported_together() -> None:
    data = valid_data()
    data.loc[1, "user_id"] = "u1"
    data.loc[2, "converted"] = 8

    with pytest.raises(DataValidationError) as error:
        validate_experiment_data(data)

    assert len(error.value.issues) == 2
