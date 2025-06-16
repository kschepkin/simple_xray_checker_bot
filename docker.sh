#!/bin/bash

# Скрипт управления Docker контейнером XRay Checker Bot

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция вывода с цветом
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен!"
        exit 1
    fi
}

# Очистка старых контейнеров перед сборкой
cleanup_old() {
    print_status "Очистка старых контейнеров..."
    docker-compose down 2>/dev/null || true
    docker container rm xray-checker-bot 2>/dev/null || true
    print_success "Очистка завершена!"
}

# Сборка образа
build() {
    print_status "Сборка Docker образа..."
    cleanup_old
    docker-compose build
    if [ $? -eq 0 ]; then
        print_success "Образ собран успешно!"
    else
        print_error "Ошибка сборки образа!"
        exit 1
    fi
}

# Запуск контейнера
start() {
    print_status "Запуск XRay Checker Bot..."
    docker-compose up -d
    if [ $? -eq 0 ]; then
        print_success "Бот запущен!"
        print_status "Для просмотра логов используйте: $0 logs"
    else
        print_error "Ошибка запуска!"
        exit 1
    fi
}

# Остановка контейнера
stop() {
    print_status "Остановка XRay Checker Bot..."
    docker-compose down
    if [ $? -eq 0 ]; then
        print_success "Бот остановлен!"
    else
        print_error "Ошибка остановки!"
        exit 1
    fi
}

# Перезапуск контейнера
restart() {
    print_status "Перезапуск XRay Checker Bot..."
    docker-compose restart
    if [ $? -eq 0 ]; then
        print_success "Бот перезапущен!"
    else
        print_error "Ошибка перезапуска!"
        exit 1
    fi
}

# Просмотр логов
logs() {
    print_status "Просмотр логов (Ctrl+C для выхода)..."
    docker-compose logs -f
}

# Статус контейнера
status() {
    print_status "Статус контейнера:"
    docker-compose ps
    echo
    print_status "Использование ресурсов:"
    docker stats xray-checker-bot --no-stream 2>/dev/null || print_warning "Контейнер не запущен"
    echo
    print_status "Логи бота (последние 10 строк):"
    if [ -f "./logs/xray_checker.log" ]; then
        tail -n 10 ./logs/xray_checker.log
    else
        print_warning "Файл логов не найден"
    fi
}

# Очистка (удаление контейнера и образа)
clean() {
    print_warning "Удаление контейнера и образа..."
    read -p "Вы уверены? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down --rmi all --volumes
        docker system prune -f
        print_success "Очистка завершена!"
    else
        print_status "Отменено"
    fi
}

# Обновление (пересборка и перезапуск)
update() {
    print_status "Обновление XRay Checker Bot..."
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    if [ $? -eq 0 ]; then
        print_success "Обновление завершено!"
    else
        print_error "Ошибка обновления!"
        exit 1
    fi
}

# Вход в контейнер для отладки
shell() {
    print_status "Вход в контейнер (exit для выхода)..."
    docker-compose exec xray-checker bash || docker-compose exec xray-checker sh
}

# Показать помощь
show_help() {
    echo "XRay Checker Bot - Docker Management Script"
    echo
    echo "Использование: $0 [команда]"
    echo
    echo "Команды:"
    echo "  build      Собрать Docker образ"
    echo "  start      Запустить бота"
    echo "  stop       Остановить бота"
    echo "  restart    Перезапустить бота"
    echo "  logs       Показать логи"
    echo "  status     Показать статус и последние логи"
    echo "  update     Обновить и перезапустить"
    echo "  shell      Войти в контейнер"
    echo "  clean      Удалить контейнер и образ"
    echo "  help       Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 build && $0 start    # Собрать и запустить"
    echo "  $0 logs                 # Посмотреть логи"
    echo "  $0 status               # Проверить статус"
}

# Основная логика
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            logs
            ;;
        status)
            status
            ;;
        update)
            update
            ;;
        shell)
            shell
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Запуск
main "$@"
