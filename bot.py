from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor

API_TOKEN = "8139186032:AAG-vUK1grO-R_II8AxCwmb20k-dKYC7bxQ"
ADMIN_GROUP_ID = -1002529705243

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Клавиатура пользователя
user_start_kb = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("✅ Принять правила и начать", callback_data="start_chat")
)

# Клавиатура админа
admin_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("✅ Принять", callback_data="admin_accept"),
    InlineKeyboardButton("⛔ Отклонить", callback_data="admin_reject")
)

# Клавиатура управления для пользователя
user_control_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛑 Остановить", callback_data="user_stop"),
    InlineKeyboardButton("♻️ Сменить админа", callback_data="user_switch")
)

# Клавиатура управления для админа
admin_control_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛑 Остановить", callback_data="admin_stop")
)


@dp.message_handler(commands=['start'])
async def send_rules(message: types.Message):
    await message.answer(
        "📌 Правила:\n1. Запрещено оскорбление\n2. Нельзя отправлять запрещённый контент\n3. Соблюдай вежливость",
        reply_markup=user_start_kb
    )


@dp.callback_query_handler(lambda cb: cb.data == "start_chat")
async def start_chat(cb: types.CallbackQuery):
    user_id = cb.from_user.id
    await cb.message.delete()

    request_msg = await bot.send_message(
        ADMIN_GROUP_ID,
        f"💬 Новая заявка от пользователя {user_id}",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🟢 Принять", callback_data=f"accept_{user_id}"),
            InlineKeyboardButton("🔴 Отклонить", callback_data=f"reject_{user_id}")
        )
    )

    await cb.message.answer("⏳ Заявка отправлена. Ожидайте ответа от администратора.")


@dp.callback_query_handler(lambda cb: cb.data.startswith("accept_"))
async def accept_user(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "✅ Ваша заявка одобрена!", reply_markup=user_control_kb)
    await cb.message.edit_text(f"✅ Пользователь {user_id} принят.")


@dp.callback_query_handler(lambda cb: cb.data.startswith("reject_"))
async def reject_user(cb: types.CallbackQuery):
    user_id = int(cb.data.split("_")[1])
    await bot.send_message(user_id, "❌ Ваша заявка отклонена.")
    await cb.message.edit_text(f"❌ Пользователь {user_id} отклонён.")


@dp.callback_query_handler(lambda cb: cb.data in ["user_stop", "user_switch"])
async def handle_user_control(cb: types.CallbackQuery):
    if cb.data == "user_stop":
        await cb.message.answer("🛑 Вы остановили чат.")
    elif cb.data == "user_switch":
        await cb.message.answer("♻️ Запрос на смену админа отправлен.")
    await cb.answer()


@dp.callback_query_handler(lambda cb: cb.data == "admin_stop")
async def handle_admin_stop(cb: types.CallbackQuery):
    await cb.message.answer("🛑 Админ остановил чат.")
    await cb.answer()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
