import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '6428099161:AAGrZB9WKRQmjI5dcToFgkJktR_mhG6xU0E'
ADMINS = [6774188449]
ADMIN_GROUP_ID = -1002529705243  # обновлённый ID группы

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    chatting = State()

# Кнопки
start_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Начать", callback_data="start_chat"))
user_kb = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("❌ Остановить", callback_data="stop_chat"),
    InlineKeyboardButton("🔁 Сменить админа", callback_data="change_admin")
)
admin_kb = InlineKeyboardMarkup().add(InlineKeyboardButton("❌ Остановить", callback_data="admin_stop"))

@dp.message_handler(commands="start")
async def start_cmd(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("""📌 Правила:
1. Никакого 18+ контента
2. Без выяснения личности
3. Общение строго анонимно
""", reply_markup=start_kb)

@dp.callback_query_handler(lambda c: c.data == "start_chat")
async def start_chat(cb: types.CallbackQuery, state: FSMContext):
    await cb.message.delete()
    await cb.message.answer("🔄 Ожидание администратора...", reply_markup=user_kb)
    for admin_id in ADMINS:
        await bot.send_message(admin_id, f"💬 Новая заявка от пользователя {cb.from_user.id}", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{cb.from_user.id}")
        ))
    await bot.send_message(ADMIN_GROUP_ID, f"💬 Новая заявка от пользователя {cb.from_user.id}")

@dp.callback_query_handler(lambda c: c.data.startswith("accept_"))
async def accept_chat(cb: types.CallbackQuery, state: FSMContext):
    user_id = int(cb.data.split("_")[1])
    await state.update_data(user=user_id, admin=cb.from_user.id)
    await bot.send_message(cb.from_user.id, f"✅ Вы подключены к пользователю {user_id}", reply_markup=admin_kb)
    await bot.send_message(user_id, "✅ Админ подключился. Вы можете писать.")
    await state.set_state(Form.chatting)

@dp.message_handler(state=Form.chatting)
async def chat_flow(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.from_user.id == data.get("admin"):
        await bot.send_message(data["user"], f"👤 Админ:\n{message.text}", reply_markup=user_kb)
    elif message.from_user.id == data.get("user"):
        await bot.send_message(data["admin"], f"🙋‍♂️ Пользователь:\n{message.text}", reply_markup=admin_kb)

@dp.callback_query_handler(lambda c: c.data in ["stop_chat", "change_admin", "admin_stop"], state=Form.chatting)
async def stop_chat(cb: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    reason = "Остановлено пользователем." if cb.data != "admin_stop" else "Остановлено админом."
    if cb.from_user.id == data.get("user") or cb.from_user.id == data.get("admin"):
        await bot.send_message(data["user"], f"🔒 Чат завершён.\n{reason}")
        await bot.send_message(data["admin"], f"🔒 Чат завершён.\n{reason}")
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
