import pandas as pd
from config import INTERVAL,TIMEREGION

def prepare_prophet_data(raw_df):
    if raw_df.empty:
        raise ValueError("Получен пустой DataFrame для обработки")
    
    # Сортировка по времени
    raw_df = raw_df.sort_values('timestamp')

    # Преобразование timestamp в числовой формат
    raw_df['timestamp'] = pd.to_numeric(raw_df['timestamp'], errors='coerce')
    
    # Удаление некорректных значений timestamp
    raw_df = raw_df.dropna(subset=['timestamp'])
    
    # Конвертация timestamp в datetime
    # Добавляем смещение часового пояса (TIMEREGION часов)
    raw_df['ds'] = pd.to_datetime(
        raw_df['timestamp'].astype('int64') // 1000 + TIMEREGION * 3600, 
        unit='s'
    )

    # Преобразование числовых колонок в float
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'turnover']
    for col in numeric_cols:
        raw_df[col] = pd.to_numeric(raw_df[col], errors='coerce')
    
    return raw_df[['ds','timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']]