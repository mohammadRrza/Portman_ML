import pandas as pd

def filter_rare_classes(X: pd.DataFrame, y: pd.Series, min_count: int = 2):

    value_counts = y.value_counts()
    valid_classes = value_counts[value_counts >= min_count].index

    mask = y.isin(valid_classes)
    return X[mask], y[mask]