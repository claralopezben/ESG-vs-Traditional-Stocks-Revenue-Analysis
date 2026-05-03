"""
analysis.py
-----------
Core statistical work:

 1. Descriptive stats per ETF: annualised return, volatility, Sharpe.
 2. Bootstrap 95% confidence interval on each Sharpe ratio.
 3. Two-sample t-test on the daily return differential between
    the equally-weighted ESG and traditional baskets.
 4. CAPM regression for every ETF (vs. Mkt-RF), with HAC standard errors.
 5. Fama-French 3-factor regression for every ETF, with HAC standard errors.

All numerical results land in outputs/ as CSV (for re-use by the notebook)
plus a human-readable TXT report.

Run:
    python scripts/analysis.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (ESG_TICKERS, NEWEY_LAGS, OUTPUTS_DIR, PROCESSED_DIR,
                    RANDOM_SEED, TRADING_DAYS, TRADITIONAL_TICKERS)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def annualise_mean(daily: pd.Series) -> float:
    return daily.mean() * TRADING_DAYS


def annualise_vol(daily: pd.Series) -> float:
    return daily.std(ddof=1) * np.sqrt(TRADING_DAYS)


def sharpe(excess_daily: pd.Series) -> float:
    """Annualised Sharpe ratio from a daily excess-return series."""
    mu  = excess_daily.mean()
    sig = excess_daily.std(ddof=1)
    if sig == 0:
        return np.nan
    return (mu / sig) * np.sqrt(TRADING_DAYS)


def bootstrap_sharpe_ci(excess_daily: pd.Series,
                        n_boot: int = 5000,
                        alpha: float = 0.05,
                        seed: int = RANDOM_SEED) -> tuple[float, float]:
    """Stationary-block bootstrap is overkill here; we use a simple
    iid resample which is conservative-on-precision but unbiased in the
    location of the CI for our sample size (~1700 obs). Returns
    (lower, upper) of the (1-alpha) percentile interval."""
    rng = np.random.default_rng(seed)
    n   = len(excess_daily)
    arr = excess_daily.to_numpy()
    sharpes = np.empty(n_boot)
    for i in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        sd = sample.std(ddof=1)
        sharpes[i] = (sample.mean() / sd) * np.sqrt(TRADING_DAYS) if sd else np.nan
    sharpes = sharpes[~np.isnan(sharpes)]
    return tuple(np.quantile(sharpes, [alpha / 2, 1 - alpha / 2]))


# --------------------------------------------------------------------------
# 1. Descriptive table
# --------------------------------------------------------------------------
def descriptive_table(returns: pd.DataFrame,
                      excess: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tkr in returns.columns:
        sr = sharpe(excess[tkr])
        lo, hi = bootstrap_sharpe_ci(excess[tkr])
        rows.append({
            "Ticker":            tkr,
            "Group":             "ESG" if tkr in ESG_TICKERS else "Traditional",
            "Ann. Return":       annualise_mean(returns[tkr]),
            "Ann. Volatility":   annualise_vol(returns[tkr]),
            "Sharpe":            sr,
            "Sharpe 95% CI low": lo,
            "Sharpe 95% CI high": hi,
        })
    return pd.DataFrame(rows).set_index("Ticker")


# --------------------------------------------------------------------------
# 2. Basket-level t-test on daily returns
# --------------------------------------------------------------------------
def basket_ttest(returns: pd.DataFrame) -> dict:
    """Equally-weighted ESG basket vs equally-weighted traditional basket.

    We run Welch's t-test (unequal variances) on the daily DIFFERENCE
    series, which is paired by date — i.e. effectively a one-sample test
    on (ESG_t - TRAD_t). This controls for common shocks.
    """
    from scipy import stats

    esg_basket  = returns[list(ESG_TICKERS)].mean(axis=1)
    trad_basket = returns[list(TRADITIONAL_TICKERS)].mean(axis=1)
    diff = (esg_basket - trad_basket).dropna()

    t_stat, p_val = stats.ttest_1samp(diff, popmean=0.0)
    return {
        "n":            len(diff),
        "mean_diff_daily":  diff.mean(),
        "mean_diff_annual": diff.mean() * TRADING_DAYS,
        "std_diff_daily":   diff.std(ddof=1),
        "t_stat":           float(t_stat),
        "p_value":          float(p_val),
    }


# --------------------------------------------------------------------------
# 3 & 4. CAPM and Fama-French regressions
# --------------------------------------------------------------------------
def run_factor_regression(y: pd.Series,
                          X: pd.DataFrame) -> dict:
    """OLS with Newey-West HAC standard errors. Returns a flat dict of
    coefficients, t-stats, p-values, and R^2.

    `y` must already be excess returns (r_i - r_f) and `X` must already
    contain only the factor columns (no constant)."""
    import statsmodels.api as sm

    # Align y and X on their common dates; drop any rows with NA on either side.
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    y_aligned = df["y"]
    X_aligned = df.drop(columns=["y"])

    X_const = sm.add_constant(X_aligned)
    model   = sm.OLS(y_aligned, X_const)
    res     = model.fit(cov_type="HAC",
                        cov_kwds={"maxlags": NEWEY_LAGS})
    out = {"r_squared": res.rsquared, "n_obs": int(res.nobs)}
    for name in res.params.index:
        out[f"{name}_coef"]   = res.params[name]
        out[f"{name}_tstat"]  = res.tvalues[name]
        out[f"{name}_pvalue"] = res.pvalues[name]
    return out


def capm_table(excess: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """Run CAPM r_i - r_f = alpha + beta * (Mkt - RF) for every ticker.

    Alpha is reported in *annualised* basis points, the convention used
    in the asset-management industry, so the result is readable to a
    non-technical reader.
    """
    mkt = factors[["Mkt-RF"]]
    rows = []
    for tkr in excess.columns:
        res = run_factor_regression(excess[tkr], mkt)
        rows.append({
            "Ticker":      tkr,
            "Group":       "ESG" if tkr in ESG_TICKERS else "Traditional",
            "alpha_daily": res["const_coef"],
            "alpha_ann_bps": res["const_coef"] * TRADING_DAYS * 1e4,
            "alpha_p":     res["const_pvalue"],
            "beta":        res["Mkt-RF_coef"],
            "beta_p":      res["Mkt-RF_pvalue"],
            "R_squared":   res["r_squared"],
            "N":           res["n_obs"],
        })
    return pd.DataFrame(rows).set_index("Ticker")


def ff3_table(excess: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    """Fama-French 3-factor regression for every ticker."""
    X = factors[["Mkt-RF", "SMB", "HML"]]
    rows = []
    for tkr in excess.columns:
        res = run_factor_regression(excess[tkr], X)
        rows.append({
            "Ticker":         tkr,
            "Group":          "ESG" if tkr in ESG_TICKERS else "Traditional",
            "alpha_ann_bps":  res["const_coef"] * TRADING_DAYS * 1e4,
            "alpha_p":        res["const_pvalue"],
            "beta_MKT":       res["Mkt-RF_coef"],
            "beta_SMB":       res["SMB_coef"],
            "beta_HML":       res["HML_coef"],
            "R_squared":      res["r_squared"],
            "N":              res["n_obs"],
        })
    return pd.DataFrame(rows).set_index("Ticker")


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------
def write_report(desc: pd.DataFrame, ttest: dict,
                 capm: pd.DataFrame, ff3: pd.DataFrame) -> str:
    def fmt_pct(x):  return f"{x*100:6.2f}%"
    def fmt_num(x):  return f"{x:7.3f}"

    lines = []
    lines.append("=" * 70)
    lines.append("ESG vs TRADITIONAL ETFs - ANALYSIS REPORT")
    lines.append("=" * 70)

    lines.append("\n[1] DESCRIPTIVE STATISTICS (annualised)\n")
    pretty = desc.copy()
    pretty["Ann. Return"]      = pretty["Ann. Return"].map(fmt_pct)
    pretty["Ann. Volatility"]  = pretty["Ann. Volatility"].map(fmt_pct)
    pretty["Sharpe"]           = pretty["Sharpe"].map(fmt_num)
    pretty["Sharpe 95% CI low"]  = pretty["Sharpe 95% CI low"].map(fmt_num)
    pretty["Sharpe 95% CI high"] = pretty["Sharpe 95% CI high"].map(fmt_num)
    lines.append(pretty.to_string())

    lines.append("\n\n[2] BASKET-LEVEL T-TEST")
    lines.append(f"  H0: mean(ESG_basket - Traditional_basket) = 0")
    lines.append(f"  N daily obs       : {ttest['n']:,}")
    lines.append(f"  Mean diff (daily) : {ttest['mean_diff_daily']*1e4:7.3f} bps")
    lines.append(f"  Mean diff (annual): {ttest['mean_diff_annual']*100:7.3f} pp")
    lines.append(f"  t-statistic       : {ttest['t_stat']:7.3f}")
    lines.append(f"  p-value           : {ttest['p_value']:7.4f}")

    lines.append("\n[3] CAPM (r_i - r_f = alpha + beta * Mkt-RF)\n")
    capm_pretty = capm.copy()
    capm_pretty["alpha_ann_bps"] = capm_pretty["alpha_ann_bps"].round(1)
    capm_pretty["alpha_p"]       = capm_pretty["alpha_p"].round(4)
    capm_pretty["beta"]          = capm_pretty["beta"].round(3)
    capm_pretty["beta_p"]        = capm_pretty["beta_p"].round(4)
    capm_pretty["R_squared"]     = capm_pretty["R_squared"].round(3)
    capm_pretty = capm_pretty.drop(columns=["alpha_daily"])
    lines.append(capm_pretty.to_string())

    lines.append("\n\n[4] FAMA-FRENCH 3-FACTOR\n")
    ff3_pretty = ff3.round(3)
    ff3_pretty["alpha_ann_bps"] = ff3_pretty["alpha_ann_bps"].round(1)
    lines.append(ff3_pretty.to_string())

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    print("=== analysis.py ===")
    returns = pd.read_csv(PROCESSED_DIR / "returns.csv",
                          parse_dates=["Date"], index_col="Date")
    excess  = pd.read_csv(PROCESSED_DIR / "excess_returns.csv",
                          parse_dates=["Date"], index_col="Date")
    factors = pd.read_csv(PROCESSED_DIR / "factors.csv",
                          parse_dates=["Date"], index_col="Date")

    print("  -> descriptive table")
    desc = descriptive_table(returns, excess)
    desc.to_csv(OUTPUTS_DIR / "descriptive_stats.csv")

    print("  -> basket t-test")
    ttest = basket_ttest(returns)
    pd.Series(ttest).to_csv(OUTPUTS_DIR / "basket_ttest.csv", header=["value"])

    print("  -> CAPM")
    capm = capm_table(excess, factors)
    capm.to_csv(OUTPUTS_DIR / "capm.csv")

    print("  -> Fama-French 3-factor")
    ff3 = ff3_table(excess, factors)
    ff3.to_csv(OUTPUTS_DIR / "ff3.csv")

    report = write_report(desc, ttest, capm, ff3)
    (OUTPUTS_DIR / "report.txt").write_text(report + "\n")
    print("\n" + report)
    print("\nDone.")


if __name__ == "__main__":
    main()
