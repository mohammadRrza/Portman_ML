import pandas as pd
import numpy as np

def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Ratio: tx / attainable rate
    if "tx_rate" in df.columns and "attainable_rate" in df.columns:
        df["tx_utilization"] = df["tx_rate"] / df["attainable_rate"]
        df["tx_utilization"] = df["tx_utilization"].clip(upper=1.0)

    # Convert uptime to hours
    if "uptime" in df.columns:
        df["uptime_sec"] = df["uptime"].fillna("00:00:00").apply(parse_uptime)
        df["uptime_hr"] = df["uptime_sec"] / 3600

    # CRC errors per hour
    if "crc_down" in df.columns and "uptime_hr" in df.columns:
        df["crc_per_hour"] = df["crc_down"] / df["uptime_hr"].replace(0, np.nan)

    # Drop intermediate or constant columns (optional)
    df.drop(columns=["uptime_sec"], inplace=True, errors="ignore")

    return df

def parse_uptime(uptime_str):
    try:
        h, m, s = map(int, uptime_str.split(":"))
        return h * 3600 + m * 60 + s
    except:
        return 0
