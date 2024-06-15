FROM python:3.10-slim-bullseye

# Отключаем кеширование внутри контейнеров и буферизацию для логов
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY . /app/

# Загружаем шрифт
RUN mkdir -p /usr/share/fonts/arial-narrow
COPY /assets/arialnarrow.ttf /usr/share/fonts/arial-narrow
RUN apt-get update && apt-get install -y fontconfig
RUN fc-cache -f -v

## Устанавливаем необходимые пакеты, Tesseract и Java
RUN apt-get update && apt-get install -y tesseract-ocr
RUN pip install --upgrade pip
RUN apt-get update && \
    apt-get install -y \
        openjdk-11-jdk

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Объявление переменных окружения
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
ENV PATH=$PATH:$JAVA_HOME/bin:/usr/lib/jvm/java-11-openjdk-amd64/bin
ENV PATH=${PATH}:/usr/local/bin/tesseract

# Запуск приложения
CMD ["python", "service_gui.py"]
