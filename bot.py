from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
import asyncio

API_TOKEN = "ТОКЕН_ЗДЕСЬ"
ADMINS = [123456789]  # замените на ID админа
ADMIN_GROUP_ID = -4869342056  # ID группы с админами

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class UserState(StatesGroup):
    waiting = State()
    connected = State()

user_admin_map = {}
admin_user_map = {}

# Команды пользователя
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🚀 Начать"))
    await message.answer("📌 Правила:
— Без 18+
— Без выяснения личности

Нажми «Начать», чтобы продолжить.", reply_markup=markup)
    await UserState.waiting.set()

@dp.message_handler(lambda msg: msg.text == "🚀 Начать", state=UserState.waiting)
async def handle_start_chat(message: types.Message, state: FSMContext):
    for admin_id in ADMINS:
        await bot.send_message(admin_id, f"📬 Новая заявка от пользователя ID {message.from_user.id}", reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("Принять", callback_data=f"accept_{message.from_user.id}")
        ))
    await bot.send_message(ADMIN_GROUP_ID, f"📬 Новая заявка от пользователя ID {message.from_user.id}")
    await message.answer("⏳ Ожидай, пока админ подключится...")

@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept_chat(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    admin_id = callback.from_user.id

    if admin_id in admin_user_map:
        await callback.answer("❌ У вас уже есть активный пользователь.")
        return

    user_admin_map[user_id] = admin_id
    admin_user_map[admin_id] = user_id

    await bot.send_message(user_id, "✅ Админ подключился! Можешь писать.")
    await bot.send_message(admin_id, "✅ Вы подключены к пользователю.")
    await callback.answer()

    await dp.current_state(user=user_id).set_state(UserState.connected)

@dp.message_handler(lambda msg: msg.text == "⛔ Остановить", state=UserState.connected)
async def stop_chat_user(message: types.Message, state: FSMContext):
    admin_id = user_admin_map.get(message.from_user.id)
    if admin_id:
        await bot.send_message(admin_id, "❌ Пользователь завершил диалог.")
        del admin_user_map[admin_id]
        del user_admin_map[message.from_user.id]
    await message.answer("❌ Диалог завершён.")
    await state.finish()

@dp.message_handler(lambda msg: msg.text == "🔁 Сменить админа", state=UserState.connected)
async def switch_admin(message: types.Message, state: FSMContext):
    old_admin = user_admin_map.get(message.from_user.id)
    if old_admin:
        await bot.send_message(old_admin, "🔁 Пользователь запросил нового админа.")
        del admin_user_map[old_admin]
        del user_admin_map[message.from_user.id]
    await cmd_start(message, state)

@dp.message_handler(lambda msg: msg.from_user.id in admin_user_map.values(), state='*')
async def admin_stop_chat(message: types.Message):
    if message.text == "⛔ Остановить":
        user_id = admin_user_map.get(message.from_user.id)
        if user_id:
            await bot.send_message(user_id, "❌ Админ завершил диалог.")
            del user_admin_map[user_id]
            del admin_user_map[message.from_user.id]
            await message.answer("❌ Диалог завершён.")

@dp.message_handler(lambda msg: msg.from_user.id in user_admin_map, state=UserState.connected)
async def relay_user_message(message: types.Message):
    admin_id = user_admin_map[message.from_user.id]
    await bot.send_message(admin_id, f"👤 Пользователь:
{message.text}")

@dp.message_handler(lambda msg: msg.from_user.id in admin_user_map)
async def relay_admin_message(message: types.Message):
    user_id = admin_user_map[message.from_user.id]
    await bot.send_message(user_id, f"🛡 Админ:
{message.text}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
