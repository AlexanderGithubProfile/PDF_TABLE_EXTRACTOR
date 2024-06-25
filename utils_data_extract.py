import os
import re
import fitz
import tabula
import logging
import pdfplumber
import pandas as pd
from typing import Dict, List, Union

def extract_table_of_contents(pdf_path: str) -> Dict[int, str]:
    """Ищем оглавление, достаем номера страниц и имя для назв таблиц"""
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                index_ = {} # Список оглавления
                pattern = r'[a-zA-Z\s]+\.{3,}\s*\d+' # Ищем строки - Имя ............. цифра
                toc = re.findall(pattern, text)
                if len(toc) > 0:
                    for i in toc:
                        value, key = re.split(r'\.{3,}', i)
                        index_[int(key.strip())] = (value.strip())
                    return index_

def is_text_page(page: fitz.Page) -> bool:
    """True/ False что страница - изображение / что на странице таблица"""
    text = page.get_text("text")
    return bool(text.strip())

def has_tables(pdf_path: str, page_num: int) -> List[pd.DataFrame]:
    """Функция для подтверждения текстовой PDF таблицы"""
    tables = tabula.read_pdf(pdf_path, pages=page_num + 1, multiple_tables=True, encoding='windows-1252')
    return tables

# Сохранение таблиц
def export_tables_to_csv(tables: List[pd.DataFrame], page_num: int, title: str, output_dir: str) -> None:
    """Сохранение файла в csv"""
    title_clean = re.sub(r'\W+', '_', title)
    for i, table in enumerate(tables):
        output_file = os.path.join(output_dir, f"{page_num}_{title_clean.upper()}_{i + 1}.csv")
        table.to_csv(output_file, index=False)

def check_page_number(pdf_path: str, number: int) -> Union[int, None]:
    """Поиск номера страницы по номеру на PDF странице для создания имени извлеченной таблицы"""
    with pdfplumber.open(pdf_path) as pdf:
        page_text = pdf.pages[number].extract_text()
        # Найти номер страницы в конце текста с пробелами перед ним
        match = re.search(r'\s+(\d+)\s*$', page_text)
        if match:
            page_number = int(match.group(1))
            return page_number
        else:
            print("\nНомер страницы не найден.")

def check_pdf_pages(self, pdf_path: str, toc: Dict[int, str], output_dir: str, logger: logging.Logger) -> List[int]:
    """Сортировка text-based и image-based страниц"""
    # Уровень логирования для org.apache.fontbox.ttf
    logging.getLogger("org.apache.fontbox.ttf").setLevel(logging.ERROR)
    # Инициализация списока стр. с изобр. в PDF и директории сохран.
    image_based = []
    os.makedirs(output_dir, exist_ok=True)

    pdf_document = fitz.open(pdf_path) # Открываем PDF-документ
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        if is_text_page(page):
            tables = has_tables(pdf_path, page_num)
            if tables:

                # Извлечение текст-таблиц, сохранение
                doc_number = check_page_number(pdf_path, page_num)
                title = toc.get(doc_number, f"NO_NAME_CHECK_PDF_PAGE_{page_num}")
                logger.info(f'csv: сохранение..Стр.{page_num}') if title.startswith("NO_NAME_CHECK_PDF_PAGE_") else logger.info(f'csv: {title}')
                export_tables_to_csv(tables, doc_number, title, output_dir)
        else:
            # Добавляем в список PDF c изображением
            image_based.append(page_num)

        percent = (page_num + 1) / len(pdf_document)
        self.progressbar.set(percent)
        self.progressbar.update()

    # Выводим линию прогресса
    return image_based