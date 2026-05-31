"""
H19: Категория отсутствует в справочнике
"""

import pandas as pd


def h19_unknown_categories(df: pd.DataFrame,
                           known_cats: list = None) -> pd.DataFrame:
    if known_cats is None:
        known_cats = [91, 92, 93, 151, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 303, 304]
    
    df = df.copy()
    actual_cats = set(df['CAT_NUM'].dropna().unique())
    unknown_cats = actual_cats - set(known_cats)
    
    results = []
    for cat in unknown_cats:
        cat_data = df[df['CAT_NUM'] == cat]
        results.append({
            'entity_type': 'category',
            'entity_id': str(cat),
            'anomaly_date': df['datetime'].min().strftime('%Y-%m'),
            'metric_name': 'unknown_category',
            'metric_value': len(cat_data),
            'threshold_value': 'not_in_known',
            'severity': 'raw',
            'hypothesis': 'H19',
            'details': f'{{"sample_cards": {cat_data["CARD"].head(3).tolist()}}}'
        })
    
    return pd.DataFrame(results)