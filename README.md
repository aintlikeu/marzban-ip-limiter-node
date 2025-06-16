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
curl -fsSL https://raw.githubusercontent.com/your-repo/marzban-node-agent/main/scripts/install.sh | sudo bash
```

### Ручная установка

1. **Настройка конфигурации:**
```bash
cp config/.env.example .env
nano .env
```

2. **Запуск с Docker Compose:**
```bash
docker-compose -f docker/docker-compose.yml up -d
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
docker-compose -f docker/docker-compose.yml logs -f

# Статус сервиса
systemctl status marzban-node-agent
```

## 📚 Документация

- [📦 Подробная установка](docs/INSTALLATION.md)
- [⚙️ Конфигурация](docs/CONFIGURATION.md)  
- [📖 Полное руководство](docs/README.md)

## 🤝 Поддержка

- **Issues**: [GitHub Issues](https://github.com/your-repo/marzban-node-agent/issues)
- **Telegram**: @marzban_support

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) для деталей.

---

**Разработано для экосистемы Marzban** 🚀
