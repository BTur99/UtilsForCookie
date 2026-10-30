import time
import cv2
import mss
import numpy as np
import pyautogui
from pynput import keyboard as kb

# ==========================================
# ⚙️ КОНФИГУРАЦИЯ
# ==========================================
CONFIG = {
    "MODEL_PATH": "best.onnx",      
    "CONFIDENCE": 0.5,              
    "NMS_THRESHOLD": 0.45,
    "IMG_SIZE": 640,                
    
    # Имена классов
    "CLASSES": ["game", "upgrade", "reclama"], 
    
    # Тайминги
    "COOKIE_CLICK_COOLDOWN": 0.01,  
    "UPGRADE_SWEEP_INTERVAL": 2.0,  
    "SWEEP_STEP_DELAY": 0.05,       
    "CLICKS_PER_SWEEP": 6,          
    
    # Смещения
    "UPGRADE_TOP_SKIP": 0.20,       
    "UPGRADE_BOTTOM_SKIP": 0.02,    
    "UPGRADE_X_OFFSET": -0.15,      
}

# ==========================================
# 🛑 ЛОГИКА ОСТАНОВКИ
# ==========================================
stop_flag = False

def on_press(key):
    global stop_flag
    if key == kb.Key.space:
        stop_flag = True
        print("\n[!] Нажат ПРОБЕЛ. Останавливаюсь...")
        return False

# ==========================================
# 🧠 КЛАСС ДЛЯ РАБОТЫ С YOLO ONNX
# ==========================================
class YOLOv8ONNX:
    def __init__(self, model_path, conf_thres, nms_thres, classes):
        self.net = cv2.dnn.readNetFromONNX(model_path)
        self.conf_thres = conf_thres
        self.nms_thres = nms_thres
        self.classes = classes
        self.input_size = CONFIG["IMG_SIZE"]

    def detect(self, image):
        blob = cv2.dnn.blobFromImage(image, 1/255.0, (self.input_size, self.input_size), swapRB=True, crop=False)
        self.net.setInput(blob)
        
        outputs = self.net.forward()[0].T

        boxes = []
        confidences = []
        class_ids = []

        for row in outputs:
            scores = row[4:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            if confidence >= self.conf_thres:
                cx, cy, w, h = row[:4]
                x = int((cx - w / 2) * image.shape[1] / self.input_size)
                y = int((cy - h / 2) * image.shape[0] / self.input_size)
                w = int(w * image.shape[1] / self.input_size)
                h = int(h * image.shape[0] / self.input_size)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_thres, self.nms_thres)

        detections = []
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                detections.append({
                    "class_id": class_ids[i],
                    "class_name": self.classes[class_ids[i]],
                    "bbox": [x, y, x + w, y + h] # x1, y1, x2, y2
                })
        return detections

# ==========================================
# 🚀 ИНИЦИАЛИЗАЦИЯ
# ==========================================
print("Загрузка ONNX модели через OpenCV DNN...")
try:
    detector = YOLOv8ONNX(CONFIG["MODEL_PATH"], CONFIG["CONFIDENCE"], CONFIG["NMS_THRESHOLD"], CONFIG["CLASSES"])
    print("✅ Модель успешно загружена (без PyTorch)!")
except Exception as e:
    print(f"❌ Ошибка загрузки модели: {e}")
    print("Убедитесь, что файл best.onnx лежит в папке со скриптом.")
    exit(1)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = True 

listener = kb.Listener(on_press=on_press)
listener.start()

print("=" * 40)
print("🍪 БОТ ЗАПУЩЕН!")
print("Нажмите ПРОБЕЛ для остановки.")
print("Аварийная остановка: мышь в левый верхний угол.")
print("=" * 40)

sct = mss.mss()
last_upgrade_sweep = 0.0
last_cookie_click = 0.0
last_reclam_click = 0.0

# ==========================================
# 🔄 ОСНОВНОЙ ЦИКЛ
# ==========================================
try:
    while not stop_flag:
        # 1. Захват экрана
        monitor = sct.monitors[1]
        frame = np.array(sct.grab(monitor))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

        # 2. Детекция (работает в разы быстрее!)
        detections = detector.detect(frame_rgb)
        current_time = time.time()

        # 3. Обработка
        for det in detections:
            cls_name = det["class_name"]
            x1, y1, x2, y2 = det["bbox"]

            # --- ПЕЧЕНЬЕ ---
            if cls_name == "game":
                if current_time - last_cookie_click > CONFIG["COOKIE_CLICK_COOLDOWN"]:
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    pyautogui.click(cx, cy)
                    last_cookie_click = current_time

            # --- УЛУЧШЕНИЯ ---
            elif cls_name == "upgrade":
                if current_time - last_upgrade_sweep > CONFIG["UPGRADE_SWEEP_INTERVAL"]:
                    box_height = y2 - y1
                    box_width = x2 - x1
                    
                    sweep_top    = y1 + box_height * CONFIG["UPGRADE_TOP_SKIP"]
                    sweep_bottom = y2 - box_height * CONFIG["UPGRADE_BOTTOM_SKIP"]

                    if sweep_top < sweep_bottom:
                        cx = int((x1 + x2) / 2 + box_width * CONFIG["UPGRADE_X_OFFSET"])
                        y_points = np.linspace(sweep_bottom, sweep_top, num=CONFIG["CLICKS_PER_SWEEP"])

                        print(f"[+] Свайп улучшений: X={cx}, Y от {int(sweep_bottom)} до {int(sweep_top)}")
                        for y in y_points:
                            pyautogui.click(cx, int(y))
                            time.sleep(CONFIG["SWEEP_STEP_DELAY"])
                        
                        last_upgrade_sweep = time.time()

            # --- РЕКЛАМА ---
            elif cls_name == "reclama":
                if current_time - last_reclam_click > 2.0:
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    pyautogui.click(cx, cy)
                    print(f"[!] Закрыта реклама в ({cx}, {cy})")
                    last_reclam_click = current_time

        time.sleep(0.005)

except KeyboardInterrupt:
    print("\n[!] Остановка (Ctrl+C).")
except pyautogui.FailSafeException:
    print("\n[!] Сработала защита (мышь в углу).")
finally:
    listener.stop()
    print("Бот остановлен.")