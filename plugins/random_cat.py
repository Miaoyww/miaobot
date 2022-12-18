from urllib import request

from nonebot import on_command
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11 import MessageSegment, Message
from nonebot.adapters.onebot.v11.event import Event
import httpx
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

cat = on_command("cat", aliases={"jrcat", "今日猫猫", "猫猫"}, block=True, priority=5)

__plugin_meta__ = PluginMetadata(
    name='每日猫猫',
    description='随机获取一只猫猫~',
    usage='''使用方法: .cat'''
)


@cat.handle()
async def _(bot: Bot, ev: Event, arg: Message = CommandArg()):
    if (code := arg.extract_plain_text()).isdigit():
        async with httpx.AsyncClient() as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
            img = await client.get(f"https://http.cat/{code}", headers=headers)
            await bot.send(event=ev, message=MessageSegment.image(img.content))
            return
    times = 0
    while True:
        try:
            async with httpx.AsyncClient() as client:
                img = await client.get(url="https://edgecats.net/")
                await bot.send(event=ev, message=MessageSegment.image(img.content))
                break
        except:
            if times < 3:
                times += 1
                continue
            else:
                return await bot.send(event=ev, message="悲 猫猫获取失败力!")
