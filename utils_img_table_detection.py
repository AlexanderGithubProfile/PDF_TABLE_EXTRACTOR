import io
import os
import fitz
import pytesseract
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN
from PIL import Image, ImageDraw, ImageFont

# Бинаризируем изображение для тесеракта
def image_loader(page_num, pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num) # Пройти по всем страницам

    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list):
        xref = img[0]  # Получить ссылку на изображение
        base_image = doc.extract_image(xref)  # Извлечь изображение
        image_bytes = base_image["image"]  # Получить байты изображения
        image = Image.open(io.BytesIO(image_bytes))
        return image

# Основной модуль извлечения текста из изображения
def image_processing(img):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    cong = r'--oem 3 --psm 6 outputbase digits'
    boxes = pytesseract.image_to_data(img, config=cong)
    right_side = []
    for i, line in enumerate(boxes.splitlines()):
        if i != 0:
            b = line.split()
            if len(b) == 12:
                right_side.append(int(b[6]) + int(b[8]))
                x, y, w, h = int(b[6]), int(b[7]), int(b[8]), int(b[9])
                draw = ImageDraw.Draw(img)
                draw.rectangle([(x, y), (w + x, h + y)], outline=(0, 10, 255), width=3)
                #font = ImageFont.truetype("arial.ttf", 20)
    return right_side

# Обнаружение таблицы на изображении. Метод кластеров
def is_table(right_indent, page_num, logger):
    X = np.array(right_indent).reshape(-1, 1) # Список данных в массив numpy
    #db = HDBSCAN(min_samples=20, min_cluster_size=30).fit(X)
    db = DBSCAN(eps=50, min_samples=20).fit(X) # Применяем DBSCAN для кластеризации, eps - расстояние
    labels = db.labels_

    # Количество кластеров (исключая шум)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    result = "Таблица обнаружена" if n_clusters >= 2 else "Таблица отсутствует"
    logger.info(f'Стр. №{page_num + 1}: {result}')
    return n_clusters >= 2

#Создание изображения для текста
def show_image(img, result, output_dir, page_num):
    text = "table detected" if result else "table not detected"

    # Создание текста "table detected", инициализация параметров, вычисление размеров и т.п.
    font = ImageFont.truetype(font="arial.ttf", size=130)  # Путь к шрифту и размер
    bbox = font.getbbox(text)
    text_width, text_height = (bbox[2] - bbox[0]) + 100, (bbox[3] - bbox[1]) + 100

    text_image = Image.new('RGBA', (text_width, text_height), (255, 255, 255, 0))
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text((0, 0), text, fill="darkred", font=font)
    rotated_text_image = text_image.rotate(0, expand=1) # Поворот текста

    # Напишем результат на изображении есть ли таблица для контроля
    img.paste(rotated_text_image, ((img.width - rotated_text_image.width), img.height - rotated_text_image.height), rotated_text_image)
    os.makedirs(f'{output_dir}/00_IMG_output/', exist_ok=True)
    img.save(f"{output_dir}/00_IMG_output/{page_num}_pdf_image.png")
    #img.show()
