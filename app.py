import time
import cv2
import mss
import numpy as np
import pyautogui
from pynput import keyboard as kb
from ultralytics import YOLO

# ==========================================
# ⚙️ НАСТРОЙКИ
# ==========================================
MODEL_PATH = "best3.pt"
CONF_THRESHOLD = 0.5         # Уверенность модели (0.5 - оптимально для новой модели)
IMG_SIZE = 640               

# ⚠️ ВАЖНО: Имена классов СТРОГО как в вашем data.yaml!
# Если в data.yaml написано "reclama", напишите "reclama" и здесь.
CLASS_NAMES = ["game", "upgrade", "reclama"] 

# --- Логика свайпа улучшений ---
UPGRADE_SWEEP_INTERVAL = 2.0   # Раз в сколько секунд делать свайп (2 секунды - хороший темп)
CLICKS_PER_SWEEP = 6           # Сколько кликов делать за один свайп
SWEEP_STEP_DELAY = 0.05        # Пауза между кликами внутри свайпа (сек)

# --- Отступы внутри рамки улучшений (в процентах от размера рамки) ---
# Отступ сверху (чтобы не кликать по заголовку "Магазин")
UPGRADE_TOP_SKIP_PERCENT = 0.20     
# Отступ снизу (чтобы не кликать по краю экрана)
UPGRADE_BOTTOM_SKIP_PERCENT = 0.02  
# Сдвиг по горизонтали: -0.15 = влево на 15% (чтобы не нажать "Купить 10")
UPGRADE_X_OFFSET_PERCENT = -0.15    

# Область экрана (если хотите захватывать только окно игры, иначе None)
SCREEN_REGION = None 
# Пример: SCREEN_REGION = {"top": 100, "left": 100, "width": 1000, "height": 800}


# ==========================================
# 🛑 ЛОГИКА ОСТАНОВКИ (ПРОБЕЛ)
# ==========================================
stop_flag = False

def on_press(key):
    global stop_flag
    if key == kb.Key.space:
        stop_flag = True
        print("\n[!] Нажат ПРОБЕЛ. Останавливаюсь...")
        return False # Останавливаем слушатель

# ==========================================
# 🚀 ИНИЦИАЛИЗАЦИЯ
# ==========================================
print("Загрузка модели...")
model = YOLO(MODEL_PATH)

# Отключаем паузу pyautogui для максимальной скорости
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True # Аварийная остановка (мышь в левый верхний угол)

# Запускаем слушатель клавиатуры
listener = kb.Listener(on_press=on_press)
listener.start()

print("=" * 40)
print("🍪 БОТ ЗАПУЩЕН!")
print("Нажмите ПРОБЕЛ для остановки.")
print("Аварийная остановка: мышь в левый верхний угол.")
print("=" * 40)

sct = mss.mss()
last_upgrade_sweep = 0.0
last_debug_save = time.time()

# ==========================================
# 🔄 ОСНОВНОЙ ЦИКЛ
# ==========================================
try:
    while not stop_flag:
        # 1. Захват экрана
        monitor = SCREEN_REGION or sct.monitors[1]
        frame = np.array(sct.grab(monitor))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        # 2. Детекция YOLO
        results = model(frame_rgb, conf=CONF_THRESHOLD, imgsz=IMG_SIZE, verbose=False)
        boxes = results[0].boxes
        current_time = time.time()

        # --- Отладка: сохраняем картинку раз в секунду (можно закомментировать) ---
        if current_time - last_debug_save > 1.0:
            annotated = results[0].plot()
            cv2.imwrite("debug_view.png", cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
            last_debug_save = current_time

        # 3. Обработка найденных объектов
        for box in boxes:
            cls_id = int(box.cls[0])
            if cls_id >= len(CLASS_NAMES):
                continue
                
            cls_name = CLASS_NAMES[cls_id]
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # Поправка на область экрана
            offset_x = SCREEN_REGION["left"] if SCREEN_REGION else 0
            offset_y = SCREEN_REGION["top"] if SCREEN_REGION else 0

            # --- ЛОГИКА ДЛЯ ПЕЧЕНЬЯ (game) ---
            if cls_name == "game":
                cx = int((x1 + x2) / 2) + offset_x
                cy = int((y1 + y2) / 2) + offset_y
                pyautogui.click(cx, cy)

            # --- ЛОГИКА ДЛЯ УЛУЧШЕНИЙ (upgrade) ---
            elif cls_name == "upgrade":
                if current_time - last_upgrade_sweep > UPGRADE_SWEEP_INTERVAL:
                    box_height = y2 - y1
                    box_width = x2 - x1
                    
                    # Высчитываем границы по Y с отступами
                    sweep_top    = y1 + box_height * UPGRADE_TOP_SKIP_PERCENT
                    sweep_bottom = y2 - box_height * UPGRADE_BOTTOM_SKIP_PERCENT

                    if sweep_top < sweep_bottom:
                        # Высчитываем X с учетом сдвига влево
                        cx = int((x1 + x2) / 2 + box_width * UPGRADE_X_OFFSET_PERCENT) + offset_x
                        
                        # Создаем точки для клика от низа к верху
                        y_points = np.linspace(sweep_bottom, sweep_top, num=CLICKS_PER_SWEEP)

                        print(f"[+] Свайп улучшений: X={cx}, Y от {int(sweep_bottom)} до {int(sweep_top)}")

                        for y in y_points:
                            click_y = int(y) + offset_y
                            pyautogui.click(cx, click_y)
                            time.sleep(SWEEP_STEP_DELAY)

                        last_upgrade_sweep = time.time()

            # --- ЛОГИКА ДЛЯ РЕКЛАМЫ (reclamd) ---
            # (Если нужно будет закрывать рекламу, раскомментируйте код ниже)
            elif cls_name == "reclama":
                cx = int((x1 + x2) / 2) + offset_x
                cy = int((y1 + y2) / 2) + offset_y
                pyautogui.click(cx, cy)

        # Микро-пауза для процессора
        time.sleep(0.005)

except KeyboardInterrupt:
    print("\n[!] Остановка (Ctrl+C).")
except pyautogui.FailSafeException:
    print("\n[!] Сработала защита (мышь в углу).")
finally:
    listener.stop()
    print("Бот остановлен.")