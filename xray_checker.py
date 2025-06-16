import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, Tuple, Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования - только в stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Только в stdout
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 5))

# Загружаем серверы из .env
def load_servers() -> Dict[str, str]:
    """Загружает список серверов из переменных окружения"""
    servers = {}
    for key, value in os.environ.items():
        if key not in ['TELEGRAM_BOT_TOKEN', 'ADMIN_ID', 'CHECK_INTERVAL'] and not key.startswith('_'):
            if value.startswith('http'):
                servers[key] = value
    return servers

SERVERS = load_servers()

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Глобальное хранилище состояний серверов
server_states = {}

class ServerState:
    def __init__(self, name: str):
        self.name = name
        self.is_down = False
        self.first_failure_time = None
        self.last_update_time = None
        self.alert_message_id = None
        self.current_error = None

class CheckCallback(CallbackData, prefix="check"):
    action: str

async def check_server(session: aiohttp.ClientSession, name: str, url: str) -> Tuple[str, bool, str]:
    """
    Проверяет статус сервера
    
    Args:
        session: HTTP сессия
        name: Имя сервера
        url: URL для проверки
    
    Returns:
        Tuple[str, bool, str]: (имя_сервера, успех, сообщение)
    """
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(url, timeout=timeout) as response:
            text = await response.text()
            
            if response.status == 200 and text.strip() == "OK":
                logger.info(f"Сервер {name} работает нормально")
                return name, True, "OK"
            else:
                error_msg = f"Неожиданный ответ: {text[:100]}"
                logger.warning(f"Сервер {name}: {error_msg}")
                return name, False, error_msg
                
    except asyncio.TimeoutError:
        error_msg = "Превышено время ожидания"
        logger.error(f"Сервер {name}: {error_msg}")
        return name, False, error_msg
    except Exception as e:
        error_msg = f"Ошибка подключения: {str(e)}"
        logger.error(f"Сервер {name}: {error_msg}")
        return name, False, error_msg

async def check_all_servers() -> Dict[str, Tuple[bool, str]]:
    """
    Проверяет все серверы параллельно
    
    Returns:
        Dict[str, Tuple[bool, str]]: {имя_сервера: (успех, сообщение)}
    """
    results = {}
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for name, url in SERVERS.items():
            task = check_server(session, name, url)
            tasks.append(task)
        
        # Выполняем все проверки параллельно
        check_results = await asyncio.gather(*tasks)
        
        for name, success, message in check_results:
            results[name] = (success, message)
    
    return results

async def send_alert(server_name: str, error_message: str):
    """Отправляет новое уведомление администратору о проблеме с сервером"""
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        alert_text = f"🚨 <b>ВНИМАНИЕ!</b>\n\n" \
                    f"Сервер: <code>{server_name}</code>\n" \
                    f"Текущий статус: ❌ Недоступен\n" \
                    f"Обнаружено: {current_time}\n" \
                    f"Время: {current_time}"
        
        message = await bot.send_message(
            chat_id=ADMIN_ID,
            text=alert_text,
            parse_mode='HTML'
        )
        
        # Сохраняем ID сообщения для дальнейших обновлений
        if server_name not in server_states:
            server_states[server_name] = ServerState(server_name)
        
        server_states[server_name].is_down = True
        server_states[server_name].first_failure_time = current_time
        server_states[server_name].last_update_time = current_time
        server_states[server_name].alert_message_id = message.message_id
        server_states[server_name].current_error = error_message
        
        logger.info(f"Отправлено новое уведомление о проблеме с сервером {server_name}")
        
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления: {e}")

async def update_alert(server_name: str, is_working: bool, error_message: str = None):
    """Обновляет существующее уведомление о статусе сервера"""
    try:
        if server_name not in server_states or not server_states[server_name].alert_message_id:
            return
        
        state = server_states[server_name]
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if is_working:
            # Сервер восстановился
            alert_text = f"🚨 <b>ВНИМАНИЕ!</b>\n\n" \
                        f"Сервер: <code>{server_name}</code>\n" \
                        f"Текущий статус: ✅ Доступен\n" \
                        f"Обнаружено: {state.first_failure_time}\n" \
                        f"Время: {current_time}"
            
            # После восстановления больше не обновляем сообщение
            state.is_down = False
            state.alert_message_id = None
            
        else:
            # Сервер по-прежнему недоступен
            state.current_error = error_message
            state.last_update_time = current_time
            
            alert_text = f"🚨 <b>ВНИМАНИЕ!</b>\n\n" \
                        f"Сервер: <code>{server_name}</code>\n" \
                        f"Текущий статус: ❌ Недоступен\n" \
                        f"Обнаружено: {state.first_failure_time}\n" \
                        f"Время: {current_time}"
        
        await bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=state.alert_message_id,
            text=alert_text,
            parse_mode='HTML'
        )
        
        logger.info(f"Обновлено уведомление для сервера {server_name}: {'восстановлен' if is_working else 'по-прежнему недоступен'}")
        
    except Exception as e:
        logger.error(f"Ошибка обновления уведомления для {server_name}: {e}")

