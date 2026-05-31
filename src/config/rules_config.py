# Конфигурационный файл с параметрами для всех гипотез детекции мошенничества

# H1: Аномально много поездок одной картой
H1_CONFIG = {
    'threshold_raw': 6,           # поездок в день (95-й перцентиль)
    'threshold_strong': 12,       # поездок в день (99-й перцентиль)
    'service_card_threshold': 12 # превышение → служебная карта
}

# H2: Резкий всплеск пассажиропотока на маршруте
H2_CONFIG = {
    'threshold_raw': 3,           # превышение медианы в N раз
    'threshold_strong': 5,        # превышение медианы в N раз
    'min_history_days': 90      # требуется минимум 90 дней истории
}

# H3: Пакетная накрутка разными картами
H3_CONFIG = {
    'threshold_raw': 3,           # транзакций в секунду
    'threshold_strong': 5,        # транзакций в секунду
    'time_window_seconds': 1     # окно анализа в секундах
}

# H4: Серия льготников в нетипичное время
H4_CONFIG = {
    'series_length': 3,           # минимум льготных транзакций подряд
    'interval_seconds': 60,       # максимальный интервал между транзакциями в серии
    'atypical_hours_start': 22,   # начало нетипичного времени
    'atypical_hours_end': 6,      # конец нетипичного времени
    'benefit_cats': [201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 303, 304]
}

# H7: Школьная карта в нерабочее время
H7_CONFIG = {
    'night_start_hour': 0,        # начало ночного времени
    'night_end_hour': 6,          # конец ночного времени
    'school_cats': [203, 208, 209, 303]  # школьные категории
}

# H8: Многократное использование школьной карты подряд
H8_CONFIG = {
    'min_consecutive': 2,         # минимум последовательных использований
    'interval_seconds': 60,       # максимальный интервал между использованиями
    'school_cats': [203, 208, 209, 303],
    'same_validator_required': True  # должен быть один валидатор
}

# H10: Нетипичный профиль использования льготы
H10_CONFIG = {
    'school_peak_threshold': 30,      # % поездок в час пик для школы (аномалия >)
    'senior_peak_threshold': 20,      # % поездок в час пик для пенсионеров (аномалия >)
    'peak_hours_morning': [7, 8, 9],  # утренние часы пик
    'peak_hours_evening': [17, 18, 19],  # вечерние часы пик
    'school_cats': [203, 208, 209, 303],
    'senior_cats': [207]
}

# H11: Аномально высокая доля наличных на валидаторе
H11_CONFIG = {
    'threshold_raw': 0.21,        # 21% — 90-й перцентиль
    'threshold_strong': 0.47,     # 47% — 95-й перцентиль
    'cash_cat': 151,              # код наличных
    'min_transactions': 10       # минимальное число транзакций для анализа
}

# H12: Аномально низкая доля наличных
H12_CONFIG = {
    'threshold_raw': 0.07,        # 7% — 5-й перцентиль
    'threshold_strong': 0.00,     # 0% — 1-й перцентиль
    'cash_cat': 151,
    'min_transactions': 10
}

# H17: Сумма равна нулю при тарифицируемой категории
H17_CONFIG = {
    'allowed_zero_cats': [151, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 303, 304],
    'fraud_zero_cats': [91, 92, 93]   # банковские карты
}

# H19: Категория отсутствует в справочнике
H19_CONFIG = {
    'known_cats': [91, 92, 93, 151, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 303, 304]
}

# H20: Дубли транзакций секунда-в-секунду
H20_CONFIG = {
    'single_threshold': 2,        # единичные дубли (2-3 раза)
    'mass_threshold': 5          # массовые дубли (>5 раз) — аномалия
}

# H21: Отклонение потока от пуассоновского
H21_CONFIG = {
    'p_value_threshold': 0.05,        # порог статистической значимости
    'test_method': 'Kolmogorov-Smirnov',  # используемый тест
    'min_history_days': 30           # требуется минимум 30 дней истории
}


# ОБЩИЕ ПАРАМЕТРЫ
GLOBAL_CONFIG = {
    'data_path': 'data',
    'sep': ';',
    'encoding': 'cp1251',
    'region_code': 65,
    'date_format': '%d.%m.%Y %H:%M:%S'
}


# СЛОВАРЬ ДЛЯ БЫСТРОГО ДОСТУПА К КОНФИГАМ ГИПОТЕЗ
ALL_HYPOTHESES_CONFIG = {
    'H1': H1_CONFIG,
    'H2': H2_CONFIG,
    'H3': H3_CONFIG,
    'H4': H4_CONFIG,
    'H7': H7_CONFIG,
    'H8': H8_CONFIG,
    'H10': H10_CONFIG,
    'H11': H11_CONFIG,
    'H12': H12_CONFIG,
    'H17': H17_CONFIG,
    'H19': H19_CONFIG,
    'H20': H20_CONFIG,
    'H21': H21_CONFIG,
}


def get_hypothesis_config(hypothesis_name: str) -> dict:
    return ALL_HYPOTHESES_CONFIG.get(hypothesis_name, {})


def get_all_configs() -> dict:
    return ALL_HYPOTHESES_CONFIG