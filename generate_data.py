import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_call_center_data(num_records=2000, seed=42):
    np.random.seed(seed)
    random.seed(seed)

    start_date = datetime(2024, 1, 1)
    end_date   = datetime(2024, 12, 31)
    date_range = (end_date - start_date).days

    agents = [f"Agent_{i:02d}" for i in range(1, 21)]
    call_reasons = [
        "Billing Inquiry", "Technical Support", "Account Management",
        "Product Information", "Complaint", "Order Tracking",
        "Cancellation Request", "General Inquiry", "Refund Request", "Upgrade Request"
    ]
    channels = ["Phone", "Chat", "Email", "Video Call"]
    outcomes  = ["Resolved", "Escalated", "Callback Scheduled", "Unresolved", "Transferred"]
    sentiments = ["Positive", "Neutral", "Negative"]

    records = []
    for _ in range(num_records):
        date      = start_date + timedelta(days=np.random.randint(0, date_range))
        hour      = int(np.random.choice(
            range(8, 20),
            p=[0.02,0.05,0.09,0.12,0.13,0.12,0.11,0.10,0.09,0.08,0.06,0.03]
        ))
        minute    = np.random.randint(0, 60)
        timestamp = date.replace(hour=hour, minute=minute)

        agent     = random.choice(agents)
        reason    = random.choice(call_reasons)
        channel   = np.random.choice(channels, p=[0.60, 0.20, 0.12, 0.08])

        wait_time     = max(0, int(np.random.exponential(3) * 60))          # seconds
        handle_time   = max(60, int(np.random.normal(300, 120)))             # seconds
        hold_time     = max(0, int(np.random.exponential(1) * 60))
        wrap_up_time  = max(0, int(np.random.normal(60, 20)))

        abandoned     = 1 if (wait_time > 180 and np.random.random() < 0.25) else 0
        resolved      = 0 if abandoned else np.random.choice([0, 1], p=[0.20, 0.80])
        fcr           = resolved and np.random.random() < 0.75

        csat          = None if abandoned else np.random.choice([1,2,3,4,5], p=[0.05,0.08,0.17,0.35,0.35])
        sentiment     = random.choice(sentiments)
        outcome       = "Abandoned" if abandoned else random.choice(outcomes)

        cost_per_min  = {"Phone": 0.85, "Chat": 0.45, "Email": 0.30, "Video Call": 1.10}[channel]
        call_cost     = round((handle_time / 60) * cost_per_min, 2)

        records.append({
            "call_id":          f"CALL{_+1:05d}",
            "timestamp":        timestamp,
            "date":             timestamp.date(),
            "hour":             hour,
            "day_of_week":      timestamp.strftime("%A"),
            "month":            timestamp.strftime("%B"),
            "agent_id":         agent,
            "call_reason":      reason,
            "channel":          channel,
            "wait_time_sec":    wait_time,
            "handle_time_sec":  handle_time,
            "hold_time_sec":    hold_time,
            "wrap_up_time_sec": wrap_up_time,
            "total_time_sec":   wait_time + handle_time + wrap_up_time,
            "abandoned":        abandoned,
            "resolved":         resolved,
            "first_call_resolution": int(fcr),
            "csat_score":       csat,
            "sentiment":        sentiment,
            "outcome":          outcome,
            "call_cost_usd":    call_cost,
        })

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["date"]      = pd.to_datetime(df["date"])
    return df

if __name__ == "__main__":
    df = generate_call_center_data(2000)
    df.to_csv("call_center_data.csv", index=False)
    print(f"Generated {len(df)} records.")
    print(df.head())
