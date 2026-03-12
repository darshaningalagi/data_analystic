"""
Call Center Analytics & Predictive Intelligence System  ─ v2.0
==============================================================
Run:  streamlit run app.py
New in v2.0
  • Day-over-Day (DoD) performance tracker
  • Quarter-over-Quarter (QoQ) comparison dashboard
  • Headcount Analysis (current HC vs Erlang-C required HC)
  • Cost-per-Headcount deep dive
  • Multi-metric forecasting (volume, cost, AHT, abandonment, CSAT)
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from generate_data import generate_call_center_data
import analytics as an

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Call Center Analytics v2",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── palette ───────────────────────────────────────────────────────────────────
BLUE   = "#1a73e8"
GREEN  = "#34a853"
ORANGE = "#fbbc04"
RED    = "#ea4335"
PURPLE = "#8e44ad"
TEAL   = "#00897b"
COLORS = [BLUE,GREEN,ORANGE,RED,PURPLE,TEAL,"#e67e22","#2ecc71","#e74c3c","#3498db"]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main{background:#f4f6fb}
.block-container{padding-top:1rem}
h1{color:#1a73e8;font-size:2rem}
h2{color:#1a1a2e;font-size:1.35rem}
.kpi-card{background:white;border-radius:12px;padding:16px 18px;
          box-shadow:0 2px 8px rgba(0,0,0,.08);border-left:4px solid #1a73e8;margin-bottom:10px}
.kpi-value{font-size:1.65rem;font-weight:700;color:#1a73e8}
.kpi-label{font-size:.8rem;color:#666;font-weight:500}
.delta-up{color:#34a853;font-size:.8rem;font-weight:600}
.delta-dn{color:#ea4335;font-size:.8rem;font-weight:600}
.delta-neu{color:#888;font-size:.8rem}
.section-hdr{background:linear-gradient(90deg,#1a73e8,#00897b);color:white;
             padding:9px 16px;border-radius:8px;margin:18px 0 10px;
             font-size:1rem;font-weight:600}
.stTabs [data-baseweb="tab"]{font-size:.93rem;font-weight:500}
.stTabs [aria-selected="true"]{color:#1a73e8!important;border-bottom:3px solid #1a73e8}
</style>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📞 Call Center Analytics")
    st.markdown("**v2.0** — Enhanced Analytics")
    st.markdown("---")
    data_src = st.radio("Data source", ["Sample Data", "Upload CSV"])

    df_raw = None
    if data_src == "Upload CSV":
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up:
            df_raw = pd.read_csv(up, parse_dates=["timestamp","date"])
            st.success(f"✅ {len(df_raw):,} records loaded")
    else:
        n = st.slider("Records to generate", 500, 5000, 2000, 500)
        if st.button("🔄 Generate Data", type="primary"):
            st.session_state["df"] = generate_call_center_data(n)
        if "df" not in st.session_state:
            st.session_state["df"] = generate_call_center_data(2000)
        df_raw = st.session_state["df"]

    st.markdown("---")
    if df_raw is not None:
        st.markdown("### 🔍 Filters")
        channels   = st.multiselect("Channel",  df_raw["channel"].unique(),   default=list(df_raw["channel"].unique()))
        agents_sel = st.multiselect("Agent",     sorted(df_raw["agent_id"].unique()), default=list(df_raw["agent_id"].unique()))
        dr         = st.date_input("Date Range", [df_raw["date"].min(), df_raw["date"].max()])
    st.markdown("---")
    st.markdown("<small>Python · Streamlit · Plotly · Prophet · Erlang-C</small>", unsafe_allow_html=True)

if df_raw is None:
    st.title("📞 Call Center Analytics & Predictive Intelligence System")
    st.info("👈 Generate or upload data from the sidebar.")
    st.stop()

# ── apply filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()
if channels:
    df = df[df["channel"].isin(channels)]
if agents_sel:
    df = df[df["agent_id"].isin(agents_sel)]
if len(dr) == 2:
    df = df[(df["date"] >= pd.Timestamp(dr[0])) & (df["date"] <= pd.Timestamp(dr[1]))]

# ── title + date range ────────────────────────────────────────────────────────
st.title("📞 Call Center Analytics & Predictive Intelligence System")
st.markdown(f"**{len(df):,} calls** &nbsp;|&nbsp; "
            f"{pd.to_datetime(df['date'].min()).strftime('%b %d, %Y')} – "
            f"{pd.to_datetime(df['date'].max()).strftime('%b %d, %Y')}")

# ── KPI row ───────────────────────────────────────────────────────────────────
kpis = an.compute_kpis(df)
st.markdown('<div class="section-hdr">📊 Key Performance Indicators</div>', unsafe_allow_html=True)
items  = list(kpis.items())
bords  = [BLUE,RED,GREEN,ORANGE,PURPLE,TEAL]*3
cols   = st.columns(6)
for i,(lbl,val) in enumerate(items[:6]):
    with cols[i]:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:{bords[i]}">
            <div class="kpi-value" style="color:{bords[i]}">{val:,}</div>
            <div class="kpi-label">{lbl}</div></div>""", unsafe_allow_html=True)
