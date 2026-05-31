"""
H17: Сумма равна нулю при тарифицируемой категории
"""

import pandas as pd


def h17_zero_sum(df: pd.DataFrame,
                 allowed_zero_cats: list = None,
                 fraud_zero_cats: list = None) -> pd.DataFrame:
    if allowed_zero_cats is None:
        allowed_zero_cats = [151, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 303, 304]
    if fraud_zero_cats is None:
        fraud_zero_cats = [91, 92, 93]
    
    df = df.copy()
    
    # Транзакции с нулевой суммой для подозрительных категорий
    zero_sum = df[
        (df['CAT_NUM'].isin(fraud_zero_cats)) &
        (df['SUMM_NUM'] == 0)
    ].copy()
    
    results = []
    for _, row in zero_sum.iterrows():
        results.append({
            'entity_type': 'transaction',
            'entity_id': row['CARD'],
            'anomaly_date': row['datetime'],
            'metric_name': 'zero_sum',
            'metric_value': 1,
            'threshold_value': 0,
            'severity': 'strong',
            'hypothesis': 'H17',
            'details': f'{{"cat": {row["CAT_NUM"]}, "validator": "{row["TRM_ID"]}", "route": "{row["ROUTE_NUM"]}"}}'
        })
    
    return pd.DataFrame(results)