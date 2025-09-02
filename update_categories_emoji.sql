-- Обновление категорий с эмодзи
-- Заменяем названия категорий на версии с эмодзи

UPDATE categories SET name = '🌇 Прогулки' WHERE name = 'Прогулки';
UPDATE categories SET name = '🏀 Спорт' WHERE name = 'Спорт';
UPDATE categories SET name = '🎬 Кино' WHERE name = 'Кино';
UPDATE categories SET name = '🔳 Культура' WHERE name = 'Культура';
UPDATE categories SET name = '🔭 Наука' WHERE name = 'Наука';
UPDATE categories SET name = '🪩 Вечеринки' WHERE name = 'Вечеринки';
UPDATE categories SET name = '🎸 Музыка' WHERE name = 'Музыка';
UPDATE categories SET name = '🎲 Настолки' WHERE name = 'Настолки';
UPDATE categories SET name = '🎮 Игры' WHERE name = 'Игры';
UPDATE categories SET name = '🧑‍💻 Бизнес' WHERE name = 'Бизнес';
UPDATE categories SET name = '🍽️ Кулинария' WHERE name = 'Кулинария';
UPDATE categories SET name = '🎙️ Стендап' WHERE name = 'Стендап';
UPDATE categories SET name = '✈️ Путешествия' WHERE name = 'Путешествия';
UPDATE categories SET name = '🎓 Образование' WHERE name = 'Образование';
UPDATE categories SET name = '📈 Карьера' WHERE name = 'Карьера';
UPDATE categories SET name = '💃 Танцы' WHERE name = 'Танцы';

-- Добавляем эмодзи к недостающим категориям
UPDATE categories SET name = '🚗 Авто' WHERE name = 'Авто';
UPDATE categories SET name = '💊 Здоровье' WHERE name = 'Здоровье';
UPDATE categories SET name = '📚 Книги' WHERE name = 'Книги';
UPDATE categories SET name = '👗 Мода' WHERE name = 'Мода';
UPDATE categories SET name = '💻 Технологии' WHERE name = 'Технологии';

-- Проверяем результат
SELECT id, name, description FROM categories ORDER BY name;
