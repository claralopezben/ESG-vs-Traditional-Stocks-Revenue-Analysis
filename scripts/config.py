"""
config.py
---------
Single source of truth for project-wide constants:
tickers, sample window, file paths, seeds.

Importing from this module keeps the other scripts free of magic numbers.
"""
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT_DIR        = Path(__file__).resolve().parents[1]
DATA_DIR        = ROOT_DIR / "data"
RAW_DIR         = DATA_DIR / "raw"
PROCESSED_DIR   = DATA_DIR / "processed"
OUTPUTS_DIR     = ROOT_DIR / "outputs"
PLOTS_DIR       = ROOT_DIR / "plots"

for _d in (RAW_DIR, PROCESSED_DIR, OUTPUTS_DIR, PLOTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Tickers
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# Sample window
# --------------------------------------------------------------------------
START_DATE = "2019-01-01"
END_DATE   = "2025-12-31"

# --------------------------------------------------------------------------
# Misc
# --------------------------------------------------------------------------
TRADING_DAYS = 252        # for annualisation
RANDOM_SEED  = 42         # bootstrap CI on Sharpe
NEWEY_LAGS   = 5          # HAC lags for regression standard errors
