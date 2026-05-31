"""
H4: Серия льготников в нетипичное время
"""

import pandas as pd


def h4_benefit_series(df: pd.DataFrame,
                      series_length: int = 3,
                      interval_seconds: int = 60,
                      atypical_hours_start: int = 22,
                      atypical_hours_end: int = 6,
                      benefit_cats: list = None) -> pd.DataFrame:
    if benefit_cats is None:
        benefit_cats = [201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 303, 304]
    
    df = df.copy()
    df['is_benefit'] = df['CAT_NUM'].isin(benefit_cats)
    
    # Сортируем по валидатору и времени
    df_sorted = df.sort_values(['TRM_ID', 'datetime']).copy()
    df_sorted['is_benefit_prev'] = df_sorted.groupby('TRM_ID')['is_benefit'].shift(1)
    df_sorted['time_diff'] = df_sorted.groupby('TRM_ID')['datetime'].diff().dt.total_seconds()
    
    # Ищем серии
    series = df_sorted[
        (df_sorted['is_benefit']) & 
        (df_sorted['is_benefit_prev']) & 
        (df_sorted['time_diff'] < interval_seconds)
    ].copy()
    
    # Проверка на нетипичное время
    hour = series['datetime'].dt.hour
    is_atypical = ((hour >= atypical_hours_start) | (hour < atypical_hours_end))
    series = series[is_atypical]
    
    # Группируем по валидатору и временным кластерам
    series['time_cluster'] = (series['time_diff'] > interval_seconds).cumsum()
    
    clusters = series.groupby(['TRM_ID', 'time_cluster']).agg(
        series_length=('CARD', 'size'),
        start_time=('datetime', 'min'),
        cards=('CARD', lambda x: list(x.unique()[:5]))
    ).reset_index()
    
    clusters = clusters[clusters['series_length'] >= series_length]
    
    results = []
    for _, row in clusters.iterrows():
        results.append({
            'entity_type': 'validator',
            'entity_id': row['TRM_ID'],
            'anomaly_date': row['start_time'],
            'metric_name': 'benefit_series_length',
            'metric_value': row['series_length'],
            'threshold_value': series_length,
            'severity': 'strong',
            'hypothesis': 'H4',
            'details': f'{{"cards": {row["cards"]}}}'
        })
    
    return pd.DataFrame(results)