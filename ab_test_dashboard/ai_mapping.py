import json
import pandas as pd
import google.generativeai as genai
import typing_extensions as typing

class ColumnMapping(typing.TypedDict):
    user_id: str
    group: str
    converted: str

def map_columns_with_gemini(df: pd.DataFrame, api_key: str) -> dict:
    """Uses Gemini to identify which columns correspond to user_id, group, and converted.
    Returns a dictionary suitable for df.rename(columns=...).
    """
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    columns = list(df.columns)
    sample_data = df.head(3).to_dict(orient="records")
    
    prompt = f"""
You are an expert data analyst. You are provided with a sample of a CSV dataset for an A/B test.
The A/B test dashboard requires exactly three concepts:
- "user_id": A unique identifier for the user.
- "group": The experiment variant the user is in (representing control or treatment).
- "converted": A binary indicator of whether the user converted.

Here are the columns in the uploaded CSV: {columns}
Here is a 3-row sample of the data:
{sample_data}

Identify which column from the uploaded CSV corresponds to "user_id", which to "group", and which to "converted".
Respond with a JSON object.
"""

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ColumnMapping,
            temperature=0.0
        )
    )
    
    mapping = json.loads(response.text)
    
    # We need a reverse mapping for pandas rename: {old_col: new_col}
    # The AI returns {new_col: old_col}
    # Clean up column names by stripping spaces just in case
    columns_clean = {c.strip(): c for c in columns}
    rename_mapping = {}
    for k, v in mapping.items():
        v_clean = str(v).strip()
        if v_clean in columns_clean:
            rename_mapping[columns_clean[v_clean]] = k
            
    print("MAPPING:", rename_mapping, flush=True)
    return rename_mapping
