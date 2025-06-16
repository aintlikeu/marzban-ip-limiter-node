# 🗑️ Скрипт удаления Marzban Node Agent

## Описание

Скрипт `uninstall.sh` предназначен для полного удаления Marzban Node Agent из системы. Он автоматически удаляет все компоненты сервиса и возвращает систему в первоначальное состояние.

## Использование

### Базовое использование

```bash
# Интерактивное удаление с подтверждением
sudo ./scripts/uninstall.sh

# Принудительное удаление без подтверждения
sudo ./scripts/uninstall.sh --force

# Помощь
./scripts/uninstall.sh --help
```

### Из установленной системы

```bash
# Если агент установлен в системе
sudo /opt/marzban-node-agent/scripts/uninstall.sh
```

### Через Makefile

```bash
# Интерактивное удаление
make uninstall

# Принудительное удаление
make uninstall-force

# Очистка локального окружения разработки
make uninstall-local
```

## Что удаляется

### 🛑 Сервисы
- Останавливает systemd сервис `marzban-node-agent`
- Отключает автозапуск сервиса
- Удаляет файл сервиса `/etc/systemd/system/marzban-node-agent.service`

### 🐳 Docker компоненты
- Останавливает и удаляет контейнер `marzban-node-agent`
- Удаляет Docker образ `marzban-node-agent:latest`
- Очищает неиспользуемые Docker ресурсы (опционально)
- Удаляет Docker сеть `marzban-network` (если не используется)

### 📁 Файлы и директории
- Основная директория: `/opt/marzban-node-agent/`
- Логи: `/var/log/marzban-node-agent/`
- Символические ссылки: `/usr/local/bin/marzban-*`

### ⚙️ Системные конфигурации
- Cron задачи с упоминанием `marzban-node-agent`
- Logrotate конфигурация: `/etc/logrotate.d/marzban-node-agent`
- Пользователь и группа: `marzban-agent`

## Безопасность

### Backup конфигурации

Скрипт предлагает создать backup конфигурации перед удалением:

```bash
# Автоматический backup
Do you want to backup configuration files? (Y/n): y
Configuration backed up to: /tmp/marzban-node-agent-backup-20240616_143022
```

### Подтверждение действий

Скрипт запрашивает подтверждение для критических операций:

- Общее подтверждение удаления
- Backup конфигурации
- Очистка Docker ресурсов

## Диагностика

### Проверка удаления

После выполнения скрипта автоматически проверяется:

- Отсутствие запущенных контейнеров
- Отсутствие Docker образов
- Отсутствие активных процессов

### Ручная проверка

```bash
# Проверка сервиса
systemctl status marzban-node-agent
# Должно показать: Unit marzban-node-agent.service could not be found

# Проверка контейнеров
docker ps -a | grep marzban-node-agent
# Не должно показать результатов

# Проверка файлов
ls -la /opt/marzban-node-agent/
# Должно показать: No such file or directory

# Проверка процессов
pgrep -f marzban-node-agent
# Не должно показать результатов
```

## Устранение проблем

### Скрипт завершился с ошибкой

```bash
# Принудительная очистка контейнеров
docker stop $(docker ps -aq --filter name=marzban-node-agent) 2>/dev/null || true
docker rm $(docker ps -aq --filter name=marzban-node-agent) 2>/dev/null || true

# Принудительная очистка образов
docker rmi $(docker images -q marzban-node-agent) 2>/dev/null || true

# Ручное удаление файлов
sudo rm -rf /opt/marzban-node-agent/
sudo rm -f /etc/systemd/system/marzban-node-agent.service
sudo systemctl daemon-reload
```

### Контейнер не останавливается

```bash
# Принудительная остановка
docker kill marzban-node-agent 2>/dev/null || true
docker rm -f marzban-node-agent 2>/dev/null || true
```

### Файлы заблокированы

```bash
# Проверка процессов, использующих файлы
sudo lsof +D /opt/marzban-node-agent/ 2>/dev/null || true

# Принудительное завершение процессов
sudo pkill -f marzban-node-agent || true
```

## Восстановление

### Повторная установка

После удаления можно выполнить чистую установку:

```bash
# Клонирование проекта заново
git clone <repository-url>
cd marzban-node-agent

# Чистая установка
sudo ./scripts/install.sh
```

### Восстановление из backup

```bash
# Если был создан backup конфигурации
cp /tmp/marzban-node-agent-backup-*/config/.env ./config/

# Установка с сохраненной конфигурацией
sudo ./scripts/install.sh
```

## Примеры использования

### Обычное удаление

```bash
$ sudo ./scripts/uninstall.sh
==============================================
Marzban Node Agent Uninstall Script
==============================================

[WARNING] This will completely remove Marzban Node Agent from your system:
  - Stop and remove the service
  - Remove Docker containers and images
  - Delete all files and configuration
  - Remove systemd service

Are you sure you want to continue? (y/N): y

[INFO] Starting uninstallation process...
...
[SUCCESS] Uninstallation completed successfully!
```

### Принудительное удаление

```bash
$ sudo ./scripts/uninstall.sh --force
[WARNING] Force uninstall mode enabled
Force mode: skipping confirmation
[INFO] Starting uninstallation process...
...
[SUCCESS] Uninstallation completed successfully!
```

---

**Скрипт обеспечивает полную очистку системы от всех компонентов агента!** 🗑️✨
