from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_renders_sample_workflow_without_exceptions() -> None:
    app_path = Path(__file__).parents[1] / "app.py"

    app = AppTest.from_file(str(app_path)).run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "A/B Test Decision Dashboard"
    assert any(metric.label == "Control users" for metric in app.metric)
    assert any(
        button.label == "Download results summary"
        for button in app.get("download_button")
    )
