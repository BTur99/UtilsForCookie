import os
import shutil
import random
from pathlib import Path

def split_dataset(image_dir, label_dir, output_dir, train_ratio=0.8):
    # Превращаем пути в объекты Path для удобства
    img_path = Path(image_dir)
    lbl_path = Path(label_dir)
    out_path = Path(output_dir)

    # Расширения картинок, которые ищем (можно дополнить)
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

    # 1. Собираем все изображения
    images = [f for f in img_path.iterdir() if f.suffix.lower() in valid_extensions]
    
    # 2. Ищем только те пары, где есть и картинка, и текстовый файл лабела
    valid_pairs = []
    for img in images:
        lbl = lbl_path / f"{img.stem}.txt"
        if lbl.exists():
            valid_pairs.append((img, lbl))
        else:
            print(f"⚠️ Пропущено: для {img.name} не найден файл разметки.")

    if not valid_pairs:
        print("❌ Не найдено пар изображений и файлов разметки с одинаковыми именами!")
        return

    # Перемешиваем датасет для случайного распределения
    random.shuffle(valid_pairs)

    # Считаем точку разделения (80%)
    split_idx = int(len(valid_pairs) * train_ratio)
    train_pairs = valid_pairs[:split_idx]
    val_pairs = valid_pairs[split_idx:]

    # Функция для безопасного копирования файлов по новым папкам
    def move_files(pairs, subset):
        img_out = out_path / subset / 'images'
        lbl_out = out_path / subset / 'labels'
        
        # Создаем структуры папок (output/train/images и т.д.)
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        for img, lbl in pairs:
            # Если нужно переместить вместо копирования, замените shutil.copy на shutil.move
            shutil.copy(img, img_out / img.name)
            shutil.copy(lbl, lbl_out / lbl.name)

    # Раскладываем файлы
    print(f"📦 Всего найдено валидных пар: {len(valid_pairs)}")
    print(f"⏳ Копирование в train ({len(train_pairs)} шт.)...")
    move_files(train_pairs, 'train')
    
    print(f"⏳ Копирование в val ({len(val_pairs)} шт.)...")
    move_files(val_pairs, 'val')

    print(f"🎉 Готово! Проверьте папку: {out_path.resolve()}")

# --- НАСТРОЙКА ПУТЕЙ ---
if __name__ == '__main__':
    # Укажите здесь свои папки:
    SOURCE_IMAGES = "dataset_raw"  # Где сейчас лежат картинки
    SOURCE_LABELS = "dataset_raw"  # Где сейчас лежат .txt файлы
    OUTPUT_FOLDER = "./dataset_splitted"    # Куда сохранить результат (создастся сама)

    split_dataset(SOURCE_IMAGES, SOURCE_LABELS, OUTPUT_FOLDER)