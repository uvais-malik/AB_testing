"""Validation and normalization for uploaded experiment data."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

REQUIRED_COLUMNS = ("user_id", "group", "converted")
EXPECTED_GROUPS = {"control", "treatment"}


class DataValidationError(ValueError):
    """Raised when experiment data contains one or more validation issues."""

    def __init__(self, issues: Iterable[str]) -> None:
        self.issues = tuple(issues)
        super().__init__("; ".join(self.issues))


def validate_experiment_data(data: pd.DataFrame) -> pd.DataFrame:
    """Return a normalized copy of valid experiment data.

    Validation issues are collected so users can correct an upload in one pass.
    Extra columns are allowed and preserved.
    """

    if not isinstance(data, pd.DataFrame):
        raise DataValidationError(["The uploaded object is not a tabular dataset."])

    issues: list[str] = []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        issues.append(f"Missing required columns: {', '.join(missing_columns)}.")
        raise DataValidationError(issues)

    if data.empty:
        raise DataValidationError(["The dataset is empty."])

    clean = data.copy()
    required = clean.loc[:, REQUIRED_COLUMNS]

    missing_counts = required.isna().sum()
    missing_details = [
        f"{column} ({int(count)})"
        for column, count in missing_counts.items()
        if count > 0
    ]

    group_as_text = clean["group"].astype("string")
    blank_group_count = int(group_as_text.str.strip().eq("").fillna(False).sum())
    user_as_text = clean["user_id"].astype("string")
    blank_user_count = int(user_as_text.str.strip().eq("").fillna(False).sum())
    if blank_group_count:
        missing_details.append(f"group ({blank_group_count} blank)")
    if blank_user_count:
        missing_details.append(f"user_id ({blank_user_count} blank)")
    if missing_details:
        issues.append("Missing values found in: " + ", ".join(missing_details) + ".")

    duplicate_mask = clean["user_id"].notna() & clean["user_id"].duplicated(keep=False)
    duplicate_count = int(duplicate_mask.sum())
    if duplicate_count:
        duplicate_ids = clean.loc[duplicate_mask, "user_id"].astype(str).unique()
        preview = ", ".join(duplicate_ids[:3])
        suffix = "…" if len(duplicate_ids) > 3 else ""
        issues.append(
            f"Duplicate user IDs found in {duplicate_count} rows "
            f"(for example: {preview}{suffix})."
        )

    normalized_groups = group_as_text.str.strip().str.lower()
    observed_groups = set(normalized_groups.dropna().loc[lambda values: values.ne("")].unique())
    if observed_groups != EXPECTED_GROUPS:
        displayed = ", ".join(sorted(observed_groups)) if observed_groups else "none"
        issues.append(
            "Expected exactly two groups named control and treatment; "
            f"found: {displayed}."
        )

    numeric_outcome = pd.to_numeric(clean["converted"], errors="coerce")
    invalid_outcome = numeric_outcome.isna() | ~numeric_outcome.isin([0, 1])
    if invalid_outcome.any():
        invalid_values = clean.loc[invalid_outcome, "converted"].astype(str).unique()
        preview = ", ".join(invalid_values[:3])
        suffix = "…" if len(invalid_values) > 3 else ""
        issues.append(f"Converted must contain only 0 or 1; found: {preview}{suffix}.")

    if issues:
        raise DataValidationError(issues)

    clean["group"] = normalized_groups.astype(str)
    clean["converted"] = numeric_outcome.astype("int8")
    return clean

