import pandas as pd
from config import INTERVAL,TIMEREGION

def prepare_prophet_data(raw_df):
    if raw_df.empty:
        raise ValueError("Получен пустой DataFrame для обработки")
    
    # Сортировка по времени
    raw_df = raw_df.sort_values('timestamp')

    # Конвертация timestamp в datetime
    raw_df['ds'] = pd.to_datetime(raw_df['timestamp'].astype(float)/1000 + TIMEREGION*3600, unit='s')

    
    return raw_df[['ds','timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']]