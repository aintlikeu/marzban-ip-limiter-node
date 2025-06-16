# Установка Marzban Node Agent

Подробное руководство по установке и первоначальной настройке агента для экспорта логов Marzban.

## 📋 Системные требования

### Минимальные требования

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **RAM**: 128 МБ свободной памяти
- **CPU**: 0.1 CPU core
- **Disk**: 500 МБ свободного места
- **Network**: Стабильное подключение к интернету

### Программные зависимости

- **Docker**: 20.10+
- **Docker Compose**: 2.0+ (или docker-compose 1.29+)
- **curl/wget**: Для скачивания файлов
- **systemctl**: Для управления сервисами (опционально)

### Проверка системы

```bash
# Проверка версии Docker
docker --version

# Проверка Docker Compose
docker-compose --version
# или
docker compose version

# Проверка доступности портов
netstat -tlnp | grep :6379  # Redis порт

# Проверка свободного места
df -h

# Проверка памяти
free -h
```

## 🔧 Предварительная настройка

### 1. Настройка Docker (если не установлен)

**Ubuntu/Debian:**
```bash
# Обновление пакетов
sudo apt update

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**CentOS/RHEL:**
```bash
# Установка Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка файрвола

```bash
# UFW (Ubuntu)
sudo ufw allow from REDIS_SERVER_IP to any port 6379

# iptables
sudo iptables -A OUTPUT -p tcp --dport 6379 -j ACCEPT

# firewalld (CentOS)
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --reload
```

### 3. Подготовка директорий

```bash
# Создание рабочих директорий
sudo mkdir -p /opt/marzban-node-agent/{config,logs,data}
sudo mkdir -p /var/log/marzban-node-agent

# Настройка прав доступа
sudo chown -R $USER:$USER /opt/marzban-node-agent
```

## 📦 Способы установки

### Способ 1: Автоматическая установка (Рекомендуется)

```bash
# Скачивание и запуск установочного скрипта
curl -fsSL https://raw.githubusercontent.com/your-repo/marzban-node-agent/main/scripts/install.sh -o install.sh
chmod +x install.sh
sudo ./install.sh
```

**Возможные параметры:**
```bash
# Установка с конкретной версией
sudo ./install.sh --version v1.0.0

# Установка без systemd сервиса
sudo ./install.sh --no-systemd

# Установка в custom директорию
sudo ./install.sh --install-dir /custom/path
```

### Способ 2: Ручная установка

#### Шаг 1: Получение исходного кода

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/marzban-node-agent.git
cd marzban-node-agent

# Или скачивание релиза
curl -L https://github.com/your-repo/marzban-node-agent/archive/refs/tags/v1.0.0.tar.gz | tar xz
cd marzban-node-agent-1.0.0
```

#### Шаг 2: Копирование файлов

```bash
# Копирование в системную директорию
sudo cp -r src/ /opt/marzban-node-agent/
sudo cp -r docker/ /opt/marzban-node-agent/
sudo cp -r scripts/ /opt/marzban-node-agent/
sudo cp -r config/ /opt/marzban-node-agent/

# Создание символических ссылок для удобства
sudo ln -sf /opt/marzban-node-agent/scripts/health-check.sh /usr/local/bin/marzban-health
sudo ln -sf /opt/marzban-node-agent/scripts/install.sh /usr/local/bin/marzban-install
```

#### Шаг 3: Настройка конфигурации

```bash
# Копирование примера конфигурации
cd /opt/marzban-node-agent
sudo cp config/.env.example config/.env

# Редактирование конфигурации
sudo nano config/.env
```

#### Шаг 4: Сборка Docker образа

```bash
cd /opt/marzban-node-agent
sudo docker build -t marzban-node-agent:latest -f docker/Dockerfile .
```

#### Шаг 5: Настройка systemd сервиса

```bash
# Создание systemd service файла
sudo tee /etc/systemd/system/marzban-node-agent.service > /dev/null <<EOF
[Unit]
Description=Marzban Node Agent
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/marzban-node-agent
ExecStart=/usr/bin/docker-compose -f docker/docker-compose.yml up -d
ExecStop=/usr/bin/docker-compose -f docker/docker-compose.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable marzban-node-agent
```

### Способ 3: Docker-only установка

```bash
# Создание docker-compose.yml
mkdir -p ~/marzban-node-agent
cd ~/marzban-node-agent

