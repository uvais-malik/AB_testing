"""Core package for the A/B Test Decision Dashboard."""

from .statistics import AnalysisResult, analyze_experiment, calculate_sample_size
from .validation import DataValidationError, validate_experiment_data

__all__ = [
    "AnalysisResult",
    "DataValidationError",
    "analyze_experiment",
    "calculate_sample_size",
    "validate_experiment_data",
]

