"""
H20: Дубли транзакций секунда-в-секунду
"""

import pandas as pd


def h20_duplicates(df: pd.DataFrame,
                   mass_threshold: int = 5,
                   single_threshold: int = 2) -> pd.DataFrame:
    df = df.copy()
    
    # Группируем по карте, валидатору, секунде
    df['time_sec'] = df['datetime'].dt.floor('s')
    dup_candidates = df.groupby(['CARD', 'TRM_ID', 'time_sec']).size().reset_index(name='count')
    
    results = []
    
    # RAW
    raw = dup_candidates[dup_candidates['count'] >= single_threshold].copy()
    for _, row in raw.iterrows():
        severity = 'strong' if row['count'] >= mass_threshold else 'raw'
        results.append({
            'entity_type': 'transaction',
            'entity_id': row['CARD'],
            'anomaly_date': row['time_sec'],
            'metric_name': 'duplicate_count',
            'metric_value': row['count'],
            'threshold_value': mass_threshold if severity == 'strong' else single_threshold,
            'severity': severity,
            'hypothesis': 'H20',
            'details': f'{{"validator": "{row["TRM_ID"]}"}}'
        })
    
    return pd.DataFrame(results)