import os
import random
import shutil
from pathlib import Path

# --- НАСТРОЙКИ ---
SOURCE_DIR = Path("dataset_raw")  # Откуда берем
TARGET_DIR = Path("dataset")      # Куда складываем (создастся автоматически)
TRAIN_RATIO = 0.8                 # 80% на обучение

# Расширения картинок, которые мы ищем
IMG_EXTENSIONS = {".jpg", ".jpeg", ".png"}

def main():
    if not SOURCE_DIR.exists():
        print(f"❌ Ошибка: Папка {SOURCE_DIR} не найдена!")
        return

    # 1. Создаем структуру папок
    paths = [
        TARGET_DIR / "images" / "train",
        TARGET_DIR / "images" / "val",
        TARGET_DIR / "labels" / "train",
        TARGET_DIR / "labels" / "val",
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
    print("✅ Структура папок создана.")

    # 2. Собираем список всех картинок
    all_images = [
        f for f in SOURCE_DIR.iterdir() 
        if f.suffix.lower() in IMG_EXTENSIONS
    ]

    if not all_images:
        print("❌ Картинки не найдены!")
        return

    # Перемешиваем список, чтобы классы распределились равномерно
    random.seed(42)  # Фиксируем seed для повторяемости
    random.shuffle(all_images)

    # 3. Вычисляем, где заканчивается train
    split_index = int(len(all_images) * TRAIN_RATIO)
    train_images = all_images[:split_index]
    val_images = all_images[split_index:]

    print(f"📊 Всего картинок: {len(all_images)}")
    print(f"   ➔ В train: {len(train_images)}")
    print(f"   ➔ В val:   {len(val_images)}")

    # 4. Копируем файлы
    def copy_files(image_list, split_name):
        copied = 0
        missing_labels = 0
        for img_path in image_list:
            # Путь для картинки
            dest_img = TARGET_DIR / "images" / split_name / img_path.name
            shutil.copy2(img_path, dest_img)

            # Ищем соответствующий .txt файл
            label_path = img_path.with_suffix(".txt")
            if label_path.exists():
                dest_label = TARGET_DIR / "labels" / split_name / label_path.name
                shutil.copy2(label_path, dest_label)
                copied += 1
            else:
                missing_labels += 1
        
        return copied, missing_labels

    print("⏳ Копирую train...")
    train_copied, train_missing = copy_files(train_images, "train")
    
    print("⏳ Копирую val...")
    val_copied, val_missing = copy_files(val_images, "val")

    print(f"✅ Готово! Успешно скопировано пар: {train_copied + val_copied}")
    if train_missing + val_missing > 0:
        print(f"⚠ Внимание: для {train_missing + val_missing} картинок не нашлось .txt файлов.")

    # 5. Генерируем data.yaml
    yaml_content = f"""path: {TARGET_DIR.absolute()}
train: images/train
val: images/val

names:
  0: game
  1: upgrade
"""
    yaml_path = TARGET_DIR / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    print(f"✅ Файл data.yaml создан по пути: {yaml_path}")

if __name__ == "__main__":
    main()