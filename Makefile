.PHONY: help build start stop restart logs status update shell clean install

# Default target
help:
	@echo "XRay Checker Bot - Makefile"
	@echo ""
	@echo "Docker команды:"
	@echo "  make build     - Собрать Docker образ"
	@echo "  make start     - Запустить бота"
	@echo "  make stop      - Остановить бота"
	@echo "  make restart   - Перезапустить бота"
	@echo "  make logs      - Показать логи"
	@echo "  make status    - Показать статус"
	@echo "  make update    - Обновить и перезапустить"
	@echo "  make shell     - Войти в контейнер"
	@echo "  make clean     - Удалить контейнер и образ"
	@echo ""
	@echo "Локальная установка:"
	@echo "  make install   - Установить зависимости"
	@echo "  make run       - Запустить локально"

# Docker commands
build:
	./docker.sh build

start:
	./docker.sh start

stop:
	./docker.sh stop

restart:
	./docker.sh restart

logs:
	./docker.sh logs

status:
	./docker.sh status

update:
	./docker.sh update

shell:
	./docker.sh shell

clean:
	./docker.sh clean

# Local commands
install:
	./install.sh

run:
	python xray_checker.py

# Quick setup
up: build start
	@echo "🚀 XRay Checker Bot запущен!"

down: stop
	@echo "⛔ XRay Checker Bot остановлен!"
