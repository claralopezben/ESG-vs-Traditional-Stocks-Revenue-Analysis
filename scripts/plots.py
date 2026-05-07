"""
plots.py

Generates all six figures used in the blog post and saves them as PNG
files to the plots/ folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (ESG_TICKERS, OUTPUTS_DIR, PLOTS_DIR, PROCESSED_DIR,
                    TRADING_DAYS, TRADITIONAL_TICKERS)

ESG_COLOUR  = "#2A9D8F"
TRAD_COLOUR = "#E76F51"
GREY        = "#6C757D"

plt.rcParams.update({
    "figure.dpi":       110,
    "savefig.dpi":      150,
    "savefig.bbox":     "tight",
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.titlesize":   13,
    "axes.titleweight": "bold",
    "axes.labelsize":   11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.25,
    "legend.frameon":    False,
})


def _color_for(ticker: str) -> str:
    return ESG_COLOUR if ticker in ESG_TICKERS else TRAD_COLOUR


def plot_cumulative_returns(returns: pd.DataFrame) -> None:
    cum = (1 + returns).cumprod()
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for tkr in cum.columns:
        ax.plot(cum.index, cum[tkr], label=tkr,
                color=_color_for(tkr), lw=1.6, alpha=0.85)
    ax.axhline(1.0, color=GREY, lw=0.8, ls="--", alpha=0.6)
    ax.set_title("Growth of $1 invested at the start of the sample")
    ax.set_ylabel("Cumulative value ($)")
    ax.legend(ncol=3, loc="upper left")
    fig.text(0.99, 0.01, "Teal = ESG  |  Orange = Traditional",
             ha="right", color=GREY, fontsize=9, style="italic")
    fig.savefig(PLOTS_DIR / "01_cumulative_returns.png")
    plt.close(fig)


def plot_rolling_vol(returns: pd.DataFrame, window: int = 63) -> None:
    rolling = returns.rolling(window).std(ddof=1) * np.sqrt(TRADING_DAYS)
    fig, ax = plt.subplots(figsize=(10, 5))
    for tkr in rolling.columns:
        ax.plot(rolling.index, rolling[tkr], label=tkr,
                color=_color_for(tkr), lw=1.4, alpha=0.85)
    ax.set_title(f"{window}-day rolling annualised volatility")
    ax.set_ylabel("Annualised σ")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    ax.legend(ncol=3, loc="upper right")
    fig.savefig(PLOTS_DIR / "02_rolling_volatility.png")
    plt.close(fig)


def plot_return_distributions(returns: pd.DataFrame) -> None:
    esg_basket  = returns[list(ESG_TICKERS)].mean(axis=1)
    trad_basket = returns[list(TRADITIONAL_TICKERS)].mean(axis=1)
    fig, ax = plt.subplots(figsize=(9, 5))
    bins = np.linspace(min(esg_basket.min(), trad_basket.min()),
                       max(esg_basket.max(), trad_basket.max()), 80)
    ax.hist(trad_basket, bins=bins, alpha=0.55, label="Traditional basket",
            color=TRAD_COLOUR, density=True)
    ax.hist(esg_basket, bins=bins, alpha=0.55, label="ESG basket",
            color=ESG_COLOUR, density=True)
    ax.axvline(0, color=GREY, lw=0.8, ls="--")
    ax.set_title("Daily return distributions: ESG vs traditional baskets")
    ax.set_xlabel("Daily simple return")
    ax.set_ylabel("Density")
    ax.legend(loc="upper left")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.1f}%"))
    fig.savefig(PLOTS_DIR / "03_return_distributions.png")
    plt.close(fig)


def plot_risk_return(desc: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 6))
    for tkr, row in desc.iterrows():
        c = ESG_COLOUR if row["Group"] == "ESG" else TRAD_COLOUR
        ax.scatter(row["Ann. Volatility"], row["Ann. Return"],
                   color=c, s=170, edgecolor="white", lw=2, zorder=3)
        ax.annotate(tkr, xy=(row["Ann. Volatility"], row["Ann. Return"]),
                    xytext=(8, 6), textcoords="offset points",
                    fontsize=11, fontweight="bold")
    ax.set_title("Risk-return profile of each ETF")
    ax.set_xlabel("Annualised volatility (σ)")
    ax.set_ylabel("Annualised return (μ)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=ESG_COLOUR,
               markersize=11, label='ESG'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=TRAD_COLOUR,
               markersize=11, label='Traditional'),
    ]
    ax.legend(handles=handles, loc="lower right")
    fig.savefig(PLOTS_DIR / "04_risk_return_scatter.png")
    plt.close(fig)


def plot_capm_bars(capm: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    capm_sorted = capm.sort_values("alpha_ann_bps")
    colours = [ESG_COLOUR if g == "ESG" else TRAD_COLOUR
               for g in capm_sorted["Group"]]
    axes[0].barh(capm_sorted.index, capm_sorted["alpha_ann_bps"],
                 color=colours, edgecolor="white")
    axes[0].axvline(0, color=GREY, lw=0.9)
    axes[0].set_title("CAPM alpha (annualised, basis points)")
    axes[0].set_xlabel("α (bps/year)")
    for i, (idx, row) in enumerate(capm_sorted.iterrows()):
        if row["alpha_p"] < 0.05:
            axes[0].text(row["alpha_ann_bps"], i, "  *",
                         va="center", fontsize=14, fontweight="bold")
    axes[1].barh(capm_sorted.index, capm_sorted["beta"],
                 color=colours, edgecolor="white")
    axes[1].axvline(1, color=GREY, lw=0.9, ls="--")
    axes[1].set_title("CAPM beta (market sensitivity)")
    axes[1].set_xlabel("β")
    fig.suptitle("CAPM regression results per ETF",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.02,
             "* alpha significant at the 5% level (HAC-robust). "
             "Dashed line: β=1 (market portfolio).",
             ha="center", color=GREY, fontsize=9, style="italic")
    fig.savefig(PLOTS_DIR / "05_capm_bars.png")
    plt.close(fig)


def plot_drawdowns(returns: pd.DataFrame) -> None:
    cum = (1 + returns).cumprod()
    drawdown = cum / cum.cummax() - 1
    esg_dd  = drawdown[list(ESG_TICKERS)].mean(axis=1)
    trad_dd = drawdown[list(TRADITIONAL_TICKERS)].mean(axis=1)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.fill_between(trad_dd.index, trad_dd, 0,
                    color=TRAD_COLOUR, alpha=0.35, label="Traditional basket")
    ax.fill_between(esg_dd.index, esg_dd, 0,
                    color=ESG_COLOUR, alpha=0.45, label="ESG basket")
    ax.set_title("Drawdown from peak (basket-level)")
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%"))
    ax.legend(loc="lower left")
    fig.savefig(PLOTS_DIR / "06_drawdowns.png")
    plt.close(fig)


def main() -> None:
    print("=== plots.py ===")
    returns = pd.read_csv(PROCESSED_DIR / "returns.csv",
                          parse_dates=["Date"], index_col="Date")
    desc    = pd.read_csv(OUTPUTS_DIR / "descriptive_stats.csv", index_col="Ticker")
    capm    = pd.read_csv(OUTPUTS_DIR / "capm.csv", index_col="Ticker")

    plot_cumulative_returns(returns)
    plot_rolling_vol(returns)
    plot_return_distributions(returns)
    plot_risk_return(desc)
    plot_capm_bars(capm)
    plot_drawdowns(returns)

    print(f"  -> 6 figures saved to {PLOTS_DIR}")
    print("\nDone.")


if __name__ == "__main__":
    main()
