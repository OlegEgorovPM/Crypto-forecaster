from data.fetch_data import fetch_bybit_candles
from data.preprocess_data import prepare_prophet_data
import time
from config import RAW_DATA_FILE, PROCESSED_DATA_FILE, DATA_SAVE_PATH
import os



def main():
    start_time = time.time()
    # Создаем папку для сохранения данных, если ее нет
    if not os.path.exists(DATA_SAVE_PATH):
        os.makedirs(DATA_SAVE_PATH)
    
    # 1. Получение данных
    raw_data = fetch_bybit_candles()
    print(f"Загружено свечей: {len(raw_data)}")

    # Сохраняем сырые данные
    raw_data.to_csv(RAW_DATA_FILE, index=False)
    print(f"Сырые данные сохранены в: {RAW_DATA_FILE}")

    # 2. Подготовка данных
    print("Обработка данных...")
    df = prepare_prophet_data(raw_data)
    last_ts = df['ds'].max()
    print(f"Данные от {df['ds'].min()} до {last_ts}")
    
    # Сохраняем обработанные данные
    df.to_csv(PROCESSED_DATA_FILE, index=False)
    print(f"Обработанные данные сохранены в: {PROCESSED_DATA_FILE}")


if __name__ == "__main__":
    main()