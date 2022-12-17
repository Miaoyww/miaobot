from nonebot.adapters.onebot.v11 import PRIVATE_FRIEND, GROUP, MessageEvent
from nonebot.internal.matcher import Matcher
from nonebot.plugin import on_command
from nonebot.permission import SUPERUSER
import nonebot
from .data_source import *

driver = nonebot.get_driver()


@driver.on_bot_connect
async def on_bot_connect():
    pass


update = on_command("upd", aliases={"更新", "update"}, permission=SUPERUSER)


@update.handle()
async def _(matcher: Matcher):
    await entry_update_plugins(matcher)


