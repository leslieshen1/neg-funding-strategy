# 策略说明（纯负费率 · v8 引擎整改版）

> 数字见 [RESULTS.md](./RESULTS.md)。公开仓不含任何真实库存数量。
> 原则：**只保留有客观依据的约束**；凡是运营参数（参与率、冲击）一律明示并给敏感性，不基于结果挑阈值。

## 1. 逻辑

币安 USDT-M 永续资金费率为**负**时多头收费率：**卖出现货 + 开等量 1× 永续多单**，收负费率；费率回落后买回现货、平永续。利润口径：净 USDT（不含库存币价盯市）。
净利 = 已实现资金费 + 对冲价格残差（含价差/冲击成本）− 手续费。

## 2. 全部规则（都在引擎 / `run_backtest.py` 里，没有后处理）

| 项目 | 规则 | 依据 |
| --- | --- | --- |
| 资金费 | **原始已实现费率，不打折**；按每个结算事件自己的间隔（1/2/4/8h）折算 8h 费率 | 数据本身 |
| 入场 | 8h 折算费率 < −10bp（`entry_fav_n`，旧参数，§6 敏感性 5/10/20/50bp）；**无基差过滤** | 旧 −38bp 是拟合常数，已删；0/−20/−38/−60 仅作敏感性 |
| 出场 | 费率不再为负后，若立即平仓不利，最多再等 168h 且额外费率 ≤ 名义 0.3%；窗口末强平 | 旧参数；敏感性 0/24/168h |
| 成交量上限 | 仓位 ≤ **10% × 截至上一个已完成小时（t−24…t−1）的滚动 24h 成交额**（min(现货, 永续)）；入场/加仓看额度，**持仓期间也每小时检查，超限即减仓**；零量 = 无额度（修复旧版 dv==0 绕过） | 因果；10% 是参与率运营参数，敏感性 5/20% |
| OI 上限 | 仓位 ≤ **10% × 上一个已完成小时的 OI**（小时 t 用小时 t−1 内最后一个 5 分钟快照）；**每小时在入场/加仓时检查，持仓期间同样每小时检查，超限即减仓**；缺 OI = 不可持有（缺的小时沿用上一个已知值）| 因果；v4 是“前一 UTC 日 5 分钟 OI 中位数”（日内常数），见 RESULTS §5/§7；敏感性 2/5/20%/关 |
| 库存上限 | 每币 ≤ `min(cap_usdt, S)`；`holdings` 模式 cap = `Borrowable Qty @ 30% (Token)`（原样使用）× 窗口末现货价；`equal` 模式 cap = S/币数 | 私有文件 / 公开等额 |
| 手续费 | 现货 taker 10bp，永续 taker 5bp | 币安标准费率 |
| 价差 | `spread_by_symbol.csv` 半价差 | 公开盘口快照 |
| **冲击** | **20bp/腿**（旧 10bp）；10/30/50bp 敏感性 | 无实盘成交可标定，保守取 20，并给区间 |
| 执行 | `pov=0.20`，`xmax=0.02`，`dfrac=0.75`，**不限次补仓**（一次补仓只作敏感性）；深度用成交量代理 | 旧参数，未重标定 |
| 闲置资金 | **头条不计收益**；0/3/5% 仅作独立敏感性列 | 无证据支持任何取值 |

减仓说明：超限时按正常下单量约束分小时卖出（不假设瞬时清仓），因此短时仍可能超过上限（比例与最大比值见 RESULTS §15）。

### v8 引擎整改（逐项开关，全部关闭 = 精确复现 v7）

| 项目 | 规则 |
| --- | --- |
| 出场/减仓判断 | 用上一小时收盘价；成交按当小时 VWAP |
| 资金费 | 按结算时刻 markPrice（`download_markprice.py`）计价；缺失回退上一根永续收盘并计数 |
| 库存上限 | 头条为成本 USDT 口径；按币数换算（USDT 上限 ÷ t−1 价）的币数账本仅为敏感性 |
| 参与预算 | 每币-小时**一份**：上一小时成交额（现货/永续取小）的 20%，入场/补仓/出场/减仓共用 |
| 硬上限 | 成交量 10%（现货名义）、OI 10%（**永续名义**）对入场/补仓为硬上限；持仓超限减仓受预算约束 |
| 窗口末/超时出场 | 按预算分摊；缺 bar 顺延；窗口末残余按 20bp+手续费记平仓成本并披露 |
| 补仓 | 不限次；部分减仓后出场盈亏按整个 episode 状态判断 |
| 占用资金 | 头条按 MTM 报告（峰值/平均并列披露）；MTM 上限为敏感性 |
| 自冲击 k | 持仓每占 OI 1%，8h 负费率被推高 k bp（k=0/4/8；头条 k=0） |
| 平方根冲击 | 敏感性：每腿 Y×σ_day×√(Q/ADV24h)，Y=0.25/0.5/1/2，未标定（RESULTS §12.1） |

## 3. 实盘开平仓顺序

1. **开仓**：先卖现货（确认成交）→ 立刻开等量永续多；
2. **平仓**：先平永续 → 再买回现货；
3. 两边数量对齐，避免单边敞口。

## 4. 库存与资金前提

- 假设可在上限内卖出现货；**不计借币利息/库存机会成本**；
- 公开仓不含 `holdings.xlsx`、持仓数量或 cap：用 `make_holdings_cap.py` 在本地从你自己的文件生成（已被 `.gitignore`），或用公开的 `equal` 模式；
- `python test_reproduce.py --holdings <你的文件>` 复现头条。

## 5. 年化定义

```
名义 S 年化   = net / S / years                （years: 1y = 365/365；6m = 180/365）
占用资金年化 = net / 平均占用 / years
闲置理财（仅敏感性） = rate × (S − 平均占用) × years
```

两种年化并排报告；**占用资金年化不是可放大的收益率**（容量受限）。另报分季度、滚动 90 天、按周 bootstrap 区间，以及资金费 / 基差 / 价差+冲击 / 手续费拆分。

## 6. 币池与数据

- 币池：[`symbols_signal.csv`](./symbols_signal.csv)（267，**事后选择**：近 1 年出现过负费率）；
- 数据：币安公开 data.binance.vision（K 线、资金费、OI metrics），`download_data.py` + `download_oi_hourly.py` + `download_markprice.py`（小时 OI，由日包里的 5 分钟快照聚合；API 的 1h 历史只有约 30 天）；`download_oi.py` 仅用于 v4 日度对照；`build_dataset.py --depth proxy`；
- 预热：数据自 2025-10-01 起，报告窗口自 2025-10-28 起，保证滚动量/OI 在窗口第一天就是因果的。

## English (short)

Sell spot + long 1x perp while funding is negative. Raw realised funding (no haircut); volume cap = 10% of trailing-24h volume up to the previous completed hour and OI cap = 10% of the previous completed hour's open interest (last 5-min snapshot of hour t-1, hourly data from data.binance.vision), both checked every hour at entry and while holding (excess is sold down at normal execution limits; zero volume/unknown OI = no room); 20bp impact (10/30 sensitivities); no basis-entry filter (−20/−38/−60 shown as sensitivities); idle-cash yield only as a separate 0/3/5% sensitivity; per-symbol inventory cap from a private file via make_holdings_cap.py (never committed) or the public equal cap S/N.
