"""
LCA Midpoint and Endpoint Impact Assessment - Radar Chart Visualizer
Streamlit app to interactively explore openLCA impact assessment exports.

Usage:
    streamlit run app.py

Input:
    - Upload one or more openLCA Excel exports
    - Each file must have a sheet named 'Impacts'
    - The sheet should have columns: Impact category, Reference unit, Result
      (with the actual headers in row 2, per openLCA export format)
"""

import io
from math import pi

import pandas as pd
import streamlit as st
from data_processing import (
    ENDPOINT_IMPACT_LABELS,
    IMPACT_LABELS,
    build_combined,
    load_excel,
    normalize,
)
from plotting import plot_radar

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LCA Studio",
    page_icon="🌿",
    layout="wide",
)

# ── Light theme styling ───────────────────────────────────────────────────────
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: -0.02em;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .streamlit-expanderHeader {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ── App shell ─────────────────────────────────────────────────────────────────

st.markdown("# 🌿 LCA Studio")
st.markdown(
    "<p style='color:#6b7280;font-family:IBM Plex Mono,monospace;font-size:0.82rem;'>"
    "Life cycle impact assessment · openLCA export visualizer"
    "</p>",
    unsafe_allow_html=True,
)

with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. Export your results from openLCA as Excel (`.xlsx`) — midpoint or endpoint
    2. Upload one or more files to compare scenarios on the same radar chart
    3. Adjust visualization parameters as needed and export as SVG

    The app expects a sheet named **`Impacts`** with standard ReCiPe 2016 headers.
    [View source on GitHub](https://github.com/peaceofsense/openlca-export-visualizer)
    """)


# ── Helper for rendering a radar tab ──────────────────────────────────────────
def render_radar_tab(tab_name, labels_dict, key_prefix):
    # ── Upload (collapsible) ──────────────────────────────────────────────────
    with st.expander("📂 Upload scenario files", expanded=True):
        uploaded_files = st.file_uploader(
            f"Drop one or more openLCA {tab_name.lower()} Excel exports (.xlsx)",
            type=["xlsx"],
            accept_multiple_files=True,
            help="Each file must contain a sheet named 'Impacts'.",
            label_visibility="collapsed",
            key=f"{key_prefix}_uploader",
        )

    if not uploaded_files:
        st.info(
            f"Upload at least one openLCA {tab_name.lower()} Excel export to get started. "
            "Multiple files can be compared on the same chart."
        )
        return

    # ── Rename (collapsible, collapsed by default) ────────────────────────────
    custom_names: dict[str, str] = {}
    with st.expander("✏️ Rename scenarios", expanded=False):
        cols_rename = st.columns(min(len(uploaded_files), 3))
        for idx, f in enumerate(uploaded_files):
            default = f.name.replace(".xlsx", "").replace(".XLSX", "")
            with cols_rename[idx % len(cols_rename)]:
                custom_names[f.name] = st.text_input(
                    f.name, value=default, key=f"{key_prefix}_name_{f.name}"
                )

    # ── Load files ────────────────────────────────────────────────────────────
    dfs: dict[str, pd.DataFrame] = {}
    for f in uploaded_files:
        label = custom_names.get(f.name, f.name.replace(".xlsx", ""))
        df = load_excel(f)
        if df is not None:
            dfs[label] = df

    if not dfs:
        st.error("No valid files loaded. Check each file has an 'Impacts' sheet.")
        return

    all_cats_raw = set()
    for df in dfs.values():
        all_cats_raw.update(df["Impact category clean"].dropna().unique().tolist())

    # Remove redundant categories if a "total: " version also exists
    to_remove = {c for c in all_cats_raw if f"total: {c}" in all_cats_raw}
    all_cats_raw -= to_remove

    all_cats_sorted = sorted(all_cats_raw)

    # ── Two-column layout: settings (left) | chart (right) ───────────────────
    col_settings, col_chart = st.columns([1, 2], gap="large")

    with col_settings:
        st.markdown("#### Chart settings")

        with st.expander("Scenarios", expanded=True):
            selected_scenarios = st.multiselect(
                "Select scenarios",
                options=list(dfs.keys()),
                default=list(dfs.keys()),
                label_visibility="collapsed",
                key=f"{key_prefix}_scenarios",
            )

        with st.expander("Impact categories", expanded=True):
            # Only select the first 3 categories by default if there are enough
            default_categories_selection = (
                all_cats_sorted[:3] if len(all_cats_sorted) >= 3 else all_cats_sorted
            )
            selected_categories = st.multiselect(
                "Select categories",
                options=all_cats_sorted,
                default=default_categories_selection,
                format_func=lambda c: f"{labels_dict.get(c, c)}  —  {c}",
                label_visibility="collapsed",
                key=f"{key_prefix}_categories",
            )

        st.markdown("---")
        angle_offset_deg = st.slider(
            "Angle offset (°)",
            min_value=0,
            max_value=360,
            value=45 if "Midpoint" in tab_name else 90,
            step=5,
            key=f"{key_prefix}_angle",
        )
        fig_size = st.slider(
            "Figure size",
            min_value=3.0,
            max_value=8.0,
            value=4.0,
            step=0.2,
            key=f"{key_prefix}_size",
        )
        chart_title = st.text_input(
            "Chart title (optional)", value="", key=f"{key_prefix}_title"
        )

    # ── Chart ─────────────────────────────────────────────────────────────────
    with col_chart:
        if not selected_scenarios:
            st.warning("Select at least one scenario.")
            return
        if len(selected_categories) < 3:
            st.warning("Select at least 3 impact categories.")
            return

        dfs_selected = {k: v for k, v in dfs.items() if k in selected_scenarios}
        df_combined = build_combined(dfs_selected, selected_categories)
        df_norm = normalize(df_combined, selected_scenarios)

        angle_offset_rad = angle_offset_deg * pi / 180
        fig = plot_radar(
            df_norm,
            categories_col="Impact category",
            scenario_cols=selected_scenarios,
            angle_offset=angle_offset_rad,
            figsize=(fig_size, fig_size),
            title=chart_title,
            labels_dict=labels_dict,
        )

        if fig:
            # Constrain rendered width to roughly match figsize
            pad = max(0.5, (8 - fig_size) / 4)
            _, c_fig, _ = st.columns([pad, fig_size, pad])
            with c_fig:
                st.pyplot(fig, use_container_width=False)

            buf = io.BytesIO()
            fig.savefig(buf, format="svg", bbox_inches="tight", facecolor="#ffffff")
            st.download_button(
                "⬇ Download SVG",
                data=buf.getvalue(),
                file_name=f"lca_{tab_name.lower()}_radar.svg",
                mime="image/svg+xml",
                key=f"{key_prefix}_dl",
            )

    # ── Data tables ───────────────────────────────────────────────────────────
    st.divider()
    with st.expander("View normalized data table"):
        # We display ONLY the impact category here (Units are hidden)
        st.dataframe(
            df_norm.style.format({col: "{:.4f}" for col in selected_scenarios}),
            use_container_width=True,
        )

    with st.expander("View raw combined data"):
        # Create a temporary display dataframe that combines Category + Unit
        df_raw_display = df_combined.copy()
        df_raw_display["Impact category"] = (
            df_raw_display["Impact category"] + " (" + df_raw_display["Unit"] + ")"
        )
        # Drop the 'Unit' column since it's now inside the 'Impact category' string
        df_raw_display = df_raw_display.drop(columns=["Unit"])

        st.dataframe(df_raw_display, use_container_width=True)

    # ── Data handling ───────────────────────────────────────────────────────────
    with st.expander("Methodology and data handling"):
        st.markdown(f"""
        ### 1. Extraction
        We extract data from the `Impacts` sheet of the uploaded `.xlsx` files,
        specifically targeting row 2 for headers to match standard **openLCA** exports.

        ### 2. Normalization
        To make different impact categories comparable on a single radar chart, **Max-Normalization** is applied:
        """)

        st.latex(r"x_{norm} = \frac{x_{raw}}{\max(X_{category})}")

        st.markdown(f"""
        ### 3. Label Mapping
        Technical names are mapped to standard LCA abbreviations
        using a predefined dictionary for {tab_name} to keep the radar chart legible.
        """)


# ── Tabs (extend here later: Endpoint, Sankey, …) ────────────────────────────
tab_midpoint, tab_endpoint = st.tabs(["Midpoint · Radar", "Endpoint · Radar"])

with tab_midpoint:
    render_radar_tab("Midpoint", IMPACT_LABELS, "mid")

with tab_endpoint:
    render_radar_tab("Endpoint", ENDPOINT_IMPACT_LABELS, "end")
