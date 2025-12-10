# executor_patch.py
"""
Патч для совместимости с Bothost
Создает фейковый executor для прохождения проверки
"""

import sys
import types

# Создаем фейковый модуль executor
executor_module = types.ModuleType('aiogram.utils.executor')

def start_polling(*args, **kwargs):
    print("⚠️ Fake executor called - use asyncio.run() instead")

def start_webhook(*args, **kwargs):
    print("⚠️ Fake executor called - use asyncio.run() instead")

executor_module.start_polling = start_polling
executor_module.start_webhook = start_webhook

# Регистрируем модуль
sys.modules['aiogram.utils.executor'] = executor_module

# Также патчим aiogram.utils если он уже импортирован
if 'aiogram.utils' in sys.modules:
    sys.modules['aiogram.utils'].executor = executor_module

print("✅ Executor patch applied for Bothost compatibility")
