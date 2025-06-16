# Конфигурация Marzban Node Agent

Подробное руководство по настройке и конфигурации агента для различных сценариев использования.

## 📋 Обзор конфигурации

Конфигурация агента осуществляется через переменные окружения, которые можно задать:
- В файле `.env`
- Через переменные окружения системы
- В docker-compose.yml
- Через systemd environment файлы

## ⚙️ Основные параметры

### Обязательные параметры

#### NODE_ID
```bash
NODE_ID=unique-node-identifier
```
- **Описание**: Уникальный идентификатор ноды в рамках всей сети
- **Формат**: Строка, только буквы, цифры, дефисы
- **Примеры**: `germany-01`, `usa-west-001`, `backup-node`
- **Важно**: Должен быть уникальным для каждой ноды

#### NODE_NAME  
```bash
NODE_NAME=Germany-Frankfurt-01
```
- **Описание**: Человекочитаемое имя ноды для отображения в логах
- **Формат**: Любая строка
- **Примеры**: `Germany Frankfurt 01`, `US West Coast`, `Backup Server`

#### CENTRAL_REDIS_URL
```bash
CENTRAL_REDIS_URL=redis://hostname:6379/0
```
- **Описание**: URL подключения к центральному Redis серверу
- **Форматы**:
  ```bash
  # Простое подключение
  redis://hostname:6379/0
  
  # С паролем
  redis://:password@hostname:6379/0
  
  # С пользователем и паролем
  redis://username:password@hostname:6379/0
  
  # SSL подключение
  rediss://username:password@hostname:6380/0
  ```

#### ACCESS_LOG_PATH
```bash
ACCESS_LOG_PATH=/var/lib/marzban-node/access.log
```
- **Описание**: Полный путь к файлу логов Marzban
- **По умолчанию**: `/var/lib/marzban-node/access.log`
- **Примеры**:
  ```bash
  /var/lib/marzban-node/access.log          # Стандартная установка
  /opt/marzban/logs/access.log         # Кастомная установка
  /home/user/marzban/access.log        # Пользовательская установка
  ```

### Параметры производительности

#### BATCH_SIZE
```bash
BATCH_SIZE=50
```
- **Описание**: Количество логов в одном батче перед отправкой
- **По умолчанию**: `50`
- **Диапазон**: 1-1000
- **Рекомендации**:
  - **Низкая нагрузка** (< 100 подключений/час): 10-25
  - **Средняя нагрузка** (100-1000 подключений/час): 50-100
  - **Высокая нагрузка** (> 1000 подключений/час): 100-500

#### FLUSH_INTERVAL
```bash
FLUSH_INTERVAL=3.0
```
- **Описание**: Максимальное время ожидания перед принудительной отправкой батча (секунды)
- **По умолчанию**: `3.0`
- **Диапазон**: 0.1-60.0
- **Рекомендации**:
  - **Реальное время**: 1.0-2.0 секунд
  - **Сбалансированный**: 3.0-5.0 секунд
  - **Экономичный**: 10.0-30.0 секунд

### Параметры надежности

#### MAX_RETRIES
```bash
MAX_RETRIES=5
```
- **Описание**: Максимальное количество попыток отправки при ошибке
- **По умолчанию**: `5`
- **Диапазон**: 0-20
- **Рекомендации**:
  - **Стабильная сеть**: 3-5
  - **Нестабильная сеть**: 8-15
  - **Критически важные данные**: 10-20

#### RETRY_DELAY
```bash
RETRY_DELAY=2.0
```
- **Описание**: Базовая задержка между попытками (секунды, с экспоненциальным увеличением)
- **По умолчанию**: `2.0`
- **Диапазон**: 0.1-10.0
- **Формула**: `delay = RETRY_DELAY * (2 ^ attempt_number)`
- **Пример**: При `RETRY_DELAY=2.0`: 2s, 4s, 8s, 16s, 32s

### Параметры логирования

#### LOG_LEVEL
```bash
LOG_LEVEL=INFO
```
- **Описание**: Уровень детализации логов
- **По умолчанию**: `INFO`
- **Возможные значения**:
  - `DEBUG`: Максимальная детализация (для отладки)
  - `INFO`: Стандартная детализация (рекомендуется)
  - `WARNING`: Только предупреждения и ошибки
  - `ERROR`: Только ошибки и критические проблемы
  - `CRITICAL`: Только критические ошибки

## 🎯 Профили конфигурации

