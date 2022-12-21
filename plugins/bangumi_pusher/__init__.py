import time
from datetime import datetime
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import MessageEvent, Message, GroupMessageEvent
from nonebot.internal.params import ArgStr, Arg
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from configs.config import config
from .data_source import *

add_sub = on_command("addsub", aliases={"添加订阅", "增加订阅"}, permission=SUPERUSER)
del_sub = on_command("delsub", aliases={"删除订阅"}, permission=SUPERUSER)
lst_sub = on_command("lstsub", aliases={"查看订阅"}, permission=SUPERUSER)
pusher_add = on_command("pd", aliases={"添加本群通知"}, permission=SUPERUSER)


@pusher_add.handle()
async def _(evt: GroupMessageEvent):
    await pusher_add.finish(await add_group_sub(evt.group_id))


@add_sub.handle()
async def _(evt: MessageEvent, state: T_State, args: Message = CommandArg()):
    msg = args.extract_plain_text().strip()
    if not msg.isdigit():
        search_result = await get_search_results(msg)
        search_map = {}

        for index, item in enumerate(search_result):
            search_map[index] = item
        content = f"\n".join(
            [
                "——————\n"
                f"{x + 1}. "
                f"{search_map[x].title}({search_map[x].season_type_name}) mid:{search_map[x].media_id} \n"
                f"上传时间: {datetime.fromtimestamp(search_map[x].pubtime).strftime('%Y年%m月%d日')}"
                for x in search_map.keys()
            ]
        )
        reply = "* 找到以下番剧, 请输入mid以确认 *\n" + content
        await add_sub.finish(MessageSegment.text(reply))
    else:
        if isinstance(evt, GroupMessageEvent):
            state["sub_user"] = f"{evt.user_id}:{evt.group_id}"
        else:
            state["sub_user"] = evt.user_id
        state["id"] = int(msg)


@add_sub.got("sub_user")
@add_sub.got("id")
async def _(id_: str = ArgStr("id"), sub_user: str = ArgStr("sub_user")):
    season_obj = await get_season_obj(id_)
    if season_obj.status == 200:
        await add_sub.finish(await add_season_sub(season_obj))
    else:
        await add_sub.finish(MessageSegment.at(sub_user) + MessageSegment.text("您输入的mid有误"))


@lst_sub.handle()
async def _(evt: MessageEvent, args: Message = CommandArg()):
    await lst_sub.finish(await get_season_lst())


@del_sub.handle()
async def _(evt: MessageEvent, args: Message = CommandArg()):
    index = args.extract_plain_text()
    if index.isdigit():
        await lst_sub.finish(await del_season_sub(int(index)))
    else:
        await lst_sub.finish(MessageSegment.at(evt.user_id) + MessageSegment.text("错误的索引值, 要求是正整数"))
