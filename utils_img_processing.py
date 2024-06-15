import io
import os
import csv
import sys
import fitz
import asyncio
import pytesseract
from PIL import Image
from g4f.client import Client as G4FClient

# Исключение ошибки клиента для чат-гпт
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Обработка таблиц в LLM
async def text_converting(prompt_text):
    client = G4FClient()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f'''Если бы я передал тебе текст и попросил вычленить из него таблицу и передать без колонки примечания в остальном неизменной, чтобы удобно ее сохранить в csv, как бы она выглядела, данные передай в виде строк, первой строкой должны заголовок для колонок то есть где наименование name а где значения ставь период к которому они соответствуют, разделяй значения между колонками через ';' а в конце строки '\n' и без ';', в числах разделители порядковых знаков убери,а если число в скшбках ( ) сделай его отрицательным а скобки убери, если вместо значения черта(прочерк) ставь 0, ответ начни с '\n[' а закончи с \n], вот текст: 
                                                "{prompt_text}" 
                                                '''}],)
    reminder_text = response.choices[0].message.content

    # Если сервис GPT не ответил повтор запроса
    if not reminder_text.strip():
        return await text_converting(prompt_text)
    else:
        return reminder_text

# Извлечение инф. из PDF изображений
def extract_image_text(pdf_path, page_number, output_dir, output_img_dir, logger):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number) # Пройти по всем страницам

    image_list = page.get_images(full=True)  # Получить список изображений на странице
    page_text = ''
    for img_index, img in enumerate(image_list):
        xref = img[0]  # Получить ссылку на изображение
        base_image = doc.extract_image(xref)  # Извлечь изображение

        image_bytes = base_image["image"]  # Получить байты изображения
        image = Image.open(io.BytesIO(image_bytes))  # Открыть изображение с помощью PIL

        text = pytesseract.image_to_string(image)  # Распознать текст с изображения
        page_text += text.strip()

    doc.close()
    data = asyncio.run(text_converting(page_text))
    convert_and_save_data(data, page_number, output_dir, output_img_dir)
    logger.info(f'Стр.{page_number + 1} обработана и сохранена')

# Сохранение таблиц из PDF изображений
def convert_and_save_data(data, page_number, output_dir, output_img_dir):
    data = data.strip("[] \n").strip('[')
    lines = data.split("\n")
    os.makedirs(f'{output_dir}', exist_ok=True)
    with open(f"{output_dir}/{output_img_dir}/{page_number}_pdf.csv", "w", newline='', encoding='utf-8-sig') as csvfile:
        csvwriter = csv.writer(csvfile)
        for line in lines:
            row = line.split(";")
            csvwriter.writerow(row)
