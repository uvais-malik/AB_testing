"""Deterministic synthetic data for the built-in dashboard example."""

from __future__ import annotations

import numpy as np
import pandas as pd


def make_sample_data(seed: int = 42) -> pd.DataFrame:
    """Create a reproducible, clearly synthetic A/B conversion dataset."""

    rng = np.random.default_rng(seed)
    n_control = 1_500
    n_treatment = 1_500
    control = rng.binomial(1, 0.10, size=n_control)
    treatment = rng.binomial(1, 0.12, size=n_treatment)

    return pd.DataFrame(
        {
            "user_id": [
                *(f"C-{index:05d}" for index in range(1, n_control + 1)),
                *(f"T-{index:05d}" for index in range(1, n_treatment + 1)),
            ],
            "group": ["control"] * n_control + ["treatment"] * n_treatment,
            "converted": np.concatenate([control, treatment]),
        }
    )

