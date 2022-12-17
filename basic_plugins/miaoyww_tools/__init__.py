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
    # 由于文件目录的调整, 直接更新会导致机器人损坏
    # await entry_update_plugins(matcher)
    await matcher.send("更新插件维护中")

