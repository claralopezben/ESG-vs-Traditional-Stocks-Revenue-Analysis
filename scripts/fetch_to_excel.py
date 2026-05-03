"""
fetch_to_excel.py
=================
One-shot script for the BEE2041 ESG-vs-Traditional empirical project.

What it does
------------
1. Downloads daily adjusted-close prices for six ETFs from Yahoo Finance:
     ESG          : ESGU, SUSA, ICLN
     Traditional  : SPY,  VTI,  DIA
2. Downloads the Fama-French 3 factors (Mkt-RF, SMB, HML) and the
   daily US risk-free rate from Kenneth French's Data Library.
3. Aligns everything on the same set of trading days.
4. Computes simple daily returns AND log returns.
5. Computes excess returns (r_i - r_f) for every ETF.
6. Computes per-ETF summary statistics (annualised mean, volatility,
   Sharpe ratio).
7. Writes everything into a single multi-sheet Excel workbook:
     esg_dataset.xlsx
        ├── README              (sheet describing every other sheet)
        ├── Prices              (adjusted close, 6 columns)
        ├── Returns_Simple      (daily simple returns)
        ├── Returns_Log         (daily log returns)
        ├── Factors             (Mkt-RF, SMB, HML, RF)
        ├── Excess_Returns      (r_i - RF for each ETF)
        ├── Summary_Statistics  (annualised stats per ETF)
        └── Tickers             (ticker -> long name mapping)

How to run
----------
    pip install yfinance pandas-datareader pandas numpy openpyxl
    python fetch_to_excel.py

Optional CLI flags
------------------
    --start  YYYY-MM-DD   (default: 2019-01-01)
    --end    YYYY-MM-DD   (default: 2025-12-31)
    --out    path.xlsx    (default: esg_dataset.xlsx)
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
ESG_TICKERS = {
    "ESGU": "iShares ESG Aware MSCI USA ETF",
    "SUSA": "iShares MSCI USA ESG Select ETF",
    "ICLN": "iShares Global Clean Energy ETF",
}

TRADITIONAL_TICKERS = {
    "SPY":  "SPDR S&P 500 ETF Trust",
    "VTI":  "Vanguard Total Stock Market ETF",
    "DIA":  "SPDR Dow Jones Industrial Average ETF",
}

ALL_TICKERS  = {**ESG_TICKERS, **TRADITIONAL_TICKERS}
TRADING_DAYS = 252                       # for annualisation


# --------------------------------------------------------------------------
# Step 1: download prices
# --------------------------------------------------------------------------
def fetch_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Download adjusted-close prices for `tickers` between `start` and `end`.

    auto_adjust=True asks yfinance to deliver the dividend-and-split-adjusted
    close in the 'Close' column, which is what we want for a return analysis.
    """
    import yfinance as yf
    print(f"[1/3] Downloading {len(tickers)} tickers from Yahoo Finance ...")
    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
    )
    # yfinance returns a MultiIndex (ticker, field) when more than one ticker
    # is requested. Flatten to one Close column per ticker.
    if isinstance(raw.columns, pd.MultiIndex):
        prices = pd.DataFrame({t: raw[t]["Close"] for t in tickers})
    else:
        prices = raw[["Close"]].rename(columns={"Close": tickers[0]})
    prices.index.name = "Date"
    return prices.sort_index()


# --------------------------------------------------------------------------
# Step 2: download Fama-French factors
# --------------------------------------------------------------------------
def fetch_fama_french(start: str, end: str) -> pd.DataFrame:
    """Daily Fama-French 3 factors + RF rate (US), converted from percent
    to decimals so that they line up with our return units."""
    from pandas_datareader import data as pdr
    print("[2/3] Downloading Fama-French 3 factors ...")
    ff = pdr.DataReader(
        "F-F_Research_Data_Factors_daily",
        "famafrench",
        start=start,
        end=end,
    )[0] / 100.0
    ff.index = pd.to_datetime(ff.index)
    ff.index.name = "Date"
    return ff


