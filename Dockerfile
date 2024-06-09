# Используем официальный образ Python в качестве базового
FROM python:slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем репозиторий PIP
RUN pip install --upgrade pip

# Копируем файлы requirements.txt и app.py в контейнер
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы (шаблоны) в контейнер
COPY . .

# Открываем порт для доступа к Flask-приложению
EXPOSE 5001

# Команда для запуска приложения
CMD ["python", "app.py"]
