from nonebot import on_command
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    PRIVATE_FRIEND,
    Message,
    MessageEvent,
    PrivateMessageEvent,
)
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from .config import Config
from .data_source import get_setu

setu_matcher = on_command(
    "setu",
    aliases={"来点涩图", "来点色图", "涩涩", "色色"},
    permission=PRIVATE_FRIEND | SUPERUSER,
)

__plugin_meta__ = PluginMetadata(
    name='Random Setu',
    description='随机一个涩图',
    usage='''使用方法: .setu|.来点涩图|.来点色图'''
)


@setu_matcher.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text()
    r18 = True if (isinstance(event, PrivateMessageEvent) and True if args.split(" ")[0] == "r18" else False) else False
    tags = args.split(" ")[r18::]
    await get_setu(setu_matcher, event, r18, tags)
    logger.debug(f"{args} | {tags} | {r18}")
