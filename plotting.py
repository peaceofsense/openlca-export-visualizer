import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from math import pi
try:
    import scienceplots
except ImportError:
    pass

from data_processing import IMPACT_LABELS

def plot_radar(
    df_norm, categories_col, scenario_cols, angle_offset=0, figsize=(5, 5), title="", labels_dict=None
):
    """Draw a radar / spider chart with a science background."""
    categories = df_norm[categories_col].tolist()
    num_vars = len(categories)
    if num_vars < 3:
        st.warning("Select at least 3 impact categories to draw a radar chart.")
        return None

    # Use the science style if available
    try:
        plt.style.use(['science', 'no-latex'])
    except Exception:
        pass

    angles = np.linspace(0, 2 * pi, num_vars, endpoint=False).tolist()
    angles = [(a + angle_offset) % (2 * pi) for a in angles]
    angles_closed = angles + angles[:1]

    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    for i, col in enumerate(scenario_cols):
        values = df_norm[col].tolist()
        values_closed = values + values[:1]
        
        line = ax.plot(
            angles_closed,
            values_closed,
            linewidth=1.8,
            linestyle="solid",
            label=col,
        )
        ax.fill(angles_closed, values_closed, alpha=0.10, color=line[0].get_color())

    labels_map = labels_dict if labels_dict is not None else IMPACT_LABELS
    labels_list = []
    
    for cat in categories:
        cat_clean = cat.split(" (")[0].strip().lower()
        labels_list.append(labels_map.get(cat_clean, cat_clean))

    max_val = df_norm[scenario_cols].max().max()
    
    # Force the maximum radius to precisely match our max data value
    ax.set_ylim(0, max_val)
    
    # Use native matplotlib ticks for categories which scale much better
    ax.set_xticks(angles)
    ax.set_xticklabels(labels_list, fontsize=10)
    ax.tick_params(axis='x', pad=10)
    
    # Draw radial y-ticks
    yticks = np.linspace(0, max_val, 5)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{v:.2f}" for v in yticks], fontsize=8)
    
    # Control the angle where the y-tick labels (0.00, 0.25, etc.) are drawn so they don't overlap lines
    ax.set_rlabel_position(90 if angle_offset == 0 else 0)
    
    # Basic radar aesthetics
    ax.yaxis.grid(True, linestyle="solid", linewidth=0.5, color="gray", alpha=0.5)
    ax.xaxis.grid(True, linestyle="solid", linewidth=0.5, color="gray", alpha=0.5) # Add spokes for clarity
    ax.spines["polar"].set_visible(False)

    if title:
        ax.set_title(title, pad=20)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=min(len(scenario_cols), 4),
        frameon=False,
        fontsize=9,
    )

    # Use constrained layout, but add negative bottom pad to give legend space
    fig.set_layout_engine(layout="constrained")
    # Tweak margin specifically to accommodate the legend's new offset
    fig.get_layout_engine().set(rect=(0, 0.15, 1, 1))
    return fig
