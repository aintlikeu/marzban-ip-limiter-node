# 🔧 Исправления установки

## Проблема
При запуске автоматической установки возникали ошибки:
- Устаревший атрибут `version` в docker-compose.yml
- Отсутствие файла `marzban.env`
- Зависимость от несуществующего сервиса Marzban

## ✅ Решение

### 1. Создан standalone docker-compose
Создан отдельный файл `docker/docker-compose.standalone.yml` только для node-agent без зависимостей от Marzban.

### 2. Исправлен install.sh
- Использует `docker-compose.standalone.yml` вместо основного
- Добавлена проверка конфигурации перед запуском
- Улучшена обработка ошибок

### 3. Добавлен скрипт конфигурации
Создан `scripts/configure.sh` для интерактивной настройки конфигурации.

### 4. Обновлены все скрипты
- `health-check.sh` - использует правильный compose файл
- `Makefile` - обновлены команды Docker
- Документация приведена в соответствие

## 🚀 Исправленная установка

### Вариант 1: Автоматическая установка

```bash
git clone https://github.com/your-repo/marzban-node-agent.git
cd marzban-node-agent
sudo ./scripts/install.sh
```

### Вариант 2: Ручная настройка

```bash
# Клонирование
git clone https://github.com/your-repo/marzban-node-agent.git
cd marzban-node-agent

# Интерактивная настройка
./scripts/configure.sh

# Сборка и запуск
docker build -t marzban-node-agent:latest -f docker/Dockerfile .
docker-compose -f docker/docker-compose.standalone.yml up -d
```

### Вариант 3: Только для разработки

```bash
# Настройка конфигурации
cp config/.env.example config/.env
nano config/.env

# Прямой запуск
python3 run.py
```

## 📁 Структура файлов Docker Compose

- `docker/docker-compose.yml` - Полная версия с Marzban (для комплексного развертывания)
- `docker/docker-compose.standalone.yml` - Только node-agent (для установки на существующих серверах)

## ⚙️ Конфигурация

### Минимальная конфигурация в .env:
```bash
NODE_ID=your-node-001
NODE_NAME=Your Node Name
CENTRAL_REDIS_URL=redis://your-redis-server:6379/0
ACCESS_LOG_PATH=/var/lib/marzban/access.log
```

### Проверка конфигурации:
```bash
# Валидация
make config-validate

# Тест Redis подключения  
make debug-redis

# Полная диагностика
./scripts/health-check.sh
```

## 🔍 Диагностика проблем

### Проверка файлов
```bash
# Проверить структуру проекта
find . -name "*.yml" -o -name "*.env*"

# Проверить права доступа
ls -la scripts/*.sh

# Проверить Docker образы
docker images | grep marzban-node-agent
```

### Логи и отладка
```bash
# Логи контейнера
docker-compose -f docker/docker-compose.standalone.yml logs -f

# Статус сервиса
systemctl status marzban-node-agent

# Проверка Redis
redis-cli -u "redis://your-server:6379/0" ping
```

**Теперь установка должна работать без ошибок!** ✅
