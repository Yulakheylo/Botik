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
        '/add_user'
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
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('add_user', add_user)],
        states={"WAITING_FOR_NAME": [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_info)]},
        fallbacks=[MessageHandler(filters.COMMAND, unknown)],
    )
    application.add_handler(conversation_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))  # введение непонятного текстового сообщения
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))  # введение неправильной команды
    application.run_polling()


if __name__ == '__main__':
    main()