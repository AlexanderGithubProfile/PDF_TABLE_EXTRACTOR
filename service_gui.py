import os
import sys
import shutil
import logging
import warnings
import threading
from pathlib import Path

import tkinter as tk
import customtkinter as ctk
from tkinterdnd2 import DND_FILES
from tkinterdnd2 import TkinterDnD
from main import main as pdf_starter

if sys.platform == 'win32':
    from ctypes import windll, byref, sizeof, c_int

logging.basicConfig(level=logging.ERROR)
warnings.filterwarnings("ignore", module="customtkinter")

def relative_to_assets(path: str) -> Path:
    ASSETS_PATH = Path(__file__).parent / "assets"
    return ASSETS_PATH / Path(path)

# Логирование
class TextHandler(logging.Handler):
    def __init__(self, label_widget):
        super().__init__()
        self.label_widget = label_widget

    def emit(self, record):
        msg = self.format(record)
        if len(msg) > 33:  # обрезаем лог
            msg = msg[:33 - 3] + "..."
        self.label_widget.configure(text=msg)

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, mode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mode = mode
        self.TkdndVersion = TkinterDnD._require(self)
        self.title('')
        self.after(201, lambda: self.iconbitmap(relative_to_assets('Logo.ico')))

        self.config(bg="white" if self.mode == 'Light' else "black")

        # Создаем центральный фрейм
        self.entry_frame = ctk.CTkFrame(self, corner_radius=10,
                                        fg_color="#E8E8E8" if self.mode == 'Light' else "#171717",
                                        bg_color="white" if self.mode == 'Light' else "#171717",
                                        border_width=0,
                                        border_color='gray')
        self.entry_frame.pack(padx=10, pady=(0, 10), fill=tk.BOTH, expand=True)
        image_2 = tk.PhotoImage(file=relative_to_assets("image_2.png" if self.mode == 'Light' else 'image_2_d.png'))

        # Frame для Drag & Drop
        self.file_ = tk.Entry(self.entry_frame,
                              bg='white' if self.mode == 'Light' else 'black',
                              borderwidth=0,
                              highlightthickness=0)
        self.file_.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 60))
        self.title = ctk.CTkLabel(self.file_, image=image_2, text="")
        self.title.pack(padx=10, pady=(15, 5), fill=tk.X, expand=True)

        # Настройка Drag & Drop виджета
        self.file_.drop_target_register(DND_FILES)
        self.file_.dnd_bind("<<Drop>>", self.get_path)
        self.icons = tk.Canvas(master=self.entry_frame,
                               width=290,
                               bg='#E8E8E8' if self.mode == 'Light' else '#171717',
                               highlightthickness=0)
        self.icons.place(x=10, y=457)

        # Иконки прогрессбара
        self.image_image_1 = tk.PhotoImage(file=relative_to_assets("image_1.png" if self.mode == 'Light' else 'image_1_d.png'))
        image_1 = self.icons.create_image(150, 70, image=self.image_image_1)

        # Настройка прогрессбара
        self.progressbar = ctk.CTkProgressBar(master=self.entry_frame,
                                              height=10,
                                              fg_color='white' if self.mode == 'Light' else 'black',
                                              progress_color='#2A72E6' if self.mode == 'Light' else '#E54B3D')
        self.progressbar.pack(padx=(73, 20), pady=(0, 70), fill=tk.X)
        self.progressbar.set(0)
        self.progressbar_image = ctk.CTkProgressBar(master=self.entry_frame,
                                                    height=10,
                                                    fg_color='white' if self.mode == 'Light' else 'black',
                                                    progress_color='#2A72E6' if self.mode == 'Light' else '#E54B3D')
        self.progressbar_image.set(0)
        self.progressbar_image.pack(padx=(73, 20), pady=(0, 15), fill=tk.X)

        # Настройка логирования
        self.log_label = ctk.CTkLabel(self, text="Ожидание файла..",
                                      fg_color=None,
                                      text_color="#A7A7A7",
                                      font=("Arial", 19 * -1),
                                      bg_color="white" if self.mode == 'Light' else 'black',
                                      anchor="nw")
        self.log_label.pack(padx=20, pady=(10, 5), fill=tk.X)

        text_handler = TextHandler(self.log_label)
        logging.getLogger().addHandler(text_handler)
        logging.getLogger().setLevel(logging.INFO)



    # Создание директорий ввода и копирование
    def make_dir_and_start_process(self, file_path):
        file_name = os.path.basename(file_path)
        input_dir = os.path.join(os.path.dirname(__file__), "INPUT_pdf_to_scan")
        os.makedirs(input_dir, exist_ok=True)

        destination_path = os.path.join(input_dir, file_name)
        shutil.copy(file_path, destination_path)
        pdf_starter(self, logging.getLogger())

        # Запуск процесса в фоновом потоке
        threading.Thread(target=pdf_starter, args=(self, logging.getLogger())).start()
        os.startfile(os.path.realpath("OUTPUT_tables"))

    def get_path(self, event):
        logging.info("Начало процесса получения пути файла")
        file_path = event.data.strip('{}')  # Удаление фигурных скобок

        if os.path.isfile(file_path) and file_path.endswith('.pdf'):
            threading.Thread(target=self.make_dir_and_start_process, args=(file_path,)).start()
        else:
            logging.info("Передан не файл PDF")



def main():
    mode = 'Light' # Dark Light
    master = App(mode)
    master.geometry("326x665")
    master.resizable(width=False, height=False)
    import pywinstyles

    #Изменение цвета заголовка окна
    if sys.platform == 'win32':
        from ctypes import windll, byref, sizeof, c_int
        # Получаем идентификатор окна
        HWND = windll.user32.GetParent(master.winfo_id())
        title_bar_color = 0x000000 if mode == 'Dark' else 0xFFFFFF # Черный цвет окна
        title_text_color = 0xFFFFFF if mode == 'Dark' else 0x000000 # Белый цвет текста

        windll.dwmapi.DwmSetWindowAttribute(HWND, 35, byref(c_int(title_bar_color)), sizeof(c_int))
        windll.dwmapi.DwmSetWindowAttribute(HWND, 36, byref(c_int(title_text_color)), sizeof(c_int))
        #pywinstyles.apply_style(master, 'transparent')

    master.mainloop()

if __name__ == '__main__':
    main()