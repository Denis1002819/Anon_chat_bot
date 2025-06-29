from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
import logging
import asyncio

API_TOKEN = "8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ"
ADMIN_GROUP_ID = -1002529705243

bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

active_chats = {}
admin_id = None

# Кнопки
start_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("✅ Начать", callback_data="start_chat")
)
stop_keyboard = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("⛔ Остановить", callback_data="stop_chat"),
    InlineKeyboardButton("♻ Сменить админа", callback_data="change_admin")
)
admin_stop_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("⛔ Остановить", callback_data="stop_chat")
)

@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await message.answer(
        "📌 <b>Правила:</b>\n1. Анонимность.\n2. Не нарушать законы.\n\nНажмите кнопку ниже, чтобы начать.",
        reply_markup=start_keyboard
    )

@dp.callback_query_handler(Text(equals="start_chat"))
async def start_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    await cb.message.edit_text("⏳ Заявка отправлена. Ожидайте ответа администратора.")

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"💬 Новая заявка от пользователя <code>{user_id}</code>",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🟢 Принять", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton("🔴 Отклонить", callback_data=f"decline_{user_id}")
        )
    )

@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept_request(cb: types.CallbackQuery):
    global admin_id
    user_id = int(cb.data.split("_")[1])
    admin_id = cb.from_user.id
    active_chats[user_id] = admin_id
    active_chats[admin_id] = user_id

    await bot.send_message(user_id, "✅ Админ принял вашу заявку. Можете писать.", reply_markup=stop_keyboard)
    await bot.send_message(admin_id, f"🔗 Связь с <code>{user_id}</code> установлена.", reply_markup=admin_stop_keyboard)
    await cb.message.edit_text("👤 Пользователь одобрен.")

@dp.callback_query_handler(lambda c: c.data.startswith("decline_"))
async def decline_request(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "❌ Ваша заявка отклонена.")
    await cb.message.edit_text("🚫 Пользователь отклонён.")

@dp.callback_query_handler(Text(equals="stop_chat"))
async def stop_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    target_id = None

    for uid, aid in active_chats.items():
        if uid == user_id:
            target_id = aid
            break
        elif aid == user_id:
            target_id = uid
            break

    if target_id:
        await bot.send_message(target_id, "🚫 Собеседник завершил чат.")
        if user_id in active_chats:
            del active_chats[user_id]
        if target_id in active_chats:
            del active_chats[target_id]

    await cb.message.edit_text("🔕 Вы завершили чат.")

@dp.callback_query_handler(Text(equals="change_admin"))
async def change_admin(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    if user_id in active_chats:
        target_id = active_chats[user_id]
        del active_chats[user_id]
        if target_id in active_chats:
            del active_chats[target_id]
        await bot.send_message(target_id, "🔁 Пользователь сменил админа.")
        await cb.message.edit_text("🔄 Вы отменили чат. Можете нажать «Начать» снова.")
        await bot.send_message(user_id, "💬 Вы можете отправить новую заявку", reply_markup=start_keyboard)
    else:
        await cb.message.answer("❌ Нет активного чата.")

@dp.message_handler()
async def relay_message(msg: types.Message):
    user_id = msg.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        try:
            if msg.text:
                await bot.send_message(partner_id, msg.text)
            elif msg.photo:
                await bot.send_photo(partner_id, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.document:
                await bot.send_document(partner_id, msg.document.file_id, caption=msg.caption)
            elif msg.sticker:
                await bot.send_sticker(partner_id, msg.sticker.file_id)
            elif msg.voice:
                await bot.send_voice(partner_id, msg.voice.file_id)
        except Exception as e:
            logging.error(f"Ошибка при пересылке: {e}")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

