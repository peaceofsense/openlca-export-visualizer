import numpy as np
import pandas as pd
import streamlit as st

IMPACT_LABELS = {
    "acidification: terrestrial": "TAP",
    "climate change": "GWP100",
    "ecotoxicity: freshwater": "FETP",
    "ecotoxicity: marine": "METP",
    "ecotoxicity: terrestrial": "TETP",
    "energy resources: non-renewable, fossil": "FFP",
    "eutrophication: freshwater": "FEP",
    "eutrophication: marine": "MEP",
    "human toxicity: carcinogenic": "HTPc",
    "human toxicity: non-carcinogenic": "HTPnc",
    "ionising radiation": "IRP",
    "land use": "LOP",
    "material resources: metals/minerals": "SOP",
    "ozone depletion": "ODP",
    "particulate matter formation": "PMFP",
    "photochemical oxidant formation: human health": "HOFP",
    "photochemical oxidant formation: terrestrial ecosystems": "EOFP",
    "water use": "WCP",
}

ENDPOINT_IMPACT_LABELS = {
    "total: ecosystem quality": "Ecosystem Quality",
    "total: human health": "Human Health",
    "total: natural resources": "Natural Resources",
}

def load_excel(uploaded_file):
    """
    Parse an openLCA midpoint Excel export.
    Row 0 of the raw read holds the real column headers; rows above are junk.
    Returns a DataFrame with: Impact category, Reference unit, Result,
    and a normalised 'Impact category clean' column.
    """
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Impacts")
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)
        df["Result"] = pd.to_numeric(df["Result"], errors="coerce")
        df["Impact category clean"] = (
            df["Impact category"].str.split(" - ").str[0].str.strip().str.lower()
        )
        return df
    except Exception as e:
        st.error(f"Could not read **{uploaded_file.name}**: {e}")
        return None

def build_combined(dfs: dict, selected_categories: list) -> pd.DataFrame:
    # Initialize dictionary with a separate column for Unit
    results = {"Impact category": [], "Unit": []}
    for label in dfs:
        results[label] = []

    for cat in selected_categories:
        unit = ""
        # Search for the unit in the uploaded files
        for df in dfs.values():
            matched = df[
                df["Impact category clean"].str.contains(
                    cat.strip().lower(), case=False, na=False
                )
            ]
            if not matched.empty:
                raw_unit = matched.iloc[0].get("Reference unit", "")
                unit = str(raw_unit).strip() if pd.notna(raw_unit) else ""
                break

        # STORE SEPARATELY: Keep the name clean
        results["Impact category"].append(cat)
        results["Unit"].append(unit)

        for label, df in dfs.items():
            matched = df[
                df["Impact category clean"].str.contains(
                    cat.strip().lower(), case=False, na=False
                )
            ]
            results[label].append(
                float(matched.iloc[0]["Result"]) if not matched.empty else np.nan
            )

    return pd.DataFrame(results)

def normalize(df_combined: pd.DataFrame, scenario_cols: list) -> pd.DataFrame:
    """Row-normalize by max value across scenarios."""
    df = df_combined.set_index("Impact category")[scenario_cols]
    df = df.div(df.max(axis=1), axis=0)
    return df.reset_index()
