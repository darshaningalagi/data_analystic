import pandas as pd
import numpy as np

# ── helpers ───────────────────────────────────────────────────────────────────

def safe_div(a, b, default=0):
    return a / b if b else default

def pct_change(new, old):
    if old == 0:
        return 0.0
    return round(((new - old) / abs(old)) * 100, 2)

# ── KPI summary ───────────────────────────────────────────────────────────────

def compute_kpis(df):
    total     = len(df)
    abandoned = df["abandoned"].sum()
    resolved  = df["resolved"].sum()
    answered  = total - abandoned

    aht_sec  = df[df["abandoned"] == 0]["handle_time_sec"].mean()
    awt_sec  = df["wait_time_sec"].mean()

    csat_df  = df[df["csat_score"].notna()]
    csat_avg = csat_df["csat_score"].mean() if len(csat_df) else 0

    fcr_rate   = safe_div(df["first_call_resolution"].sum(), total) * 100
    sl_calls   = df[df["wait_time_sec"] <= 20].shape[0]
    sl_pct     = safe_div(sl_calls, answered) * 100
    total_cost = df["call_cost_usd"].sum()

    return {
        "Total Calls":            total,
        "Abandoned Calls":        int(abandoned),
        "Abandonment Rate (%)":   round(safe_div(abandoned, total) * 100, 2),
        "Resolved Calls":         int(resolved),
        "Resolution Rate (%)":    round(safe_div(resolved, answered) * 100, 2),
        "Avg Handle Time (min)":  round(aht_sec / 60, 2),
        "Avg Wait Time (sec)":    round(awt_sec, 1),
        "Service Level (%)":      round(sl_pct, 2),
        "FCR Rate (%)":           round(fcr_rate, 2),
        "CSAT Score (avg)":       round(csat_avg, 2),
        "Total Cost (USD)":       round(total_cost, 2),
        "Cost per Call (USD)":    round(safe_div(total_cost, total), 2),
    }

# ── call volume helpers ───────────────────────────────────────────────────────

def hourly_volume(df):
    return df.groupby("hour").size().reset_index(name="call_count")

def dow_volume(df):
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    v = df.groupby("day_of_week").size().reset_index(name="call_count")
    v["day_of_week"] = pd.Categorical(v["day_of_week"], categories=order, ordered=True)
    return v.sort_values("day_of_week")

def daily_volume(df):
    return df.groupby("date").size().reset_index(name="call_count")

def monthly_volume(df):
    order = ["January","February","March","April","May","June",
             "July","August","September","October","November","December"]
    v = df.groupby("month").size().reset_index(name="call_count")
    v["month"] = pd.Categorical(v["month"], categories=order, ordered=True)
    return v.sort_values("month")

def aht_by_channel(df):
    d = df[df["abandoned"] == 0]
    return (
        d.groupby("channel")["handle_time_sec"]
         .mean().reset_index()
         .rename(columns={"handle_time_sec": "avg_handle_time_sec"})
         .assign(avg_handle_time_min=lambda x: round(x["avg_handle_time_sec"] / 60, 2))
    )

def reason_distribution(df):
    return df.groupby("call_reason").size().reset_index(name="count").sort_values("count", ascending=False)

def agent_performance(df):
    answered = df[df["abandoned"] == 0]
    grp = answered.groupby("agent_id")
    perf = pd.DataFrame({
        "total_calls":    df.groupby("agent_id").size(),
        "handled_calls":  grp.size(),
        "avg_handle_min": grp["handle_time_sec"].mean().div(60).round(2),
        "avg_wait_sec":   df.groupby("agent_id")["wait_time_sec"].mean().round(1),
        "resolved":       grp["resolved"].sum(),
        "fcr_count":      grp["first_call_resolution"].sum(),
        "avg_csat":       grp["csat_score"].mean().round(2),
        "total_cost":     grp["call_cost_usd"].sum().round(2),
    }).reset_index()
    perf["resolution_rate"] = (perf["resolved"] / perf["handled_calls"] * 100).round(2)
    perf["fcr_rate"]        = (perf["fcr_count"] / perf["handled_calls"] * 100).round(2)
    return perf.fillna(0)

