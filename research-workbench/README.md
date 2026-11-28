# NIL Research Workbench — UI prototype

Responsive browser workspace for inspecting CSV datasets and creating descriptive-statistics experiments through the local NIL Research API.

## Features
- Responsive lab dashboard and navigation
- CSV import with browser-side validation and 2 MB preview limit
- Sample climate dataset, table preview, numeric-column chart
- Local quick statistics for numeric columns
- Connect to a local API health endpoint
- Upload a selected dataset to the connected API
- Create and run a descriptive-statistics experiment with a hypothesis
- View and export a reproducible Markdown report with dataset fingerprint

## Run

1. In a terminal, open `nil-research-api`, install dependencies, and run the API on `127.0.0.1:8000` (see its README).
2. From the repository root, serve this folder: `python -m http.server 5500 --directory research-workbench`.
3. Open `http://127.0.0.1:5500`, connect to the API, then load a CSV or sample dataset.
4. Enter the experiment name and hypothesis, run it, and export the Markdown report.

When connected, the dataset is sent to the API address you entered. The API is local-development software; do not expose it publicly without authentication, authorization, dataset isolation, rate limiting, request-size enforcement, audit logging, and deployment hardening.
