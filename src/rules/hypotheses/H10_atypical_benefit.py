"""
H10: Нетипичный профиль использования льготы
"""

import pandas as pd


def h10_atypical_benefit(df: pd.DataFrame,
                         school_peak_threshold: int = 30,
                         senior_peak_threshold: int = 20,
                         peak_hours_morning: list = None,
                         peak_hours_evening: list = None,
                         school_cats: list = None,
                         senior_cats: list = None) -> pd.DataFrame:
    if peak_hours_morning is None:
        peak_hours_morning = [7, 8, 9]
    if peak_hours_evening is None:
        peak_hours_evening = [17, 18, 19]
    if school_cats is None:
        school_cats = [203, 208, 209, 303]
    if senior_cats is None:
        senior_cats = [207]
    
    df = df.copy()
    peak_hours = peak_hours_morning + peak_hours_evening
    df['hour'] = df['datetime'].dt.hour
    
    results = []
    
    # Школьные карты
    school_trips = df[df['CAT_NUM'].isin(school_cats)]
    total_school = len(school_trips)
    school_peak = len(school_trips[school_trips['hour'].isin(peak_hours)])
    school_pct = school_peak / total_school * 100 if total_school > 0 else 0
    
    if school_pct > school_peak_threshold:
        results.append({
            'entity_type': 'category',
            'entity_id': 'school',
            'anomaly_date': df['datetime'].min().strftime('%Y-%m'),
            'metric_name': 'peak_hour_share',
            'metric_value': round(school_pct, 1),
            'threshold_value': school_peak_threshold,
            'severity': 'strong',
            'hypothesis': 'H10',
            'details': f'{{"total_trips": {total_school}, "peak_trips": {school_peak}}}'
        })
    
    # Пенсионные карты
    senior_trips = df[df['CAT_NUM'].isin(senior_cats)]
    total_senior = len(senior_trips)
    senior_peak = len(senior_trips[senior_trips['hour'].isin(peak_hours)])
    senior_pct = senior_peak / total_senior * 100 if total_senior > 0 else 0
    
    if senior_pct > senior_peak_threshold:
        results.append({
            'entity_type': 'category',
            'entity_id': 'senior',
            'anomaly_date': df['datetime'].min().strftime('%Y-%m'),
            'metric_name': 'peak_hour_share',
            'metric_value': round(senior_pct, 1),
            'threshold_value': senior_peak_threshold,
            'severity': 'strong',
            'hypothesis': 'H10',
            'details': f'{{"total_trips": {total_senior}, "peak_trips": {senior_peak}}}'
        })
    
    return pd.DataFrame(results)