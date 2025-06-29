from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
import logging

TOKEN = "8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ"
ADMIN_GROUP_ID = -1002529705243

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# active_chats: user_id -> admin_id
active_chats = {}

# --- Кнопки ---
start_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Начать", callback_data="start_chat"))
user_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛑 Остановить", callback_data="stop_chat"),
    InlineKeyboardButton("🔁 Сменить админа", callback_data="change_admin")
)
admin_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🛑 Остановить", callback_data="stop_chat"))

# --- Команды ---
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await message.answer(
        "📌 <b>Правила:</b>\n1. Анонимность.\n2. Не нарушать закон.\n\nНажмите кнопку ниже, чтобы начать:",
        reply_markup=start_kb
    )

@dp.callback_query_handler(Text(equals="start_chat"))
async def send_request(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    await bot.send_message(
        ADMIN_GROUP_ID,
        f"📥 Новая заявка от пользователя: <code>{user_id}</code>",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_{user_id}")
        )
    )
    await cb.message.edit_text("⏳ Заявка отправлена. Ожидайте ответа администратора.")

@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept_request(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    active_chats[user_id] = cb.from_user.id
    await bot.send_message(user_id, "✅ Вас подключили к чату. Можете писать.", reply_markup=user_kb)
    await cb.message.edit_text("✅ Пользователь подключён.", reply_markup=admin_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("decline_"))
async def decline_request(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "❌ Ваша заявка была отклонена.")
    await cb.message.edit_text("❌ Пользователь отклонён.")

@dp.callback_query_handler(Text(equals="stop_chat"))
async def stop_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    target_id = None
    for u, a in active_chats.items():
        if u == user_id:
            target_id = a
        elif a == user_id:
            target_id = u

    if target_id:
        await bot.send_message(target_id, "🚫 Собеседник завершил чат.")
        del active_chats[user_id] if user_id in active_chats else active_chats[target_id]
    await cb.message.edit_text("🔕 Вы завершили чат.")

@dp.callback_query_handler(Text(equals="change_admin"))
async def change_admin(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    if user_id in active_chats:
        admin_id = active_chats.pop(user_id)
        await bot.send_message(admin_id, "🔁 Пользователь запросил нового собеседника.")
        await bot.send_message(user_id, "🔄 Ваша заявка отправлена повторно.", reply_markup=start_kb)

@dp.message_handler()
async def forward_messages(msg: types.Message):
    sender_id = msg.from_user.id
    if sender_id in active_chats:
        recipient_id = active_chats[sender_id]
        await bot.send_message(recipient_id, f"💬 Сообщение:\n{msg.text}")
    elif sender_id in active_chats.values():
        for uid, aid in active_chats.items():
            if aid == sender_id:
                await bot.send_message(uid, f"👮 Ответ от админа:\n{msg.text}")
                break

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
