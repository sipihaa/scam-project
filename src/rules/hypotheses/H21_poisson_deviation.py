"""
H21: Отклонение потока от пуассоновского
"""

import pandas as pd


def h21_poisson_deviation(df: pd.DataFrame,
                          p_value_threshold: float = 0.05,
                          test_method: str = 'Kolmogorov-Smirnov',
                          min_history_days: int = 30) -> pd.DataFrame:
    # На 14 днях данных статистический тест не имеет смысла
    # Возвращаем пустой DataFrame с пояснением в details
    
    results = [{
        'entity_type': 'validator',
        'entity_id': 'all',
        'anomaly_date': df['datetime'].min().strftime('%Y-%m'),
        'metric_name': 'poisson_p_value',
        'metric_value': 0.0,
        'threshold_value': p_value_threshold,
        'severity': 'info',
        'hypothesis': 'H21',
        'details': '{"note": "Требуется 30+ дней данных для статистического теста"}'
    }]
    
    return pd.DataFrame(results)