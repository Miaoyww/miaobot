import asyncio
from nonebot import on_message
from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import *
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
)
from nonebot.rule import to_me
from .data_source import *

__plugin_meta__ = PluginMetadata(
    name='随机回复',
    description='随机回复一句话~',
    usage='''当你at bot并且回复一些话的时候，它可能会随机回复你()'''
)

reply = on_message(rule=to_me(), permission=GROUP)


@reply.handle()
async def _(evt: MessageEvent):
    text = str(evt.message)
    nickname = evt.sender.nickname
    user_id = evt.sender.user_id
    result = await get_reply_result(text)
    if result is not None:
        await asyncio.sleep(random.randint(5, 10) / 10)
        logger.info(f"USER {user_id}|{nickname} 发送了 {text} 其回复是 {result} ")
        if type(result) is Message:
            for item in result:
                await asyncio.sleep(random.randint(10, 20) / 10)
                await reply.send(item)
        else:
            await reply.finish(result)
    else:
        return
