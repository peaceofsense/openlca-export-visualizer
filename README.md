# openLCA Export Visualizer

![openLCA](https://img.shields.io/badge/openLCA-2.0+-green.svg)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

![Midpoint Radar Chart](sample-data/midpoint-shell.png)

This is a personal interactive visualization tool I built to quickly plot and compare openLCA midpoint and endpoint projections. It takes standard openLCA Excel outputs and generates cleaner, publication-ready radar charts (using the `scienceplots` Matplotlib style) to aid in comparative Life Cycle Assessments (LCAs).

## Motivation

I originally developed this as a set of static Python automation scripts for my own technical LCA workflows. To make the pipeline more transparent, interactive, and easier to showcase, I refactored the core data processing logic and built this Streamlit front-end. 

## Features

- **Automated Data Processing**: Effortlessly parses and aligns impact categories from multiple `.xlsx` scenario exports.
- **Midpoint & Endpoint Support**: Features dedicated logic and dictionary mappings for interpreting ReCiPe 2016 (or similar) midpoint and endpoint impact abbreviations.
- **Comparative Radar Charts**: Overlays multiple scenarios on dynamic radar charts.
- **Scientific Styling**: The charts are formatted according to rigorous scientific standards using the `scienceplots` Matplotlib theme, avoiding the generic defaults typical of automated plotters.
- **Responsive UI**: Built on Streamlit, the app offers fully customizable visualization parameters (figure sizing, rotation offsets, category filtering) and SVG export options.

## How It Works

1. **Extraction**: `app.py` accepts one or more openLCA Excel files and triggers `data_processing.py`, reading from the `Impacts` sheet and targeting row 2 for standard headers.
2. **Standardization**: Redundant category variations are removed, and complex technical names are mapped via dictionaries to standard, readable LCA abbreviations.
3. **Normalization**: Max-Normalization is applied column-wise across the selected scenarios so that disparate metrics (eg: kg CO2 eq vs m3 water) can be plotted on the same relative axis: $x_{norm} = \frac{x_{raw}}{\text{max}(X_{category})}$.
4. **Drawing**: `plotting.py` uses Matplotlib with an imposed scientific aesthetic to generate circular polygon plots, scaling dynamically to the input selections.

## Installation

**Using pip:**
```bash
pip install -r requirements.txt
```

**Using Nix Flakes (recommended for reproducible environments):**
```bash
nix develop
```



Simply run the Streamlit app locally:

```bash
streamlit run app.py
```

## License

This tool and its modified source code are licensed under the [GNU General Public License v3.0 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.en.html).