### Development профиль
```bash
# .env.development
NODE_ID=dev-node-001
NODE_NAME=Development Node
CENTRAL_REDIS_URL=redis://localhost:6379/0
ACCESS_LOG_PATH=/tmp/marzban_access.log
BATCH_SIZE=5
FLUSH_INTERVAL=1.0
MAX_RETRIES=3
RETRY_DELAY=0.5
LOG_LEVEL=DEBUG
```

### Production профиль (Низкая нагрузка)
```bash
# .env.production.low
NODE_ID=prod-low-001
NODE_NAME=Production Low Load
CENTRAL_REDIS_URL=redis://prod-redis:6379/0
ACCESS_LOG_PATH=/var/lib/marzban-node/access.log
BATCH_SIZE=25
FLUSH_INTERVAL=5.0
MAX_RETRIES=5
RETRY_DELAY=2.0
LOG_LEVEL=INFO
```

### Production профиль (Высокая нагрузка)
```bash
# .env.production.high
NODE_ID=prod-high-001
NODE_NAME=Production High Load
CENTRAL_REDIS_URL=redis://prod-redis:6379/0
ACCESS_LOG_PATH=/var/lib/marzban-node/access.log
BATCH_SIZE=200
FLUSH_INTERVAL=2.0
MAX_RETRIES=8
RETRY_DELAY=1.0
LOG_LEVEL=WARNING
```

### Экономичный профиль (VPS с ограниченными ресурсами)
```bash
# .env.economy
NODE_ID=economy-001
NODE_NAME=Economy VPS Node
CENTRAL_REDIS_URL=redis://redis-server:6379/0
ACCESS_LOG_PATH=/var/lib/marzban-node/access.log
BATCH_SIZE=100
FLUSH_INTERVAL=10.0
MAX_RETRIES=3
RETRY_DELAY=5.0
LOG_LEVEL=WARNING
```

## 🔐 Настройки безопасности

### Redis аутентификация

#### Базовая аутентификация
```bash
CENTRAL_REDIS_URL=redis://:your_password@redis-server:6379/0
```

#### ACL пользователи (Redis 6+)
```bash
CENTRAL_REDIS_URL=redis://node_agent:secure_password@redis-server:6379/0
```

#### SSL/TLS подключения
```bash
CENTRAL_REDIS_URL=rediss://username:password@redis-server:6380/0
```

### Настройка Redis ACL для агента

```bash
# На Redis сервере создайте пользователя для агента
redis-cli

# Создание пользователя с минимальными правами
ACL SETUSER node_agent on >secure_password +@list +@string +ping +info

# Проверка прав пользователя
ACL GETUSER node_agent
```

### Защита конфигурационных файлов

```bash
# Ограничение доступа к .env файлу
sudo chmod 600 /opt/marzban-node-agent/config/.env
sudo chown root:root /opt/marzban-node-agent/config/.env

# Создание отдельного пользователя для агента
sudo useradd -r -s /bin/false marzban-agent
sudo chown marzban-agent:marzban-agent /opt/marzban-node-agent/
```

## 🌐 Сетевые настройки

### Настройка прокси

```bash
# HTTP прокси
HTTP_PROXY=http://proxy-server:8080
HTTPS_PROXY=http://proxy-server:8080

# Socks прокси
ALL_PROXY=socks5://proxy-server:1080

# Исключения
NO_PROXY=localhost,127.0.0.1,redis-local
```

### Настройка DNS

```bash
# В docker-compose.yml
services:
  node-agent:
    dns:
      - 8.8.8.8
      - 1.1.1.1
    dns_search:
      - yourdomain.com
```

### Настройка файрвола

```bash
# UFW
sudo ufw allow out 6379/tcp comment "Redis connection"

# iptables
sudo iptables -A OUTPUT -p tcp --dport 6379 -j ACCEPT

# firewalld
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --reload
```

## 📊 Мониторинг

### Настройка health checks

```bash
# Docker health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from node_agent.config import ConfigService; import redis.asyncio as redis; import asyncio; config = ConfigService.load_from_env(); client = redis.from_url(config.central_redis_url); asyncio.run(client.ping()); asyncio.run(client.close())" || exit 1
```

### Метрики для мониторинга

```bash
# Проверка очереди Redis
redis-cli -u "$CENTRAL_REDIS_URL" llen node_logs_queue

# Проверка позиции агента
redis-cli -u "$CENTRAL_REDIS_URL" get "node_agent:$NODE_ID:position"

# Проверка последней активности
redis-cli -u "$CENTRAL_REDIS_URL" get "node_agent:$NODE_ID:last_seen"
```

### Интеграция с Prometheus

