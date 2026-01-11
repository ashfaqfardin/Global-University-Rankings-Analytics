# Global University Rankings Analytics
![Project Thumbnail](./thumbnail.png)

![Contributors](https://img.shields.io/github/contributors/ashfaqfardin/Global-University-Rankings-Analytics)
![Issues](https://img.shields.io/github/issues/ashfaqfardin/Global-University-Rankings-Analytics)
![Good First Issues](https://img.shields.io/github/issues/ashfaqfardin/Global-University-Rankings-Analytics/good%20first%20issue)
![Last Commit](https://img.shields.io/github/last-commit/ashfaqfardin/Global-University-Rankings-Analytics)
![Repo Size](https://img.shields.io/github/repo-size/ashfaqfardin/Global-University-Rankings-Analytics)
![License](https://img.shields.io/github/license/ashfaqfardin/Global-University-Rankings-Analytics)

## Table of Contents

[Overview](#overview) | [Tableau Dashboard Preview](#tableau-dashboard-preview) | [What this repository contains](#what-this-repository-contains) | [Quick Start](#quick-start-windows--powershell) | [Script options](#script-options) | [Data Preprocessing](#data-preprocessing) | [How the scraper works](#how-the-scraper-works-summary) | [Debugging & Troubleshooting](#debugging--troubleshooting) | [Reproducing the exact run](#reproducing-the-exact-run) | [Findings](#findings) | [Limitations](#limitations) | [Files added](#files-added) | [Contact Details](#contact-details)

## Overview

This repository contains a Selenium-based Python scraper that extracts university ranking data from the [THE World University Rankings](https://www.timeshighereducation.com/world-university-rankings/latest/world-ranking). The scraper targets the page's virtualized, scrollable table and performs a deterministic sweep to gather all rows.

### Tableau Dashboard

View the interactive analysis here: [Global University Rankings Analytics Dashboard](https://public.tableau.com/app/profile/mohammad.ashfaq.ur.rahman/viz/GlobalUniversityRankingsAnalytics/GlobalUniversityRankingAnalysis)

### Tableau Dashboard Preview

![Tableau Preview](./snapshots/tableau_preview_1.png)
![Tableau Preview](./snapshots/tableau_preview_2.png)

This preview image shows the key metrics and visualizations from the interactive Tableau dashboard, providing a quick overview of the data insights before viewing the full dashboard.


## What this repository contains

- `selenium_scraper/scraper.py` — the scraper script. Use the `--help` flag to see runtime options.
- `data_preprocessing/preprocessing.ipynb` - the data preprocessing script.
- `data/the_world_ranking.csv` — example output saved from a recent run (may be overwritten when you run the scraper).
- `data/cleaned_world_ranking.csv` — example output of recent run after data preprocessing.
- `requirements.txt` — Python package requirements for the project.

## Quick Start (Windows / PowerShell)

1. Clone or copy this project to a folder on your machine.
2. (Recommended) Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

3. Install required packages:

```powershell
pip install -r requirements.txt
```

4. Install Chrome and download a matching ChromeDriver (or use another WebDriver). Two common options:

- Manually: Download a ChromeDriver that matches your installed Chrome from https://chromedriver.chromium.org/downloads and put the `chromedriver.exe` on your `PATH` (e.g. `C:\Windows\System32` or any folder listed in your PATH).

- Use `webdriver-manager` (optional): install `webdriver-manager` and modify the script to use it. This README assumes `chromedriver.exe` is available on PATH.

5. Run the scraper (non-headless to watch what happens):

```powershell
python .\selenium_scraper\scraper.py --output the_world_ranking.csv
```

To run headless and speed up scraping, set the `--headless` flag:

```powershell
python .\selenium_scraper\scraper.py --headless --min-wait 0.15 --max-wait 0.30 --output the_world_ranking.csv
```

To only test the extraction (don't write CSV):

```powershell
python .\selenium_scraper\scraper.py --dry-run
```

## Script options

Run `python selenium_scraper/scraper.py --help` for details. Key flags used in practice:

- `--output, -o`: CSV output path (default `data/the_world_ranking.csv`).
- `--headless`: Run browser in headless mode.
- `--dry-run`: Do not save CSV (useful for quick checks).
- `--min-wait` / `--max-wait`: Small random wait window between actions to mimic human behaviour and allow lazy loading.
- `--url`: Alternate URL to scrape (default is the THE world ranking page).

## Data Preprocessing

After scraping, the raw data is cleaned and preprocessed using the Jupyter notebook located at `data_preprocessing/preprocessing.ipynb`. This notebook:

- Removes duplicate entries
- Handles missing or null values
- Normalizes column names and formats
- Converts data types (e.g., rankings from string to numeric)
- Filters out incomplete records
- Generates the cleaned output file: `data/cleaned_world_ranking.csv`

## How the scraper works (summary)

- The script locates the first `<table>` element on the page.
- It finds the nearest ancestor element of the table that is scrollable (overflow-y: auto/scroll and scrollHeight > clientHeight).
- The scraper deterministically steps through the container's scrollTop positions (with overlap) and reads the visible `<tr>` elements from the `<tbody>` at each offset.
- Collected rows are deduplicated (keyed on Rank + Name columns) and written to a CSV.

This approach was chosen because THE uses a virtualized table (huge `tbody` heights with absolutely positioned row elements) where page scrolling doesn't reveal the table rows reliably. Scrolling the table container directly allows the site to render the visible rows at that offset.

## Debugging & Troubleshooting

- If you see that the script extracts far fewer rows than expected:

  - Make sure ChromeDriver matches your installed Chrome version.
  - Run without `--headless` to watch the browser; overlays (cookie dialogs) or interstitials might prevent correct rendering or interaction.
  - Increase `--max-wait` to give the site more time to render rows.

- If the site displays cookie-consent modal or accepts geographic checks, you may need to accept or close that overlay manually (or add a handler in `scraper.py` to close it automatically).

- If you get `selenium.common.exceptions.SessionNotCreatedException` or `chromedriver` errors, check that `chromedriver.exe` is on PATH and matches Chrome.

- If you prefer automatic driver management, install `webdriver-manager` and either modify `scraper.py` to use it or install ChromeDriver into PATH using a package manager.

## Reproducing the exact run

Run with the smaller human-wait window used during development (faster, but keep it polite):

```powershell
python .\selenium_scraper\scraper.py --headless --min-wait 0.12 --max-wait 0.30 --output the_world_ranking.csv
```

Expected outcome: a CSV with ~3,000+ rows (the exact number depends on the live ranking dataset).:


## Findings

- **Singapore stands out as the strongest overall performer**, even though it has just two ranked universities (NUS and NTU). Both institutions consistently score highly across all evaluation areas.

- **Among the top 25 universities globally**, Singapore achieves the highest results in all major categories—Teaching, Research Environment, Research Quality, and Industry Income. This reflects a well-rounded and robust higher-education system.

- **Singapore’s lead is most evident in Research and Industry-related metrics**, where it outperforms every other country by a wide margin. Hong Kong and the Netherlands follow, but the difference remains substantial.

- **Hong Kong ranks as the next strongest performer**, especially in Teaching and Research Quality. However, Singapore still maintains a noticeably higher Teaching score, suggesting a more advanced academic and instructional environment.

## Limitations

- The scraper is a best-effort tool for a public website. The site structure may change and future changes could break the script.
- This script does not attempt to bypass paywalls, authentication, or anti-bot measures.
- Use responsibly and obey the site's terms of service and robots.txt when scraping.

## Files added

- `selenium_scraper/scraper.py` — scraping logic.
- `requirements.txt` — dependency manifest for Python packages used.

## Contact Details

If you need assistance running this code or help with any scraping-related tasks, feel free to contact me at **[imashfaqfardin@gmail.com](mailto:imashfaqfardin@gmail.com)**.