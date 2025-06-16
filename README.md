# Marzban Node Agent

**Легковесный агент для экспорта логов Marzban с нод в центральный Redis сервер**

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)

## 🎯 Описание

Marzban Node Agent - это высокопроизводительный агент для мониторинга и пересылки логов доступа Marzban с удаленных нод на центральный сервер через Redis. Агент обеспечивает надежную доставку логов в реальном времени с поддержкой буферизации, повторных попыток и восстановления позиции.

### ✨ Ключевые особенности

- 🔄 **Мониторинг в реальном времени** - Отслеживание `access.log` методом tail
- 🛡️ **Надежная доставка** - Буферизация, повторные попытки и восстановление позиции  
- ⚡ **Высокая производительность** - Асинхронная архитектура, минимальное потребление ресурсов
- 🐳 **Простое развертывание** - Готовые Docker образы и скрипты установки
- 📊 **Встроенный мониторинг** - Health checks, метрики и детальное логирование
- 🔐 **Безопасность** - Работа от непривилегированного пользователя

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Marzban       │    │   Node Agent     │    │  Central Redis  │
│   access.log    │───▶│   (Docker)       │───▶│   Server        │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### Автоматическая установка

```bash
# Клонирование и установка
git clone https://github.com/your-repo/marzban-node-agent.git
cd marzban-node-agent
sudo ./scripts/install.sh
```

### Настройка конфигурации

```bash
# Интерактивная настройка
./scripts/configure.sh

# Или ручная настройка
cp config/.env.example config/.env
nano config/.env
```

### Запуск

```bash
# Через systemd (рекомендуется)
sudo systemctl start marzban-node-agent

# Или через Docker Compose
docker-compose -f docker/docker-compose.standalone.yml up -d
```

### Базовая конфигурация

```bash
# .env
NODE_ID=germany-01
NODE_NAME=Germany-Frankfurt-01  
CENTRAL_REDIS_URL=redis://your-redis-server:6379/0
ACCESS_LOG_PATH=/var/lib/marzban/access.log
```

## 📊 Мониторинг

```bash
# Проверка здоровья системы
sudo /opt/marzban-node-agent/scripts/health-check.sh

# Просмотр логов
docker-compose -f docker/docker-compose.standalone.yml logs -f

# Статус сервиса
systemctl status marzban-node-agent
```

## 📚 Документация

- [📦 Подробная установка](docs/INSTALLATION.md)
- [⚙️ Конфигурация](docs/CONFIGURATION.md)
- [🗑️ Удаление сервиса](docs/UNINSTALL.md)
- [📖 Полное руководство](docs/README.md)

## 🤝 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-repo/marzban-node-agent/issues)
- **Telegram**: @marzban_support

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) для деталей.

---

**Разработано для экосистемы Marzban** 🚀

## 🗑️ Удаление

### Полное удаление агента

```bash
# Автоматическое удаление
sudo ./scripts/uninstall.sh

# Принудительное удаление без подтверждения
sudo ./scripts/uninstall.sh --force
```

### Что удаляется:
- ✅ Systemd сервис и конфигурация
- ✅ Docker контейнеры и образы  
- ✅ Файлы приложения и конфигурация
- ✅ Логи и временные файлы
- ✅ Cron задачи и logrotate правила
- ✅ Символические ссылки