```yaml
# docker-compose.yml
services:
  node-agent:
    # ... основная конфигурация
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8080"
      - "prometheus.io/path=/metrics"
    environment:
      - PROMETHEUS_ENABLED=true
      - PROMETHEUS_PORT=8080
```

## 🔧 Расширенные настройки

### Кастомные Redis ключи

```bash
# Префиксы для Redis ключей
REDIS_PREFIX=custom_prefix
QUEUE_KEY=custom_logs_queue
POSITION_KEY_PREFIX=custom_position
```

### Настройка буферизации файлов

```bash
# Размер буфера чтения файла
FILE_BUFFER_SIZE=8192

# Интервал проверки новых данных
FILE_POLL_INTERVAL=0.1
```

### Настройка сжатия

```bash
# Включение сжатия данных перед отправкой
COMPRESSION_ENABLED=true
COMPRESSION_LEVEL=6  # 1-9, где 9 = максимальное сжатие
```

## 📁 Структуры конфигурационных файлов

### Systemd environment файл

```bash
# /etc/systemd/system/marzban-node-agent.service.d/environment.conf
[Service]
EnvironmentFile=/opt/marzban-node-agent/config/.env
```

### Docker Compose конфигурация

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  node-agent:
    build:
      context: .
      dockerfile: docker/Dockerfile
    environment:
      - NODE_ID=${NODE_ID}
      - NODE_NAME=${NODE_NAME}
      - CENTRAL_REDIS_URL=${CENTRAL_REDIS_URL}
      - ACCESS_LOG_PATH=${ACCESS_LOG_PATH}
      - BATCH_SIZE=${BATCH_SIZE:-50}
      - FLUSH_INTERVAL=${FLUSH_INTERVAL:-3.0}
      - MAX_RETRIES=${MAX_RETRIES:-5}
      - RETRY_DELAY=${RETRY_DELAY:-2.0}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ${ACCESS_LOG_PATH}:${ACCESS_LOG_PATH}:ro
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128M
          cpus: '0.2'
        reservations:
          memory: 64M
          cpus: '0.1'
    healthcheck:
      test: ["CMD-SHELL", "/app/scripts/health-check.sh --quiet"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 🛠️ Утилиты для конфигурации

### Валидация конфигурации

```bash
#!/bin/bash
# validate-config.sh

python3 -c "
import sys
sys.path.append('/opt/marzban-node-agent/src')
from node_agent.config import ConfigService
try:
    config = ConfigService.load_from_env()
    print('✅ Configuration is valid')
    print(f'Node ID: {config.node_id}')
    print(f'Node Name: {config.node_name}')
    print(f'Redis URL: {config.central_redis_url}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    exit(1)
"
```

### Тестирование подключения

```bash
#!/bin/bash
# test-connection.sh

python3 -c "
import sys
sys.path.append('/opt/marzban-node-agent/src')
import asyncio
import redis.asyncio as redis
from node_agent.config import ConfigService

async def test():
    config = ConfigService.load_from_env()
    client = redis.from_url(config.central_redis_url)
    try:
        await client.ping()
        print('✅ Redis connection successful')
        return True
    except Exception as e:
        print(f'❌ Redis connection failed: {e}')
        return False
    finally:
        await client.close()

result = asyncio.run(test())
exit(0 if result else 1)
"
```

## 📚 Примеры специальных конфигураций

### Мультирегиональная установка

```bash
# Европейский регион
NODE_ID=eu-west-001
NODE_NAME=Europe West 01
CENTRAL_REDIS_URL=redis://eu-redis.example.com:6379/0

# Американский регион  
NODE_ID=us-east-001
NODE_NAME=US East 01
CENTRAL_REDIS_URL=redis://us-redis.example.com:6379/0

# Азиатский регион
NODE_ID=asia-001
NODE_NAME=Asia Singapore 01  
CENTRAL_REDIS_URL=redis://asia-redis.example.com:6379/0
```

### Конфигурация для тестирования

```bash
# Быстрая отправка для тестов
BATCH_SIZE=1
FLUSH_INTERVAL=0.5
LOG_LEVEL=DEBUG
MAX_RETRIES=1
RETRY_DELAY=0.1
```

### Конфигурация для критически важных систем

```bash
# Максимальная надежность
BATCH_SIZE=10          # Маленькие батчи для быстрой отправки
FLUSH_INTERVAL=1.0     # Частая отправка
MAX_RETRIES=20         # Много попыток
RETRY_DELAY=1.0        # Агрессивные повторы
LOG_LEVEL=INFO         # Детальное логирование
```

---

**Следующий раздел**: [API и разработка](API.md)
