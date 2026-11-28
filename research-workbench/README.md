# NIL Research Workbench — UI prototype

A browser-only, no-backend preview of the NIL research workspace.

## Features
- Responsive lab dashboard and navigation
- CSV import (2 MB browser preview limit)
- CSV header/row validation and dataset preview
- Numeric column selection and canvas line chart
- Quick mean/min/max statistics for numeric columns
- Sample climate dataset
- No data upload: processing occurs in the browser

## Run

1. Install the API requirements and start the backend on `127.0.0.1:8000` (see `nil-research-api/README.md`).
2. From the repository root, serve this folder: `python -m http.server 5500 --directory research-workbench`.
3. Open `http://127.0.0.1:5500`, connect to the local API, and load a CSV or sample dataset.
4. Enter an experiment name and hypothesis, run the descriptive-statistics method, and export the generated Markdown report.


The browser preview remains local; when connected, the CSV is sent only to the API address you entered. The API is intended for local development and should not be exposed publicly without security controls.

## Next integration milestone
Connect this UI to the NILcenter dataset, analysis, artifact, and experiment APIs; add persistence, report export, chart controls, and accessibility tests.
