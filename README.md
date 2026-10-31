# neg-funding-backtest（v8）

币安 **负资金费率「卖现货 + 1× 永续多」** 公开回测包（引擎整改版，基于 v7 = 20d9522）。

> **头条（近 1 年 · S=7000 万 U · 原始已实现资金费 · 冲击 20bp/腿 · 无基差过滤 · OI 滞后 0 · 自冲击 k=0 · 借币利息 0 · 闲置理财 0）**
> - 真实库存上限（私有文件，不在仓内）：**20.43%**（名义 S 年化）/ 近 6 个月 **11.64%**（v7：17.99% / 10.46%）
> - 公开可复现（每币 S/267 等额上限）：**17.45%** / 近 6 个月 **11.99%**（v7：17.01% / 11.84%）
> - **组合现实场景（OI 滞后 1h + 冲击 30bp + k=4）**：A 8.38% / 5.03%，B 10.50% / 7.12%（1y / 6m）。全网格（冲击 10/20/30/50bp × OI 滞后 0/1 × k 0/4/8）见 RESULTS §11。
> - v8 整改：出场按上一小时收盘判断；资金费用结算时刻 markPrice；入场/补仓/出场/减仓共用每币-小时一份参与预算（上一小时成交额 20%）；成交量 10% 与 OI 10%（永续名义）是**入场/补仓的硬上限（减仓按参与预算分批，持仓可短时超限：A 1y 5.1% 币-小时，RESULTS §15.1）**；窗口末/超时出场按参与率分摊、缺 bar 顺延；部分减仓后出场盈亏状态按整个 episode；占用另报 MTM。逐项瀑布见 RESULTS §10。
> - **补仓规则：不限次补仓**（满足入场条件且有额度即补）。一次补仓、币数账本、MTM 资金上限、平方根冲击模型只作敏感性（RESULTS §12）。
> - **模型选择披露**：硬上限相对软目标在 A 1y 约 +1.3pp（换手 −7.5%），是建模选择不是容量；同小时参与率超 20% 的成交 A 1y 28%（RESULTS §15.2）；出场状态依赖沿用的 wait_max=168h，**v8 占用数字与 v7 不可比**（A 1y 平均占用 1345 → 1860 万）。
> - **占用披露**：A 1y 峰值占用按市值（MTM）= 8,371 万 U（120% of S），成本口径峰值 6,306 万；平均占用 MTM 1,860 万。
> - 对账：独立审查官的全量修复组合（min(上一小时,当前小时) 深度、软上限）与本仓 `reviewer_equiv` 行差 < 0.1pp（RESULTS §13）；头条采用严格因果的上一小时与硬上限，所以与审查官数字有 0.1–0.5pp 差异。
> - “3,201 次负费率转折事件”无法在任何合理定义下复现，RESULTS §14 给出定义与实际数字。
> - 收益**随季度剧烈波动**（见 RESULTS §1–§2），1y 头条不是稳态预期。

旧 v3 头条 14.74% / 19.29% 已作废（含 ×0.8 费率折扣、5% 理财、前视成交量、仅入场检查、−38bp 过滤）。

本仓库**不含**任何库存数量或 cap（`holdings.xlsx` 不在仓内，`holdings_cap.csv` 已 gitignore）。隐私保护依赖 `.gitignore` 的文件名模式（`holdings_cap*.csv` 等），改用其他文件名需自查。

## 文档

| 文件 | 内容 |
| --- | --- |
| [STRATEGY.md](./STRATEGY.md) | 全部规则与依据 |
| [RESULTS.md](./RESULTS.md) | 头条、分季度、滚动、bootstrap、收益拆分、整改桥接、v8 瀑布、全网格、敏感性（含平方根冲击）、审查官对账、局限 |
| [results/](./results/) | 全部数字源 CSV（`headline_*`、`quarterly_*`、`rolling90d_*`、`sensitivity_*`、`bridge_*`、`waterfall_*`、`grid_*`、`sens_v8_*`、`oi_turn_events.csv`、`reference_headline.json`） |
| [symbols_signal.csv](./symbols_signal.csv) | 币池 267（事后选择） |

## 复现

```bash
pip install -r requirements.txt
export NFB_DATA_DIR=/path/to/data
python download_data.py            # 公开 K 线 + 资金费（2025-10-01 起）
python download_oi.py              # 公开日度 OI（仅 v4 对照 / 桥接用）
python download_oi_hourly.py       # 公开小时 OI（Binance Vision metrics 5 分钟快照聚合，约 10 万个日包）
python download_markprice.py       # 公开 markPriceKlines（资金费按结算时刻 markPrice 计价）
python build_dataset.py --depth proxy
python run_backtest.py             # 公开等额上限，S=7000 万，1y + 6m；写 out/
python run_sensitivity.py          # 敏感性 + 整改桥接，写 results/
python run_robustness.py           # 前后半年、剔除盈利最多前 5/10 币（净 PnL 排序）
python waterfall.py                # v8 逐项整改瀑布（累计 / 单独 / 拿掉）
python run_sens_v8.py              # 一次补仓、币数账本、MTM 上限、平方根冲击、审查官口径
python run_grid.py                 # 冲击 × OI 滞后 × k 全网格 + 分季度 + 剔除前 5/10 + bootstrap
python oi_turn_events.py           # “负费率转折事件”核对
python oi_coverage.py              # 小时 OI 覆盖汇总
python make_results_md.py          # 由 results/*.csv 生成 RESULTS.md
python test_reproduce.py           # 对照 results/reference_headline.json
```

用你自己的库存上限（私有文件，**不要提交**）：

```bash
python make_holdings_cap.py --holdings /path/holdings.xlsx --out holdings_cap.csv   # 列 'Binance Symbols', 'Borrowable Qty @ 30% (Token)'；原样 × 窗口末现货价
python run_backtest.py --cap-mode holdings --holdings-cap holdings_cap.csv
python test_reproduce.py --holdings /path/holdings.xlsx     # 复现私有头条（容差：年化 0.05pp）
```

常用参数：`--impact-bp 10|20|30|50`、`--entry-basis-bp -38`（可选过滤，默认无）、`--vol-frac`、`--oi-frac`、`--S`、`--window 1y|6m|both`。

## 年化口径

`名义 S 年化 = net / S / years`，`占用资金年化 = net / 平均占用 / years`，两者并排；1y = 365/365，6m = 180/365。

## English summary

Negative-funding carry on Binance USDT-M: sell spot + long 1x perp while funding is negative. v8 = v7 plus engine fixes (exit decisions on the previous-hour close, funding at the settlement markPrice, one shared per-coin-hour participation budget of 20% of prior-hour volume, hard 10% volume / 10% perp-notional OI caps at entry/add, window-end exits spread over the budget, whole-episode exit PnL state after partial de-risking, MTM capital use reported). Adds are unlimited (add-once is a sensitivity only). Headline 1y, S=70M, 20bp impact: **20.43%** with the (private) inventory cap, **17.45%** with the public equal cap; 6m 11.64% / 11.99%. Combined realistic case (OI lag 1h + 30bp + own-impact k=4): 8.38% / 5.03% (private cap) and 10.50% / 7.12% (equal cap). Peak MTM capital use with the private cap is 120% of S (cost-basis peak 90%). No inventory quantities are in this repo; `make_holdings_cap.py` and `test_reproduce.py --holdings` reproduce the private-cap headline locally.
