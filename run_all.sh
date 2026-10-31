#!/usr/bin/env bash
# One-shot: download -> build -> headline (public equal cap) -> sensitivities/bridge.
# Set NFB_DATA_DIR to change where data is stored.  For your own inventory cap see make_holdings_cap.py / README.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}
$PY download_data.py
$PY download_oi.py          # daily OI: only for the v4 comparison row / bridge
$PY download_oi_hourly.py   # hourly OI used by the headline
$PY download_markprice.py   # markPrice klines for funding valuation
# (download_depth.py = optional real order-book depth, ~10 GB traffic, NOT used by default: the volume-based depth proxy is used)
$PY build_dataset.py --depth proxy
$PY run_backtest.py "$@"
$PY run_sensitivity.py
$PY run_robustness.py
$PY waterfall.py
$PY run_sens_v8.py
$PY run_grid.py
$PY oi_turn_events.py
$PY oi_coverage.py
$PY make_results_md.py
