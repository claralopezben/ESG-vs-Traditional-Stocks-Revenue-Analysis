"""
config.py

Central place for all the settings used across the project: ticker names,
date range, file paths and a few constants for the statistical analysis.
"""
from pathlib import Path

# File paths
ROOT_DIR        = Path(__file__).resolve().parents[1]
DATA_DIR        = ROOT_DIR / "data"
RAW_DIR         = DATA_DIR / "raw"
PROCESSED_DIR   = DATA_DIR / "processed"
OUTPUTS_DIR     = ROOT_DIR / "outputs"
PLOTS_DIR       = ROOT_DIR / "plots"

for _d in (RAW_DIR, PROCESSED_DIR, OUTPUTS_DIR, PLOTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ETFs in the analysis
ESG_TICKERS = {
    "ESGU": "iShares ESG Aware MSCI USA",
    "SUSA": "iShares MSCI USA ESG Select",
    "ICLN": "iShares Global Clean Energy",
}

TRADITIONAL_TICKERS = {
    "SPY":  "SPDR S&P 500",
    "VTI":  "Vanguard Total Stock Market",
    "DIA":  "SPDR Dow Jones Industrial Average",
}

ALL_TICKERS = {**ESG_TICKERS, **TRADITIONAL_TICKERS}

# Sample window
START_DATE = "2019-01-01"
END_DATE   = "2025-12-31"

# Constants used in the analysis
TRADING_DAYS = 252        # trading days per year for annualisation
RANDOM_SEED  = 42         # used for the bootstrap confidence intervals
NEWEY_LAGS   = 5          # number of lags for Newey-West standard errors
