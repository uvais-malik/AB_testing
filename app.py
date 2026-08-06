"""Streamlit entry point for the A/B Test Decision Dashboard."""

from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from ab_test_dashboard.charts import confidence_interval_chart, conversion_rate_chart
from ab_test_dashboard.reporting import explain_result, results_summary
from ab_test_dashboard.sample_data import make_sample_data
from ab_test_dashboard.statistics import analyze_experiment, calculate_sample_size
from ab_test_dashboard.validation import DataValidationError, validate_experiment_data
from ab_test_dashboard.ai_mapping import map_columns_with_gemini

st.set_page_config(
    page_title="A/B Test Decision Dashboard",
    page_icon="↗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #09090E 0%, #111A28 50%, #150F24 100%);
        color: #E2E8F0;
    }
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.4) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        width: 280px !important;
        min-width: 280px !important;
        max-width: 280px !important;
    }
    [data-testid="stSidebar"] * { color: #E2E8F0; }
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0.65rem;
        padding: 0.55rem 0.7rem;
        margin-bottom: 0.25rem;
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-1px);
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.03);
        border-color: rgba(255, 255, 255, 0.1);
        border-radius: 0.75rem;
    }
    [data-testid="stSidebar"] .stDownloadButton button {
        background: linear-gradient(90deg, #00F0FF 0%, #0066FF 100%);
        border: none;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 102, 255, 0.3);
    }
    [data-testid="stSidebar"] .stDownloadButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(0, 102, 255, 0.5);
    }
    [data-testid="stSidebar"] .stDownloadButton button * {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    .block-container {
        max-width: 1240px;
        padding-top: 4rem;
        padding-bottom: 4rem;
    }
    h1, h2, h3, h4, h5, h6 { 
        letter-spacing: -0.025em; 
        color: #F8FAFC !important; 
        font-weight: 800;
    }
    p, span, div {
        color: #CBD5E1;
    }
    .eyebrow {
        color: #00F0FF;
        display: block;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        line-height: 1.5;
        min-height: 1.25rem;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
    }
    .subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 760px;
        margin-top: -0.5rem;
        margin-bottom: 1.75rem;
    }
    .result-banner {
        border-radius: 0.9rem;
        padding: 1.2rem 1.5rem;
        margin: 0.2rem 0 1.25rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 750;
        font-size: 1.1rem;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }
    .result-win { 
        background: rgba(0, 255, 170, 0.1); 
        border-color: rgba(0, 255, 170, 0.3); 
        color: #00FFAA !important; 
        box-shadow: 0 0 20px rgba(0, 255, 170, 0.1);
    }
    .result-loss { 
        background: rgba(255, 42, 109, 0.1); 
        border-color: rgba(255, 42, 109, 0.3); 
        color: #FF2A6D !important; 
        box-shadow: 0 0 20px rgba(255, 42, 109, 0.1);
    }
    .result-neutral { 
        background: rgba(255, 204, 0, 0.1); 
        border-color: rgba(255, 204, 0, 0.3); 
        color: #FFCC00 !important; 
        box-shadow: 0 0 20px rgba(255, 204, 0, 0.1);
    }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        padding: 1.2rem 1.2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(0, 240, 255, 0.3);
        box-shadow: 0 8px 15px rgba(0, 240, 255, 0.1);
    }
    [data-testid="stMetricLabel"] { 
        color: #94A3B8; 
        font-weight: 600; 
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] { 
        color: #FFFFFF; 
        letter-spacing: -0.02em; 
        font-weight: 700;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.02);
        border-color: rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        backdrop-filter: blur(10px);
        padding: 1rem;
    }
    .section-kicker {
        color: #94A3B8;
        font-size: 0.9rem;
        margin-top: -0.8rem;
        margin-bottom: 1.2rem;
    }
    .source-note {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 0.7rem;
        padding: 0.7rem 0.8rem;
        color: #CBD5E1 !important;
        font-size: 0.82rem;
        line-height: 1.45;
    }
    .schema-code {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 0.6rem;
        color: #00F0FF !important;
        font-family: 'Fira Code', monospace;
        font-size: 0.85rem;
        padding: 0.65rem 0.7rem;
        text-align: center;
        letter-spacing: 0.05em;
    }
    .footer-note { color: #64748B; font-size: 0.8rem; margin-top: 3rem; text-align: center; }
    .impact-box {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.1) 0%, rgba(138, 43, 226, 0.1) 100%);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 1.2rem;
        padding: 1.5rem 2rem;
        margin: 1rem 0 2rem 0;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    .impact-box h4 { 
        color: #FFFFFF !important; 
        margin: 0 0 1rem 0; 
        font-size: 1.1rem; 
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .impact-row { display: flex; gap: 2rem; flex-wrap: wrap; margin-top: 0.75rem; }
    .impact-item { flex: 1; min-width: 140px; }
    .impact-label { font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; }
    .impact-value { font-size: 1.8rem; font-weight: 800; line-height: 1.2; color: #00F0FF; text-shadow: 0 0 15px rgba(0, 240, 255, 0.4); }
    .impact-sub { font-size: 0.8rem; color: #64748B; margin-top: 0.2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _format_relative(value: float | None) -> str:
    return "N/A" if value is None else f"{value:+.2%}"


def _render_sidebar() -> tuple[pd.DataFrame | None, str, int]:
    with st.sidebar:
        st.markdown("## Experiment data")
        st.caption("Choose the included synthetic example or analyze your own CSV.")
        source = st.radio(
            "Data source",
            ("Built-in sample", "Upload CSV"),
            label_visibility="collapsed",
        )

        if source == "Built-in sample":
            data = make_sample_data()
            st.markdown(
                '<div class="source-note">Synthetic demonstration data · '
                f'{len(data):,} users · deterministic seed</div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                "Download sample CSV",
                data.to_csv(index=False).encode("utf-8"),
                file_name="synthetic_ab_experiment.csv",
                mime="text/csv",
                width="stretch",
            )
            source_label = "Built-in synthetic sample"
        else:
            uploaded = st.file_uploader(
                "Upload experiment CSV",
                type=["csv"],
                help="Required columns: user_id, group, converted",
            )
            if uploaded is None:
                st.info("Upload a CSV to start the analysis.")
                data = None
            else:
                try:
                    data = pd.read_csv(uploaded)
                except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
                    st.error(f"Could not read this CSV: {error}")
                    data = None
            source_label = uploaded.name if uploaded is not None else "Uploaded CSV"

        st.divider()
        st.markdown("**Required schema**")
        st.markdown(
            '<div class="schema-code">user_id, group, converted</div>',
            unsafe_allow_html=True,
        )
        st.caption("Groups must be control and treatment. Converted must be 0 or 1.")

        st.divider()
        st.markdown("**Business impact settings**")
        monthly_users = st.number_input(
            "Monthly active users",
            min_value=100,
            max_value=100_000_000,
            value=50_000,
            step=1_000,
            help="How many users see this feature per month? Used to estimate real-world impact.",
        )

        st.divider()
        st.markdown("**AI Settings**")
        use_ai_mapping = st.checkbox("Auto-map columns using Gemini", value=True)
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except:
            api_key = ""
        if use_ai_mapping and not api_key:
            api_key = st.text_input("Gemini API Key", type="password")

    return data, source_label, monthly_users, use_ai_mapping, api_key


raw_data, source_label, monthly_users, use_ai_mapping, api_key = _render_sidebar()

st.markdown('<p class="eyebrow">Experiment intelligence</p>', unsafe_allow_html=True)
st.title("A/B Test Decision Dashboard")
st.markdown(
    '<div class="subtitle">Turn user-level conversion data into a defensible '
    "ship, stop, or keep-testing decision — in seconds.</div>",
    unsafe_allow_html=True,
)

if raw_data is None:
    st.info("Select the built-in sample or upload a CSV from the sidebar to continue.")
    st.stop()

try:
    data = validate_experiment_data(raw_data)
except DataValidationError as error:
    missing_cols_error = any("Missing required columns" in issue for issue in error.issues)
    if missing_cols_error and use_ai_mapping and api_key:
        with st.spinner("AI is analyzing column names..."):
            try:
                mapping = map_columns_with_gemini(raw_data, api_key)
            except Exception as e:
                mapping = {}
                st.error(f"AI crashed with error: {e}")
            if mapping:
                st.success(f"AI auto-mapped columns: {mapping}")
                raw_data = raw_data.rename(columns=mapping)
                try:
                    data = validate_experiment_data(raw_data)
                except DataValidationError as e2:
                    st.error("This dataset needs attention before it can be analyzed.")
                    for issue in e2.issues:
                        st.markdown(f"- {issue}")
                    st.stop()
            else:
                st.error("This dataset needs attention before it can be analyzed.")
                for issue in error.issues:
                    st.markdown(f"- {issue}")
                st.error(f"AI auto-mapping failed or couldn't find a mapping. Raw mapping returned: {mapping}")
                st.stop()
    else:
        st.error("This dataset needs attention before it can be analyzed.")
        for issue in error.issues:
            st.markdown(f"- {issue}")
        st.stop()

result = analyze_experiment(data)
banner_class = {
    "Treatment wins": "result-win",
    "Control performs better": "result-loss",
}.get(result.recommendation, "result-neutral")
st.markdown(
    f'<div class="result-banner {banner_class}">Recommendation · '
    f"{result.recommendation}</div>",
    unsafe_allow_html=True,
)

# ── Business Impact Panel ─────────────────────────────────────────────────────
extra_conversions_per_month = round(result.absolute_uplift * monthly_users)
direction_word = "more" if result.absolute_uplift >= 0 else "fewer"
sign = "+" if result.absolute_uplift >= 0 else ""

relative_label = (
    _format_relative(result.relative_uplift)
    if result.relative_uplift is not None
    else "N/A"
)
annualised = extra_conversions_per_month * 12

st.markdown(
    f"""
    <div class="impact-box">
        <h4>📈 Projected Business Impact — based on {monthly_users:,} monthly users</h4>
        <div class="impact-row">
            <div class="impact-item">
                <div class="impact-label">Extra conversions / month</div>
                <div class="impact-value">{sign}{extra_conversions_per_month:,}</div>
                <div class="impact-sub">{direction_word} than control</div>
            </div>
            <div class="impact-item">
                <div class="impact-label">Annualised lift</div>
                <div class="impact-value">{sign}{annualised:,}</div>
                <div class="impact-sub">conversions over 12 months</div>
            </div>
            <div class="impact-item">
                <div class="impact-label">Relative uplift</div>
                <div class="impact-value">{relative_label}</div>
                <div class="impact-sub">vs. current baseline</div>
            </div>
            <div class="impact-item">
                <div class="impact-label">Statistical confidence</div>
                <div class="impact-value">{result.confidence_level:.0%}</div>
                <div class="impact-sub">p-value: {result.p_value:.4f}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_row_one = st.columns(4)
metric_row_one[0].metric("Control users", f"{result.control_sample_size:,}")
metric_row_one[1].metric("Treatment users", f"{result.treatment_sample_size:,}")
metric_row_one[2].metric("Control conversions", f"{result.control_conversions:,}")
metric_row_one[3].metric("Treatment conversions", f"{result.treatment_conversions:,}")

st.write("")
metric_row_two = st.columns(4)
metric_row_two[0].metric("Control conversion rate", f"{result.control_rate:.2%}")
metric_row_two[1].metric(
    "Treatment conversion rate",
    f"{result.treatment_rate:.2%}",
    delta=f"{result.absolute_uplift:+.2%}",
)
metric_row_two[2].metric("Relative uplift", _format_relative(result.relative_uplift))
metric_row_two[3].metric("P-value", f"{result.p_value:.4f}")

st.write("")
chart_left, chart_right = st.columns((1, 1), gap="large")
with chart_left:
    with st.container(border=True):
        st.subheader("Conversion rate")
        st.markdown(
            '<div class="section-kicker">Observed performance by experiment group</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            conversion_rate_chart(result),
            width="stretch",
            config={"displayModeBar": False},
        )

with chart_right:
    with st.container(border=True):
        st.subheader("Uncertainty around uplift")
        st.markdown(
            f'<div class="section-kicker">{result.confidence_level:.0%} confidence '
            "interval for treatment minus control</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            confidence_interval_chart(result),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.caption(
            f"Estimate: {result.absolute_uplift:+.2%} · "
            f"CI: [{result.ci_lower:+.2%}, {result.ci_upper:+.2%}]"
        )

with st.container(border=True):
    st.subheader("What this means")
    st.write(explain_result(result))
    with st.expander("Statistical details (for analysts)"):
        st.markdown(
            f"""
            - **Test:** two-sided, pooled two-proportion z-test
            - **Null hypothesis:** control and treatment conversion rates are equal
            - **Z-statistic:** {result.z_statistic:.4f}
            - **Significance level:** {result.alpha:.0%}
            - **Confidence interval:** unpooled Wald interval for treatment − control
            - **Decision rule:** recommend a winner only when p < {result.alpha:.2f}
            """
        )

    summary = results_summary(result, source_label)
    st.download_button(
        "Download results summary (CSV)",
        summary.to_csv(index=False).encode("utf-8"),
        file_name="ab_test_results_summary.csv",
        mime="text/csv",
        type="primary",
    )

with st.expander(f"Validated data preview · {len(data):,} rows"):
    st.dataframe(data.head(100), width="stretch", hide_index=True)
    st.caption("Preview shows the first 100 validated rows.")

st.divider()
st.header("Plan the next experiment")
st.markdown(
    '<div class="section-kicker">Estimate the minimum sample needed before launching '
    "a new test — so you don't stop too early or run too long.</div>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    input_columns = st.columns(4)
    baseline_percent = input_columns[0].number_input(
        "Current conversion rate (%)",
        min_value=0.1,
        max_value=99.0,
        value=10.0,
        step=0.5,
        help="What percentage of users currently convert? (e.g. 10 means 10%)",
    )
    mde_percent = input_columns[1].number_input(
        "Smallest improvement worth detecting (pp)",
        min_value=0.1,
        max_value=50.0,
        value=2.0,
        step=0.5,
        help="The smallest real-world gain you'd care about, in percentage points. "
             "E.g. 2 means going from 10% to 12% conversion.",
    )
    power = input_columns[2].select_slider(
        "Test sensitivity",
        options=[0.70, 0.75, 0.80, 0.85, 0.90, 0.95],
        value=0.80,
        format_func=lambda value: f"{value:.0%}",
        help="How reliably should the test detect a real improvement? 80% is the industry standard.",
    )
    significance = input_columns[3].select_slider(
        "Significance level",
        options=[0.01, 0.05, 0.10],
        value=0.05,
        format_func=lambda value: f"{value:.0%}",
        help="Acceptable false-positive rate. 5% is the most common choice.",
    )

    try:
        required_per_group = calculate_sample_size(
            baseline_rate=baseline_percent / 100,
            minimum_detectable_effect=mde_percent / 100,
            power=power,
            alpha=significance,
        )
        result_columns = st.columns((1, 2))
        result_columns[0].metric("Required users per group", f"{required_per_group:,}")
        result_columns[1].success(
            f"Plan for at least **{required_per_group * 2:,} total users** "
            f"({required_per_group:,} in each group) to confidently detect an increase "
            f"from {baseline_percent:.1f}% to {baseline_percent + mde_percent:.1f}% conversion."
        )
    except ValueError as error:
        st.warning(str(error))

st.markdown(
    '<div class="footer-note">Decisions should also consider guardrail metrics, '
    "experiment integrity, novelty effects, and business costs. "
    "Statistical significance is one input — not the final answer.</div>",
    unsafe_allow_html=True,
)