cat > docker-compose.yml <<EOF
version: '3.8'
services:
  node-agent:
    image: marzban/node-agent:latest
    container_name: marzban-node-agent
    restart: unless-stopped
    environment:
      - NODE_ID=\${NODE_ID}
      - NODE_NAME=\${NODE_NAME}
      - CENTRAL_REDIS_URL=\${CENTRAL_REDIS_URL}
      - ACCESS_LOG_PATH=/var/lib/marzban-node/access.log
    volumes:
      - /var/lib/marzban-node/access.log:/var/lib/marzban-node/access.log:ro
    networks:
      - marzban-network

networks:
  marzban-network:
    external: true
EOF

# Создание .env файла
cat > .env <<EOF
NODE_ID=node-001
NODE_NAME=My-Node-01
CENTRAL_REDIS_URL=redis://your-redis:6379/0
EOF

# Запуск
docker-compose up -d
```

## ⚙️ Первоначальная настройка

### 1. Базовая конфигурация

Отредактируйте файл `/opt/marzban-node-agent/config/.env`:

```bash
# Обязательные параметры
NODE_ID=unique-node-identifier         # Уникальный в рамках всей сети
NODE_NAME=Germany-Frankfurt-01         # Читаемое имя
CENTRAL_REDIS_URL=redis://main-server:6379/0
ACCESS_LOG_PATH=/var/lib/marzban-node/access.log

# Настройки производительности
BATCH_SIZE=50                          # Для VPS: 25-50, для мощных серверов: 100+
FLUSH_INTERVAL=3.0                     # Для реального времени: 1-2s, для экономии: 5-10s
MAX_RETRIES=5                          # Количество попыток при ошибках
RETRY_DELAY=2.0                        # Задержка между попытками

# Логирование
LOG_LEVEL=INFO                         # DEBUG для отладки, WARNING для минимума
```

### 2. Настройка доступа к файлам Marzban

```bash
# Проверка расположения файла логов Marzban
sudo find /var -name "access.log" -type f 2>/dev/null | grep marzban

# Если Marzban в Docker, найти volume
docker inspect marzban | grep -A 10 "Mounts"

# Настройка прав доступа (если нужно)
sudo chmod 644 /var/lib/marzban-node/access.log
sudo chown marzban:marzban /var/lib/marzban-node/access.log
```

### 3. Проверка сетевого подключения

```bash
# Тест подключения к Redis
redis-cli -u "redis://your-redis:6379/0" ping

# Тест из контейнера
docker run --rm redis:alpine redis-cli -u "redis://your-redis:6379/0" ping

# Проверка DNS разрешения
nslookup your-redis-host
```

## 🚀 Запуск и проверка

### 1. Первый запуск

```bash
# Запуск сервиса
sudo systemctl start marzban-node-agent

# Проверка статуса
sudo systemctl status marzban-node-agent

# Просмотр логов
sudo journalctl -u marzban-node-agent -f
```

### 2. Проверка работоспособности

```bash
# Полная диагностика
sudo /opt/marzban-node-agent/scripts/health-check.sh

# Проверка контейнера
docker ps | grep marzban-node-agent

# Проверка логов агента
docker logs marzban-node-agent

# Проверка отправки данных в Redis
redis-cli -u "$CENTRAL_REDIS_URL" llen node_logs_queue
```

### 3. Проверка функциональности

```bash
# Генерация тестового лога (если возможно)
echo "2024/01/15 10:30:45 [info] accepted connection from 192.168.1.100 email: test@example.com" >> /var/lib/marzban-node/access.log

# Проверка появления данных в Redis
redis-cli -u "$CENTRAL_REDIS_URL" lpop node_logs_queue

# Проверка позиции агента
redis-cli -u "$CENTRAL_REDIS_URL" get "node_agent:$NODE_ID:position"
```

## 🔧 Настройка для production

### 1. Настройки безопасности

```bash
# Ограничение доступа к конфигурации
sudo chmod 600 /opt/marzban-node-agent/config/.env
sudo chown root:root /opt/marzban-node-agent/config/.env

# Настройка SELinux (если используется)
sudo setsebool -P container_manage_cgroup on
```

### 2. Настройки логирования

```bash
# Настройка ротации логов Docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

sudo systemctl restart docker
```

### 3. Мониторинг и алерты

```bash
# Настройка cron для health check
echo "*/5 * * * * root /opt/marzban-node-agent/scripts/health-check.sh --quiet || echo 'Marzban Node Agent unhealthy' | mail admin@example.com" | sudo tee -a /etc/crontab

