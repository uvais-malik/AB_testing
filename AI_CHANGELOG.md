# AI Modifications & Enhancements Changelog

This document tracks all the autonomous modifications and features added to the A/B Test Decision Dashboard to enable AI-powered data processing and Exploratory Data Analysis (EDA).

## 1. Dependency Management
- **File Modified**: `requirements.txt`
- **Change**: Added `google-generativeai` to the project dependencies to enable interaction with the Gemini API.

## 2. Secure API Key Management
- **File Created**: `.streamlit/secrets.toml`
- **Change**: Created a Streamlit secrets file to securely store the `GEMINI_API_KEY`.
- **File Modified**: `app.py`
- **Change**: Updated the sidebar UI to attempt to read the key from `secrets.toml`. If not found, it seamlessly provides a password-masked text input for the user to inject their API key on the fly.

## 3. Autonomous AI Column Mapping
- **File Created**: `ab_test_dashboard/ai_mapping.py`
- **Change**: Created a core AI utility that passes the first 5 rows of any uploaded CSV to the `gemini-2.5-flash` model. The AI interprets the column context (e.g., understanding that `VARIANT_NAME` means `group`, or `REVENUE` means `converted`) and returns a strict JSON mapping.
- **File Modified**: `app.py`
- **Change**: Integrated a seamless fallback mechanism into the main dashboard pipeline. If a user uploads a CSV and it immediately fails validation due to missing columns, the app catches the error, triggers the Gemini mapping process, renames the dataset columns on-the-fly, and re-submits it for validation. Added UI components (spinners, success banners, error states) to keep the user informed.

## 4. Auto-EDA (Exploratory Data Analysis & Cleaning)
- **File Modified**: `ab_test_dashboard/validation.py`
- **Change**: Completely revamped the `validate_experiment_data` function. Instead of strictly rejecting imperfect data, it now attempts to autonomously clean it before validation:
  - **Auto-Binarization**: Detects continuous conversion metrics (like tracking `$4.27` in revenue instead of a `0` or `1` click). It auto-converts any numeric value `> 0` to a `1` (converted) to satisfy the Two-Proportion Z-Test assumptions.
  - **Auto-Deduplication**: Detects if a dataset has multiple entries per `user_id` (e.g. longitudinal session data). It automatically groups the rows by `user_id`, retaining a conversion if the user converted in *any* of their sessions, and discarding the duplicate rows to prevent sample ratio inflation.
  - **Auto-Group Mapping**: Detects if a dataset has exactly two groups that are not named "control" and "treatment" (e.g., "control" and "variant"). It runs a synonym check to auto-map alternative names. As a final fallback, it calculates the conversion rate of both unknown groups and maps the underperforming one to "control" and the other to "treatment".

## 5. Server Lifecycle Management
- **Actions Taken**: Managed the background Uvicorn/Streamlit server processes, performing hard restarts to clear Streamlit's internal cache and ensure newly created modules (like `validation.py` edits) were successfully hot-reloaded into the runtime environment.
