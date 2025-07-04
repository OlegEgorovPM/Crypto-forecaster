from datetime import datetime

# Константы для работы с API Bybit
BYBIT_API_URL = "https://api.bybit.com"
SYMBOL = "BTCUSDT"  # Торговая пара
INTERVAL = 1         # 1-минутные свечи (в минутах)
MAX_RETRIES = 3      # Максимальное количество попыток при ошибках
REQUEST_DELAY = 1    # Задержка между запросами в секундах
CATEGORY = "spot"    # Тип рынка (spot/linear)

# Параметры данных
HISTORY_HOURS = 24   # Сколько часов данных загружать (2 дня)
FORECAST_PERIODS = 60 # Прогноз на 60 минут
TIMEREGION = 3       # Часовой пояс, для смещения UTS-0

# Сохранения данных
DATA_SAVE_PATH = "saved_data/"
RAW_DATA_FILE = f"{DATA_SAVE_PATH}raw_{SYMBOL}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
PROCESSED_DATA_FILE = f"{DATA_SAVE_PATH}processed_{SYMBOL}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"