import os
import dotenv
import telegram

dotenv.load_dotenv("src/.env")

bot = telegram.Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
chat_id = os.environ["TELEGRAM_CHAT_ID"]


async def send_message(text):
    async with bot:
        await bot.send_message(text=text, chat_id=chat_id)
