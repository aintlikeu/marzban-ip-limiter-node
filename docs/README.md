# Marzban Node Agent

**Легковесный агент для экспорта логов Marzban с нод в центральный Redis сервер**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

## 📖 Описание

Marzban Node Agent - это специализированный агент для мониторинга и пересылки логов доступа Marzban с удаленных нод на центральный сервер через Redis. Агент обеспечивает надежную доставку логов в реальном времени с поддержкой буферизации, повторных попыток и восстановления позиции.

### 🎯 Основные возможности

- **Мониторинг в реальном времени**: Отслеживание файла `access.log` методом tail
- **Надежная доставка**: Буферизация, повторные попытки и восстановление позиции
- **Минимальные ресурсы**: Оптимизирован для работы на VPS с ограниченными ресурсами  
- **Простое развертывание**: Готовые Docker образы и скрипты установки
- **Мониторинг**: Встроенные health checks и метрики
- **Безопасность**: Работа от непривилегированного пользователя

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Marzban       │    │   Node Agent     │    │  Central Redis  │
│   access.log    │───▶│   (Docker)       │───▶│   Server        │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Поток данных:**
1. Marzban записывает логи в `access.log`
2. Node Agent читает новые записи в реальном времени
3. Парсит логи и извлекает email, IP, временные метки
4. Группирует логи в батчи для эффективной отправки
5. Отправляет в центральный Redis через список `node_logs_queue`
6. Сохраняет позицию в файле для восстановления после перезапуска

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Работающий Marzban сервер
- Доступ к центральному Redis серверу

### Установка одной командой

```bash
# Скачать и запустить установку
curl -fsSL https://raw.githubusercontent.com/your-repo/marzban-node-agent/main/scripts/install.sh | sudo bash
```

### Ручная установка

1. **Клонирование репозитория:**
```bash
git clone https://github.com/your-repo/marzban-node-agent.git
cd marzban-node-agent
```

2. **Настройка конфигурации:**
```bash
cp config/.env.example .env
nano .env
```

3. **Запуск с Docker Compose:**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Пример конфигурации

```bash
# .env
NODE_ID=germany-01
NODE_NAME=Germany-Frankfurt-01  
CENTRAL_REDIS_URL=redis://your-redis-server:6379/0
ACCESS_LOG_PATH=/var/lib/marzban-node/access.log
BATCH_SIZE=50
FLUSH_INTERVAL=3.0
LOG_LEVEL=INFO
```

## ⚙️ Конфигурация

### Основные параметры

| Параметр | Описание | По умолчанию | Обязательный |
|----------|----------|--------------|--------------|
| `NODE_ID` | Уникальный ID ноды | - | ✅ |
| `NODE_NAME` | Читаемое имя ноды | - | ✅ |
| `CENTRAL_REDIS_URL` | URL центрального Redis | - | ✅ |
| `ACCESS_LOG_PATH` | Путь к access.log | `/var/lib/marzban-node/access.log` | ✅ |
| `BATCH_SIZE` | Размер батча логов | `50` | ❌ |
| `FLUSH_INTERVAL` | Интервал отправки (сек) | `3.0` | ❌ |
| `MAX_RETRIES` | Макс. попыток отправки | `5` | ❌ |
| `RETRY_DELAY` | Задержка между попытками | `2.0` | ❌ |
| `LOG_LEVEL` | Уровень логирования | `INFO` | ❌ |

### Формат Redis URL

```bash
# Обычное подключение
CENTRAL_REDIS_URL=redis://hostname:6379/0

# С паролем  
CENTRAL_REDIS_URL=redis://:password@hostname:6379/0

# С пользователем и паролем
CENTRAL_REDIS_URL=redis://user:password@hostname:6379/0

# SSL подключение
CENTRAL_REDIS_URL=rediss://user:password@hostname:6380/0
```

## 📊 Мониторинг и диагностика

### Проверка статуса

```bash
# Статус контейнера
docker-compose -f docker/docker-compose.yml ps

# Проверка здоровья системы
sudo /opt/marzban-node-agent/scripts/health-check.sh

# Просмотр логов
docker-compose -f docker/docker-compose.yml logs -f node-agent
```

### Метрики и статистика

```bash
# JSON формат для мониторинга
sudo /opt/marzban-node-agent/scripts/health-check.sh --json

# Тихий режим (только ошибки)
sudo /opt/marzban-node-agent/scripts/health-check.sh --quiet
```

### Пример структуры лога

```json
{
  "timestamp": 1642247445.123,
  "node_id": "germany-01",
  "node_name": "Germany-Frankfurt-01",
  "email": "user@example.com",
  "client_ip": "192.168.1.100",
  "raw_line": "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100 email: user@example.com",
  "processed_at": 1642247445.456
}
```

## 🔧 Управление сервисом

### Systemd команды

```bash
# Запуск
sudo systemctl start marzban-node-agent

# Остановка  
sudo systemctl stop marzban-node-agent

# Перезапуск
sudo systemctl restart marzban-node-agent

# Статус
sudo systemctl status marzban-node-agent

# Автозапуск
sudo systemctl enable marzban-node-agent
```

### Docker Compose команды

```bash
cd /opt/marzban-node-agent

# Запуск
docker-compose -f docker/docker-compose.yml up -d

# Остановка
docker-compose -f docker/docker-compose.yml down

# Перезапуск
docker-compose -f docker/docker-compose.yml restart

# Логи
docker-compose -f docker/docker-compose.yml logs -f
```

## 🛠️ Обновление

### Обновление агента

```bash
# Остановка сервиса
sudo systemctl stop marzban-node-agent

# Обновление кода
cd /opt/marzban-node-agent
git pull origin main

# Пересборка образа
docker-compose -f docker/docker-compose.yml build

# Запуск
sudo systemctl start marzban-node-agent
```

## 🐛 Устранение проблем

### Частые проблемы

**1. Контейнер не запускается**
```bash
# Проверить логи
docker-compose -f docker/docker-compose.yml logs node-agent

# Проверить конфигурацию
cat /opt/marzban-node-agent/config/.env

# Проверить Redis подключение
redis-cli -u $CENTRAL_REDIS_URL ping
```

**2. Логи не отправляются**
```bash
# Проверить доступность файла логов
ls -la /var/lib/marzban-node/access.log

# Проверить права доступа
docker exec marzban-node-agent ls -la /var/lib/marzban/

# Проверить здоровье
sudo /opt/marzban-node-agent/scripts/health-check.sh
```

**3. Высокое потребление ресурсов**
```bash
# Уменьшить BATCH_SIZE
echo "BATCH_SIZE=25" >> .env

# Увеличить FLUSH_INTERVAL  
echo "FLUSH_INTERVAL=5.0" >> .env

# Перезапуск
docker-compose restart
```

### Отладка

```bash
# Включить DEBUG логирование
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart

# Проверить позицию в файле
redis-cli -u $CENTRAL_REDIS_URL get "node_agent:$NODE_ID:position"

# Проверить очередь логов
redis-cli -u $CENTRAL_REDIS_URL llen "node_logs_queue"
```

## 📚 Дополнительная документация

- [Подробная установка](docs/INSTALLATION.md)
- [Конфигурация](docs/CONFIGURATION.md)
- [Удаление сервиса](docs/UNINSTALL.md)
- [API и разработка](docs/API.md)

## 🤝 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-repo/marzban-node-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/marzban-node-agent/discussions)
- **Telegram**: @marzban_support

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. [LICENSE](LICENSE) для деталей.

---

**Разработано для экосистемы Marzban** 🚀
