"""
H8: Многократное использование школьной карты подряд
"""

import pandas as pd


def h8_school_card_multiple(df: pd.DataFrame,
                            min_consecutive: int = 2,
                            interval_seconds: int = 60,
                            school_cats: list = None,
                            same_validator_required: bool = True) -> pd.DataFrame:
    if school_cats is None:
        school_cats = [203, 208, 209, 303]
    
    df = df.copy()
    school_trips = df[df['CAT_NUM'].isin(school_cats)].copy()
    school_trips = school_trips.sort_values(['CARD', 'datetime'])
    
    # Считаем последовательные использования
    school_trips['prev_time'] = school_trips.groupby('CARD')['datetime'].shift(1)
    school_trips['prev_trm'] = school_trips.groupby('CARD')['TRM_ID'].shift(1)
    school_trips['time_diff'] = (school_trips['datetime'] - school_trips['prev_time']).dt.total_seconds()
    
    if same_validator_required:
        consecutive = school_trips[
            (school_trips['TRM_ID'] == school_trips['prev_trm']) &
            (school_trips['time_diff'] < interval_seconds)
        ]
    else:
        consecutive = school_trips[school_trips['time_diff'] < interval_seconds]
    
    # Группируем по карте и кластерам
    consecutive = consecutive.copy()
    consecutive['time_cluster'] = (consecutive['time_diff'] > interval_seconds).cumsum()
    
    clusters = consecutive.groupby(['CARD', 'time_cluster']).agg(
        consecutive_count=('CARD', 'size'),
        start_time=('datetime', 'min'),
        validator=('TRM_ID', lambda x: x.iloc[0])
    ).reset_index()
    
    clusters = clusters[clusters['consecutive_count'] >= min_consecutive]
    
    results = []
    for _, row in clusters.iterrows():
        results.append({
            'entity_type': 'card',
            'entity_id': row['CARD'],
            'anomaly_date': row['start_time'],
            'metric_name': 'consecutive_uses',
            'metric_value': row['consecutive_count'],
            'threshold_value': min_consecutive,
            'severity': 'raw',
            'hypothesis': 'H8',
            'details': f'{{"validator": "{row["validator"]}"}}'
        })
    
    return pd.DataFrame(results)