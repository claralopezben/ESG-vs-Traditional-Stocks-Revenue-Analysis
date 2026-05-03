# ESG vs Traditional Stocks: A Risk-Adjusted Performance Analysis

**BEE2041 — Data Science in Economics: Empirical Project**

---

## 1. Project Overview

This project investigates whether ESG (Environmental, Social, and Governance) equity investments deliver superior risk-adjusted performance relative to traditional broad-market portfolios. The analysis uses daily price data on six Exchange-Traded Funds (ETFs), three ESG-focused and three traditional, together with the Fama–French research factors, to estimate returns, volatility, Sharpe ratios, CAPM alphas and betas, and Fama–French three-factor alphas.
I chose ETFs rather than individual stocks to keep the comparison clean and avoid stock-picking bias.
The deliverable is a data-driven blog post (`notebooks/blog.ipynb`) targeted at a financially literate but non-technical reader.

## 2. Research Question

> **Do ESG-focused equity ETFs outperform traditional broad-market ETFs on a risk-adjusted basis once exposure to common systematic risk factors is taken into account?**

We answer this in three layers of increasing rigor:

1. Raw cumulative returns and annualized volatility.
2. The **Sharpe ratio** (excess return per unit of total risk).
3. **CAPM** and **Fama–French three-factor** regressions, recovering the alpha — the portion of return that is *not* explained by market exposure or by the size and value factors.

A two-sample **t-test** on daily excess returns formally checks whether the ESG–traditional return differential is statistically distinguishable from zero.

## 3. Data Sources

All data are downloaded automatically by the scripts; no manual files are required.
One practical challenge was aligning ETF returns with the Fama–French factors, as they come in different formats and calendars. This was handled during the cleaning step.
| Source | Series | Provider |
|---|---|---|
| Yahoo Finance (via `yfinance`) | Daily adjusted close prices for 6 ETFs | Yahoo |
| Kenneth French Data Library | Fama–French 3 factors + risk-free rate (daily, US) | Dartmouth (`pandas_datareader`) |

**ETFs analyzed:**

- *ESG basket*: `ESGU` (iShares ESG Aware MSCI USA), `SUSA` (iShares MSCI USA ESG Select), `ICLN` (iShares Global Clean Energy)
- *Traditional basket*: `SPY` (S&P 500), `VTI` (Vanguard Total Stock Market), `DIA` (Dow Jones Industrial Average)

**Sample window:** 1 January 2019 to 31 December 2025 (configurable in `scripts/config.py`).

## 4. Repository Structure

```
esg-vs-traditional/
├── README.md                <- You are here
├── requirements.txt         <- Pinned Python dependencies
├── .gitignore
├── data/
│   ├── raw/                 <- Untouched data straight from APIs
│   └── processed/           <- Cleaned, aligned, returns-computed
├── scripts/
│   ├── config.py            <- Tickers, dates, output paths
│   ├── fetch_data.py        <- Download ETF prices + FF factors
│   ├── clean_data.py        <- Align, drop NAs, compute returns
│   ├── analysis.py          <- Summary stats, Sharpe, CAPM, FF3, t-test
│   └── plots.py             <- All figures used in the blog
├── outputs/                 <- Tables (CSV) and regression results (TXT)
├── plots/                   <- PNG figures
└── notebooks/
    └── blog.ipynb           <- Final blog post (the deliverable)
```

## 5. Replication Guide

The full pipeline runs in under two minutes on a standard laptop with an internet connection.

### 5.1 Prerequisites

- Python 3.10 or higher
- `git`
- An internet connection (for the first run only — data is cached locally)

### 5.2 Step-by-step

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/esg-vs-traditional.git
cd esg-vs-traditional

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the pipeline (each script is independent and idempotent)
python scripts/fetch_data.py      # Downloads raw data into data/raw/
python scripts/clean_data.py      # Produces data/processed/returns.csv
python scripts/analysis.py        # Produces tables in outputs/
python scripts/plots.py           # Produces figures in plots/

# 5. Open the blog post
Jupyter notebook notebooks/blog.ipynb
```

Each script can also be run from inside the notebook — see the first code cell of `blog.ipynb`.

### 5.3 Reproducibility notes

- All random seeds are set in `scripts/config.py` (only used for the bootstrap CI on Sharpe ratios).
- Yahoo Finance occasionally back-fills or revises adjusted-close prices. The scripts therefore cache the raw download in `data/raw/`; delete that folder to force a fresh pull.
- The Fama–French factors are versioned by Kenneth French; the cleaning script records the download date in a header comment of `data/raw/ff_factors_meta.txt`.

## 6. Methods & Formulas used 

- **Returns**: simple daily returns from adjusted close, $r_t = P_t / P_{t-1} - 1$.
- **Annualisation**: $\sigma_{\text{ann}} = \sigma_{\text{daily}} \sqrt{252}$, $\mu_{\text{ann}} = \mu_{\text{daily}} \times 252$.
- **Sharpe ratio**: $(\bar{r} - \bar{r}_f) / \sigma$, annualised.
- **CAPM**: $r_{i,t} - r_{f,t} = \alpha_i + \beta_i (r_{m,t} - r_{f,t}) + \varepsilon_{i,t}$
- **Fama–French 3-factor**: adds SMB (size) and HML (value) regressors.
- **Inference**: heteroskedasticity-and-autocorrelation-consistent (HAC, Newey–West) standard errors with 5 lags.

## 7. Required Packages

See `requirements.txt`. Headline list:

```
yfinance>=0.2.40
pandas-datareader>=0.10.0
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.13
statsmodels>=0.14
scipy>=1.11
jupyter
```

## 8. Author


Clara Ofelia Lopez, BEE2041 Data Science in Economics, University of Exeter, 2026
All analysis was implemented by the author, and the full pipeline can be reproduced by running the scripts in order. 
