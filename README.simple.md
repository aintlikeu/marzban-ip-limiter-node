# Marzban Node Agent

**Легковесный агент для экспорта логов Marzban с нод в центральный Redis сервер**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)

## 🎯 Описание

Marzban Node Agent - это простой и надежный агент для пересылки логов доступа Marzban с удаленных нод на центральный сервер через Redis. Работает в Docker контейнере и не требует сложной настройки.

### ✨ Ключевые особенности

- 🔄 **Мониторинг в реальном времени** - Отслеживание `access.log` 
- 🛡️ **Надежная доставка** - Буферизация и повторные попытки
- ⚡ **Простое развертывание** - Один Docker Compose файл
- 📊 **Встроенный мониторинг** - Health checks и логирование
- 🔐 **Минимальные зависимости** - Только Docker

## 🚀 Quick Start

### 1. Подготовка
```bash
# Клонируем репозиторий
git clone https://github.com/your-repo/marzban-node-agent.git
cd marzban-node-agent

# Создаем конфигурацию
cp .env.example .env
```

### 2. Настройка .env
```bash
# Обязательные параметры:
NODE_ID=node-001                # Уникальный ID ноды
NODE_NAME=My Marzban Node       # Имя ноды
CENTRAL_REDIS_URL=redis://:password@host:6379/0  # URL Redis сервера
```

### 3. Запуск
```bash
# Простое развертывание одной командой
./deploy.sh

# Или вручную
docker-compose up -d
```

### 4. Мониторинг
```bash
# Просмотр логов
docker-compose logs -f

# Проверка статуса
docker-compose ps

# Остановка
docker-compose down
```

## 📋 Управление

### Основные команды
```bash
# Запуск
docker-compose up -d

# Перезапуск
docker-compose restart

# Обновление
git pull && docker-compose up -d --build

# Просмотр логов
docker-compose logs -f node-agent

# Остановка
docker-compose down
```

### Конфигурация

Все настройки в файле `.env`:

```bash
# Основные настройки
NODE_ID=node-001                    # ID ноды
NODE_NAME=Germany-Frankfurt-01      # Имя ноды
CENTRAL_REDIS_URL=redis://:pass@host:6379/0  # Redis сервер

# Путь к логам (внутри контейнера)  
ACCESS_LOG_PATH=/app/access.log

# Производительность
BUFFER_SIZE=50          # Размер батча
FLUSH_INTERVAL=3.0      # Интервал отправки (сек)

# Подключение к Redis
REDIS_CONNECTION_TIMEOUT=5
REDIS_SOCKET_TIMEOUT=5
REDIS_MAX_CONNECTIONS=10
```

## 🔧 Требования

- **Docker** и **Docker Compose**
- **Доступ** к файлу `/var/lib/marzban-node/access.log`
- **Сетевое подключение** к центральному Redis серверу

## 📊 Мониторинг

### Health Check
```bash
# Проверка статуса через Docker
docker-compose ps

# Проверка health check
docker inspect marzban-node-agent | grep Health -A 10
```

### Логи
```bash
# Все логи
docker-compose logs -f

# Только агент
docker-compose logs -f node-agent

# Последние 100 строк
docker-compose logs --tail=100 node-agent
```

## 🐛 Troubleshooting

### Частые проблемы

1. **Permission denied на access.log**
   ```bash
   # Проверить права
   ls -la /var/lib/marzban-node/access.log
   
   # Исправить права (если нужно)
   sudo chmod 644 /var/lib/marzban-node/access.log
   ```

2. **Не подключается к Redis**
   ```bash
   # Проверить URL в .env
   # Формат: redis://:password@host:port/db
   ```

3. **Файл логов не найден**
   ```bash
   # Проверить путь в .env
   # Убедиться что файл существует на хосте
   ```

## 📝 Структура проекта

```
marzban-node-agent/
├── src/                    # Исходный код
├── .env.example           # Пример конфигурации
├── .env                   # Ваша конфигурация
├── docker-compose.yml     # Docker Compose
├── Dockerfile            # Docker образ
├── deploy.sh             # Скрипт развертывания
└── README.md             # Документация
```

## 📄 Лицензия

MIT License
