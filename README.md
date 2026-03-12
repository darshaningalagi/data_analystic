# 📞 Call Center Analytics & Predictive Intelligence System

An interactive, automated analytics dashboard for call center performance monitoring and forecasting — built with **Python, Streamlit, Plotly, and Prophet**.

---

## 🚀 Features

| Module | Description |
|--------|-------------|
| **KPI Dashboard** | Total calls, abandonment rate, AHT, service level, FCR, CSAT, cost |
| **Call Volume Analysis** | Hourly, daily, weekly, monthly trends; channel & reason breakdown |
| **Handling Time Analysis** | AHT by channel and agent; wait-time buckets; handle-time histogram |
| **Service Level Analysis** | Monthly SL %, FCR by channel, abandonment rate, outcome distribution |
| **Agent Performance** | CSAT, resolution rate, FCR, call volume, handle time per agent |
| **Customer Insights** | CSAT distribution, sentiment analysis, satisfaction by reason & channel |
| **Cost Analysis** | Cost by channel, agent, reason, and monthly trend |
| **Forecasting** | Prophet time-series forecast with 90% confidence intervals |
| **Raw Data Explorer** | Searchable, filterable data table with CSV export |

---

## 🗂️ Project Structure

```
callcenter_project/
├── app.py              ← Main Streamlit application
├── analytics.py        ← Analytics & metrics engine
├── generate_data.py    ← Synthetic dataset generator
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## ⚙️ Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the app
```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 📊 Dataset Format

Upload your own CSV or use the built-in generator. Expected columns:

| Column | Type | Description |
|--------|------|-------------|
| `call_id` | str | Unique call identifier |
| `timestamp` | datetime | Date + time of call |
| `agent_id` | str | Agent identifier |
| `call_reason` | str | Reason for call |
| `channel` | str | Phone / Chat / Email / Video |
| `wait_time_sec` | int | Seconds caller waited |
| `handle_time_sec` | int | Seconds agent handled call |
| `abandoned` | int | 1 = abandoned, 0 = answered |
| `resolved` | int | 1 = resolved, 0 = not |
| `first_call_resolution` | int | 1 = resolved in 1 call |
| `csat_score` | float | 1–5 customer satisfaction |
| `sentiment` | str | Positive / Neutral / Negative |
| `call_cost_usd` | float | Cost of this call in USD |

---

## 🔮 Forecasting

The forecasting module uses **Facebook Prophet** for time-series prediction:
- Automatically detects weekly & yearly seasonality
- 90% confidence interval bands
- Component decomposition (trend, weekly, yearly)
- Configurable horizon: 7–90 days

If Prophet is unavailable, a linear trend + moving-average fallback is used.

---

## 🛠️ Technologies

- **Python 3.9+**
- **Pandas & NumPy** – data manipulation
- **Streamlit** – interactive web dashboard
- **Plotly** – interactive charts
- **Prophet** – time-series forecasting
- **Scikit-learn** – ML utilities

---

## 📈 Key Metrics Computed

- **Service Level (SL%)** – % of calls answered within 20 seconds
- **Abandonment Rate** – % of callers who hung up before being answered  
- **Average Handle Time (AHT)** – average call duration per agent/channel
- **First Call Resolution (FCR)** – % of issues resolved in a single call
- **CSAT Score** – customer satisfaction average (1–5 scale)
- **Cost per Call** – calculated from handle time × per-minute rate by channel

---

*Call Center Analytics v1.0 — Academic Project*