def sentiment_dist(df):
    return df.groupby("sentiment").size().reset_index(name="count")

def outcome_dist(df):
    return df.groupby("outcome").size().reset_index(name="count").sort_values("count", ascending=False)

def wait_time_buckets(df):
    bins   = [0, 30, 60, 120, 180, 300, float("inf")]
    labels = ["0-30s","31-60s","1-2min","2-3min","3-5min","5min+"]
    df2 = df.copy()
    df2["wait_bucket"] = pd.cut(df2["wait_time_sec"], bins=bins, labels=labels, right=False)
    return df2.groupby("wait_bucket", observed=True).size().reset_index(name="count")

def channel_mix(df):
    return df.groupby("channel").size().reset_index(name="count")

def cost_by_reason(df):
    return (
        df.groupby("call_reason")["call_cost_usd"]
          .agg(["mean","sum"]).reset_index()
          .rename(columns={"mean":"avg_cost","sum":"total_cost"})
          .sort_values("total_cost", ascending=False)
    )

# ═══════════════════════════════════════════════════════════════════════════════
# DAY-OVER-DAY (DoD) PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

def dod_performance(df, last_n_days=30):
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"])
    max_date = df2["date"].max()
    df2 = df2[df2["date"] >= max_date - pd.Timedelta(days=last_n_days - 1)]

    grp     = df2.groupby("date")
    ans_grp = df2[df2["abandoned"] == 0].groupby("date")
    csat_g  = df2[df2["csat_score"].notna()].groupby("date")

    daily = pd.DataFrame({
        "total_calls":    grp.size(),
        "abandoned":      grp["abandoned"].sum(),
        "avg_handle_min": ans_grp["handle_time_sec"].mean().div(60).round(2),
        "avg_wait_sec":   grp["wait_time_sec"].mean().round(1),
        "fcr_rate":       (grp["first_call_resolution"].mean() * 100).round(2),
        "avg_csat":       csat_g["csat_score"].mean().round(2),
        "total_cost":     grp["call_cost_usd"].sum().round(2),
    }).reset_index().fillna(0)

    daily["abandon_rate"] = (daily["abandoned"] / daily["total_calls"] * 100).round(2)
    daily["date"]         = pd.to_datetime(daily["date"])

    for col in ["total_calls","abandon_rate","avg_handle_min","avg_wait_sec",
                "fcr_rate","avg_csat","total_cost"]:
        daily[f"{col}_delta"] = daily[col].diff().round(2)
        daily[f"{col}_pct"]   = daily[col].pct_change().mul(100).round(2)

    return daily.fillna(0)

# ═══════════════════════════════════════════════════════════════════════════════
# QUARTER-OVER-QUARTER (QoQ) PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════════

def qoq_performance(df):
    df2 = df.copy()
    df2["date"]    = pd.to_datetime(df2["date"])
    df2["quarter"] = df2["date"].dt.to_period("Q").astype(str)

    grp   = df2.groupby("quarter")
    ans   = df2[df2["abandoned"] == 0].groupby("quarter")
    csat  = df2[df2["csat_score"].notna()].groupby("quarter")
    sl_df = df2[df2["wait_time_sec"] <= 20].groupby("quarter")

    q = pd.DataFrame({
        "total_calls":    grp.size(),
        "abandoned":      grp["abandoned"].sum(),
        "resolved":       ans["resolved"].sum(),
        "fcr":            grp["first_call_resolution"].sum(),
        "avg_handle_min": ans["handle_time_sec"].mean().div(60).round(2),
        "avg_wait_sec":   grp["wait_time_sec"].mean().round(1),
        "avg_csat":       csat["csat_score"].mean().round(2),
        "total_cost":     grp["call_cost_usd"].sum().round(2),
        "sl_calls":       sl_df.size(),
    }).reset_index().fillna(0)

    q["answered"]        = q["total_calls"] - q["abandoned"]
    q["abandon_rate"]    = (q["abandoned"]  / q["total_calls"].replace(0,1) * 100).round(2)
    q["resolution_rate"] = (q["resolved"]   / q["answered"].replace(0,1)    * 100).round(2)
    q["fcr_rate"]        = (q["fcr"]        / q["total_calls"].replace(0,1) * 100).round(2)
    q["service_level"]   = (q["sl_calls"]   / q["answered"].replace(0,1)    * 100).round(2)
    q["cost_per_call"]   = (q["total_cost"] / q["total_calls"].replace(0,1)).round(2)

    metrics = ["total_calls","abandon_rate","resolution_rate","fcr_rate",
               "avg_handle_min","avg_wait_sec","service_level","avg_csat",
               "total_cost","cost_per_call"]
    for m in metrics:
        q[f"{m}_qoq"] = q[m].pct_change().mul(100).round(2)

    return q.fillna(0)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADCOUNT ANALYSIS (Erlang-C)
