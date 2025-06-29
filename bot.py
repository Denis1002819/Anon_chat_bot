from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
import logging

TOKEN = "8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ"
ADMIN_GROUP_ID = -1002529705243

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

sessions = {}

start_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("✅ Начать", callback_data="start_chat")
)

user_keyboard = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("🛑 Остановить", callback_data="stop_chat"),
    InlineKeyboardButton("🔁 Сменить админа", callback_data="change_admin")
)

admin_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛑 Остановить", callback_data="stop_chat")
)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "📌 Правила:\n1. Анонимность.\n2. Запрещён спам и оскорбления.\n\nНажмите кнопку, чтобы начать:",
        reply_markup=start_keyboard
    )

@dp.callback_query_handler(Text(equals="start_chat"))
async def request_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    if user_id in sessions:
        await cb.message.edit_text("⏳ Вы уже подали заявку.")
        return

    msg = await bot.send_message(
        ADMIN_GROUP_ID,
        f"📨 Новая заявка от пользователя.",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🟢 Принять", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton("🔴 Отклонить", callback_data=f"decline_{user_id}")
        )
    )
    sessions[user_id] = {"status": "pending", "request_msg_id": msg.message_id}
    await cb.message.edit_text("✅ Заявка отправлена. Ожидайте ответа.")

@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    admin_id = cb.from_user.id
    sessions[user_id] = {"admin_id": admin_id}
    sessions[admin_id] = {"user_id": user_id}
    await bot.send_message(user_id, "✅ Админ подключился. Можете писать.", reply_markup=user_keyboard)
    await bot.send_message(admin_id, "✅ Вы подключены к пользователю.", reply_markup=admin_keyboard)
    await cb.message.edit_text("Пользователь принят.")

@dp.callback_query_handler(lambda c: c.data.startswith("decline_"))
async def decline(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "❌ Ваша заявка отклонена.")
    await cb.message.edit_text("❌ Заявка отклонена.")
    sessions.pop(user_id, None)

@dp.callback_query_handler(Text(equals="stop_chat"))
async def stop_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    partner_id = sessions.get(user_id, {}).get("admin_id") or sessions.get(user_id, {}).get("user_id")
    if partner_id:
        await bot.send_message(partner_id, "❌ Собеседник завершил чат.")
        sessions.pop(partner_id, None)
    sessions.pop(user_id, None)
    await cb.message.edit_text("🔕 Чат завершён.")

@dp.callback_query_handler(Text(equals="change_admin"))
async def change_admin(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    partner_id = sessions.get(user_id, {}).get("admin_id")
    if partner_id:
        await bot.send_message(partner_id, "🔄 По
