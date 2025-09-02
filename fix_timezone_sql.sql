-- Исправление timezone в существующих данных  
-- Конвертируем event_at из UTC в МСК (прибавляем 3 часа)

-- 1. Исправляем event_at в posts (из UTC в МСК)
UPDATE posts 
SET event_at = event_at + INTERVAL '3 hours'
WHERE event_at IS NOT NULL;

-- Теперь ВСЁ в БД будет в МСК
-- created_at уже в МСК (правильно)
-- event_at теперь тоже в МСК (исправлено)

-- Проверяем результат
SELECT 
    id,
    title,
    created_at,
    event_at,
    published_at,
    CASE 
        WHEN event_at > created_at THEN 'OK'
        ELSE 'ПРОБЛЕМА'
    END as status
FROM posts 
WHERE event_at IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
