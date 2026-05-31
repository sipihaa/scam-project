"""
H7: Школьная карта в нерабочее время
"""

import pandas as pd


def h7_night_school(df: pd.DataFrame,
                    night_start_hour: int = 0,
                    night_end_hour: int = 6,
                    school_cats: list = None) -> pd.DataFrame:
    if school_cats is None:
        school_cats = [203, 208, 209, 303]
    
    df = df.copy()
    df['is_school'] = df['CAT_NUM'].isin(school_cats)
    df['hour'] = df['datetime'].dt.hour
    
    # Ночные поездки школьников
    night_trips = df[
        (df['is_school']) & 
        ((df['hour'] >= night_start_hour) & (df['hour'] < night_end_hour))
    ].copy()
    
    results = []
    for _, row in night_trips.iterrows():
        results.append({
            'entity_type': 'card',
            'entity_id': row['CARD'],
            'anomaly_date': row['datetime'],
            'metric_name': 'night_trip',
            'metric_value': 1,
            'threshold_value': 'night',
            'severity': 'strong',
            'hypothesis': 'H7',
            'details': f'{{"validator": "{row["TRM_ID"]}", "route": "{row["ROUTE_NUM"]}"}}'
        })
    
    return pd.DataFrame(results)