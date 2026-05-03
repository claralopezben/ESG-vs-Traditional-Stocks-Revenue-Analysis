# CV / Cover Letter Description

## Short version (one-liner for CV)

**ESG vs Traditional Equity ETFs — Risk-Adjusted Performance Analysis** (Python, 2026)
Built a fully reproducible empirical project comparing three ESG and three broad-market US equity ETFs over 2019–2025. Pulled daily prices via `yfinance` and Fama–French factors via `pandas-datareader`, computed annualised returns, volatilities and Sharpe ratios, and estimated **CAPM** and **Fama–French three-factor** regressions with HAC (Newey–West) standard errors using `statsmodels`. Found that broad ESG ETFs deliver risk-adjusted performance statistically indistinguishable from the market, while thematic clean-energy exposure adds substantial idiosyncratic volatility without a corresponding alpha. Code published on GitHub.

---

## Bulleted version (technical CV)

**Empirical Finance Project — ESG vs Traditional Equity ETFs**  *Python • pandas • statsmodels • Git*
- Designed and shipped a fully reproducible end-to-end research pipeline (six modular Python scripts, automated data ingestion, no manual files) analysing ~10,000 ETF–day observations
- Estimated single-factor (CAPM) and multi-factor (Fama–French three-factor) regressions with **Newey–West HAC standard errors**; benchmarked alphas, betas and explanatory power across an ESG and a traditional equity basket
- Quantified risk-adjusted performance using Sharpe ratios with bootstrap 95% confidence intervals; tested the ESG–traditional return differential with a paired t-test
- Built six publication-quality matplotlib figures (cumulative returns, rolling volatility, return distributions, risk–return scatter, regression-coefficient bars, drawdowns) and a 2,500-word data-driven blog post
- Demonstrated cleanly that broad-ESG ETFs match market performance once factor exposures are controlled for, while thematic clean-energy products carry concentrated, uncompensated style risk

---

## Cover-letter version (one paragraph, IB tone)

I recently completed an independent empirical research project on whether ESG-focused US equity ETFs deliver superior risk-adjusted performance compared with traditional broad-market funds. Using daily price data on six ETFs from 2019 to 2025 alongside the Fama–French research factors, I built a fully reproducible Python pipeline to compute annualised returns, volatilities and Sharpe ratios, and to estimate single-factor and multi-factor regression models with HAC-robust standard errors. The work combined practical financial econometrics — CAPM, Fama–French three-factor, alpha–beta decomposition, hypothesis testing — with the engineering discipline of modular code, version control and clear documentation. The research found no evidence that broad ESG ETFs sacrifice risk-adjusted return relative to the market, while clarifying that thematic ESG products are better understood as concentrated factor bets than as efficient diversified vehicles. The full project, including all source code, data pipelines and a written report, is available on my GitHub.

---

## Skills demonstrated (one-liners — pick what fits)

- **Python:** pandas, NumPy, matplotlib, statsmodels, yfinance, pandas-datareader
- **Financial econometrics:** CAPM, Fama–French three-factor model, Sharpe ratio, alpha/beta decomposition, HAC (Newey–West) standard errors, bootstrap confidence intervals, paired t-test
- **Software engineering:** modular project structure, version control with Git/GitHub, reproducible pipelines, clear README documentation
- **Communication:** translated quantitative results into a written narrative aimed at a non-technical financial audience
