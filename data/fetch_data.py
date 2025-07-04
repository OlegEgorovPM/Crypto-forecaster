import requests
import pandas as pd
from datetime import datetime, timedelta
from config import BYBIT_API_URL, SYMBOL, INTERVAL, HISTORY_HOURS, CATEGORY, MAX_RETRIES, REQUEST_DELAY
import sys
import time
import math

def fetch_bybit_candles():
    end_time = datetime.now().replace(microsecond=0)
    start_time = end_time - timedelta(hours=HISTORY_HOURS)
    total_minutes = HISTORY_HOURS * 60
    
    # Рассчитаем необходимое количество запросов
    candles_per_request = 200
    num_requests = math.ceil(total_minutes / candles_per_request)
    
    all_candles = []
    loaded = 0
    print(f"Загрузка данных {SYMBOL} ({HISTORY_HOURS} часов = {total_minutes} минут)")
    print(f"Требуется запросов: {num_requests}")
    
    # Рассчитаем временные интервалы для каждого запроса
    time_step = timedelta(minutes=candles_per_request)
    current_start = start_time
    
    for i in range(num_requests):
        # Рассчитаем конечное время для текущего запроса
        current_end = min(current_start + time_step, end_time)
        
        # Преобразуем время в миллисекунды
        start_ms = int(current_start.timestamp() * 1000)
        end_ms = int(current_end.timestamp() * 1000)
        
        # Подготовим параметры запроса
        params = {
            'category': CATEGORY,
            'symbol': SYMBOL,
            'interval': str(INTERVAL),
            'start': start_ms,
            'end': end_ms,
            'limit': candles_per_request
        }
        
        # Выполняем запрос с повторными попытками
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    f"{BYBIT_API_URL}/v5/market/kline",
                    params=params,
                    timeout=10
                )
                
                if response.status_code != 200:
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                
                data = response.json().get('result', {}).get('list', [])
                if not data:
                    break
                
                all_candles.extend(data)
                loaded += len(data)
                
                # Обновляем прогресс
                progress = min(100, int(loaded / total_minutes * 100))
                sys.stdout.write(f"\rЗапрос {i+1}/{num_requests} | Прогресс: {progress}% ({loaded}/{total_minutes})")
                sys.stdout.flush()
                break
                
            except Exception as e:
                print(f"\nОшибка при запросе: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    print(f"Повторная попытка {attempt+1}/{MAX_RETRIES} через 2 сек...")
                    time.sleep(2)
                else:
                    print("Превышено максимальное количество попыток. Пропускаем этот интервал.")
                    break
        
        # Переходим к следующему интервалу
        current_start = current_end
        if current_start >= end_time:
            break
            
        # Задержка между запросами
        time.sleep(REQUEST_DELAY)
    
    # Обработка случая, когда загружено больше данных, чем нужно
    if loaded > total_minutes:
        all_candles = all_candles[:total_minutes]
        loaded = total_minutes
    
    sys.stdout.write(f"\rЗагрузка завершена! Загружено минут: {loaded}/{total_minutes}\n")
    
    # Создаем DataFrame
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
    return df

def fetch_recent_candles(last_timestamp):
    """Загрузка только последних свечей с биржи"""
    # Рассчитываем время начала - последняя свеча + 1 минута
    start_time = datetime.fromtimestamp(last_timestamp / 1000)
    end_time = datetime.now()
    
    params = {
        'category': CATEGORY,
        'symbol': SYMBOL,
        'interval': str(INTERVAL),
        'start': int(start_time.timestamp() * 1000),
        'end': int(end_time.timestamp() * 1000),
        'limit': 200  # Максимальное количество свечей за запрос
    }
    
    try:
        response = requests.get(
            f"{BYBIT_API_URL}/v5/market/kline",
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
        
        data = response.json().get('result', {}).get('list', [])
        return pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        
    except Exception as e:
        print(f"Ошибка при загрузке новых свечей: {str(e)}")
        return pd.DataFrame()