# Настройка logrotate
sudo tee /etc/logrotate.d/marzban-node-agent > /dev/null <<EOF
/var/log/marzban-node-agent/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 root root
}
EOF
```

## 🛠️ Устранение проблем при установке

### Проблема: Docker не запускается

```bash
# Проверка статуса
sudo systemctl status docker

# Проверка логов
sudo journalctl -u docker

# Перезапуск
sudo systemctl restart docker

# Проверка пространства
df -h /var/lib/docker
```

### Проблема: Права доступа

```bash
# Проверка владельца файлов
ls -la /opt/marzban-node-agent/

# Исправление прав
sudo chown -R root:root /opt/marzban-node-agent/
sudo chmod +x /opt/marzban-node-agent/scripts/*.sh
```

### Проблема: Сеть

```bash
# Проверка сетевого подключения
ping your-redis-server

# Проверка портов
telnet your-redis-server 6379

# Проверка DNS
nslookup your-redis-server
```

### Проблема: Файл логов недоступен

```bash
# Поиск правильного пути
sudo find /var -name "access.log" -type f 2>/dev/null

# Проверка Marzban контейнера
docker inspect marzban | grep -A 5 "Mounts"

# Создание тестового файла
sudo touch /var/lib/marzban-node/access.log
sudo chmod 644 /var/lib/marzban-node/access.log
```

## 📚 Следующие шаги

После успешной установки:

1. **Настройте мониторинг** - См. [Конфигурация мониторинга](CONFIGURATION.md#мониторинг)
2. **Настройте бэкапы** - См. [Backup и восстановление](CONFIGURATION.md#backup)
3. **Оптимизируйте производительность** - См. [Оптимизация](CONFIGURATION.md#производительность)
4. **Настройте алерты** - См. [Алерты и уведомления](CONFIGURATION.md#алерты)

---

**Следующий раздел**: [Конфигурация](CONFIGURATION.md)

## 🗑️ Удаление сервиса

### Полное удаление

Если вам нужно полностью удалить Marzban Node Agent из системы:

```bash
# Автоматическое удаление
sudo /opt/marzban-node-agent/scripts/uninstall.sh

# Или из исходного кода
sudo ./scripts/uninstall.sh

# Принудительное удаление без подтверждения
sudo ./scripts/uninstall.sh --force
```

### Что удаляется

Скрипт удаления выполняет следующие действия:

1. **Остановка сервисов**:
   - Останавливает systemd сервис
   - Останавливает и удаляет Docker контейнеры

2. **Удаление файлов**:
   - Удаляет все файлы приложения из `/opt/marzban-node-agent/`
   - Удаляет логи из `/var/log/marzban-node-agent/`
   - Предлагает создать backup конфигурации

3. **Очистка системы**:
   - Удаляет systemd сервис `/etc/systemd/system/marzban-node-agent.service`
   - Удаляет Docker образы
   - Очищает cron задачи
   - Удаляет logrotate конфигурацию
   - Удаляет пользователя `marzban-agent`

### Ручное удаление

Если автоматический скрипт не работает, выполните ручное удаление:

```bash
# Остановка сервиса
sudo systemctl stop marzban-node-agent
sudo systemctl disable marzban-node-agent

# Удаление systemd сервиса
sudo rm -f /etc/systemd/system/marzban-node-agent.service
sudo systemctl daemon-reload

# Остановка Docker контейнеров
docker stop marzban-node-agent
docker rm marzban-node-agent

# Удаление Docker образов
docker rmi marzban-node-agent:latest

# Удаление файлов
sudo rm -rf /opt/marzban-node-agent/
sudo rm -rf /var/log/marzban-node-agent/

# Очистка cron и logrotate
sudo crontab -l | grep -v marzban-node-agent | sudo crontab -
sudo rm -f /etc/logrotate.d/marzban-node-agent
```

### Сохранение конфигурации

Перед удалением вы можете сохранить конфигурацию:

```bash
# Backup конфигурации
cp /opt/marzban-node-agent/config/.env ~/marzban-node-agent-backup.env

# Backup логов
cp -r /var/log/marzban-node-agent/ ~/marzban-node-agent-logs-backup/
```

### Проверка удаления

После удаления проверьте, что все компоненты удалены:

```bash
# Проверка сервиса
systemctl status marzban-node-agent

# Проверка контейнеров
docker ps -a | grep marzban-node-agent

# Проверка файлов
ls -la /opt/marzban-node-agent/
ls -la /var/log/marzban-node-agent/

# Проверка процессов
ps aux | grep marzban-node-agent
```
