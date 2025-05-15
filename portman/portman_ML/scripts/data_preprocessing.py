import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

def parse_uptime(uptime_str):
    try:
        days, time_str = uptime_str.split(' days, ')
        h, m, s = map(int, time_str.split(':'))
        return int(days) * 86400 + h * 3600 + m * 60 + s
    except:
        return np.nan

def load_and_preprocess(filepath):
    df = pd.read_csv(filepath, low_memory=False)

    # Drop unnecessary or high-cardinality columns
    cols_to_drop = ['id', 'created_at', 'updated_at', 'port_name', 'port_index', 'selt_value']
    df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

    # Only drop missing targets if the target exists
    if 'oper_status' in df.columns:
        df.dropna(subset=['oper_status'], inplace=True)

    # Convert uptime to numeric
    if 'uptime' in df.columns:
        df['uptime_sec'] = df['uptime'].apply(parse_uptime)
        df.drop(columns=['uptime'], inplace=True)

    # Encode categorical features
    label_encoders = {}
    categorical_cols = df.select_dtypes(include='object').columns
    for col in categorical_cols:
        le = LabelEncoder()
        df[col] = df[col].astype(str)
        df[col] = le.fit_transform(df[col])
        label_encoders[col] = le

    # Fill NaNs with column means
    df.fillna(df.mean(numeric_only=True), inplace=True)
    print('-------------------------------------------------------------------------------------------------')
    print(df["line_profile"])
    print(categorical_cols)

    print('-------------------------------------------------------------------------------------------------')
    return df, label_encoders

