import asyncio
import json
import os

import ollama
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from loguru import logger

from prompt_builder import build_prompt, find_client

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не найден BOT_TOKEN в .env")

with open("crm.json", encoding="utf-8") as f:
    CRM_DATA_LIST = json.load(f)["clients"]

LOG_FILE = "chat_history.log"
logger.add(LOG_FILE, encoding="utf-8", rotation="10 MB", enqueue=True)

MODEL_NAME = "llama3"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id

    # Сбросить данные пользователя при /start
    if hasattr(message.bot, "user_to_client"):
        message.bot.user_to_client.pop(user_id, None)
    if hasattr(message.bot, "user_histories"):
        message.bot.user_histories.pop(user_id, None)

    logger.info(f"USER_ID: {user_id} | Диалог сброшен по /start")
    await message.answer(
        "Здравствуйте! Я — ИИ-менеджер премиального автосалона.\n"
        "Пожалуйста, представьтесь: отправьте своё имя (то же, что в CRM)."
    )


@dp.message()
async def message_handler(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id

    if not hasattr(message.bot, "user_to_client"):
        message.bot.user_to_client = {}
    if not hasattr(message.bot, "user_histories"):
        message.bot.user_histories = {}

    user_to_client = message.bot.user_to_client
    user_histories = message.bot.user_histories

    # Получаем имя клиента
    if user_id not in user_to_client:
        client_name = text
        client_data = find_client(CRM_DATA_LIST, client_name)
        if client_data is None:
            logger.warning(f"USER_ID: {user_id} | Имя '{client_name}' не найдено в CRM")
            await message.answer("Извини, не нашёл тебя в CRM. Проверь имя и повтори.")
            return
        user_to_client[user_id] = client_name
        user_histories[user_id] = []
        logger.info(
            f"USER_ID: {user_id} | CLIENT_NAME: {client_name} успешно идентифицирован"
        )
        await message.answer(f"Привет, {client_name}! Чем могу помочь?")
        return

    client_name = user_to_client[user_id]
    client_data = find_client(CRM_DATA_LIST, client_name)

    prompt = build_prompt(client_data, text)
    history = user_histories.get(user_id, [])
    history.append({"role": "user", "content": prompt})

    logger.info(f"CLIENT_NAME: {client_name} | USER: {text}")

    try:
        response = ollama.chat(model=MODEL_NAME, messages=history)
        bot_reply = response["message"]["content"]
    except Exception as e:
        bot_reply = f"[Ошибка LLM: {e}]"
        logger.error(f"CLIENT_NAME: {client_name} | Ошибка LLM: {e}")

    history.append({"role": "assistant", "content": bot_reply})
    user_histories[user_id] = history

    logger.info(f"CLIENT_NAME: {client_name} | BOT: {bot_reply}\n")
    await message.answer(bot_reply)


async def main():
    try:
        print("Бот запущен...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
