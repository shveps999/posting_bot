-- Добавляем поле display_name к категориям
-- 1. Добавляем новое поле
ALTER TABLE categories ADD COLUMN display_name VARCHAR(255);

-- 2. Заполняем display_name эмодзи + название, а name делаем чистым
UPDATE categories SET display_name = name WHERE display_name IS NULL;

-- 3. Обновляем display_name с эмодзи, а name оставляем чистым
UPDATE categories SET 
    display_name = '🌇 Прогулки',
    name = 'Прогулки' 
WHERE name LIKE '%Прогулки%';

UPDATE categories SET 
    display_name = '🏀 Спорт',
    name = 'Спорт' 
WHERE name LIKE '%Спорт%';

UPDATE categories SET 
    display_name = '🎬 Кино',
    name = 'Кино' 
WHERE name LIKE '%Кино%';

UPDATE categories SET 
    display_name = '🔳 Культура',
    name = 'Культура' 
WHERE name LIKE '%Культура%';

UPDATE categories SET 
    display_name = '🔭 Наука',
    name = 'Наука' 
WHERE name LIKE '%Наука%';

UPDATE categories SET 
    display_name = '🪩 Вечеринки',
    name = 'Вечеринки' 
WHERE name LIKE '%Вечеринки%';

UPDATE categories SET 
    display_name = '🎸 Музыка',
    name = 'Музыка' 
WHERE name LIKE '%Музыка%';

UPDATE categories SET 
    display_name = '🎲 Настолки',
    name = 'Настолки' 
WHERE name LIKE '%Настолки%';

UPDATE categories SET 
    display_name = '🎮 Игры',
    name = 'Игры' 
WHERE name LIKE '%Игры%';

UPDATE categories SET 
    display_name = '🧑‍💻 Бизнес',
    name = 'Бизнес' 
WHERE name LIKE '%Бизнес%';

UPDATE categories SET 
    display_name = '🍽️ Кулинария',
    name = 'Кулинария' 
WHERE name LIKE '%Кулинария%';

UPDATE categories SET 
    display_name = '🎙️ Стендап',
    name = 'Стендап' 
WHERE name LIKE '%Стендап%';

UPDATE categories SET 
    display_name = '✈️ Путешествия',
    name = 'Путешествия' 
WHERE name LIKE '%Путешествия%';

UPDATE categories SET 
    display_name = '🎓 Образование',
    name = 'Образование' 
WHERE name LIKE '%Образование%';

UPDATE categories SET 
    display_name = '📈 Карьера',
    name = 'Карьера' 
WHERE name LIKE '%Карьера%';

UPDATE categories SET 
    display_name = '💃 Танцы',
    name = 'Танцы' 
WHERE name LIKE '%Танцы%';

UPDATE categories SET 
    display_name = '🚗 Авто',
    name = 'Авто' 
WHERE name LIKE '%Авто%';

UPDATE categories SET 
    display_name = '💊 Здоровье',
    name = 'Здоровье' 
WHERE name LIKE '%Здоровье%';

UPDATE categories SET 
    display_name = '📚 Книги',
    name = 'Книги' 
WHERE name LIKE '%Книги%';

UPDATE categories SET 
    display_name = '👗 Мода',
    name = 'Мода' 
WHERE name LIKE '%Мода%';

UPDATE categories SET 
    display_name = '💻 Технологии',
    name = 'Технологии' 
WHERE name LIKE '%Технологии%';

-- 4. Проверяем результат
SELECT id, name, display_name, description FROM categories ORDER BY name;

-- 5. Устанавливаем NOT NULL для display_name (опционально)
-- ALTER TABLE categories ALTER COLUMN display_name SET NOT NULL;