cols2 = st.columns(6)
for i,(lbl,val) in enumerate(items[6:12]):
    with cols2[i]:
        st.markdown(f"""<div class="kpi-card" style="border-left-color:{bords[i+6]}">
            <div class="kpi-value" style="color:{bords[i+6]}">{val}</div>
            <div class="kpi-label">{lbl}</div></div>""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "📈 Call Volume",
    "⏱️ Handle Time",
    "📋 Service Level",
    "👤 Agent Perf",
    "😊 Customer",
    "💰 Cost",
    "📆 DoD Tracker",
    "📊 QoQ Analysis",
    "👥 Headcount",
    "💵 Cost per HC",
    "🔮 Forecasting",
    "📄 Raw Data",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 – CALL VOLUME
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="section-hdr">📈 Call Volume Analysis</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        hv = an.hourly_volume(df)
        fig = px.bar(hv, x="hour", y="call_count", title="Calls by Hour",
                     color="call_count", color_continuous_scale="Blues")
        fig.update_layout(showlegend=False, height=340)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        dv = an.dow_volume(df)
        fig = px.bar(dv, x="day_of_week", y="call_count", title="Calls by Day of Week",
                     color="call_count", color_continuous_scale="Teal")
        fig.update_layout(showlegend=False, height=340)
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        mv = an.monthly_volume(df)
        fig = px.line(mv, x="month", y="call_count", title="Monthly Volume", markers=True)
        fig.update_traces(line_color=BLUE, line_width=2.5)
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        cm = an.channel_mix(df)
        fig = px.pie(cm, names="channel", values="count", title="Channel Mix",
                     color_discrete_sequence=COLORS, hole=0.4)
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)
    rd = an.reason_distribution(df)
    fig = px.bar(rd, x="count", y="call_reason", orientation="h",
                 title="Call Volume by Reason", color="count", color_continuous_scale="Sunset")
    fig.update_layout(height=420, showlegend=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – HANDLE TIME
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-hdr">⏱️ Handle Time Analysis</div>', unsafe_allow_html=True)
    answered = df[df["abandoned"] == 0]
    c1,c2 = st.columns(2)
    with c1:
        ac = an.aht_by_channel(df)
        fig = px.bar(ac, x="channel", y="avg_handle_time_min",
                     title="AHT by Channel (min)", color="channel",
                     color_discrete_sequence=COLORS, text="avg_handle_time_min")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(height=360, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        aa = answered.groupby("agent_id")["handle_time_sec"].mean().div(60).round(2).reset_index()
        aa.columns = ["agent_id","avg_handle_min"]
        aa = aa.sort_values("avg_handle_min")
        fig = px.bar(aa, x="avg_handle_min", y="agent_id", orientation="h",
                     title="AHT by Agent (min)", color="avg_handle_min",
                     color_continuous_scale="RdYlGn_r")
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        fig = px.histogram(answered, x=answered["handle_time_sec"].div(60), nbins=40,
                           title="Handle Time Distribution (min)",
                           color_discrete_sequence=[BLUE])
        fig.update_layout(height=340)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        wt = an.wait_time_buckets(df)
        fig = px.bar(wt, x="wait_bucket", y="count", title="Wait Time Buckets",
                     color="count", color_continuous_scale="Oranges")
        fig.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – SERVICE LEVEL
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<div class="section-hdr">📋 Service Level & Abandonment</div>', unsafe_allow_html=True)
    sl = df.copy()
    sl["month"] = pd.to_datetime(sl["date"]).dt.to_period("M").astype(str)
    slm = sl.groupby("month").apply(lambda x: pd.Series({
        "total": len(x), "abandoned": x["abandoned"].sum(),
        "sl_calls": (x["wait_time_sec"] <= 20).sum()
    })).reset_index()
    slm["abandon_rate"]  = (slm["abandoned"] / slm["total"] * 100).round(2)
    slm["service_level"] = (slm["sl_calls"] / (slm["total"] - slm["abandoned"]).replace(0,1) * 100).round(2)
    c1,c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=slm["month"], y=slm["service_level"], name="SL%", marker_color=GREEN))
        fig.add_hline(y=80, line_dash="dash", line_color=RED, annotation_text="Target 80%")
        fig.update_layout(title="Monthly Service Level (%)", height=360, yaxis_range=[0,110])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=slm["month"], y=slm["abandon_rate"], name="Abandon%", marker_color=RED))
        fig.add_hline(y=5, line_dash="dash", line_color=ORANGE, annotation_text="Target ≤5%")
        fig.update_layout(title="Monthly Abandonment Rate (%)", height=360)
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        fcr_ch = df.groupby("channel")["first_call_resolution"].mean().mul(100).round(2).reset_index()
        fig = px.bar(fcr_ch, x="channel", y="first_call_resolution", title="FCR Rate by Channel (%)",
                     color="channel", color_discrete_sequence=COLORS, text="first_call_resolution")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(height=350, showlegend=False, yaxis_range=[0,100])
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        od = an.outcome_dist(df)
        fig = px.bar(od, x="outcome", y="count", title="Call Outcome Distribution",
                     color="outcome", color_discrete_sequence=COLORS)
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – AGENT PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<div class="section-hdr">👤 Agent Performance</div>', unsafe_allow_html=True)
    ap = an.agent_performance(df)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(ap.sort_values("avg_csat",ascending=False), x="agent_id", y="avg_csat",
                     title="Agent CSAT Score", color="avg_csat",
                     color_continuous_scale="RdYlGn", range_color=[1,5], text="avg_csat")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(height=380, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.scatter(ap, x="avg_handle_min", y="resolution_rate",
                         size="handled_calls", color="avg_csat",
                         hover_name="agent_id", color_continuous_scale="RdYlGn",
                         range_color=[1,5], title="Handle Time vs Resolution Rate")
        fig.update_layout(height=380)
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        fig = px.bar(ap.sort_values("fcr_rate",ascending=False), x="agent_id", y="fcr_rate",
                     title="Agent FCR Rate (%)", color="fcr_rate",
                     color_continuous_scale="Blues", text="fcr_rate")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(height=360, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        fig = px.bar(ap.sort_values("total_calls",ascending=False), x="agent_id", y="total_calls",
                     title="Calls per Agent", color="total_calls", color_continuous_scale="Purples")
        fig.update_layout(height=360, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    disp = ["agent_id","total_calls","handled_calls","avg_handle_min",
            "avg_wait_sec","resolution_rate","fcr_rate","avg_csat","total_cost"]
    st.dataframe(
        ap[disp].sort_values("avg_csat",ascending=False)
          .style.background_gradient(subset=["avg_csat","resolution_rate","fcr_rate"], cmap="RdYlGn")
          .format({"avg_handle_min":"{:.2f}","avg_wait_sec":"{:.1f}",
                   "resolution_rate":"{:.1f}%","fcr_rate":"{:.1f}%",
                   "avg_csat":"{:.2f}","total_cost":"${:.2f}"}),
        use_container_width=True, height=420)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – CUSTOMER INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<div class="section-hdr">😊 Customer Satisfaction & Sentiment</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        cd = df[df["csat_score"].notna()]["csat_score"].value_counts().sort_index().reset_index()
        cd.columns = ["score","count"]
        fig = px.bar(cd, x="score", y="count", title="CSAT Distribution",
                     color="score", color_discrete_map={1:"#ea4335",2:"#fbbc04",
                     3:"#34a853",4:"#1a73e8",5:"#8e44ad"})
        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        sd = an.sentiment_dist(df)
        fig = px.pie(sd, names="sentiment", values="count", title="Sentiment Distribution",
                     color="sentiment",
                     color_discrete_map={"Positive":GREEN,"Neutral":ORANGE,"Negative":RED},
                     hole=0.45)
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        cr = df[df["csat_score"].notna()].groupby("call_reason")["csat_score"].mean().round(2).reset_index()
        fig = px.bar(cr.sort_values("csat_score"), x="csat_score", y="call_reason",
                     orientation="h", title="Avg CSAT by Reason",
                     color="csat_score", color_continuous_scale="RdYlGn", range_color=[1,5])
        fig.update_layout(height=370, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        cc = df[df["csat_score"].notna()].groupby("channel")["csat_score"].mean().round(2).reset_index()
        fig = px.bar(cc, x="channel", y="csat_score", title="Avg CSAT by Channel",
                     color="channel", color_discrete_sequence=COLORS, text="csat_score")
        fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig.update_layout(height=370, showlegend=False, yaxis_range=[0,6])
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 – COST
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown('<div class="section-hdr">💰 Cost Analysis</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        cc2 = df.groupby("channel")["call_cost_usd"].agg(["mean","sum"]).reset_index()
        cc2.columns = ["channel","avg_cost","total_cost"]
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Bar(x=cc2["channel"], y=cc2["total_cost"],
                             name="Total Cost", marker_color=BLUE), secondary_y=False)
        fig.add_trace(go.Scatter(x=cc2["channel"], y=cc2["avg_cost"],
                                 name="Avg/Call", mode="lines+markers",
                                 line=dict(color=RED,width=2)), secondary_y=True)
        fig.update_layout(title="Cost by Channel", height=370)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        cbr = an.cost_by_reason(df)
        fig = px.bar(cbr, x="total_cost", y="call_reason", orientation="h",
                     title="Total Cost by Reason", color="avg_cost",
                     color_continuous_scale="Reds", text="total_cost")
        fig.update_traces(texttemplate="$%{text:.0f}", textposition="outside")
        fig.update_layout(height=370, showlegend=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        mc = df.copy()
        mc["month"] = pd.to_datetime(mc["date"]).dt.to_period("M").astype(str)
        mc = mc.groupby("month")["call_cost_usd"].sum().reset_index()
        fig = px.area(mc, x="month", y="call_cost_usd",
                      title="Monthly Total Cost (USD)", color_discrete_sequence=[TEAL])
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        ca = df.groupby("agent_id")["call_cost_usd"].sum().reset_index().sort_values("call_cost_usd",ascending=False)
        fig = px.bar(ca, x="agent_id", y="call_cost_usd", title="Cost per Agent",
                     color="call_cost_usd", color_continuous_scale="Oranges")
        fig.update_layout(height=350, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 – DAY-OVER-DAY
# ══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    st.markdown('<div class="section-hdr">📆 Day-over-Day (DoD) Performance Tracker</div>', unsafe_allow_html=True)

    n_days = st.slider("Look-back window (days)", 7, 90, 30, key="dod_days")
    dod    = an.dod_performance(df, last_n_days=n_days)

    # Latest day delta cards
    if len(dod) >= 2:
        latest = dod.iloc[-1]
        prev   = dod.iloc[-2]

        def delta_html(val, pct, higher_is_good=True):
            if pct == 0:
                return '<span class="delta-neu">── 0.0%</span>'
            arrow  = "▲" if pct > 0 else "▼"
            colour = ("delta-up" if pct > 0 else "delta-dn") if higher_is_good else \
                     ("delta-dn" if pct > 0 else "delta-up")
            return f'<span class="{colour}">{arrow} {abs(pct):.1f}%</span>'

        st.markdown(f"#### Latest Day: **{latest['date'].strftime('%b %d, %Y')}** vs previous day")
        dcols = st.columns(7)
        pairs = [
            ("📞 Calls",       latest["total_calls"],    latest["total_calls_pct"],   True),
            ("🚫 Abandon%",    latest["abandon_rate"],   latest["abandon_rate_pct"],  False),
            ("⏱️ AHT (min)",   latest["avg_handle_min"], latest["avg_handle_min_pct"],False),
            ("⏳ Wait (sec)",  latest["avg_wait_sec"],   latest["avg_wait_sec_pct"],  False),
            ("✅ FCR%",        latest["fcr_rate"],       latest["fcr_rate_pct"],      True),
            ("⭐ CSAT",        latest["avg_csat"],       latest["avg_csat_pct"],      True),
            ("💰 Cost",        f"${latest['total_cost']:.0f}", latest["total_cost_pct"], False),
        ]
        for i,(lbl,val,pct,hig) in enumerate(pairs):
            with dcols[i]:
                st.markdown(f"""<div class="kpi-card">
                    <div class="kpi-value" style="font-size:1.3rem">{val}</div>
                    <div class="kpi-label">{lbl}</div>
                    {delta_html(val,pct,hig)}</div>""", unsafe_allow_html=True)

    st.markdown("---")
    metric_map = {
        "Total Calls":      ("total_calls",    True),
        "Abandonment Rate": ("abandon_rate",   False),
        "Avg Handle (min)": ("avg_handle_min", False),
        "Avg Wait (sec)":   ("avg_wait_sec",   False),
        "FCR Rate (%)":     ("fcr_rate",       True),
        "CSAT Score":       ("avg_csat",       True),
        "Total Cost ($)":   ("total_cost",     False),
    }
    sel_metric = st.selectbox("Select metric to plot", list(metric_map.keys()), key="dod_metric")
    col_name, higher_good = metric_map[sel_metric]

    c1,c2 = st.columns([2,1])
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dod["date"], y=dod[col_name],
                                 mode="lines+markers", name=sel_metric,
                                 line=dict(color=BLUE, width=2.5),
                                 marker=dict(size=7)))
        # 7-day rolling average
        roll = dod[col_name].rolling(7, min_periods=1).mean()
        fig.add_trace(go.Scatter(x=dod["date"], y=roll,
                                 mode="lines", name="7-day avg",
                                 line=dict(color=ORANGE, width=2, dash="dot")))
        # colour background by delta direction
        for i in range(1, len(dod)):
            d = dod.iloc[i][f"{col_name}_delta"]
            good = (d > 0 and higher_good) or (d < 0 and not higher_good)
            if d != 0:
                fig.add_vrect(
                    x0=dod.iloc[i-1]["date"], x1=dod.iloc[i]["date"],
                    fillcolor="rgba(52,168,83,.12)" if good else "rgba(234,67,53,.10)",
                    layer="below", line_width=0
                )
        fig.update_layout(title=f"DoD – {sel_metric}", height=420,
                          xaxis_title="Date", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # bar chart of daily delta
        delta_col = f"{col_name}_delta"
        dod_plot  = dod.iloc[1:].copy()
        dod_plot["colour"] = dod_plot[delta_col].apply(
            lambda x: GREEN if (x > 0 and higher_good) or (x < 0 and not higher_good) else RED
        )
        fig2 = go.Figure(go.Bar(
            x=dod_plot[delta_col], y=dod_plot["date"].dt.strftime("%b %d"),
            orientation="h",
            marker_color=dod_plot["colour"].tolist(),
        ))
        fig2.update_layout(title="Daily Delta", height=420,
                           xaxis_title="Δ Change", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 📋 DoD Data Table")
    show_cols = ["date","total_calls","total_calls_pct","abandon_rate","abandon_rate_pct",
                 "avg_handle_min","avg_handle_min_pct","fcr_rate","fcr_rate_pct",
                 "avg_csat","avg_csat_pct","total_cost","total_cost_pct"]
    st.dataframe(
        dod[show_cols].sort_values("date",ascending=False).style
          .format({"total_calls_pct":"{:.1f}%","abandon_rate_pct":"{:.1f}%",
                   "avg_handle_min_pct":"{:.1f}%","fcr_rate_pct":"{:.1f}%",
                   "avg_csat_pct":"{:.1f}%","total_cost_pct":"{:.1f}%",
                   "total_cost":"${:.2f}"}),
        use_container_width=True, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 – QoQ ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    st.markdown('<div class="section-hdr">📊 Quarter-over-Quarter (QoQ) Performance</div>', unsafe_allow_html=True)
    qoq = an.qoq_performance(df)

    if len(qoq) < 2:
        st.warning("Need at least 2 quarters of data for QoQ analysis.")
    else:
        # QoQ summary cards for latest quarter
        latest_q  = qoq.iloc[-1]
        prev_q    = qoq.iloc[-2]
        st.markdown(f"#### {latest_q['quarter']} vs {prev_q['quarter']}")

        qcols = st.columns(5)
        q_pairs = [
            ("📞 Calls",       latest_q["total_calls"],     latest_q["total_calls_qoq"],     True),
            ("🚫 Abandon%",    f"{latest_q['abandon_rate']:.1f}%",  latest_q["abandon_rate_qoq"],    False),
            ("✅ SL%",         f"{latest_q['service_level']:.1f}%", latest_q["service_level_qoq"],   True),
            ("⭐ CSAT",        f"{latest_q['avg_csat']:.2f}",       latest_q["avg_csat_qoq"],        True),
            ("💰 Cost/Call",   f"${latest_q['cost_per_call']:.2f}", latest_q["cost_per_call_qoq"],   False),
        ]
        for i,(lbl,val,qpct,hig) in enumerate(q_pairs):
            with qcols[i]:
                colour = GREEN if (qpct > 0 and hig) or (qpct < 0 and not hig) else RED
                arrow  = "▲" if qpct > 0 else "▼"
                st.markdown(f"""<div class="kpi-card" style="border-left-color:{colour}">
                    <div class="kpi-value" style="color:{colour}">{val}</div>
                    <div class="kpi-label">{lbl}</div>
                    <span style="color:{colour};font-size:.82rem;font-weight:600">
                    {arrow} {abs(qpct):.1f}% QoQ</span></div>""", unsafe_allow_html=True)

        st.markdown("---")
        qmetric = st.selectbox("Select metric for QoQ chart", [
            "total_calls","service_level","abandon_rate","fcr_rate",
            "avg_csat","avg_handle_min","total_cost","cost_per_call","resolution_rate"
        ], key="qoq_metric")

        c1,c2 = st.columns(2)
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=qoq["quarter"], y=qoq[qmetric],
                                 name=qmetric, marker_color=COLORS[:len(qoq)],
                                 text=qoq[qmetric]))
            fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
            fig.update_layout(title=f"{qmetric} by Quarter", height=380)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            # Waterfall chart for QoQ delta
            wf_y   = [qoq.iloc[0][qmetric]]
            wf_x   = [qoq.iloc[0]["quarter"]]
            wf_msr = ["absolute"]
            wf_txt = [str(round(wf_y[0],2))]
            for i in range(1, len(qoq)):
                delta = qoq.iloc[i][qmetric] - qoq.iloc[i-1][qmetric]
                wf_x.append(qoq.iloc[i]["quarter"])
                wf_y.append(round(delta, 2))
                wf_msr.append("relative")
                wf_txt.append(f"{'+' if delta>=0 else ''}{delta:.2f}")
            wf_x.append("Total")
            wf_y.append(round(qoq.iloc[-1][qmetric], 2))
            wf_msr.append("total")
            wf_txt.append(str(round(qoq.iloc[-1][qmetric],2)))

            fig2 = go.Figure(go.Waterfall(
                x=wf_x, y=wf_y, measure=wf_msr, text=wf_txt,
                increasing=dict(marker_color=GREEN),
                decreasing=dict(marker_color=RED),
                totals=dict(marker_color=BLUE),
                connector=dict(line=dict(color="#ccc",width=1)),
            ))
            fig2.update_layout(title=f"QoQ Waterfall – {qmetric}", height=380, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Multi-metric radar per quarter
        st.markdown("#### 🕸️ Multi-Metric Radar Comparison")
        radar_metrics = ["service_level","fcr_rate","resolution_rate","avg_csat"]
        radar_norm = qoq[radar_metrics].copy()
        for m in radar_metrics:
            mx = radar_norm[m].max()
            radar_norm[m] = (radar_norm[m] / mx * 100).round(1) if mx else 0

        fig3 = go.Figure()
        for i, row in qoq.iterrows():
            vals = [radar_norm.loc[i,m] for m in radar_metrics] + [radar_norm.loc[i,radar_metrics[0]]]
            fig3.add_trace(go.Scatterpolar(
                r=vals, theta=radar_metrics + [radar_metrics[0]],
                fill="toself", name=row["quarter"],
                line=dict(color=COLORS[i % len(COLORS)])
            ))
        fig3.update_layout(title="Quarter Radar (normalised to 100)", height=420,
                           polar=dict(radialaxis=dict(range=[0,105])))
        st.plotly_chart(fig3, use_container_width=True)

        # Full QoQ table
        st.markdown("#### 📋 Full QoQ Table")
        show_q = ["quarter","total_calls","total_calls_qoq","service_level","service_level_qoq",
                  "abandon_rate","abandon_rate_qoq","fcr_rate","fcr_rate_qoq",
                  "avg_csat","avg_csat_qoq","total_cost","total_cost_qoq","cost_per_call","cost_per_call_qoq"]
        st.dataframe(
            qoq[[c for c in show_q if c in qoq.columns]]
              .style.format({c: "{:.2f}" for c in show_q if c in qoq.columns and c != "quarter"}),
            use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 – HEADCOUNT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown('<div class="section-hdr">👥 Headcount Analysis — Current vs Required</div>', unsafe_allow_html=True)

    sh_col, oc_col = st.columns(2)
    with sh_col:
        shrink = st.slider("Shrinkage (%)", 10, 50, 30, 5, key="shrink") / 100
    with oc_col:
        st.info("ℹ️ **Erlang-C model** — calculates minimum agents needed to answer 80% of calls within 20 seconds, adjusted for shrinkage.")

    hc_sum  = an.headcount_summary(df)
    hc_data = an.headcount_analysis(df, shrinkage=shrink)

    # Summary cards
    hc_items = list(hc_sum.items())
    hc_cols  = st.columns(4)
    hc_colors= [BLUE,RED,GREEN,ORANGE,PURPLE,TEAL,GREEN,ORANGE]
    for i,(lbl,val) in enumerate(hc_items[:4]):
        with hc_cols[i]:
            st.markdown(f"""<div class="kpi-card" style="border-left-color:{hc_colors[i]}">
                <div class="kpi-value" style="color:{hc_colors[i]}">{val}</div>
                <div class="kpi-label">{lbl}</div></div>""", unsafe_allow_html=True)
    hc_cols2 = st.columns(4)
    for i,(lbl,val) in enumerate(hc_items[4:8]):
        with hc_cols2[i]:
            st.markdown(f"""<div class="kpi-card" style="border-left-color:{hc_colors[i+4]}">
                <div class="kpi-value" style="color:{hc_colors[i+4]}">{val}</div>
                <div class="kpi-label">{lbl}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=hc_data["hour"], y=hc_data["agents_required"],
                             name="Required HC", marker_color=RED, opacity=0.85))
        fig.add_trace(go.Bar(x=hc_data["hour"], y=hc_data["agents_current"],
                             name="Current HC",  marker_color=BLUE, opacity=0.85))
        fig.update_layout(title="HC Required vs Current by Hour",
                          barmode="group", height=400,
                          xaxis_title="Hour", yaxis_title="Agents")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        surplus = hc_data["surplus_deficit"].tolist()
        colors  = [GREEN if x >= -1 else (RED if x < -1 else ORANGE) for x in surplus]
        fig2 = go.Figure(go.Bar(
            x=hc_data["hour"], y=surplus,
            marker_color=colors,
            text=[f"{'+' if x>=0 else ''}{x}" for x in surplus],
            textposition="outside"
        ))
        fig2.add_hline(y=0, line_color="#333", line_width=1)
        fig2.update_layout(title="Surplus / Deficit by Hour (+ = overstaffed, − = understaffed)",
                           height=400, xaxis_title="Hour", yaxis_title="Δ Agents")
        st.plotly_chart(fig2, use_container_width=True)

    c3,c4 = st.columns(2)
    with c3:
        fig3 = px.area(hc_data, x="hour", y="occupancy",
                       title="Agent Occupancy Rate by Hour",
                       color_discrete_sequence=[PURPLE])
        fig3.add_hline(y=an.OCCUPANCY_TARGET, line_dash="dash", line_color=RED,
                       annotation_text=f"Target {an.OCCUPANCY_TARGET*100:.0f}%")
        fig3.update_layout(height=350, yaxis_tickformat=".0%")
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        status_cnt = hc_data["status"].value_counts().reset_index()
        status_cnt.columns = ["status","hours"]
        scolors = {
            "✅ OK": GREEN,
            "🔴 Understaffed": RED,
            "🟡 Overstaffed": ORANGE,
        }
        fig4 = px.pie(status_cnt, names="status", values="hours",
                      title="Staffing Status Distribution (hours)",
                      color="status", color_discrete_map=scolors, hole=0.4)
        fig4.update_layout(height=350)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### 📋 Hourly Headcount Detail")
    st.dataframe(
        hc_data[["hour","calls_per_hour","avg_handle_sec","agents_raw",
                 "agents_required","agents_current","surplus_deficit",
                 "occupancy","cost_per_agent","status"]]
          .style.applymap(
              lambda v: "background-color:#fce8e6" if v=="🔴 Understaffed"
                        else ("background-color:#fef9e7" if v=="🟡 Overstaffed"
                              else "background-color:#e6f4ea"),
              subset=["status"]
          )
          .format({"calls_per_hour":"{:.1f}","avg_handle_sec":"{:.0f}s",
                   "occupancy":"{:.1%}","cost_per_agent":"${:.2f}"}),
        use_container_width=True, height=420)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 – COST PER HC
