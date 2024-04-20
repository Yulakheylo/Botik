import logging
from telegram.ext import Updater, CommandHandler, Application, MessageHandler, ConversationHandler, filters
from telegram import ReplyKeyboardMarkup
from telebot import types
import sqlite3
from config import BOT_TOKEN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        f"Добро пожаловать в бот-планировщик, {user.mention_html()}!\n"
        "Чтобы просмотреть все возможности бота, воспользуйтесь командой /help.",
    )
    return ConversationHandler.END


# добавление первой информации о пользователе, переход в состояние добавления
async def add_user(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет! Введи свою информацию, которую хочешь сохранить в базе данных.",
    )
    return "WAITING_FOR_NAME"


# измемение информации переход в состояние обновления
async def add_info(update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет! Введи свою информацию, которую хочешь сохранить в базе данных.",
    )
    return "WAITING_FOR_UPDATE_INFO"


# сохранение первой информации о пользоваетеле
async def handle_user_info(update, context):
    user_info = update.message.text
    chat_id = update.effective_chat.id

    # Соединение с базой данных
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()

    # Создание таблицы, если она еще не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            user_info TEXT
        )
    ''')

    # Сохранение данных в базу данных
    cursor.execute('''
        INSERT INTO users (chat_id, user_info) VALUES (?, ?)
    ''', (chat_id, user_info))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Информация '{user_info}' успешно сохранена."
    )
    return ConversationHandler.END


# профиль где записана информация о пользователе.
async def profile(update, context):
    # Получаем информацию о пользователе из базы данных
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    user_id = update.effective_user.id
    cursor.execute("SELECT * FROM users WHERE chat_id = ?", (user_id,))
    user_info = cursor.fetchone()

    # Если пользователь не найден в базе данных, отправляем сообщение об ошибке
    if user_info is None:
        await update.message.reply_text("Вы еще не добавили информацию о себе. Используйте команду /add_user.")
    else:
        # Формируем сообщение с информацией о пользователе
        message = f"Ваша информация:\n{user_info[1]}"
        await update.message.reply_text(message)

    conn.close()


# обновление информации
async def update_info(update, context):
    user_info = update.message.text
    chat_id = update.effective_chat.id

    # Соединение с базой данных
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()

    # Получаем текущую информацию о пользователе
    cursor.execute("SELECT user_info FROM users WHERE chat_id = ?", (chat_id,))
    current_info = cursor.fetchone()

    # Если пользователь уже добавил информацию
    if current_info is not None:
        # Объединяем текущую информацию и новую информацию в одну строку
        combined_info = f"{current_info[0]}\n{user_info}"
    else:
        combined_info = user_info

    # Обновление данных в базе данных
    cursor.execute('''
        UPDATE users SET user_info = ? WHERE chat_id = ?
    ''', (combined_info, chat_id))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"Информация '{user_info}' успешно обновлена."
    )
    return ConversationHandler.END


# подтверждение удаления информации из профиля
async def delete_info(update, context):
    await update.message.reply_text(f'Вы точно хотите удалить информацию из профиля?',
                                    reply_markup=ReplyKeyboardMarkup(
                                        [["Да"], ["Нет"]],
                                        one_time_keyboard=False))
    return "DELE"


# удаление информации из профиля
async def delete_info_user(update, context):
    subject = update.message.text
    user_id = update.effective_user.id

    # Соединение с базой данных
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    if subject == 'Да':
        # Удаление данных о пользователе из базы данных
        cursor.execute('''
            DELETE FROM users WHERE chat_id = ?
        ''', (user_id,))
        await update.message.reply_text(
            f"Информация о Вас успешно удалена из профиля."
        )
        reply_markup = markup
    if subject == 'Нет':
        await update.message.reply_text(
            f"Действие отменено."
        )
        reply_markup = markup
    conn.commit()
    conn.close()
    return ConversationHandler.END


# Подсказки с возможными командами бота
async def help(update, context):
    await update.message.reply_text(
        '/add_task - добавление задачи\n'
        '/assign_task - добавление ответственного за задачу и срок её выполнения.\n'
        "/list_task - список всех задач, вместе с ее ответственными и сроком выполнения.\n"
        "/get_task - информация о конкретной задаче\n"
        '/delete_task - удаление задачи\n'
        '/complete_task - выполнение задачи.\n'
        '/responsible_task - ...\n'
        '/edit_task - ... \n'
        '/user_task \n'
        '/add_user - заполнить информацию о себе (используеться 1 раз)\n'
        '/add_info - изменить информацию о себе\n'
        '/profile - посмотеть информацию о себе'
    )
    return ConversationHandler.END


# Ответ на неизвестное сообщение
async def unknown(update, context):
    await update.message.reply_text(
        "Извините, я не могу понять Ваш запрос. Пожалуйста, воспользуйтесь командой /help для получения помощи.")


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("profile", profile))
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('add_user', add_user), CommandHandler('add_info', add_info)],
        states={"WAITING_FOR_NAME": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_info)],
                "WAITING_FOR_UPDATE_INFO": [MessageHandler(filters.TEXT & ~filters.COMMAND, update_info)]},
        fallbacks=[MessageHandler(filters.COMMAND, unknown)],
    )
    del_user_info = ConversationHandler(
        entry_points=[CommandHandler('delete_info', delete_info)],
        states={"DELE": [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_info_user)]},
        fallbacks=[MessageHandler(filters.COMMAND, unknown)],
    )
    application.add_handler(del_user_info)
    application.add_handler(conversation_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))  # введение непонятного текстового сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))  # введение неправильной команды
    application.run_polling()


if __name__ == '__main__':
    main()
