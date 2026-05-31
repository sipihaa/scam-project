"""
H12: Аномально низкая доля наличных на валидаторе
"""

import pandas as pd


def h12_low_cash(df: pd.DataFrame,
                 cash_cat: int = 151,
                 min_transactions: int = 10,
                 threshold_raw: float = 0.07,
                 threshold_strong: float = 0.00) -> pd.DataFrame:
    df = df.copy()
    
    validator_stats = df.groupby('TRM_ID').agg(
        total_tx=('CARD', 'size'),
        cash_tx=('CAT_NUM', lambda x: (x == cash_cat).sum())
    )
    validator_stats['cash_share'] = validator_stats['cash_tx'] / validator_stats['total_tx']
    validator_stats = validator_stats[validator_stats['total_tx'] >= min_transactions]
    
    results = []
    
    # RAW слой
    raw = validator_stats[validator_stats['cash_share'] <= threshold_raw].copy()
    for trm_id, row in raw.iterrows():
        results.append({
            'entity_type': 'validator',
            'entity_id': trm_id,
            'anomaly_date': df['datetime'].min().strftime('%Y-%m'),
            'metric_name': 'cash_share',
            'metric_value': round(row['cash_share'], 3),
            'threshold_value': threshold_raw,
            'severity': 'raw',
            'hypothesis': 'H12',
            'details': f'{{"total_tx": {row["total_tx"]}}}'
        })
    
    # STRONG слой
    strong = validator_stats[validator_stats['cash_share'] <= threshold_strong].copy()
    for trm_id, row in strong.iterrows():
        results.append({
            'entity_type': 'validator',
            'entity_id': trm_id,
            'anomaly_date': df['datetime'].min().strftime('%Y-%m'),
            'metric_name': 'cash_share',
            'metric_value': round(row['cash_share'], 3),
            'threshold_value': threshold_strong,
            'severity': 'strong',
            'hypothesis': 'H12',
            'details': f'{{"total_tx": {row["total_tx"]}}}'
        })
    
    return pd.DataFrame(results)