#!/usr/bin/env python3
"""
DEBUG: Что происходит на сервере с timezone
"""

from datetime import datetime, timezone, timedelta
import os

print("=== SERVER TIMEZONE DEBUG ===")

# Проверяем системные настройки
print(f"🖥️  СИСТЕМА:")
print(f"   TZ environment: {os.environ.get('TZ', 'не установлен')}")

# Проверяем Python timezone
import time
print(f"   System timezone: {time.tzname}")

# Проверяем ZoneInfo
try:
    from zoneinfo import ZoneInfo
    print("✅ ZoneInfo доступен")
    
    # Тестируем проблемный случай
    user_input = "10:37"
    dt = datetime.strptime(f"2025-09-02 {user_input}", "%Y-%m-%d %H:%M")
    print(f"\n📱 Пользователь ввёл: {user_input} МСК")
    print(f"📅 После strptime: {dt}")
    
    # Применяем МСК timezone  
    msk = ZoneInfo("Europe/Moscow")
    dt_msk = dt.replace(tzinfo=msk)
    print(f"🇷🇺 С МСК timezone: {dt_msk}")
    
    # Конвертируем в UTC
    utc = ZoneInfo("UTC")
    dt_utc = dt_msk.astimezone(utc)
    print(f"🌍 В UTC: {dt_utc}")
    
    # Убираем timezone для сохранения в БД
    dt_naive_utc = dt_utc.replace(tzinfo=None)
    print(f"💾 Naive UTC для БД: {dt_naive_utc}")
    
    if dt_naive_utc.hour == 7:  # 10:37 - 3 = 07:37
        print("✅ ZoneInfo работает правильно")
    elif dt_naive_utc.hour == 13:  # 10:37 + 3 = 13:37
        print("❌ ZoneInfo ДОБАВЛЯЕТ часы вместо вычитания!")
        print("   Это означает что Europe/Moscow настроен как UTC-3 вместо UTC+3")
    else:
        print(f"❓ Неожиданный результат: {dt_naive_utc.hour}:37")
        
    # Проверим timezone offset
    msk_offset = msk.utcoffset(dt)
    print(f"🔢 Moscow UTC offset: {msk_offset}")
    
except ImportError:
    print("❌ ZoneInfo недоступен - будет использоваться fallback")
    
    # Тестируем fallback
    user_input = "10:37"
    dt = datetime.strptime(f"2025-09-02 {user_input}", "%Y-%m-%d %H:%M")
    print(f"\n📱 Пользователь ввёл: {user_input} МСК")
    print(f"📅 После strptime: {dt}")
    
    # Fallback: вычитаем 3 часа
    dt_utc = dt - timedelta(hours=3)
    print(f"🌍 После fallback (-3h): {dt_utc}")
    
    if dt_utc.hour == 7:
        print("✅ Fallback работает правильно")
    else:
        print("❌ Fallback работает неправильно")

print(f"\n🎯 ЗАКЛЮЧЕНИЕ:")
print("Если в БД время 13:37 при вводе 10:37:")
print("• ZoneInfo может работать в обратную сторону на сервере")  
print("• Или timezone данные сервера повреждены")
print("• Или есть другая проблема в коде")

# Проверим что сейчас в системе
now_naive = datetime.now()
now_utc = datetime.now(timezone.utc)
print(f"\n⏰ ВРЕМЯ СЕЙЧАС:")
print(f"   Системное: {now_naive}")
print(f"   UTC: {now_utc}")
print(f"   Разница: {(now_naive - now_utc.replace(tzinfo=None)).total_seconds() / 3600:.1f} часов")
