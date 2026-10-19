# FY-4A + NWP Paired Sample Database — Kaggle Notebook Converter
# Run this script to convert fy4a_nwp_paired_database.py into a .ipynb

import json, re, sys

SOURCE_FILE = "fy4a_nwp_paired_database.py"
OUTPUT_FILE = "fy4a_nwp_paired_database.ipynb"

with open(SOURCE_FILE, encoding="utf-8") as f:
    source = f.read()

# Split on %% markers (each %% starts a new cell)
raw_cells = re.split(r"\n# %%\n", source)

cells = []
for raw in raw_cells:
    raw = raw.strip()
    if not raw:
        continue

    # Detect if cell is pure docstring/comment -> make markdown cell
    stripped = raw.strip()
    if stripped.startswith('"""') and stripped.endswith('"""'):
        md_text = stripped[3:-3].strip()
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [md_text],
        })
    else:
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {"trusted": True},
            "outputs": [],
            "source": [raw],
        })

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "cells": cells,
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Created {OUTPUT_FILE} with {len(cells)} cells.")
