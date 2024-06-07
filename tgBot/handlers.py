from aiogram.filters import Command
from aiogram.types import Message

from router import MyRouter
from tgBot.content.text import *

router = MyRouter()


@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer(start_msg)


@router.message()
async def message_handler(msg: Message):
    if msg.content_type == "document" or msg.content_type == "text":
        game = ""
        if msg.content_type == "document":
            file = await msg.bot.get_file(msg.document.file_id)
            binary = await msg.bot.download_file(file.file_path)
            game = binary.read().decode('utf-8')
        elif msg.content_type == "text":
            game = msg.text

        try:
            res = router.model.predict(game)
        except Exception:
            await msg.reply(err_predict_msg)
            return

        if res == 0:
            await msg.reply(newbie)
            return
        elif res == 1:
            await msg.reply(advanced)
            return
        elif res == 2:
            await msg.reply(professional)
            return

    await msg.reply(err_msg)
