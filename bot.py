from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from aiogram.dispatcher import filters
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

import logging
from collections import defaultdict

API_TOKEN = '8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ'
ADMIN_GROUP_ID = -1002529705243  # ID группы с админами

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Пары user_id <-> admin_id
active_chats = defaultdict(dict)

# Старт для пользователя
@dp.message_handler(CommandStart())
async def send_welcome(message: types.Message):
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🚀 Начать", callback_data="start_chat"))
    await message.answer(
        "📌 Правила:\n1. Общение происходит анонимно\n2. Не передавайте свои контакты\n\nНажмите кнопку ниже, чтобы начать.",
        reply_markup=kb
    )

# Пользователь нажал "начать"
@dp.callback_query_handler(lambda c: c.data == "start_chat")
async def start_chat(cb: types.CallbackQuery):
    await cb.message.edit_text("⏳ Ожидаем подтверждения от администратора...")

    markup = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🟢 Принять", callback_data=f"accept_{cb.from_user.id}"),
        InlineKeyboardButton("🔴 Отклонить", callback_data=f"reject_{cb.from_user.id}")
    )

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"💬 Новая заявка от пользователя",
        reply_markup=markup
    )

# Админ нажал "Принять"
@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept_user(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    admin_id = cb.from_user.id

    active_chats[user_id]['admin'] = admin_id
    active_chats[admin_id]['user'] = user_id

    await bot.send_message(user_id, "✅ Вас подключили к чату с админом. Напишите сообщение.")
    await bot.send_message(admin_id, "✅ Вы подключены к пользователю. Напишите сообщение.")

# Админ нажал "Отклонить"
@dp.callback_query_handler(lambda c: c.data.startswith("reject_"))
async def reject_user(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "❌ Админ отклонил запрос.")

# Обработка всех сообщений
@dp.message_handler()
async def relay_messages(message: types.Message):
    uid = message.from_user.id
    if uid in active_chats:
        partner_id = active_chats[uid].get('admin') or active_chats[uid].get('user')
        if partner_id:
            forwarded = await bot.forward_message(partner_id, message.chat.id, message.message_id)
        else:
            await message.reply("⏳ Ожидайте подключения...")
    else:
        await message.reply("⏳ Вы не подключены. Нажмите /start")

# Остановка чата
@dp.message_handler(commands=["stop"])
async def stop_chat(message: types.Message):
    uid = message.from_user.id
    if uid in active_chats:
        partner_id = active_chats[uid].get('admin') or active_chats[uid].get('user')
        await bot.send_message(partner_id, "🚫 Собеседник завершил чат.")
        await message.reply("❌ Вы завершили чат.")

        del active_chats[partner_id]
        del active_chats[uid]
    else:
        await message.reply("Вы не находитесь в чате.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)
