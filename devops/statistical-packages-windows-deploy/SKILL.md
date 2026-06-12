---
name: statistical-packages-windows-deploy
description: Install large statistical analysis Python packages (scipy, statsmodels, seaborn, pingouin, pymc, prophet, pomegranate, arviz, bambi) on Hermes embedded Python (Windows). Uses uv pip install instead of pip to avoid timeouts, and handles PIP_PREFIX/PIP_TARGET env var conflicts.
tags: [windows, python, statistics, pip, uv, embedded-python, hermes]
---

# Statistical Packages Windows Deploy

Install large statistical/ML Python packages on the Hermes embedded Python (Windows).

## When to use

- User asks to install statistical analysis packages for Hermes or Claude Code
- `pip install` keeps timing out or hanging on Windows embedded Python
- Need scipy, statsmodels, seaborn, pingouin, pymc, prophet, pomegranate, arviz, bambi
- Want to save offline wheel cache for future reinstallation

## Step-by-step

### 1. Clear interfering env vars

The Hermes embedded Python has `PIP_PREFIX` and `PIP_TARGET` set, which cause pip to fail:

```bash
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" pip install <package>
```

### 2. Use uv pip install (much faster)

`uv` is already bundled with Hermes. It resolves and downloads packages 10-50x faster than pip:

```bash
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" uv pip install <packages> --system
```

Key flags:
- `--system` — install into the system/interpreter environment (by default uv uses isolated venvs)
- No `--user` needed — the embedded Python is the target

### 3. Install order (foundational first)

```bash
# Core statistical packages (installed together in ~13s)
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" uv pip install scipy statsmodels seaborn pingouin --system

# Advanced Bayesian/probabilistic packages (installed together in ~2min)
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" uv pip install pymc arviz bambi pomegranate --system

# Time series forecasting
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" uv pip install prophet --system
```

### 4. Save offline wheel cache

To save all downloaded wheels for offline installation:

```bash
mkdir -p /d/Hermes/statistical-packages
cd /d/Hermes/statistical-packages
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" pip download scipy statsmodels seaborn pingouin pymc prophet pomegranate arviz bambi -d .
```

This saves ~71 wheel files (~280MB) for future use.

### 5. Verify

```bash
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" python -c "import scipy; import statsmodels; import seaborn; import pingouin; print('core ok')"
PIP_PREFIX="" PIP_TARGET="" PYTHONPATH="" python -c "import pymc; import prophet; import pomegranate; import arviz; import bambi; print('advanced ok')"
```

## Packages installed

| Package | Version | Purpose |
|---------|---------|---------|
| scipy | 1.17.1 | Scientific computing, stats module |
| statsmodels | 0.14.6 | Regression, time series, hypothesis tests, GLM |
| seaborn | 0.13.2 | Statistical data visualization |
| pingouin | 0.6.1 | Comprehensive statistical tests (ANOVA, effect size) |
| pymc | 6.0.1 | Bayesian modeling, MCMC |
| prophet | 1.3.0 | Facebook time series forecasting |
| pomegranate | 1.1.2 | Probabilistic modeling (Bayesian networks, HMM) |
| arviz | 1.1.0 | Bayesian model diagnostics & visualization |
| bambi | 0.18.0 | Bayesian mixed-effects models |

## Usage

In Hermes Agent or Claude Code terminal:

```python
import statsmodels.api as sm
import scipy.stats as stats
import seaborn as sns
import pingouin as pg
import pymc as pm
```

The `execute_code` tool can also import these directly since it uses the embedded Python.

## Pitfalls

- **Do NOT use `pip install` for large packages** — it frequently times out (>600s). `uv pip install` finishes in seconds.
- **PIP_PREFIX and PIP_TARGET must be cleared** — they point to the embedded Python dist-info dir and cause `--home`/`--prefix` conflicts.
- **Prophet (Facebook)** normally requires a C++ compiler (g++) for CmdStan. On the embedded Python 3.13, `uv pip install prophet` works cleanly with pre-compiled wheels — the `g++ not available` warning on import is benign for standard usage. Does NOT require manual C++ toolchain setup on Windows.
- **PyMC installs torch as dependency** (~117MB download) for its neural network components.
- **After `uv cache clean`**, reinstalling will re-download everything. The `pip download -d` cache in D:\Hermes\statistical-packages preserves offline copies.
