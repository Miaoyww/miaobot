# copied from https://github.com/monsterxcn/nonebot_plugin_epicfree/blob/main/nonebot_plugin_epicfree/__init__.py

from re import IGNORECASE
from traceback import format_exc
from typing import Dict

from nonebot import get_bot, get_driver, on_regex, require
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.typing import T_State

try:
    from nonebot.adapters.onebot.v11 import Bot, Event, Message, GROUP  # type: ignore
    from nonebot.adapters.onebot.v11.event import (  # type: ignore
        GroupMessageEvent,
        MessageEvent,
    )
except ImportError:
    from nonebot.adapters.cqhttp import Bot, Event, Message  # type: ignore
    from nonebot.adapters.cqhttp.event import GroupMessageEvent, MessageEvent  # type: ignore

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler  # noqa: E402

from .data_source import getEpicFree, subscribeHelper  # noqa: E402

day_of_week, hour, minute, second = 5, 8, 8, 8
epicMatcher = on_regex(r"^(epic|Epic)?喜(加|\+|＋)(一|1)$", priority=2, flags=IGNORECASE, permission=GROUP)


@epicMatcher.handle()
async def onceHandle(bot: Bot, event: Event):
    imfree = await getEpicFree()
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=imfree)  # type: ignore


epicSubMatcher = on_regex(r"^(epic|Epic)?喜(加|\+|＋)(一|1)(私聊)?订阅(删除|取消)?$", priority=1, permission=GROUP)


@epicSubMatcher.handle()
async def subHandle(event: MessageEvent, state: T_State):
    msg = event.get_plaintext()
    state["action"] = "删除" if any(s in msg for s in ["删除", "取消"]) else "启用"
    state["subType"] = "群聊"


@epicSubMatcher.got(
    "subType", prompt=Message.template("回复内容{action}群聊订阅：")
)
async def subEpic(event: MessageEvent, state: T_State):
    state["targetId"] = str(event.group_id)  # type: ignore
    state["subType"] = "群聊"
    msg = await subscribeHelper(state["action"], state["subType"], state["targetId"])
    await epicSubMatcher.finish(str(msg))


@scheduler.scheduled_job(
    "cron", day_of_week=day_of_week, hour=hour, minute=minute, second=second
)
async def weeklyEpic():
    bot = get_bot()
    whoSubscribe = await subscribeHelper()
    msgList = await getEpicFree()
    try:
        assert isinstance(whoSubscribe, Dict)
        for group in whoSubscribe["群聊"]:
            await bot.send_group_forward_msg(group_id=group, messages=msgList)
    except FinishedException:
        pass
    except Exception as e:
        logger.error(f"Epic 限免游戏资讯定时任务出错 {e.__class__.__name__}：{format_exc()}")
