from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
import logging

TOKEN = "8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ"
ADMIN_GROUP_ID = -1002529705243  # ID админ-группы

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

user_sessions = {}

start_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Начать", callback_data="start_chat"))

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("📌 Правила:\n1. Анонимность.\n2. Не нарушать законы.\n\nНажмите кнопку ниже, чтобы начать:", reply_markup=start_kb)

@dp.callback_query_handler(Text(equals="start_chat"))
async def start_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    request_msg = await bot.send_message(
        ADMIN_GROUP_ID,
        f"💬 Новая заявка от пользователя `{user_id}`",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🟢 Принять", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton("🔴 Отклонить", callback_data=f"decline_{user_id}")
        ),
        parse_mode="Markdown"
    )
    user_sessions[user_id] = {"request_msg_id": request_msg.message_id}
    await cb.message.edit_text("⏳ Заявка отправлена. Ожидайте ответа администратора.")

@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept_user(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "✅ Ваша заявка принята. Ожидайте подключения.")
    await cb.message.edit_text("🔔 Пользователь одобрен.")

@dp.callback_query_handler(lambda c: c.data.startswith("decline_"))
async def decline_user(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "❌ Ваша заявка была отклонена.")
    await cb.message.edit_text("❌ Пользователь отклонён.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
