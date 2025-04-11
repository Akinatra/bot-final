
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler,
    filters, ContextTypes, ChatJoinRequestHandler
)
import asyncio
from datetime import datetime, timedelta

BOT_TOKEN = "7720035221:AAGBf8myXR5OYDiyFVL1kzHZnJyU3NNE4Ok"
responded_users = set()
pending_users = {}

THANK_YOU_MESSAGE = (
    "✨Спасибо за представление, {name}.\n\n"
    "Добро пожаловать в нашу группу 😊\n\n"
    "Ознакомьтесь, пожалуйста, с правилами группы [здесь](https://t.me/irynatest/9)."
)

REMINDER_MESSAGE = (
    "⏰ Напоминаем, что осталось немного времени, чтобы представиться.\n"
    "Пожалуйста, напишите сообщение с хэштегом *#whoareyou* в **конце текста**, иначе вы будете удалены."
)

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.chat_join_request.from_user
    chat_id = update.chat_join_request.chat.id
    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user.id)
        print(f"[JOIN] {user.first_name} одобрен ботом")
    except Exception as e:
        print(f"[SKIP JOIN] {user.first_name} уже в группе или ошибка: {e}")

    deadline = datetime.utcnow() + timedelta(hours=24)
    pending_users[user.id] = {
        "chat_id": chat_id,
        "name": user.first_name,
        "deadline": deadline
    }

    asyncio.create_task(schedule_reminder_and_kick(user.id, context))

async def filter_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    message = update.message.text.strip()

    print(f"[MESSAGE] {user.first_name}: {message}")

    if user_id not in responded_users:
        if message.lower().endswith("#whoareyou"):
            responded_users.add(user_id)
            pending_users.pop(user_id, None)
            print(f"[REPLY] {user.first_name} прошёл проверку.")
            await context.bot.send_message(
                chat_id=chat_id,
                reply_to_message_id=update.message.message_id,
                text=THANK_YOU_MESSAGE.format(name=user.first_name),
                parse_mode="Markdown"
            )
        else:
            try:
                await update.message.delete()
                print(f"[DELETE] Сообщение от {user.first_name} удалено (неверный формат)")
            except Exception as e:
                print(f"[ERROR] Не удалось удалить сообщение от {user.first_name}: {e}")

async def schedule_reminder_and_kick(user_id, context):
    await asyncio.sleep(20 * 3600)
    user_data = pending_users.get(user_id)
    if user_data:
        print(f"[REMINDER] Напоминаем {user_data['name']}")
        try:
            await context.bot.send_message(chat_id=user_data["chat_id"], text=REMINDER_MESSAGE, parse_mode="Markdown")
        except:
            pass

    await asyncio.sleep(4 * 3600)
    user_data = pending_users.get(user_id)
    if user_data:
        print(f"[REMOVE] {user_data['name']} удалён из группы.")
        try:
            await context.bot.ban_chat_member(chat_id=user_data["chat_id"], user_id=user_id)
            await context.bot.unban_chat_member(chat_id=user_data["chat_id"], user_id=user_id)
        except:
            pass
        pending_users.pop(user_id, None)

async def heartbeat():
    while True:
        print("[HEARTBEAT] Бот активен")
        await asyncio.sleep(120)

async def after_startup(app):
    asyncio.create_task(heartbeat())

if __name__ == '__main__':
    print("[START] Бот запускается...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, filter_and_reply))
    app.post_init = after_startup
    print("[READY] Бот работает и слушает сообщения...")
    app.run_polling()
