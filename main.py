import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import matplotlib.dates as mdates
import threading
import time
import numpy as np
from tkinter import ttk
from data.fetch_data import fetch_bybit_candles, fetch_recent_candles
from data.preprocess_data import prepare_prophet_data
from config import SYMBOL, INTERVAL, CATEGORY, HISTORY_HOURS

class ProfessionalCandlestickApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        # Настройка основного окна
        self.title("Профессиональный свечной график")
        self.geometry("1200x800")
        
        # Инициализация переменных для сохранения масштаба
        self.xlim = None
        self.ylim = None
        self.last_timestamp = None  # Время последней загруженной свечи
        # Загрузка данных
        self.df = self.load_live_data()  # Заменяем загрузку из строки
        
        # Создание левой панели с кнопками
        left_panel = tk.Frame(self, width=150, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5), pady=5)
        
        # Заголовок для методов предсказания
        lbl_methods = tk.Label(
            left_panel, 
            text="Методы предсказания",
            bg="#f0f0f0",
            font=("Arial", 10, "bold"),
            pady=5
        )
        lbl_methods.pack(pady=(10, 5), padx=10)
        
        # Выпадающий список методов предсказания
        self.method_var = tk.StringVar()
        methods = ["ARIMA", "LSTM", "Prophet", "SVM", "XGBoost", "Горизонтальные уровни"]
        self.method_combo = ttk.Combobox(
            left_panel,
            textvariable=self.method_var,
            values=methods,
            state="readonly",
            width=15,
            height=10
        )
        self.method_combo.current(0)
        self.method_combo.pack(pady=5, padx=10)
        
        # Кнопка настроек метода
        self.btn_settings = tk.Button(
            left_panel,
            text="Настройки",
            width=12,
            height=1,
            bg="#e0e0e0",
            relief=tk.FLAT,
            font=("Arial", 9),
            command=self.open_settings
        )
        self.btn_settings.pack(pady=5, padx=10)
        
        # Разделитель
        separator = ttk.Separator(left_panel, orient='horizontal')
        separator.pack(fill='x', pady=10, padx=5)
        
        # Заголовок для параметров графика
        lbl_params = tk.Label(
            left_panel, 
            text="Параметры графика",
            bg="#f0f0f0",
            font=("Arial", 10, "bold"),
            pady=5
        )
        lbl_params.pack(pady=(10, 5), padx=10)
        
        # Выпадающий список таймфреймов
        self.timeframe_var = tk.StringVar()
        timeframes = ["1 минута", "5 минут", "15 минут", "30 минут", "1 час", "4 часа", "1 день"]
        timeframe_combo = ttk.Combobox(
            left_panel,
            textvariable=self.timeframe_var,
            values=timeframes,
            state="readonly",
            width=15
        )
        timeframe_combo.current(0)
        timeframe_combo.pack(pady=5, padx=10)
        
        # Создание основной области для графика и элементов управления
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Создание фрейма для инструментов графика
        toolbar_frame = tk.Frame(main_frame, height=30)
        toolbar_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Создание фрейма для графика
        graph_frame = tk.Frame(main_frame, bg='white')
        graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание фигуры и осей для графика
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        # Встраивание графика в Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Добавление панели инструментов для графика
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(fill=tk.X)
        
        # Убрать отображение координат в правом верхнем углу
        self.ax.format_coord = lambda x, y: ""
        
        # Статус бар (размещаем в главном окне, а не во фрейме)
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = tk.Label(self, textvariable=self.status_var, bd=1, 
                            relief=tk.SUNKEN, anchor=tk.W, bg="#e0e0e0", font=("Arial", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, before=left_panel)  # Размещаем до левой панели
        
        # Инициализация графика
        self.plot_candlestick()
        
        # Подключение обработчика движения мыши
        self.canvas.mpl_connect('motion_notify_event', self.on_hover)

        # Запуск потока обновления
        self.update_thread = threading.Thread(target=self.update_data, daemon=True)
        self.update_thread.start()
        
    def load_live_data(self, initial_load=True):
        """Загрузка данных с биржи с оптимизацией"""
        try:
            if initial_load:
                # Первоначальная загрузка полного набора данных
                raw_data = fetch_bybit_candles()
                df = prepare_prophet_data(raw_data)
                
                if not df.empty:
                    self.last_timestamp = df['timestamp'].max()
                
                return df
            else:
                # Последующие обновления - только новые данные
                if not self.last_timestamp:
                    return self.load_live_data(initial_load=True)
                
                # Загружаем только последние 5 минут (на случай пропущенных свечей)
                raw_data = fetch_recent_candles(self.last_timestamp)
                if raw_data.empty:
                    return pd.DataFrame()
                
                new_df = prepare_prophet_data(raw_data)
                
                # Фильтруем только действительно новые данные
                new_df = new_df[new_df['timestamp'] > self.last_timestamp]
                
                if not new_df.empty:
                    self.last_timestamp = new_df['timestamp'].max()
                
                return new_df
                
        except Exception as e:
            print(f"Ошибка загрузки данных: {str(e)}")
            return pd.DataFrame()

    def update_data(self):
        """Поток для обновления данных"""
        # Первоначальная загрузка уже сделана в __init__, ждем 60 секунд
        time.sleep(20)
        
        while True:
            try:
                # Загружаем только новые данные
                new_df = self.load_live_data(initial_load=False)
                
                if not new_df.empty:
                    # Объединяем новые данные с существующими
                    self.df = pd.concat([self.df, new_df]).drop_duplicates(subset=['timestamp'], keep='last')
                    self.df.sort_values('ds', inplace=True)
                    
                    # Обновляем график
                    self.after(0, self.plot_candlestick)
                    self.update_status()
                
                # Пауза 60 секунд
                time.sleep(20)
            except Exception as e:
                self.status_var.set(f"Ошибка обновления: {str(e)}")
                time.sleep(10)
    
    def plot_candlestick(self):
        """Построение свечного графика с обработкой пустых данных"""
        if self.ax.lines:  # Если на графике уже есть данные
            self.xlim = self.ax.get_xlim()
            self.ylim = self.ax.get_ylim()
        
        self.ax.clear()
        
        if self.df.empty:
            # Отображаем сообщение об отсутствии данных
            self.ax.text(0.5, 0.5, "Нет данных для отображения", 
                         ha='center', va='center', fontsize=12)
            self.canvas.draw()
            return
        
        # Преобразование времени в числовой формат Matplotlib
        dates = mdates.date2num(self.df['ds'])
        
        # Рассчет пределов для осей
        min_low = self.df['low'].min()
        max_high = self.df['high'].max()
        price_range = max_high - min_low
        y_min = min_low - price_range * 0.05
        y_max = max_high + price_range * 0.05
        
        # Определение ширины свечи (автоматическая)
        # Вычисляем средний интервал между свечами
        time_diffs = np.diff(dates)
        avg_time_diff = np.mean(time_diffs) if len(time_diffs) > 0 else 0.001
        width = avg_time_diff * 0.7  # 70% от среднего интервала
        
        # Построение свечей
        for i in range(len(dates)):
            t = dates[i]
            open_price = self.df['open'].iloc[i]
            close_price = self.df['close'].iloc[i]
            high_price = self.df['high'].iloc[i]
            low_price = self.df['low'].iloc[i]
            
            # Определение цвета свечи
            color = '#2ecc71' if close_price >= open_price else '#e74c3c'  # Зеленый/красный
            
            # Построение тени (вертикальная линия)
            self.ax.plot([t, t], [low_price, high_price], 
                        color=color, linewidth=1, solid_capstyle='round')
            
            # Построение тела свечи
            self.ax.bar(
                t, 
                abs(close_price - open_price), 
                bottom=min(open_price, close_price),
                width=width,
                color=color,
                edgecolor=color
            )
        
        # Настройка осей
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_title("Свечной график", fontsize=14)
        self.ax.set_xlabel("Время", fontsize=10)
        self.ax.set_ylabel("Цена", fontsize=10)
        self.ax.grid(True, linestyle='--', alpha=0.3)
        
        # Форматирование оси времени
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        
        # Автоматическое форматирование дат
        self.fig.autofmt_xdate(rotation=0, ha='center')
        
        # Установка правильных пределов по времени
        self.ax.set_xlim(min(dates) - avg_time_diff, max(dates) + avg_time_diff)
        
        # Перерисовка
        self.canvas.draw()
        
        # Обновление статуса
        self.update_status()
    
        # Восстанавливаем масштаб, если он был сохранен
        if self.xlim and self.ylim:
            self.ax.set_xlim(self.xlim)
            self.ax.set_ylim(self.ylim)
        
        self.canvas.draw()

    def on_hover(self, event):
        """Обработчик движения мыши для обновления статус бара"""
        if event.inaxes == self.ax:
            x = event.xdata
            # Преобразование координаты X во время
            hover_time = mdates.num2date(x)
            
            # Поиск ближайшей свечи
            idx = self.find_nearest_candle(hover_time)
            
            if idx is not None:
                candle = self.df.iloc[idx]
                self.update_status(candle)

    def find_nearest_candle(self, target_time):
        """Поиск индекса ближайшей свечи к указанному времени"""
        # Если target_time содержит информацию о часовом поясе, преобразуем в наивное время
        if target_time.tzinfo is not None:
            target_time = target_time.replace(tzinfo=None)
        
        times = self.df['ds'].values
        if len(times) == 0:
            return None
            
        # Преобразование в numpy datetime64 для сравнения
        target_np = np.datetime64(target_time)
        times_np = np.array(times, dtype='datetime64[ns]')
        
        # Вычисление разницы времени
        time_diffs = np.abs(times_np - target_np)
        min_idx = np.argmin(time_diffs)
        
        return min_idx

    def update_status(self, candle=None):
        """Обновление статус бара с данными свечи"""
        if candle is None:
            candle = self.df.iloc[-1]
            
        status_text = (
            f"Время: {candle['ds'].strftime('%H:%M:%S')} | "
            f"Цена: {candle['close']:.2f} | "
            f"Объем: {candle['volume']:.2f} | "
            f"Макс: {candle['high']:.2f} | "
            f"Мин: {candle['low']:.2f}"
        )
        self.status_var.set(status_text)

    def open_settings(self):
        """Открытие окна настроек для выбранного метода"""
        selected_method = self.method_var.get()
        if not selected_method:
            return
            
        # Создание окна настроек
        settings_window = tk.Toplevel(self)
        settings_window.title(f"Настройки: {selected_method}")
        settings_window.geometry("400x300")
        settings_window.grab_set()  # Модальное окно
        
        # Заголовок
        lbl_title = tk.Label(
            settings_window,
            text=f"Настройки параметров для {selected_method}",
            font=("Arial", 11, "bold"),
            pady=10
        )
        lbl_title.pack()
        
        # Заглушка - содержимое настроек
        lbl_content = tk.Label(
            settings_window,
            text="Здесь будут настройки выбранного метода.\n\n"
                 "Например, для ARIMA можно настроить:\n"
                 "- Порядок авторегрессии (p)\n"
                 "- Порядок интегрирования (d)\n"
                 "- Порядок скользящего среднего (q)\n\n"
                 "Для LSTM можно настроить:\n"
                 "- Количество слоев\n"
                 "- Количество нейронов\n"
                 "- Размер окна",
            justify=tk.LEFT,
            padx=20,
            pady=10
        )
        lbl_content.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка закрытия
        btn_close = tk.Button(
            settings_window,
            text="Закрыть",
            width=10,
            command=settings_window.destroy
        )
        btn_close.pack(pady=10)

if __name__ == "__main__":
    app = ProfessionalCandlestickApp()
    app.mainloop()