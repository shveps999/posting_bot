-- БЭКАП перед исправлением timezone
-- Выполните ЭТО СНАЧАЛА!

-- Создаем таблицу для бэкапа
CREATE TABLE posts_backup AS 
SELECT * FROM posts;

CREATE TABLE users_backup AS 
SELECT * FROM users;

-- Проверяем что бэкап создался
SELECT COUNT(*) as posts_backup_count FROM posts_backup;
SELECT COUNT(*) as users_backup_count FROM users_backup;

-- Показываем текущие данные ДО исправления
SELECT 
    id,
    title,
    created_at,
    event_at,
    (event_at - created_at) as time_diff
FROM posts 
WHERE event_at IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;