# --------------------------------------------------------------------------
# Step 3: build the working dataset
# --------------------------------------------------------------------------
def build_dataset(prices: pd.DataFrame,
                  factors: pd.DataFrame
                  ) -> dict[str, pd.DataFrame]:
    """Align prices and factors on the same trading-day index, then derive
    every secondary table the project needs.

    Returns a dict of {sheet_name: DataFrame}.
    """
    print("[3/3] Aligning, computing returns and excess returns ...")

    # --- Align on the intersection of the two calendars --------------------
    common_idx = prices.index.intersection(factors.index)
    prices  = prices.loc[common_idx].dropna(how="any")
    factors = factors.loc[prices.index]

    # --- Returns -----------------------------------------------------------
    simple_ret = prices.pct_change().dropna(how="any")
    log_ret    = np.log(prices / prices.shift(1)).dropna(how="any")

    # --- Excess returns (subtract daily RF rate) ---------------------------
    rf = factors["RF"].reindex(simple_ret.index)
    excess_ret = simple_ret.sub(rf, axis=0)

    # --- Per-ETF summary statistics ----------------------------------------
    rows = []
    for tkr in simple_ret.columns:
        r  = simple_ret[tkr]
        er = excess_ret[tkr]
        ann_mean = r.mean()  * TRADING_DAYS
        ann_vol  = r.std(ddof=1) * np.sqrt(TRADING_DAYS)
        sharpe   = (er.mean() / er.std(ddof=1)) * np.sqrt(TRADING_DAYS)
        rows.append({
            "Ticker":           tkr,
            "Name":             ALL_TICKERS[tkr],
            "Group":            "ESG" if tkr in ESG_TICKERS else "Traditional",
            "N_obs":            int(len(r)),
            "Mean_Daily":       r.mean(),
            "Std_Daily":        r.std(ddof=1),
            "Ann_Return":       ann_mean,
            "Ann_Volatility":   ann_vol,
            "Sharpe_Ratio":     sharpe,
            "Min_Daily":        r.min(),
            "Max_Daily":        r.max(),
            "Skewness":         r.skew(),
            "Kurtosis":         r.kurtosis(),
        })
    summary = pd.DataFrame(rows).set_index("Ticker")

    tickers_table = pd.DataFrame(
        [(t, n, "ESG" if t in ESG_TICKERS else "Traditional")
         for t, n in ALL_TICKERS.items()],
        columns=["Ticker", "Name", "Group"],
    ).set_index("Ticker")

    return {
        "Prices":             prices,
        "Returns_Simple":     simple_ret,
        "Returns_Log":        log_ret,
        "Factors":            factors,
        "Excess_Returns":     excess_ret,
        "Summary_Statistics": summary,
        "Tickers":            tickers_table,
    }


# --------------------------------------------------------------------------
# Step 4: write the workbook
# --------------------------------------------------------------------------
def make_readme(start: str, end: str, n_obs: int) -> pd.DataFrame:
    """A first-sheet description so the workbook is self-documenting."""
    rows = [
        ("Project",            "BEE2041 - ESG vs Traditional ETFs"),
        ("Created",             datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")),
        ("Sample window",       f"{start}  to  {end}"),
        ("Trading days in set", str(n_obs)),
        ("Data source 1",       "Yahoo Finance (yfinance) - adjusted close prices"),
        ("Data source 2",       "Kenneth French Data Library - FF3 factors + RF"),
        ("",                    ""),
        ("Sheet: Prices",
            "Daily adjusted-close prices for the 6 ETFs (USD)."),
        ("Sheet: Returns_Simple",
            "Daily simple returns r_t = P_t / P_{t-1} - 1."),
        ("Sheet: Returns_Log",
            "Daily log returns r_t = ln(P_t / P_{t-1})."),
        ("Sheet: Factors",
            "Fama-French daily factors: Mkt-RF, SMB, HML, and the "
            "risk-free rate RF (all decimals, not percentages)."),
        ("Sheet: Excess_Returns",
            "Daily simple return minus daily RF rate, per ETF. "
            "Used as the dependent variable in CAPM/FF3 regressions."),
        ("Sheet: Summary_Statistics",
            "Per-ETF annualised mean, volatility, Sharpe ratio, plus "
            "moments of the daily distribution."),
        ("Sheet: Tickers",
            "Mapping of ticker -> fund name -> group."),
    ]
    return pd.DataFrame(rows, columns=["Field", "Description"])


def write_excel(sheets: dict[str, pd.DataFrame],
                readme: pd.DataFrame,
                out_path: Path) -> None:
    """Write every DataFrame to a single .xlsx workbook with light
    formatting (frozen panes, column widths, bold header)."""
    from openpyxl.styles import Font, Alignment

    print(f"\nWriting workbook -> {out_path}")
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        # README first so it opens by default
        readme.to_excel(writer, sheet_name="README", index=False)
        for name, df in sheets.items():
            df.to_excel(writer, sheet_name=name)

        # --- Light formatting pass -----------------------------------------
        wb = writer.book
        bold = Font(bold=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            # Bold header row, freeze it, set a sensible width
            for cell in ws[1]:
                cell.font = bold
                cell.alignment = Alignment(horizontal="left")
            ws.freeze_panes = "B2"
            # Auto-fit-ish column widths (cheap but effective)
            for col_idx, col_cells in enumerate(ws.columns, start=1):
                max_len = max(
                    (len(str(c.value)) for c in col_cells if c.value is not None),
                    default=10,
                )
                # Cap very wide text columns (e.g. README descriptions)
                ws.column_dimensions[
                    ws.cell(row=1, column=col_idx).column_letter
                ].width = min(max_len + 2, 60)

    print(f"Done. {len(sheets) + 1} sheets written.")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", default="2019-01-01")
    p.add_argument("--end",   default="2025-12-31")
    p.add_argument("--out",   default="esg_dataset.xlsx")
    args = p.parse_args()

    out_path = Path(args.out).resolve()

    prices  = fetch_prices(list(ALL_TICKERS), args.start, args.end)
    factors = fetch_fama_french(args.start, args.end)
    sheets  = build_dataset(prices, factors)

    readme = make_readme(args.start, args.end,
                         n_obs=len(sheets["Returns_Simple"]))
    write_excel(sheets, readme, out_path)

    # --- Quick sanity check printed to console -----------------------------
    print("\n----- quick sanity check -----")
    print(sheets["Summary_Statistics"][
        ["Group", "Ann_Return", "Ann_Volatility", "Sharpe_Ratio"]
    ].round(4))


if __name__ == "__main__":
    main()
