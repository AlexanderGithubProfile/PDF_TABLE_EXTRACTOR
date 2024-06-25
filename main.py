import os
import logging
from typing import List, Union, Any
from utils_img_processing import extract_image_text
from utils_data_extract import extract_table_of_contents, check_pdf_pages
from utils_img_table_detection import image_loader, image_processing, is_table, show_image

# PIPELINE_START
#######################################################################
def main(self: Any, logger: logging.Logger) -> None:
    # Директории ввода и сохранения
    input_dir = 'INPUT_pdf_to_scan'
    output_dir = 'OUTPUT_tables'
    output_img_dir = '00_IMG_output'

    # Сканируем папку ввода
    for pdf_file in os.listdir(input_dir):
        pdf_path=os.path.join(input_dir, pdf_file)

        # Создание папки для каждого файла PDF в каталоге OUTPUT_tables
        output_dir = os.path.join(output_dir, os.path.splitext(pdf_file)[0])
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Извлечение таблиц из PDF")
        toc: List[Union[str, int]] = extract_table_of_contents(fr'{pdf_path}') # Ищем оглавление, извлекаем № стр. и имя для назв. табл. csv
        image_based: List[int] = check_pdf_pages(self, pdf_path, toc, output_dir, logger) # Извлеч. text-based и отдел. image-based стр. в список

        # Определим на каких изображениях таблицы
        image_list = []
        if len(image_based) > 0:
            logger.info(f'В стр. {", ".join(map(lambda x: str(x + 1), image_based))} изображение: ')
            for page_num in image_based:
                img = image_loader(page_num, pdf_path) # загрузчик
                right_indent=image_processing(img) # находим отступы в изображении
                result = is_table(right_indent, page_num, logger) # определяем есть ли таблица в изображении
                image_list.append(page_num) if result else None
                show_image(img, result, output_dir, page_num) # надпись на изображении о результате обнаружения таблицы

                self.progressbar_image.set((page_num + 1) / len(image_based))
                self.progressbar_image.update()


        # Извлечение PDF изображений
        logger.info('Обработка ..')
        for page in image_list:
            extract_image_text(pdf_path, page, output_dir, output_img_dir, logger)
        logger.info('Done !👍')
        os.remove(pdf_path)


if __name__ == "__main__":
    main()