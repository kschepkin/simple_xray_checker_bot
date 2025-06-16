# XRay Checker Bot

Telegram бот для мониторинга VPN серверов с автоматическими уведомлениями.
Работает совместно с https://github.com/kutovoys/xray-checker

## Функциональность

- ✅ Автоматическая проверка серверов каждые 5 минут
- 📱 Уведомления в Telegram при недоступности серверов  
- 🔍 Ручная проверка через команду в боте
- 📊 Подробные отчеты о состоянии серверов
- 📝 Логирование всех событий
- 🐳 Docker поддержка для легкого развертывания

## Быстрый запуск с Docker

### 1. Сборка и запуск
```bash
# Сборка образа
./docker.sh build

# Запуск бота
./docker.sh start

# Или сразу оба действия
./docker.sh build && ./docker.sh start
```

### 2. Управление контейнером
```bash
# Просмотр логов
./docker.sh logs

# Статус контейнера
./docker.sh status

# Перезапуск
./docker.sh restart

# Остановка
./docker.sh stop

# Обновление (пересборка + перезапуск)
./docker.sh update
```

### 3. Отладка
```bash
# Вход в контейнер
./docker.sh shell

# Полная очистка
./docker.sh clean
```

## Альтернативная установка (без Docker)

### 1. Установка зависимостей
```bash
chmod +x install.sh
./install.sh
```

### 2. Запуск
```bash
python xray_checker.py
```

## Конфигурация

Все настройки находятся в файле `.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=Ваш_токен
ADMIN_ID=id пользователя

# VPN Servers Configuration
ServerName=https://urlToCheck

# Check interval in minutes
CHECK_INTERVAL=5
```

### Добавление новых серверов
Просто добавьте новую строку в `.env`:
```env
НОВЫЙ_СЕРВЕР=https://example.com/config
```

## Использование

1. Запустите бота (Docker или обычным способом)
2. Отправьте команду `/start` боту в Telegram
3. Используйте кнопку "🔍 Проверить серверы" для ручной проверки
4. Бот автоматически отправит уведомление при проблемах с серверами

## Docker команды

| Команда | Описание |
|---------|----------|
| `./docker.sh build` | Собрать Docker образ |
| `./docker.sh start` | Запустить бота |
| `./docker.sh stop` | Остановить бота |
| `./docker.sh restart` | Перезапустить бота |
| `./docker.sh logs` | Показать логи |
| `./docker.sh status` | Показать статус |
| `./docker.sh update` | Обновить и перезапустить |
| `./docker.sh shell` | Войти в контейнер |
| `./docker.sh clean` | Удалить контейнер и образ |

## Логи

- При использовании Docker: `./docker.sh logs`
- Локальный файл: `xray_checker.log`

## Структура проекта

```
xray_checker_bot/
├── .env                   # Конфигурация
├── xray_checker.py        # Основной скрипт
├── requirements.txt       # Зависимости Python
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose
├── docker.sh            # Скрипт управления Docker
├── .dockerignore        # Исключения для Docker
├── README.md           # Документация
└── xray_checker.log    # Логи (создается автоматически)
```

## Автозапуск

### С Docker
Docker контейнер настроен с `restart: unless-stopped`, поэтому будет автоматически перезапускаться.

## Мониторинг

Бот включает встроенную проверку здоровья (healthcheck) и подробное логирование всех операций.

## Безопасность

- Контейнер запускается от непривилегированного пользователя
- Переменные окружения изолированы в `.env`
- Минимальный базовый образ Python

## Требования

- Docker и Docker Compose (для Docker развертывания)
- Python 3.11+ (для локального запуска)
- Интернет соединение для проверки серверов и отправки уведомлений