# ═══════════════════════════════════════════════════════════════════════════════

SHRINKAGE        = 0.30
OCCUPANCY_TARGET = 0.85

def _erlang_c(A, N):
    """Return Erlang-C probability for traffic A and N agents."""
    import math
    if N <= A:
        return 1.0
    sum_term = sum(A**k / math.factorial(k) for k in range(int(N)))
    ec_num   = (A**N / math.factorial(int(N))) * (N / (N - A))
    ec_denom = ec_num + sum_term
    return ec_num / ec_denom if ec_denom else 1.0

def erlang_agents_required(calls_per_hour, aht_sec,
                            target_sl=0.80, target_sec=20):
    import math
    if calls_per_hour <= 0 or aht_sec <= 0:
        return 0
    lam = calls_per_hour / 3600
    A   = lam * aht_sec
    for N in range(1, 500):
        if N <= A:
            continue
        C  = _erlang_c(A, float(N))
        sl = 1 - C * np.exp(-(N - A) * (target_sec / aht_sec))
        if sl >= target_sl:
            return N
    return N

def headcount_analysis(df, shrinkage=SHRINKAGE):
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"])
    n_days = max(1, df2["date"].nunique())

    hourly = df2.groupby("hour").agg(
        total_calls    = ("call_id",        "count"),
        avg_handle_sec = ("handle_time_sec", "mean"),
        avg_wait_sec   = ("wait_time_sec",   "mean"),
        total_cost     = ("call_cost_usd",   "sum"),
    ).reset_index()

    hourly["calls_per_hour"] = (hourly["total_calls"] / n_days).round(1)

    hourly["agents_raw"] = hourly.apply(
        lambda r: erlang_agents_required(r["calls_per_hour"], r["avg_handle_sec"]), axis=1
    )
    # apply shrinkage
    hourly["agents_required"] = np.ceil(
        hourly["agents_raw"] / (1 - shrinkage)
    ).astype(int)

    hourly["occupancy"] = (
        hourly["calls_per_hour"] * (hourly["avg_handle_sec"] / 3600)
        / hourly["agents_raw"].replace(0, 1)
    ).clip(0, 1).round(3)

    current = df2.groupby("hour")["agent_id"].nunique().reset_index().rename(
        columns={"agent_id": "agents_current"}
    )
    hourly = hourly.merge(current, on="hour", how="left").fillna(0)
    hourly["agents_current"] = hourly["agents_current"].astype(int)
    hourly["surplus_deficit"] = hourly["agents_current"] - hourly["agents_required"]
    hourly["cost_per_agent"]  = (hourly["total_cost"] / hourly["agents_current"].replace(0, 1)).round(2)
    hourly["status"] = hourly["surplus_deficit"].apply(
        lambda x: "✅ OK" if abs(x) <= 1
                  else ("🔴 Understaffed" if x < 0 else "🟡 Overstaffed")
    )
    return hourly

