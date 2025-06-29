from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ'
ADMINS_GROUP_ID = -1002529705243

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Состояния
class ChatState(StatesGroup):
    waiting = State()
    chatting = State()

# Хранилище активных чатов
active_chats = {}

# Старт команды
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("✅ Принять правила", callback_data="accept_rules"))
    await message.answer("📌 Правила:\n— Без 18+\n— Без раскрытия личности", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "accept_rules")
async def accept_rules(cb: types.CallbackQuery):
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🚀 Начать чат", callback_data="start_chat"))
    await cb.message.edit_text("Отлично! Теперь вы можете начать анонимный чат.", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "start_chat")
async def start_chat(cb: types.CallbackQuery, state: FSMContext):
    user_id = cb.from_user.id
    if user_id in active_chats:
        await cb.message.answer("⛔ Вы уже в чате.")
        return

    # Отправка в группу админов
    request_msg = await bot.send_message(
        chat_id=ADMINS_GROUP_ID,
        text=f"💬 Новая заявка от пользователя `{user_id}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🟢 Принять", callback_dat_
