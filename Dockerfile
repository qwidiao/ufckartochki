FROM python:3.11-slim

WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект (включая executor_patch.py)
COPY . .

# Проверка с использованием нашего патча
RUN python -c "import executor_patch; from aiogram.utils import executor; print('✅ Проверка Bothost пройдена!')"

# Запуск бота
CMD ["python", "main.py"]
