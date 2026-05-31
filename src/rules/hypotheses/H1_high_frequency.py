"""
H1: Аномально много поездок одной картой
"""

import pandas as pd


def h1_high_frequency(df: pd.DataFrame,
                      threshold_raw: int = 6,
                      threshold_strong: int = 12,
                      exclude_service_cards: bool = True,
                      service_card_threshold: int = 12) -> pd.DataFrame:
    df = df.copy()
    
    # Считаем поездки на карту в день
    daily_trips = df.groupby(['CARD', df['datetime'].dt.date]) \
                    .size().reset_index(name='trips_per_day')
    daily_trips.columns = ['CARD', 'date', 'trips_per_day']
    
    # Исключаем служебные карты
    if exclude_service_cards:
        service_cards = daily_trips[daily_trips['trips_per_day'] > service_card_threshold]['CARD'].unique()
        daily_trips = daily_trips[~daily_trips['CARD'].isin(service_cards)]
    
    results = []
    
    # RAW слой
    raw = daily_trips[daily_trips['trips_per_day'] >= threshold_raw].copy()
    for _, row in raw.iterrows():
        results.append({
            'entity_type': 'card',
            'entity_id': row['CARD'],
            'anomaly_date': row['date'],
            'metric_name': 'trips_per_day',
            'metric_value': row['trips_per_day'],
            'threshold_value': threshold_raw,
            'severity': 'raw',
            'hypothesis': 'H1',
            'details': f'{{"card": "{row["CARD"]}"}}'
        })
    
    # STRONG слой
    strong = daily_trips[daily_trips['trips_per_day'] >= threshold_strong].copy()
    for _, row in strong.iterrows():
        results.append({
            'entity_type': 'card',
            'entity_id': row['CARD'],
            'anomaly_date': row['date'],
            'metric_name': 'trips_per_day',
            'metric_value': row['trips_per_day'],
            'threshold_value': threshold_strong,
            'severity': 'strong',
            'hypothesis': 'H1',
            'details': f'{{"card": "{row["CARD"]}"}}'
        })
    
    return pd.DataFrame(results)