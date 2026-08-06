"""Plotly visualizations for experiment results."""

from __future__ import annotations

import plotly.graph_objects as go

from .statistics import AnalysisResult

CONTROL_COLOR = "#64748B"
TREATMENT_COLOR = "#00F0FF"
TEXT_COLOR = "#E2E8F0"
GRID_COLOR = "rgba(255, 255, 255, 0.05)"


def _base_layout() -> dict:
    return {
        "font": {"family": "Inter, Arial, sans-serif", "color": TEXT_COLOR},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "margin": {"l": 12, "r": 12, "t": 20, "b": 12},
        "hoverlabel": {"bgcolor": "#1E293B", "bordercolor": "#334155", "font": {"color": "#FFFFFF"}},
    }


def conversion_rate_chart(result: AnalysisResult) -> go.Figure:
    """Compare control and treatment conversion rates."""

    rates = [result.control_rate, result.treatment_rate]
    figure = go.Figure(
        go.Bar(
            x=["Control", "Treatment"],
            y=rates,
            marker_color=[CONTROL_COLOR, TREATMENT_COLOR],
            text=[f"{rate:.2%}" for rate in rates],
            textposition="outside",
            hovertemplate="%{x}<br>Conversion rate: %{y:.2%}<extra></extra>",
            width=0.55,
        )
    )
    upper = min(1.0, max(rates) * 1.28 + 0.01)
    figure.update_layout(
        **_base_layout(),
        height=320,
        showlegend=False,
        bargap=0.45,
        yaxis={
            "title": "Conversion rate",
            "tickformat": ".0%",
            "range": [0, upper],
            "gridcolor": GRID_COLOR,
            "zeroline": False,
        },
        xaxis={"title": None, "showgrid": False},
    )
    return figure


def confidence_interval_chart(result: AnalysisResult) -> go.Figure:
    """Plot the treatment-minus-control estimate and its confidence interval."""

    lower_error = result.absolute_uplift - result.ci_lower
    upper_error = result.ci_upper - result.absolute_uplift
    figure = go.Figure(
        go.Scatter(
            x=[result.absolute_uplift],
            y=["Rate difference"],
            mode="markers",
            marker={"size": 13, "color": TREATMENT_COLOR, "symbol": "diamond"},
            error_x={
                "type": "data",
                "symmetric": False,
                "array": [upper_error],
                "arrayminus": [lower_error],
                "color": TREATMENT_COLOR,
                "thickness": 3,
                "width": 7,
            },
            hovertemplate=(
                "Difference: %{x:.2%}<br>"
                f"{result.confidence_level:.0%} CI: "
                f"[{result.ci_lower:.2%}, {result.ci_upper:.2%}]"
                "<extra></extra>"
            ),
        )
    )
    padding = max(0.01, (result.ci_upper - result.ci_lower) * 0.35)
    x_min = min(result.ci_lower - padding, -0.005)
    x_max = max(result.ci_upper + padding, 0.005)
    figure.add_vline(x=0, line_width=2, line_dash="dash", line_color=CONTROL_COLOR)
    figure.update_layout(
        **_base_layout(),
        height=250,
        showlegend=False,
        xaxis={
            "title": "Treatment − control",
            "tickformat": ".1%",
            "range": [x_min, x_max],
            "gridcolor": GRID_COLOR,
            "zeroline": False,
        },
        yaxis={"title": None, "showgrid": False},
    )
    return figure