# ══════════════════════════════════════════════════════════════════════════════
with tabs[9]:
    st.markdown('<div class="section-hdr">💵 Cost per Headcount Analysis</div>', unsafe_allow_html=True)
    hc_summary, per_agent = an.cost_per_hc(df)

    # Summary cards
    hc_s_items = list(hc_summary.items())
    hcs_cols   = st.columns(4)
    hcs_bords  = [BLUE,RED,GREEN,ORANGE,PURPLE,TEAL,GREEN,RED]
    for i,(lbl,val) in enumerate(hc_s_items[:4]):
        with hcs_cols[i]:
            st.markdown(f"""<div class="kpi-card" style="border-left-color:{hcs_bords[i]}">
                <div class="kpi-value" style="color:{hcs_bords[i]}">{val}</div>
                <div class="kpi-label">{lbl}</div></div>""", unsafe_allow_html=True)
    hcs_cols2 = st.columns(4)
    for i,(lbl,val) in enumerate(hc_s_items[4:8]):
        with hcs_cols2[i]:
            st.markdown(f"""<div class="kpi-card" style="border-left-color:{hcs_bords[i+4]}">
                <div class="kpi-value" style="color:{hcs_bords[i+4]}">{val}</div>
                <div class="kpi-label">{lbl}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(per_agent, x="agent_id", y="cost_per_call",
                     title="Cost per Call by Agent (USD)",
                     color="cost_per_call", color_continuous_scale="RdYlGn_r",
                     text="cost_per_call",
                     labels={"agent_id":"Agent","cost_per_call":"Cost/Call ($)"})
        fig.update_traces(texttemplate="$%{text:.2f}", textposition="outside")
        fig.update_layout(height=400, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.scatter(per_agent, x="calls_per_day", y="cost_per_call",
                         size="total_cost", color="avg_csat",
                         hover_name="agent_id",
                         title="Calls/Day vs Cost/Call (bubble=total cost, colour=CSAT)",
                         color_continuous_scale="RdYlGn", range_color=[1,5],
                         labels={"calls_per_day":"Calls/Day","cost_per_call":"Cost/Call ($)"})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    c3,c4 = st.columns(2)
    with c3:
        fig = px.bar(per_agent.sort_values("efficiency_score",ascending=False),
                     x="agent_id", y="efficiency_score",
                     title="Agent Efficiency Score (CSAT×20 − Cost/Call×2)",
                     color="efficiency_score", color_continuous_scale="RdYlGn",
                     text="efficiency_score")
        fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig.update_layout(height=380, showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        # cost/call by channel & agent heatmap
        heat = df.groupby(["agent_id","channel"])["call_cost_usd"].mean().reset_index()
        heat = heat.pivot(index="agent_id", columns="channel", values="call_cost_usd").fillna(0)
        fig = px.imshow(heat, title="Avg Cost/Call Heatmap (Agent × Channel)",
                        color_continuous_scale="RdYlGn_r", aspect="auto",
                        text_auto=".2f")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📋 Full Per-Agent Cost Table")
    st.dataframe(
        per_agent[["agent_id","calls","total_cost","cost_per_call","cost_per_min",
                   "calls_per_day","avg_csat","efficiency_score"]]
          .style.background_gradient(subset=["cost_per_call","efficiency_score"], cmap="RdYlGn_r")
          .format({"total_cost":"${:.2f}","cost_per_call":"${:.2f}",
                   "cost_per_min":"${:.3f}","avg_csat":"{:.2f}",
                   "efficiency_score":"{:.2f}","calls_per_day":"{:.1f}"}),
        use_container_width=True, height=450)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 10 – MULTI-METRIC FORECASTING
# ══════════════════════════════════════════════════════════════════════════════
with tabs[10]:
    st.markdown('<div class="section-hdr">🔮 Multi-Metric Predictive Forecasting</div>', unsafe_allow_html=True)

    fc_days = st.slider("Forecast horizon (days)", 7, 120, 30, key="fc_days")
    fc_metric_map = {
        "📞 Call Volume":      "call_volume",
        "💰 Total Cost ($)":   "total_cost",
        "⏱️ Avg AHT (min)":   "avg_aht_min",
        "🚫 Abandonment Rate":"abandon_rate",
        "⭐ Avg CSAT":        "avg_csat",
        "💵 Cost per Call":   "cost_per_call",
    }
    sel_fc = st.multiselect("Metrics to forecast", list(fc_metric_map.keys()),
                            default=["📞 Call Volume","💰 Total Cost ($)"])

    daily_m = an.daily_metrics_for_forecast(df)

    try:
        from prophet import Prophet
        import matplotlib
        matplotlib.use("Agg")

        if not sel_fc:
            st.info("Select at least one metric above.")
        else:
            for fc_label in sel_fc:
                col_name = fc_metric_map[fc_label]
                if col_name not in daily_m.columns:
                    continue
                prophet_df = daily_m[["date", col_name]].rename(
                    columns={"date":"ds", col_name:"y"}
                )
                prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
                prophet_df = prophet_df[prophet_df["y"] > 0]

                with st.spinner(f"Training model for {fc_label}..."):
                    m = Prophet(
                        yearly_seasonality=True,
                        weekly_seasonality=True,
                        daily_seasonality=False,
                        changepoint_prior_scale=0.15,
                        interval_width=0.90,
                    )
                    m.fit(prophet_df)
                    future   = m.make_future_dataframe(periods=fc_days)
                    forecast = m.predict(future)

                # Build chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=prophet_df["ds"], y=prophet_df["y"],
                    mode="markers", name="Historical",
                    marker=dict(color=BLUE, size=5, opacity=0.7)
                ))
                fig.add_trace(go.Scatter(
                    x=forecast["ds"], y=forecast["yhat"],
                    mode="lines", name="Forecast",
                    line=dict(color=RED, width=2.5)
                ))
                fig.add_trace(go.Scatter(
                    x=pd.concat([forecast["ds"], forecast["ds"][::-1]]),
                    y=pd.concat([forecast["yhat_upper"], forecast["yhat_lower"][::-1]]),
                    fill="toself", fillcolor="rgba(255,100,100,.13)",
                    line=dict(color="rgba(0,0,0,0)"),
                    name="90% CI"
                ))
                # vertical line at forecast start (add_vline broken on datetime axes in some Plotly versions)
                vline_x = str(prophet_df["ds"].max())
                fig.add_shape(type="line",
                              x0=vline_x, x1=vline_x, y0=0, y1=1,
                              xref="x", yref="paper",
                              line=dict(dash="dot", color="#555", width=1.5))
                fig.add_annotation(x=vline_x, y=1, xref="x", yref="paper",
                                   text="Forecast start", showarrow=False,
                                   font=dict(size=11, color="#555"),
                                   xanchor="left", yanchor="top")

                # Next 30-day summary
                fut_only = forecast[forecast["ds"] > prophet_df["ds"].max()].head(30)
                avg_pred = fut_only["yhat"].mean()
                trend    = "📈" if forecast["trend"].iloc[-1] > forecast["trend"].iloc[len(prophet_df)] else "📉"

                fig.update_layout(
                    title=f"{fc_label} — {fc_days}-day Forecast {trend}",
                    height=420, xaxis_title="Date",
                    yaxis_title=fc_label, hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)

                # mini stats
                m1,m2,m3,m4 = st.columns(4)
                last_actual = prophet_df["y"].iloc[-7:].mean()
                m1.metric("Last 7d avg (actual)",  f"{last_actual:.2f}")
                m2.metric("Next 30d avg (pred)",   f"{avg_pred:.2f}",
                          delta=f"{((avg_pred-last_actual)/last_actual*100):+.1f}%")
                m3.metric("Forecast max",           f"{fut_only['yhat'].max():.2f}")
                m4.metric("Forecast min",           f"{fut_only['yhat'].min():.2f}")

                with st.expander(f"📅 {fc_label} — Daily Forecast Table"):
                    tbl = fut_only[["ds","yhat","yhat_lower","yhat_upper"]].copy()
                    tbl.columns = ["Date","Predicted","Lower","Upper"]
                    tbl["Date"] = tbl["Date"].dt.strftime("%Y-%m-%d")
                    tbl[["Predicted","Lower","Upper"]] = tbl[["Predicted","Lower","Upper"]].round(2)
                    st.dataframe(tbl.set_index("Date"), use_container_width=True)

                st.markdown("---")

    except ImportError:
        st.warning("⚠️ Prophet not installed — showing linear trend forecast instead.")
        daily_vol = an.daily_volume(df)
        daily_vol["date"] = pd.to_datetime(daily_vol["date"])
        daily_vol = daily_vol.sort_values("date")

        x = np.arange(len(daily_vol))
        coef = np.polyfit(x, daily_vol["call_count"], 1)
        last_date    = daily_vol["date"].iloc[-1]
        future_dates = pd.date_range(last_date + pd.Timedelta("1D"), periods=fc_days)
        x_fut = np.arange(len(daily_vol), len(daily_vol) + fc_days)
        y_fut = np.polyval(coef, x_fut)
        ma7   = daily_vol["call_count"].rolling(7).mean()
        ma30  = daily_vol["call_count"].rolling(30).mean()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_vol["date"], y=daily_vol["call_count"],
                                 mode="lines", name="Actual", line=dict(color=BLUE)))
        fig.add_trace(go.Scatter(x=daily_vol["date"], y=ma7,
                                 mode="lines", name="7d MA",  line=dict(color=ORANGE, dash="dot")))
        fig.add_trace(go.Scatter(x=daily_vol["date"], y=ma30,
                                 mode="lines", name="30d MA", line=dict(color=GREEN,  dash="dot")))
        fig.add_trace(go.Scatter(x=future_dates, y=y_fut,
                                 mode="lines", name="Trend forecast",
                                 line=dict(color=RED, dash="dash", width=2.5)))
        fig.update_layout(title="Call Volume — Linear Trend Forecast", height=460,
                          xaxis_title="Date", yaxis_title="Call Volume", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 11 – RAW DATA
# ══════════════════════════════════════════════════════════════════════════════
with tabs[11]:
    st.markdown('<div class="section-hdr">📄 Raw Data Explorer</div>', unsafe_allow_html=True)
    c1_,c2_ = st.columns([3,1])
    with c2_:
        csv = df.to_csv(index=False)
        st.download_button("⬇️ Download CSV", data=csv,
                           file_name="call_center_data.csv", mime="text/csv", type="primary")
    search = st.text_input("🔍 Search agent ID or call reason", "")
    disp_df = df.copy()
    if search:
        mask = (disp_df["agent_id"].str.contains(search, case=False, na=False) |
                disp_df["call_reason"].str.contains(search, case=False, na=False))
        disp_df = disp_df[mask]
    st.dataframe(disp_df.sort_values("timestamp",ascending=False)
                   .drop(columns=["date"], errors="ignore"),
                 use_container_width=True, height=520)
    st.caption(f"Showing {len(disp_df):,} of {len(df):,} records")

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center><small>📞 Call Center Analytics & Predictive Intelligence v2.0 &nbsp;|&nbsp; "
    "Python · Streamlit · Plotly · Prophet · Erlang-C</small></center>",
    unsafe_allow_html=True)
