import os
import time
from datetime import datetime
import mss
import mss.tools

# Папка для сохранения скриншотов
save_dir = "screenshots"
os.makedirs(save_dir, exist_ok=True)

print("Начинаю делать скриншоты каждые 2 секунд...")
print("Нажмите Ctrl+C для остановки\n")

count = 0

try:
    # Инициализируем mss один раз для переиспользования ресурсов
    with mss.mss() as sct:
        while True:
            # Делаем скриншот главного экрана (монитор 1)
            # Если нужно снять все экраны вместе, используйте: sct.monitors[0]
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            # Формируем имя файла с датой и временем
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            filename = f"{save_dir}/screenshot_{timestamp}.png"

            # Сохраняем скриншот на диск
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=filename)
            
            count += 1
            print(f"[{count}] Сохранено: {filename}")

            # Ждём 2 секунд
            time.sleep(2)

except KeyboardInterrupt:
    print(f"\nОстановлено. Всего сделано скриншотов: {count}")