def headcount_summary(df):
    hc = headcount_analysis(df)
    return {
        "Current Unique Agents":      int(df["agent_id"].nunique()),
        "Peak HC Required":           int(hc["agents_required"].max()),
        "Off-Peak HC Required":       int(hc["agents_required"].min()),
        "Avg HC Required (all hrs)":  int(hc["agents_required"].mean().round(0)),
        "Understaffed Hours":         int((hc["surplus_deficit"] < -1).sum()),
        "Overstaffed Hours":          int((hc["surplus_deficit"] >  1).sum()),
        "Optimal Hours":              int((hc["surplus_deficit"].abs() <= 1).sum()),
        "Avg Agent Occupancy (%)":    round(hc["occupancy"].mean() * 100, 1),
    }

# ═══════════════════════════════════════════════════════════════════════════════
# COST PER HEADCOUNT
# ═══════════════════════════════════════════════════════════════════════════════

def cost_per_hc(df):
    n_agents   = df["agent_id"].nunique()
    n_days     = max(1, pd.to_datetime(df["date"]).nunique())
    total_cost = df["call_cost_usd"].sum()

    per_agent = df.groupby("agent_id").agg(
        calls      = ("call_id",         "count"),
        total_cost = ("call_cost_usd",   "sum"),
        avg_handle = ("handle_time_sec",  "mean"),
        avg_csat   = ("csat_score",       "mean"),
    ).reset_index()
    per_agent["cost_per_call"]    = (per_agent["total_cost"] / per_agent["calls"]).round(2)
    per_agent["handle_min_total"] = (per_agent["avg_handle"] / 60 * per_agent["calls"])
    per_agent["cost_per_min"]     = (per_agent["total_cost"] / per_agent["handle_min_total"].replace(0,1)).round(3)
    per_agent["calls_per_day"]    = (per_agent["calls"] / n_days).round(1)
    per_agent["efficiency_score"] = (
        per_agent["avg_csat"].fillna(0) * 20
        - per_agent["cost_per_call"]   *  2
    ).round(2)

    summary = {
        "Total HC (Agents)":           n_agents,
        "Total Cost (USD)":            round(total_cost, 2),
        "Cost per HC / Day (USD)":     round(total_cost / n_agents / n_days, 2),
        "Cost per HC / Month (USD)":   round(total_cost / n_agents / (n_days / 30), 2),
        "Avg Cost per Call (USD)":     round(total_cost / len(df), 2),
        "Calls per HC / Day":          round(len(df) / n_agents / n_days, 1),
        "Best Efficiency Agent":       per_agent.loc[per_agent["efficiency_score"].idxmax(), "agent_id"],
        "Highest Cost Agent":          per_agent.loc[per_agent["total_cost"].idxmax(),       "agent_id"],
    }
    return summary, per_agent.sort_values("total_cost", ascending=False)

# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-METRIC DAILY SERIES (for multi-forecast)
# ═══════════════════════════════════════════════════════════════════════════════

def daily_metrics_for_forecast(df):
    df2 = df.copy()
    df2["date"] = pd.to_datetime(df2["date"])
    ans  = df2[df2["abandoned"] == 0]
    csat = df2[df2["csat_score"].notna()]

    base = df2.groupby("date").agg(
        call_volume   = ("call_id",        "count"),
        total_cost    = ("call_cost_usd",  "sum"),
        abandon_count = ("abandoned",      "sum"),
        avg_wait      = ("wait_time_sec",  "mean"),
    ).reset_index()

    aht  = ans.groupby("date")["handle_time_sec"].mean().div(60).reset_index()
    aht.columns  = ["date", "avg_aht_min"]
    cs   = csat.groupby("date")["csat_score"].mean().reset_index()
    cs.columns   = ["date", "avg_csat"]

    daily = base.merge(aht, on="date", how="left").merge(cs, on="date", how="left")
    daily["abandon_rate"] = (daily["abandon_count"] / daily["call_volume"] * 100).round(2)
    daily["cost_per_call"]= (daily["total_cost"]    / daily["call_volume"]).round(2)

    # forward-fill gaps
    daily = daily.sort_values("date")
    daily = daily.ffill().fillna(0)
    return daily
