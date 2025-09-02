-- Исправление timezone в существующих данных
-- Конвертируем МСК в UTC (вычитаем 3 часа)

-- 1. Исправляем таблицу posts
UPDATE posts 
SET 
    created_at = created_at - INTERVAL '3 hours',
    updated_at = updated_at - INTERVAL '3 hours'
WHERE created_at IS NOT NULL;

-- 2. Исправляем таблицу users (если есть)
UPDATE users 
SET 
    created_at = created_at - INTERVAL '3 hours',
    updated_at = updated_at - INTERVAL '3 hours'  
WHERE created_at IS NOT NULL;

-- 3. Исправляем таблицу categories (если есть)
UPDATE categories 
SET 
    created_at = created_at - INTERVAL '3 hours',
    updated_at = updated_at - INTERVAL '3 hours'
WHERE created_at IS NOT NULL;

-- 4. Исправляем таблицу moderation_records (если есть)
UPDATE moderation_records
SET 
    created_at = created_at - INTERVAL '3 hours',
    updated_at = updated_at - INTERVAL '3 hours'
WHERE created_at IS NOT NULL;

-- 5. Исправляем published_at в posts (если оно тоже в МСК)
UPDATE posts 
SET published_at = published_at - INTERVAL '3 hours'
WHERE published_at IS NOT NULL;

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
