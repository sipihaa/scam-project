"""
H3: Пакетная накрутка разными картами (пачка за секунду)
"""

import pandas as pd


def h3_bursts(df: pd.DataFrame,
              threshold_raw: int = 3,
              threshold_strong: int = 5,
              time_window_seconds: int = 1,
              min_cards_in_burst: int = 2,
              exclude_service_cards: bool = True,
              service_card_threshold: int = 12) -> pd.DataFrame:
    df = df.copy()
    
    df['time_window'] = df['datetime'].dt.floor(f'{time_window_seconds}s')
    
    # Исключаем служебные карты, если нужно
    if exclude_service_cards:
        daily_trips = df.groupby(['CARD', df['datetime'].dt.date])['CARD'].transform('size')
        service_cards = df[daily_trips > service_card_threshold]['CARD'].unique()
        df = df[~df['CARD'].isin(service_cards)].copy()
    
    # Группируем по валидатору и временному окну
    bursts = df.groupby(['TRM_ID', 'time_window']).agg(
        tx_count=('CARD', 'size'),
        unique_cards=('CARD', 'nunique'),
        sample_cards=('CARD', lambda x: list(x.unique()[:5]))
    ).reset_index()
    
    # Создаем строку с результатами
    def make_result(bursts_subset, current_threshold, severity_level):
        if bursts_subset.empty:
            return pd.DataFrame()
        
        result = pd.DataFrame({
            'entity_type': ['validator'] * len(bursts_subset),
            'entity_id': bursts_subset['TRM_ID'].values,
            'anomaly_date': bursts_subset['time_window'].values,
            'metric_name': ['tx_per_sec'] * len(bursts_subset),
            'metric_value': bursts_subset['tx_count'].values,
            'threshold_value': [current_threshold] * len(bursts_subset),
            'severity': [severity_level] * len(bursts_subset),
            'hypothesis': ['H3'] * len(bursts_subset),
            'details': bursts_subset.apply(
                lambda x: f'{{"unique_cards": {x["unique_cards"]}, "sample_cards": {x["sample_cards"]}}}',
                axis=1
            ).values
        })
        return result
    
    # RAW слой
    bursts_raw = bursts[
        (bursts['tx_count'] >= threshold_raw) &
        (bursts['unique_cards'] >= min_cards_in_burst)
    ].copy()
    result_raw = make_result(bursts_raw, threshold_raw, 'raw')
    
    # STRONG слой
    bursts_strong = bursts_raw[bursts_raw['tx_count'] >= threshold_strong].copy()
    result_strong = make_result(bursts_strong, threshold_strong, 'strong')
    
    result = pd.concat([result_raw, result_strong], ignore_index=True)
    
    # Сортируем по metric_value
    result = result.sort_values('metric_value', ascending=False).reset_index(drop=True)
    
    return result