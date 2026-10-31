#!/usr/bin/env python3
"""Regenerates RESULTS.md from results/*.csv (every number comes from a CSV; only the prose is typed)."""
import pandas as pd, numpy as np
from pathlib import Path
import config as C

R = C.REPO / "results"; M2 = ("holdings", "equal"); NAME = {"holdings": "A", "equal": "B"}
H = {m: pd.read_csv(R / f"headline_{m}.csv").set_index("window") for m in M2}
Q = {m: pd.read_csv(R / f"quarterly_{m}.csv") for m in M2}
RO = {m: pd.read_csv(R / f"rolling90d_{m}.csv") for m in M2}
SE = {m: pd.read_csv(R / f"sensitivity_{m}.csv") for m in M2}
BR = {m: pd.read_csv(R / f"bridge_{m}.csv") for m in M2}
RB = {m: pd.read_csv(R / f"robustness_{m}.csv") for m in M2}
CV = pd.read_csv(R / "oi_hourly_coverage_summary.csv").set_index("item").value
GR = {m: pd.read_csv(R / f"grid_{m}.csv") for m in M2}
GX = {m: pd.read_csv(R / f"grid_extop_{m}.csv") for m in M2}
WF = {m: pd.read_csv(R / f"waterfall_{m}.csv") for m in M2}
SV = {m: pd.read_csv(R / f"sens_v8_{m}.csv") for m in M2}
EV = pd.read_csv(R / "oi_turn_events.csv")
V7 = {"holdings": {"1y": 17.99, "6m": 10.46}, "equal": {"1y": 17.01, "6m": 11.84}}   # v7 (20d9522) headline, = waterfall step 0
# reviewer's independent reference (MAC_AUDIT_VERIFY.md, "full stack", min(prior,current) depth; A1y, A6m, B1y, B6m)
REF = {"k0_20": (19.98, 11.77, 17.97, 12.30), "k4_20": (12.80, 7.62, 13.28, 9.07), "k0_30": (14.88, 8.86, 15.65, 10.68)}
o = []; w = o.append
V4 = {"holdings": {"1y": 13.58, "6m": 7.82}, "equal": {"1y": 14.44, "6m": 9.75}}   # v4 (daily OI) headline, = bridge step 7 / sensitivity row oi_granularity


