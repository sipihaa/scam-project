"""
H2: Резкий всплеск пассажиропотока на маршруте
"""

import pandas as pd


def h2_route_spike(df: pd.DataFrame,
                   threshold_raw: int = 3,
                   threshold_strong: int = 5,
                   min_history_days: int = 90) -> pd.DataFrame:
    df = df.copy()
    
    df['weekday'] = df['datetime'].dt.dayofweek
    df['hour'] = df['datetime'].dt.hour
    
    # Группируем по маршруту, дню недели, часу
    route_hourly = df.groupby(['ROUTE_NUM', 'weekday', 'hour']).size().reset_index(name='flow')
    
    # Считаем медиану для каждой группы
    baseline = route_hourly.groupby(['ROUTE_NUM', 'weekday', 'hour'])['flow'] \
                .agg(median_flow='median').reset_index()
    
    route_hourly = route_hourly.merge(baseline, on=['ROUTE_NUM', 'weekday', 'hour'])
    route_hourly['excess'] = route_hourly['flow'] / route_hourly['median_flow']
    
    results = []
    
    # RAW слой
    raw = route_hourly[(route_hourly['excess'] >= threshold_raw) & (route_hourly['median_flow'] > 0)].copy()
    for _, row in raw.iterrows():
        results.append({
            'entity_type': 'route',
            'entity_id': str(row['ROUTE_NUM']),
            'anomaly_date': f"weekday={row['weekday']}, hour={row['hour']}",
            'metric_name': 'flow_excess',
            'metric_value': round(row['excess'], 2),
            'threshold_value': threshold_raw,
            'severity': 'raw',
            'hypothesis': 'H2',
            'details': f'{{"flow": {row["flow"]}, "median": {row["median_flow"]:.0f}}}'
        })
    
    # STRONG слой
    strong = route_hourly[(route_hourly['excess'] >= threshold_strong) & (route_hourly['median_flow'] > 0)].copy()
    for _, row in strong.iterrows():
        results.append({
            'entity_type': 'route',
            'entity_id': str(row['ROUTE_NUM']),
            'anomaly_date': f"weekday={row['weekday']}, hour={row['hour']}",
            'metric_name': 'flow_excess',
            'metric_value': round(row['excess'], 2),
            'threshold_value': threshold_strong,
            'severity': 'strong',
            'hypothesis': 'H2',
            'details': f'{{"flow": {row["flow"]}, "median": {row["median_flow"]:.0f}}}'
        })
    
    return pd.DataFrame(results)