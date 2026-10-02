import urllib.parse
import json
import pandas as pd

def make_search_link_esp(ocupacion: str) -> str:
    """
    Generate dynamic Spanish job search URL.
    Format: https://www.google.com/search?q=puerto%20rico%20empleo%20[ocupacion]
    Does not generate link if ocupacion is empty.
    """
    if not ocupacion:
        return ""
    query = f"puerto rico empleo {ocupacion}"
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"


def make_search_link_eng(occupation: str) -> str:
    """
    Generate dynamic English job search URL.
    Format: https://www.google.com/search?q=puerto%20rico%20jobs%20[occupation]
    Does not generate link if occupation is empty.
    """
    if not occupation:
        return ""
    query = f"puerto rico jobs {occupation}"
    return f"https://www.google.com/search?q={urllib.parse.quote(query)}"


def load_json_dataset(filepath: str) -> list:
    """
    Load data from a JSON file.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv_dataset(records: list, filepath: str) -> None:
    """
    Export final processed data to CSV.
    """
    df = pd.DataFrame(records)
    # Ensure columns order is clean
    columns_order = [
        "id_persona",
        "interestedareaofwork",
        "interestedareaofstudy",
        "areaofworkexperience",
        "areaofstudy",
        "ocupacion",
        "occupation",
        "ocup_link_esp",
        "ocup_link_eng",
        "selected_field",
        "raw_text",
        "confidence"
    ]
    # Filter for existing columns in case some records don't have all metadata columns
    existing_columns = [c for c in columns_order if c in df.columns]
    df = df[existing_columns]
    
    df.to_csv(filepath, index=False, encoding="utf-8")
    print(f"Exported dataset successfully to {filepath}")