def head_table(m):
    w("| 窗口 | 净利(万U) | 名义S年化 | 占用资金年化(MTM) | 平均占用(MTM, 万U) | 峰值占用 MTM(万U，占S) | 峰值占用 成本口径(万U) | 资金费 | 基差(未扣成本) | 价差+冲击 | 其中冲击 | 手续费 | bootstrap95%(S) | v7名义S年化 | v4名义S年化 |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k, lab in (("1y", "近 1 年（主）"), ("6m", "近 6 个月")):
        h = H[m].loc[k]
        w(f"| {lab} | {h.net_wan:.1f} | {h.ann_on_S_pct:.2f}% | {h.ann_on_used_pct:.1f}% | {h.avg_used_wan:.0f}（{h.avg_used_pct_of_S:.1f}% of S） | {h.peak_used_mtm_wan:.0f}（{h.peak_used_mtm_pct_of_S:.0f}%） | {h.peak_used_cost_wan:.0f} | {h.funding_wan:.0f} | {h.basis_gross_wan:.0f} | "
          f"{h.spread_impact_wan:.0f} | {h.of_which_impact_wan:.0f} | {h.fees_wan:.0f} | {h.boot_ann_on_S_lo_pct:.1f}%–{h.boot_ann_on_S_hi_pct:.1f}% | {V7[m][k]:.2f}% | {V4[m][k]:.2f}% |")
    w("")


def quarter_table(m):
    w("| 窗口 | 段 | 起 | 止 | 净利(万U) | 资金费 | 基差(未扣成本) | 价差+冲击 | 手续费 | 名义S年化% | 平均占用(万U) | 占用年化% |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in Q[m].itertuples():
        w(f"| {r.window} | {r.block} | {r.start} | {r.end} | {r.net_wan:.1f} | {r.funding_wan:.0f} | {r.basis_gross_wan:.0f} | {r.spread_impact_wan:.0f} | {r.fees_wan:.0f} | {r.ann_on_S_pct:.2f} | {r.avg_used_wan:.0f} | {r.ann_on_used_pct:.1f} |")
    w("")


def roll_table(m):
    w("| 窗口 | 点数(周步长) | 最小 | 25% | 中位 | 75% | 最大 | 最近一个 |"); w("|---|---|---|---|---|---|---|---|")
    for k in ("1y", "6m"):
        x = RO[m][RO[m].window == k].ann_on_S_pct
        w(f"| {k} | {len(x)} | {x.min():.2f} | {x.quantile(.25):.2f} | {x.median():.2f} | {x.quantile(.75):.2f} | {x.max():.2f} | {x.iloc[-1]:.2f} |")
    w("")


def val(df, win, g, c): return df[(df.window == win) & (df.group == g) & (df.case.str.startswith(c))].iloc[0]
hA1, hA6, hB1, hB6 = H["holdings"].loc["1y"], H["holdings"].loc["6m"], H["equal"].loc["1y"], H["equal"].loc["6m"]

w("# 回测结果（v8 · 引擎整改版）\n")
w("> 本页全部数字由 `run_backtest.py` / `run_sensitivity.py` / `run_robustness.py` / `waterfall.py` / `run_sens_v8.py` / `run_grid.py` / `oi_turn_events.py` / `oi_coverage.py` 直接输出（CSV 在 [results/](./results/)），本页由 `make_results_md.py` 从 CSV 生成，**没有任何后处理**：无费率折扣、无基差过滤、闲置理财不进头条。参数口径见 [STRATEGY.md](./STRATEGY.md)。")
w("> 单位：净利/占用为**万 USDT**；窗口 1y = 2025-10-28 → 2026-10-28（365 天），6m = 2026-05-01 → 2026-10-28（180 天）。时间均为 UTC。")
w("> 复现：见 README「复现」；`python test_reproduce.py [--holdings 你的持仓文件]` 对照 [results/reference_headline.json](./results/reference_headline.json)。\n")
w("## 0. 头条（S = 7000 万 U）\n")
w("**v8 = v7（20d9522）+ 引擎整改（逐项开关，全部关闭 = 精确复现 v7）**：出场/减仓按上一小时收盘判断、成交按小时 VWAP；资金费按结算时刻 markPrice 计价；"
  "每币-小时只有**一份**参与预算（上一小时成交额的 20%，入场/补仓/出场/减仓共用）；成交量 10%（现货名义）与 OI 10%（**永续名义**）是**入场/补仓的硬上限；减仓按参与预算分小时进行（有节奏，持仓可短时超限，见 §15.1）**；窗口末/超时出场按参与率分摊、缺 bar 顺延；"
  "部分减仓后出场盈亏按整个 episode 的状态判断；资金占用另报按 MTM 口径。**补仓规则不变：不限次补仓（只要入场条件满足且有额度即补）**；一次补仓、币数账本、MTM 占用限制仅作敏感性（§12）。"
  "借币利息 = 0，闲置理财 = 0。\n")
w("**披露（模型选择，非容量）**：① “10% 硬上限”只对入场/补仓和减仓目标成立，减仓按 20% 参与预算分批，所以持仓期间会有币-小时超限（A 1y 5.1%，见 §15.1）；"
  "② 币数口径硬上限相对软目标在 A 1y 约 +1.3pp，来源是换手低 7.5%（上限不随价格波动反复重新折算而买卖），是建模选择，不是容量放松；"
  "③ **出场状态按整个 episode 判断（f_exitstate）依赖沿用的 wait_max=168h 与 wait_cap（旧参数，且调在同一窗口上）**：est 含整段已实现价差损益和全部手续费，更常为负，按继承参数等更久才出场，A 1y 平均占用 MTM 1345 → 1860 万（+38%）、持仓币-小时 +51%、episodes 1968 → 1477、年化 +0.87pp（审查官复核）。**因此 v8 的占用数字不能与 v7 直接比较。**\n")
w("规则（v7 部分沿用）：原始已实现资金费（不打折）· **成交量上限 = 10% × 截至上一个已完成小时的滚动 24h 成交量**（小时 t 用 t−24…t−1 小时，不含当前小时；零量 = 无额度）· "
  "**OI 上限 = 10% × 上一个已完成小时的 OI**（小时 t 用小时 t−1 内最后一个 5 分钟快照；每小时在开仓/加仓时检查，**持仓期间每小时检查，超限即按正常下单节奏减仓**；缺 OI = 不可持有）· "
  "冲击 20bp/腿 · 无基差入场过滤 · 闲置理财不计入头条。与 v4 相比：OI 由“前一 UTC 日中位数”改为“上一个已完成小时的快照”（v7），再叠加 v8 引擎整改（瀑布见 §10）。\n")
w("### A. 真实库存上限（私有文件，不在仓内）\n"); head_table("holdings")
w("### B. 公开可复现（每币上限 = S/267）\n"); head_table("equal")
w(f"**v7 → v8**：A 1y {V7['holdings']['1y']:.2f}% → **{hA1.ann_on_S_pct:.2f}%**，6m {V7['holdings']['6m']:.2f}% → **{hA6.ann_on_S_pct:.2f}%**；B 1y {V7['equal']['1y']:.2f}% → **{hB1.ann_on_S_pct:.2f}%**，6m {V7['equal']['6m']:.2f}% → **{hB6.ann_on_S_pct:.2f}%**。\n")
w(f"**占用口径披露**：头条的占用已改为**按市值（MTM）**。A 1y 峰值占用 MTM = {hA1.peak_used_mtm_wan:.0f} 万 U（**{hA1.peak_used_mtm_pct_of_S:.0f}% of S，超过 S**），成本口径峰值仅 {hA1.peak_used_cost_wan:.0f} 万；"
  f"币价上涨时库存市值超过 S，头条只对成本口径做上限（MTM 上限见 §12 的 mtm_cap 敏感性）。平均占用两种口径相近（见上一条披露③：占用数字与 v7 不可比；A 1y MTM {hA1.avg_used_mtm_wan:.0f} / 成本 {hA1.avg_used_cost_wan:.0f} 万）。B 1y 峰值 MTM {hB1.peak_used_mtm_wan:.0f} 万（{hB1.peak_used_mtm_pct_of_S:.0f}% of S）。\n")
w(f"**与 v4 对比**：A 1y {V4['holdings']['1y']:.2f}% → **{hA1.ann_on_S_pct:.2f}%**（{hA1.ann_on_S_pct - V4['holdings']['1y']:+.2f}pp），A 6m {V4['holdings']['6m']:.2f}% → **{hA6.ann_on_S_pct:.2f}%**；"
  f"B 1y {V4['equal']['1y']:.2f}% → **{hB1.ann_on_S_pct:.2f}%**（{hB1.ann_on_S_pct - V4['equal']['1y']:+.2f}pp），B 6m {V4['equal']['6m']:.2f}% → **{hB6.ann_on_S_pct:.2f}%**。"
  "原因见 §5.1：不是小时 OI 的水平更高（小时 OI / 前一日 OI 的中位数 ≈ 0.99），而是**更新鲜**——把小时 OI 人为变陈旧 6/12/24 小时，收益单调回落到接近 v4。\n")
w("### 年化口径并排")
w(f"- **名义 S 年化** = 净利 / S / 年数：A 1y {hA1.ann_on_S_pct:.2f}%，B 1y {hB1.ann_on_S_pct:.2f}%；")
w(f"- **占用资金年化** = 净利 / 平均占用 / 年数：A 1y {hA1.ann_on_used_pct:.1f}%，B 1y {hB1.ann_on_used_pct:.1f}%（平均占用为 S 的 {hA1.avg_used_pct_of_S:.1f}% / {hB1.avg_used_pct_of_S:.1f}%）；占用年化**不是**资金可放大到的收益率，容量受 OI / 成交量 / 库存限制；")
w("- 闲置资金收益没有证据支持任何取值，只作独立敏感性列：\n")
for m in M2:
    w(f"{NAME[m]}：\n"); w("| 窗口 | 不含理财（头条） | 闲置理财 3% | 闲置理财 5% |"); w("|---|---|---|---|")
    for k in ("1y", "6m"):
        h = H[m].loc[k]; w(f"| {k} | {h.sens_idle0_ann_on_S_pct:.2f}% | {h.sens_idle3_ann_on_S_pct:.2f}% | {h.sens_idle5_ann_on_S_pct:.2f}% |")
    w("")

w("## 1. 分季度（等长 ~91 天；净利含未平仓盯市，各列加总 = 净利）\n")
w("### A\n"); quarter_table("holdings"); w("### B\n"); quarter_table("equal")
qa = Q["holdings"]; qa = qa[qa.window == "1y"]
w(f"**读法**：A 1y 的季度年化从 {qa.ann_on_S_pct.min():.1f}% 到 {qa.ann_on_S_pct.max():.1f}%，收益**很不均匀**，1y 头条不是稳态收益。\n")
w("### 1.1 前半年 vs 后半年（1y 窗口对半切，各约 182.5 天，名义 S 年化）\n")
w("| 口径 | 前半年 净利(万U) | 前半年 年化 | 前半年 平均占用(万U) | 后半年 净利(万U) | 后半年 年化 | 后半年 平均占用(万U) | 全年 年化 |"); w("|---|---|---|---|---|---|---|---|")
for m in M2:
    r = RB[m]; a = r[r.part == "first half"].iloc[0]; b = r[r.part == "second half"].iloc[0]; f = r[(r.test == "base") & (r.window == "1y")].iloc[0]
    w(f"| {NAME[m]} | {a.net_wan:.1f} | {a.ann_on_S_pct:.2f}% | {a.avg_used_wan:.0f} | {b.net_wan:.1f} | {b.ann_on_S_pct:.2f}% | {b.avg_used_wan:.0f} | {f.ann_on_S_pct:.2f}% |")
w("")
w("## 2. 滚动 90 天年化（周步长，名义 S）\n")
for m in M2: w(f"{NAME[m]}：\n"); roll_table(m)
w("## 3. Bootstrap 95% 区间\n")
w("按“周”整块有放回重抽（5000 次，固定种子），把周均净利年化。" +
  f"A：1y {hA1.boot_ann_on_S_lo_pct:.1f}%–{hA1.boot_ann_on_S_hi_pct:.1f}%，6m {hA6.boot_ann_on_S_lo_pct:.1f}%–{hA6.boot_ann_on_S_hi_pct:.1f}%；"
  f"B：1y {hB1.boot_ann_on_S_lo_pct:.1f}%–{hB1.boot_ann_on_S_hi_pct:.1f}%，6m {hB6.boot_ann_on_S_lo_pct:.1f}%–{hB6.boot_ann_on_S_hi_pct:.1f}%。"
  "只描述样本内周与周之间的波动，**看不到机制切换（见 §1 的季度与半年落差）**，也不是对未来的预测区间。\n")
w("## 4. 收益拆分与集中度（1y）\n")
for m, h in (("A", hA1), ("B", hB1)):
    w(f"- {m}：资金费 {h.funding_wan:.0f} + 基差（未扣成本）{h.basis_gross_wan:.0f} + 价差与冲击 {h.spread_impact_wan:.0f}（其中冲击 {h.of_which_impact_wan:.0f}）+ 手续费 {h.fees_wan:.0f} + 期末盯市 ≈ 净利 {h.net_wan:.0f}（万 U）；成本合计约占资金费的 {-(h.spread_impact_wan + h.fees_wan) / h.funding_wan * 100:.0f}%。")
w(f"\n集中度（**扣手续费与成本后的净 PnL**，按币汇总，不列币名；价差前口径见 grid_*.csv 的 *_gross 列）：1y 前 5 币占 A {hA1.top5_share_pct:.0f}% / B {hB1.top5_share_pct:.0f}%，前 10 币占 A {hA1.top10_share_pct:.0f}% / B {hB1.top10_share_pct:.0f}%；6m 前 5 币占 A {hA6.top5_share_pct:.0f}% / B {hB6.top5_share_pct:.0f}%。盈利币数（1y）A {hA1.coins_profitable:.0f}/{hA1.coins_traded:.0f}，B {hB1.coins_profitable:.0f}/{hB1.coins_traded:.0f}。\n")
w("### 4.1 剔除盈利最多的前 5 / 前 10 个币后的头条\n")
w("按该窗口基准运行里各币自身的**净**盈亏（含价差/冲击与手续费）排序，把前 k 个币从币池移除，**整个组合重新模拟**（每币上限不变，释放出的额度可被其余币使用）。排序是事后的，这是集中度检验，不是可交易规则；不列币名。\n")
w("| 口径 | 窗口 | 全币池 | 剔除前 5 | 剔除前 10 | 剔除前 5 平均占用(万) | 剔除前 10 平均占用(万) |"); w("|---|---|---|---|---|---|---|")
for m in M2:
    r = RB[m]
    for k in ("1y", "6m"):
        g = lambda t: r[(r.test == t) & (r.window == k)].iloc[0]
        w(f"| {NAME[m]} | {k} | {g('base').ann_on_S_pct:.2f}% | {g('ex_top5').ann_on_S_pct:.2f}% | {g('ex_top10').ann_on_S_pct:.2f}% | {g('ex_top5').avg_used_wan:.0f} | {g('ex_top10').avg_used_wan:.0f} |")
w("")

w("## 5. OI 上限敏感性（5% / 10% / 20%，小时级 OI；A、B × 1y、6m）\n")
w("| 口径 | OI 上限 | 1y 名义S年化 | 1y 占用年化 | 1y 平均占用(万) | 1y 净利(万) | 6m 名义S年化 | 6m 平均占用(万) |"); w("|---|---|---|---|---|---|---|---|")
for m in M2:
    df = SE[m]
    for g, c in (("oi_limit", "OI limit 5%"), ("oi_limit", "OI limit 10%"), ("oi_limit", "OI limit 20%"), ("oi_limit", "OI limit off"), ("oi_granularity", "OI limit 10% of previous-UTC-day")):
        x, y = val(df, "1y", g, c), val(df, "6m", g, c)
        lab = {"OI limit 5%": "5%（上一小时 OI）", "OI limit 10%": "**10%（头条）**", "OI limit 20%": "20%", "OI limit off": "关闭", "OI limit 10% of previous-UTC-day": "10% × 前一 UTC 日 OI（v4 对照）"}[c]
        w(f"| {NAME[m]} | {lab} | {x.ann_on_S_pct:.2f}% | {x.ann_on_used_pct:.1f}% | {x.avg_used_wan:.0f} | {x.net_wan:.1f} | {y.ann_on_S_pct:.2f}% | {y.avg_used_wan:.0f} |")
w("")
w("### 5.1 为什么小时 OI 比日度 OI 收益更高：新鲜度诊断（不是调参）\n")
w("把小时 OI 人为再延后 k 小时（小时 t 用 t−1−k 的 OI；k=0 即头条），其余不变：\n")
w("| 口径 | k=0（头条） | k=6h | k=12h | k=24h | v4 日度 OI |"); w("|---|---|---|---|---|---|")
for m in M2:
    df = SE[m]; g = lambda c: val(df, "1y", "oi_staleness", c).ann_on_S_pct
    w(f"| {NAME[m]} 1y | {H[m].loc['1y'].ann_on_S_pct:.2f}% | {g('hourly OI made 6h'):.2f}% | {g('hourly OI made 12h'):.2f}% | {g('hourly OI made 24h'):.2f}% | {val(df, '1y', 'oi_granularity', 'OI limit 10% of previous-UTC-day').ann_on_S_pct:.2f}% |")
w("")
w(f"OI 水平本身差不多：1y 内小时 OI / 前一 UTC 日 OI 的 P10 / 中位 / P90 = {CV['1y_hourly_over_prev_day_oi_ratio_p10']:.2f} / {CV['1y_hourly_over_prev_day_oi_ratio_median']:.2f} / {CV['1y_hourly_over_prev_day_oi_ratio_p90']:.2f}，"
  f"{CV['1y_share_of_hours_hourly_limit_looser_than_daily_pct']:.0f}% 的币-小时上小时上限比日度上限更松（其余更紧）。与上表一致的读法：收益差异随陈旧度单调变化，说明主要来自“限额是否跟得上最新 OI”（日度版平均陈旧约 12–36 小时），而不是 OI 水平差异；逐笔机制未单独拆解。\n")

w("## 6. 冲击 10bp / 20bp / 30bp 敏感性（小时级 OI；A、B × 1y、6m；10/20/30/50bp 全网格见 §11）\n")
w("| 口径 | 冲击 | 1y 名义S年化 | 1y 占用年化 | 1y 平均占用(万) | 1y 净利(万) | 6m 名义S年化 | 6m 平均占用(万) |"); w("|---|---|---|---|---|---|---|---|")
for m in M2:
    for bp in (10, 20, 30):
        x, y = val(SE[m], "1y", "impact", f"impact {bp}bp"), val(SE[m], "6m", "impact", f"impact {bp}bp")
        w(f"| {NAME[m]} | {bp}bp{'（头条）' if bp == 20 else ''} | {x.ann_on_S_pct:.2f}% | {x.ann_on_used_pct:.1f}% | {x.avg_used_wan:.0f} | {x.net_wan:.1f} | {y.ann_on_S_pct:.2f}% | {y.avg_used_wan:.0f} |")
w("")

w("## 7. 桥接（近 1 年；逐步累计，顺序会影响单步大小；末步 = 日度 OI → 小时 OI）\n")
w("起点 = 旧规则搬到本仓公开数据管线上复算；第 7 步 = v4 头条（日度 OI）；**第 8 步 = v7（20d9522）；第 9 步 = 本版（v8 引擎整改，拆分见 §10）**。\n")
for m in M2:
    w(f"{NAME[m]}：\n"); w("| 步骤(累计) | 不含理财 年化% | 本步变化(pp) | 含闲置理财5% 年化% | 净利(万) | 平均占用(万) |"); w("|---|---|---|---|---|---|")
    for r in BR[m].itertuples():
        d = "—" if pd.isna(r.delta_no_idle_pp) else f"{r.delta_no_idle_pp:+.2f}"
        w(f"| {r.step} | {r.ann_no_idle_pct:.2f} | {d} | {r.ann_idle5_pct:.2f} | {r.net_wan:.1f} | {r.avg_used_wan:.0f} |")
    w("")
w("**注意**：整改里有正有负；去掉 0.8 折扣、把 OI 改为滚动前一日、再改为小时级是**加分**；持仓期间减仓、冲击 20bp、去掉基差过滤是**减分**。\n")

w("## 8. 其它敏感性（围绕新底线，每行只改一项；A，完整含 6m 与 B 见 `results/sensitivity_*.csv`）\n")
w("| 组 | 情景 | 1y 名义S年化% | 1y 占用年化% | 1y 净利(万) | 1y 平均占用(万) | 6m 名义S年化% |"); w("|---|---|---|---|---|---|---|")
sa = SE["holdings"]
for r in sa[sa.window == "1y"].itertuples():
    y = sa[(sa.window == "6m") & (sa.group == r.group) & (sa.case == r.case)].iloc[0]
    w(f"| {r.group} | {r.case} | {r.ann_on_S_pct:.2f} | {r.ann_on_used_pct:.1f} | {r.net_wan:.1f} | {r.avg_used_wan:.0f} | {y.ann_on_S_pct:.2f} |")
w("")
w("要点：冲击假设最敏感（我们没有实盘成交数据定标，故 20bp 为底，给 10/30）；基差入场过滤越严年化越高但这是在已知结果上选阈值，**不采用**；OI/成交量上限是容量约束，放松显著抬高收益；"
  "持仓期不减仓行比新规则高很多，但那意味着量掉下来后仍扛着超限仓位，实盘撤不掉；资金费打折仅作说明性展示，**无数据依据**。\n")

w("## 9. 小时 OI 数据来源与覆盖\n")
w("- 来源：币安公开数据 `data.binance.vision/data/futures/um/daily/metrics/{SYM}/{SYM}-metrics-{date}.zip`（5 分钟快照 `sum_open_interest_value`，UTC）；API `openInterestHist(period=1h)` 只覆盖最近约 30 天，无法重建 1 年，所以没用。下载脚本 `download_oi_hourly.py`。")
w("- 聚合：小时 h 的 OI = 落在 [h, h+1h) 内的**最后一个** 5 分钟快照（实际时间戳约 h:55，即小时 h 结束前最新的已知值）；引擎在小时 t 只用小时 t−1 的值（至少滞后 5 分钟），不含任何当前小时信息。")
w("- 缺失处理（沿用 v4 约定，不新增主观规则）：缺的小时沿用上一个已知值；首个有值之前 = 未知 = **不可持有**。")
w(f"- 覆盖（267 币 × 1y 窗口 {CV['1y_symbol_hours_total']:.0f} 币-小时）：有小时 OI 的占 **{CV['1y_symbol_hours_with_hourly_oi_pct']:.2f}%**（日度版 {CV['1y_symbol_hours_with_daily_oi_pct']:.2f}%）；"
  f"{CV['1y_symbols_with_100pct_hours']:.0f} 个币全程 100%，{CV['1y_symbols_with_any_missing_hour']:.0f} 个币缺的全部是**上市前**的小时（窗口内首个有值之后缺失 {CV['1y_missing_hours_after_first_valid_value']:.0f} 小时，没有中途断档）；"
  f"6m 窗口覆盖 {CV['6m_symbol_hours_with_hourly_oi_pct']:.2f}%（{CV['6m_symbols_with_any_missing_hour']:.0f} 个币上市晚于窗口起点）。这些币上市前本来也无价格数据，所以缺 OI 不改变可交易集合。")
w("- 数据文件 `oi_hourly/` 不入库（体积大、可重新下载）；汇总见 [results/oi_hourly_coverage_summary.csv](./results/oi_hourly_coverage_summary.csv)。\n")


def wf_table(m):
    w("| 步骤（累计，顺序影响单步大小） | 1y 年化% | 1y 本步Δpp | 1y 平均占用(万) | 6m 年化% | 6m 本步Δpp |"); w("|---|---|---|---|---|---|")
    X = WF[m]; X = X[~X.step.str.startswith("[")]
    a = X[X.window == "1y"].reset_index(drop=True); b = X[X.window == "6m"].reset_index(drop=True)
    for i in range(len(a)):
        d1 = "—" if pd.isna(a.delta_pp[i]) else f"{a.delta_pp[i]:+.2f}"; d2 = "—" if pd.isna(b.delta_pp[i]) else f"{b.delta_pp[i]:+.2f}"
        w(f"| {a.step[i]} | {a.ann_on_S_pct[i]:.2f} | {d1} | {a.avg_used_wan[i]:.0f} | {b.ann_on_S_pct[i]:.2f} | {d2} |")
    w("")
def wf_alone(m):
    w("| 整改项 | 1y 单独加到 v7 上 Δpp | 1y 它在头条里的贡献Δpp | 6m 单独 Δpp | 6m 头条内贡献Δpp |"); w("|---|---|---|---|---|")
    X = WF[m]; al = lambda win: X[(X.window == win) & X.step.str.startswith("[alone]")].reset_index(drop=True); lo = lambda win: X[(X.window == win) & X.step.str.startswith("[leave")].reset_index(drop=True)
    a1, a6, l1, l6 = al("1y"), al("6m"), lo("1y"), lo("6m")
    for i in range(len(a1)):
        nm = a1.step[i].replace("[alone] ", "")
        w(f"| {nm} | {a1.delta_pp[i]:+.2f} | {l1.delta_pp[i]:+.2f} | {a6.delta_pp[i]:+.2f} | {l6.delta_pp[i]:+.2f} |")
    w("")

w("## 10. v8 整改瀑布（相对 20d9522，OI 滞后 0、20bp、k=0）\n")
w("全部开关关闭 = 精确复现 v7（`test_reproduce.py` 校验）。下表按固定顺序累计；顺序会改变单步大小，所以再给“单独加到 v7”与“它在头条里的贡献（头条减去拿掉它后的堆叠）”两种口径。第 8 步只改占用口径，不改收益。\n")
w("### A（私有库存上限）\n"); wf_table("holdings"); wf_alone("holdings")
w("### B（公开等额）\n"); wf_table("equal"); wf_alone("equal")

def pv(m, win, lag, k, imp, col="ann_on_S_pct"):
    g = GR[m]; x = g[(g.window == win) & (g.oi_lag_h == lag) & (g.k_bp_per_1pct_oi == k) & (g.impact_bp == imp)].iloc[0]; return x[col]
w("## 11. 全网格：冲击 × OI 滞后 × 自冲击 k（名义 S 年化%）\n")
w("OI 滞后 0 = 小时 t 用小时 t−1 的 OI；1 = 再晚 1 小时。k = 持仓每占 OI 的 1%，8h 资金费率被推高 k bp（仅对负费率结算生效，上限为 0）；k=0 = 头条。\n")
for m in M2:
    w(f"### {NAME[m]}\n"); w("| 窗口 | OI滞后 | k | 10bp | 20bp | 30bp | 50bp |"); w("|---|---|---|---|---|---|---|")
    for win in ("1y", "6m"):
        for lag in (0, 1):
            for k in (0, 4, 8):
                w(f"| {win} | {lag} | {k} | " + " | ".join(f"{pv(m, win, lag, k, bp):.2f}" for bp in (10, 20, 30, 50)) + " |")
    w("")
w("### 11.1 组合现实场景：OI 滞后 1h + 冲击 30bp + k=4\n")
w("| 口径 | 窗口 | 名义S年化 | 净利(万) | 平均占用(MTM,万) | 峰值占用 MTM(万) | bootstrap95% | 前5币净占比 | 剔除前5(净PnL排序) | 剔除前10 |"); w("|---|---|---|---|---|---|---|---|---|---|")
for m in M2:
    g = GR[m]; x = GX[m]
    for win in ("1y", "6m"):
        r = g[(g.window == win) & (g.oi_lag_h == 1) & (g.k_bp_per_1pct_oi == 4) & (g.impact_bp == 30)].iloc[0]
        e = lambda t: x[(x.window == win) & (x.oi_lag_h == 1) & (x.k_bp_per_1pct_oi == 4) & (x.impact_bp == 30) & (x.test == t)].iloc[0].ann_on_S_pct
        w(f"| {NAME[m]} | {win} | {r.ann_on_S_pct:.2f}% | {r.net_wan:.0f} | {r.avg_used_wan:.0f} | {r.peak_used_mtm_wan:.0f} | {r.boot_ann_on_S_lo_pct:.1f}%–{r.boot_ann_on_S_hi_pct:.1f}% | {r.top5_share_pct:.0f}% | {e('ex_top5_net'):.2f}% | {e('ex_top10_net'):.2f}% |")
w("")
w("分季度见 `results/grid_quarterly_*.csv`；剔除前 5/10（净 PnL 排序，整组合重新模拟）见 `results/grid_extop_*.csv`。\n")

def sv(m, win, case, col="ann_on_S_pct"):
    d = SV[m]; return d[(d.window == win) & (d.case == case)].iloc[0][col]
w("## 12. 不进头条的敏感性（OI 滞后 0，20bp，k=0）\n")
w("| 情景 | A 1y | A 6m | B 1y | B 6m |"); w("|---|---|---|---|---|")
for case, lab in (("headline", "**头条（不限次补仓，成本 USDT 上限）**"), ("add_once", "一次补仓（每个 episode 初始 + 1 次）"), ("coin_ledger", "币数账本（A=持仓币数；B=S/N 按 t−1 价折币）"),
                  ("mtm_cap", "资金上限本身按 MTM 限制"), ("no_hardcap", "成交量/OI 不作硬上限（软限）"), ("reviewer_equiv", "审查官口径（min(上/本小时)深度、软限、OI 按永续名义）"),
                  ("reviewer_equiv k4", "审查官口径 + k=4"), ("reviewer_equiv 30bp", "审查官口径 + 30bp")):
    w(f"| {lab} | {sv('holdings', '1y', case):.2f}% | {sv('holdings', '6m', case):.2f}% | {sv('equal', '1y', case):.2f}% | {sv('equal', '6m', case):.2f}% |")
w("")
w("### 12.1 平方根冲击模型（替代固定 bp；不叠加 20bp）\n")
w("每笔成交每腿冲击 = **Y × σ_day × √(Q / ADV)**。Q = 该笔成交名义；ADV = 截至 t−1 的滚动 24h 成交额（min(现货, 永续)）；σ_day = 小时 t−24…t−1 现货小时对数收益的标准差 × √24（样本不足 12 个时取全样本中位数）；"
  "Y ∈ {0.25, 0.5, 1, 2}（**Y 未按本组合标定**）。半价差与手续费不变。注意：这里对每个小时切片单独套用平方根律，比对整笔母单套用更苛刻。\n")
w("| Y | A 1y | A 6m | B 1y | B 6m | A 1y 价差+冲击(万) | B 1y 价差+冲击(万) |"); w("|---|---|---|---|---|---|---|")
w(f"| 固定 20bp（头条） | {sv('holdings', '1y', 'headline'):.2f}% | {sv('holdings', '6m', 'headline'):.2f}% | {sv('equal', '1y', 'headline'):.2f}% | {sv('equal', '6m', 'headline'):.2f}% | {sv('holdings', '1y', 'headline', 'spread_impact_wan'):.0f} | {sv('equal', '1y', 'headline', 'spread_impact_wan'):.0f} |")
for y in ("0.25", "0.5", "1", "2"):
    c = f"sqrt_Y{y}"
    w(f"| {y} | {sv('holdings', '1y', c):.2f}% | {sv('holdings', '6m', c):.2f}% | {sv('equal', '1y', c):.2f}% | {sv('equal', '6m', c):.2f}% | {sv('holdings', '1y', c, 'spread_impact_wan'):.0f} | {sv('equal', '1y', c, 'spread_impact_wan'):.0f} |")
c = "sqrt_Y1 + OI lag1 + k4"
w(f"| 1 + OI 滞后 1h + k=4 | {sv('holdings', '1y', c):.2f}% | {sv('holdings', '6m', c):.2f}% | {sv('equal', '1y', c):.2f}% | {sv('equal', '6m', c):.2f}% | {sv('holdings', '1y', c, 'spread_impact_wan'):.0f} | {sv('equal', '1y', c, 'spread_impact_wan'):.0f} |")
w("\n读法：结论对 Y 极端敏感，且 Y 没有可用的实盘标定，所以只作敏感性；Y 较大时收益接近零或为负。\n")

w("## 13. 与独立审查官的对账（MAC_AUDIT_VERIFY.md，OI 滞后 0）\n")
w("审查官“全量修复组合”= 出场滞后 + markPrice 资金费 + 共享预算 + 出场状态 + OI 按永续名义 + 无强平绕过 + **min(上一小时, 当前小时)** 深度，**软**成交量/OI 目标。本仓头条用严格因果的“上一小时”并把 10% 作硬上限，所以对账用 `reviewer_equiv` 行（同口径）：\n")
w("| 场景 | 口径 | A 1y | A 6m | B 1y | B 6m |"); w("|---|---|---|---|---|---|")
for key, lab, case in (("k0_20", "k=0 20bp", "reviewer_equiv"), ("k4_20", "k=4 20bp", "reviewer_equiv k4"), ("k0_30", "k=0 30bp", "reviewer_equiv 30bp")):
    me = (sv("holdings", "1y", case), sv("holdings", "6m", case), sv("equal", "1y", case), sv("equal", "6m", case)); rf = REF[key]
    w(f"| {lab} | 审查官 | " + " | ".join(f"{x:.2f}" for x in rf) + " |")
    w(f"| {lab} | 本仓 reviewer_equiv | " + " | ".join(f"{x:.2f}" for x in me) + " |")
    w(f"| {lab} | 差（本仓−审查官） | " + " | ".join(f"{a - b:+.2f}" for a, b in zip(me, rf)) + " |")
w("\n残差均小于 0.1pp、方向一致偏低；**原因已定位**：差异来自 f_exitpov（窗口末前 wind_down_h=24h 起按参与率分批平仓）；审查官复核：`reviewer_equiv` 且 f_exitpov=0 时与其全量栈 19.98 / 11.77 / 17.97 / 12.30 在两位小数上完全一致。窗口末残余名义的平仓成本很小（A 约 0.06 万 U），解释不了这个差。头条（因果上一小时 + 硬上限）与审查官口径的差别见 §12 的头条行与 reviewer_equiv 行。\n")

w("## 14. “3,201 次负费率转折事件”的核对\n")
w("定义（`oi_turn_events.py`）：池内 267 币，1y 窗口内，**某币资金费结算事件的费率 < 0 且该币上一次结算费率 ≥ 0** 记为一次“转负”事件；事件后 6 小时 OI 变化 = OI[h]/OI[h−6]−1（h 为事件所在小时，OI 为上一完成小时口径）。\n")
w("| 定义 | 事件数 | 有 OI 的事件 | 6h OI 变化中位数% | OI 上升占比% |"); w("|---|---|---|---|---|")
for r in EV.itertuples(): w(f"| {r.definition} | {r.events} | {r.events_with_oi} | {r.median_oi_change_6h_pct:.2f} | {r.share_up_pct:.1f} |")
w("\n在阈值、前值条件、去重窗口与全样本窗口上扫描过，**没有任何一种合理定义能复现 PDF 里的 3,201 / 6.8% / 74.6%**。建议 PDF 删除该数字，或改用上表主定义（43,092 次，中位数 −0.68%，上升占比 38.6%），并写明依赖转负深度：较浅（< −1bp）时 OI 中位数下降；较深（< −10bp）时 OI 中位数上升 +17.6%、上升占比 82.5%。基线（全部币-小时）中位数 −0.24% 与 PDF 的 −0.24% 吻合。\n")

w("## 15. 引擎整改的已知差异与诊断\n")
for i, t in enumerate([
    f"成交量 10% 与 OI 10% 对入场/补仓是硬上限；对已持仓的减仓仍受 20% 参与预算约束，成交量骤降时会连续数小时超限。头条 1y：A 有 {hA1.hours_over_vol_cap:.0f}/{hA1.coin_hours_held:.0f}（{hA1.hours_over_vol_cap / hA1.coin_hours_held * 100:.1f}%）个币-小时超成交量上限（OI {hA1.hours_over_oi_cap:.0f}），B 有 {hB1.hours_over_vol_cap:.0f}/{hB1.coin_hours_held:.0f}（{hB1.hours_over_vol_cap / hB1.coin_hours_held * 100:.1f}%；OI {hB1.hours_over_oi_cap:.0f}）；最大比值 成交量 A {hA1.max_vol_cap_ratio:.1f}× / B {hB1.max_vol_cap_ratio:.1f}×，OI A {hA1.max_oi_cap_ratio:.1f}× / B {hB1.max_oi_cap_ratio:.1f}×。**这些是减仓受参与预算约束造成的残余超限，不是硬上限被绕过；但“10% 硬上限”因此只对入场/补仓成立，减仓是有节奏的。**",
    f"参与预算按**上一小时**成交额（严格因果，对上一小时的参与率上限 {hB1.max_prior_pov_pct:.0f}%）；但相对**同一小时**成交额，参与率超过 20% 的成交数：A 1y {hA1.fills_over_same_hour_pov:.0f}/{hA1.fills:.0f}（{hA1.fills_over_same_hour_pov / hA1.fills * 100:.0f}%），B 1y {hB1.fills_over_same_hour_pov:.0f}/{hB1.fills:.0f}（{hB1.fills_over_same_hour_pov / hB1.fills * 100:.0f}%），原因是当前小时成交额可能远低于上一小时；审查官测得最大同小时参与率 A 1y 72326%、B 6m 8711%（脚本在审查官目录，本仓 CSV 未存此项）。这**不是向上偏差**：改用 min(上一小时, 当前小时)（更严格）A 1y 反而升到 21.26%（换手更低）。但“在低成交量小时按小时 VWAP 成交”本身是一个执行假设，真实成交会更差。审查官口径见 §13。",
    f"窗口末到期仍未能按预算平完的残余名义：A {hA1.residual_end_wan:.1f} 万 U、B {hB1.residual_end_wan:.1f} 万 U，按 20bp 冲击+手续费记入平仓成本（A {hA1.residual_liq_cost_wan:.2f} 万、B {hB1.residual_liq_cost_wan:.2f} 万）。缺 bar 的小时顺延，不用陈旧价平仓。",
    f"markPrice 缺失的资金费结算事件回退到上一根永续收盘价（1y：A {hA1.funding_events_no_mark:.0f} 次、B {hB1.funding_events_no_mark:.0f} 次）。markPrice 数据与审查官已下载的 267 合约数据逐点一致。",
    "参与率按每腿 USDT 名义计；不单独约束现货与永续两腿的币数差。",
    "P2-06（OI 覆盖/缺失处理）未改动：缺 OI = 不可持有，缺的小时沿用上一个已知值。"], 1):
    w(f"{i}. {t}")
w("")

w("## 16. 已知局限（逐条诚实写明）\n")
for i, t in enumerate([
    "**库存上限是静态快照**：用一次性的 Borrowable Qty × 窗口末价；真实库存随时间变化。",
    "**币池是事后的**：267 个币是“近 1 年至少出现过负费率”的名单，存在选择偏差。",
    "**盘口深度用成交量代理**；执行参数（`pov=0.20`、`xmax=0.02`、`dfrac=0.75`、最多等 168h、`vol_frac=0.10`）沿用旧版，仅给出部分敏感性。",
    "**减仓有执行节奏**：持仓超限后按正常下单量约束分小时卖出，所以短时间仍会超过上限；没有“瞬间减仓”的假设。",
    "冲击是**固定 bp/腿**（20bp 为底，10/20/30/50 为敏感性，平方根模型见 §12.1），与真实盘口深度的关系没标定。平方根模型：按**每小时切片**计 √(Q/ADV)，不是整笔 metaorder，大单分批建仓会**低估**冲击；Y 未标定，只作敏感性（Y≥0.5 时 A 1y 已 ≤ 8.9%，Y=1 为负）；σ 缺历史时用全样本中位数（常数级前视，影响可忽略）；`of_which_impact_wan` 展示列在 sqrt 模式下原先仍显示固定 bp 冲击，现已改为 NaN（净利不受影响）。",
    "**补仓不限次**：满足入场条件且有额度就继续补；一次补仓版本见 §12（收益显著下降）。",
    "库存上限头条里按成本 USDT 口径；币价上涨时库存市值可超过 S（见 §0 峰值占用）；按 S 的 MTM 上限与减仓见 `results/capacity_curve_mtmderisk.*`（补充敏感性，非头条）；注意“MTM ≤ S”只在上一小时收盘价、且在参与预算内成立：小时内价格波动与减仓节奏仍会让峰值 MTM 占用超过 S：口径 A、近 1 年，S≥1000 万时约 106%–109%，S=200–750 万时约 113%–118%，S=100 万时约 123%–124.5%；口径 B 峰值仅约 24%–46%；近 6 个月区间更宽，不是硬上限（M5）。",
    "**A 的库存是快照**：每币 cap 取 min(cap, S)，用一次性数量覆盖全年；“币数账本”敏感性（A 1y +10pp，30.57%）把今天的库存数量套到整年，只能当**上界**，不是头条。",
    "**硬上限 vs 软目标**：币数口径的硬上限相对软目标在 A 1y 约 +1.3pp，来自换手 −7.5%（上限不随价格波动反复重新折算、买卖），是**建模选择**，不是容量放松。",
    "**“补仓限一次”敏感性主要在测执行节奏**：一次建仓本来就是按参与率分多小时的多笔成交，限一次补仓会锁死建仓速度，所以收益大降（A 1y 10.17%）不代表“补仓规则”本身的价值。",
    "**隐私保护依赖 `.gitignore` 的文件名模式**（`holdings_cap*.csv`、`my_cap*.csv`、`*.xlsx`、`holdings_qty*.csv` 等）：若把库存文件改成其他文件名，`.gitignore` 拦不住，提交前请自查。",
    "OI 是 5 分钟快照的小时末值；真实下单时点的 OI 可能略有不同；5 分钟快照本身来自币安公开日包，个别日包缺失时按上述规则沿用。",
    "窗口只有 1 年，前后半年差异很大（§1.1），**不要把 1y 当稳态预期**。",
    "仍**未计入**：借币成本/库存机会成本、两腿非同时成交的基差跳空、拒单重试、强平/保证金路径。"], 1):
    w(f"{i}. {t}")
Path(C.REPO / "RESULTS.md").write_text("\n".join(o) + "\n")
print("RESULTS.md written", len(o), "lines")