async def process_server_status(server_name: str, is_working: bool, error_message: str):
    """Обрабатывает изменение статуса сервера"""
    # Инициализируем состояние сервера если его нет
    if server_name not in server_states:
        server_states[server_name] = ServerState(server_name)
    
    state = server_states[server_name]
    
    if not is_working:  # Сервер недоступен
        if not state.is_down:
            # Сервер только что упал - отправляем новое уведомление
            await send_alert(server_name, error_message)
        elif state.alert_message_id:
            # Сервер уже был недоступен - обновляем существующее сообщение
            await update_alert(server_name, False, error_message)
    else:  # Сервер работает
        if state.is_down and state.alert_message_id:
            # Сервер восстановился - обновляем сообщение в последний раз
            await update_alert(server_name, True)

async def monitoring_loop():
    """Основной цикл мониторинга"""
    logger.info(f"Запуск мониторинга. Проверка каждые {CHECK_INTERVAL} минут")
    logger.info(f"Мониторим серверы: {list(SERVERS.keys())}")
    
    while True:
        try:
            logger.info("Начинаем проверку серверов...")
            results = await check_all_servers()
            
            # Обрабатываем результаты для каждого сервера
            for server_name, (success, message) in results.items():
                await process_server_status(server_name, success, message)
            
            # Ждем следующую проверку
            await asyncio.sleep(CHECK_INTERVAL * 60)
            
        except Exception as e:
            logger.error(f"Ошибка в цикле мониторинга: {e}")
            await asyncio.sleep(60)  # Ждем минуту перед повтором

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет доступа к этому боту.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Проверить серверы", callback_data=CheckCallback(action="check").pack())]
    ])
    
    welcome_text = f"🤖 <b>XRay Checker Bot</b>\n\n" \
                  f"Мониторинг серверов:\n"
    
    for server_name in SERVERS.keys():
        welcome_text += f"• {server_name}\n"
    
    welcome_text += f"\n⏱ Автопроверка каждые {CHECK_INTERVAL} минут"
    
    await message.answer(welcome_text, parse_mode='HTML', reply_markup=keyboard)

@dp.callback_query(CheckCallback.filter())
async def check_callback(callback_query: types.CallbackQuery, callback_data: CheckCallback):
    """Обработчик кнопки проверки"""
    if callback_query.from_user.id != ADMIN_ID:
        await callback_query.answer("❌ У вас нет доступа.", show_alert=True)
        return
    
    await callback_query.answer("🔄 Проверяю серверы...")
    
    # Показываем индикатор загрузки
    loading_message = await callback_query.message.edit_text(
        "🔄 <b>Проверка серверов...</b>\n\nПожалуйста, подождите...",
        parse_mode='HTML'
    )
    
    try:
        results = await check_all_servers()
        
        # Формируем отчет
        report = f"📊 <b>Результат проверки</b>\n" \
                f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        all_ok = True
        for server_name, (success, message) in results.items():
            if success:
                report += f"✅ <code>{server_name}</code>: OK\n"
            else:
                report += f"❌ <code>{server_name}</code>: {message}\n"
                all_ok = False
        
        if all_ok:
            report += f"\n🎉 <b>Все серверы работают нормально!</b>"
        else:
            report += f"\n⚠️ <b>Обнаружены проблемы с серверами</b>"
        
        # Кнопка для повторной проверки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить снова", callback_data=CheckCallback(action="check").pack())]
        ])
        
        await loading_message.edit_text(report, parse_mode='HTML', reply_markup=keyboard)
        
    except Exception as e:
        error_text = f"❌ <b>Ошибка при проверке серверов</b>\n\n" \
                    f"<code>{str(e)}</code>"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Повторить", callback_data=CheckCallback(action="check").pack())]
        ])
        
        await loading_message.edit_text(error_text, parse_mode='HTML', reply_markup=keyboard)

async def main():
    """Главная функция"""
    try:
        # Проверяем конфигурацию
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен")
        if not ADMIN_ID:
            raise ValueError("ADMIN_ID не установлен")
        if not SERVERS:
            raise ValueError("Не найдено ни одного сервера для мониторинга")
        
        logger.info("Инициализация бота...")
        
        # Уведомляем администратора о запуске
        startup_message = f"🚀 <b>XRay Checker Bot запущен</b>\n\n" \
                         f"📊 Мониторинг серверов:\n"
        
        for server_name in SERVERS.keys():
            startup_message += f"• {server_name}\n"
        
        startup_message += f"\n⏱ Проверка каждые {CHECK_INTERVAL} минут"
        
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=startup_message,
            parse_mode='HTML'
        )
        
        # Запускаем мониторинг и бота параллельно
        monitoring_task = asyncio.create_task(monitoring_loop())
        polling_task = asyncio.create_task(dp.start_polling(bot))
        
        await asyncio.gather(monitoring_task, polling_task)
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
