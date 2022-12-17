from nonebot import on_command
from nonebot.adapters.onebot.v11 import *
from nonebot.plugin import PluginMetadata

formsg = on_command("formsg")

__plugin_meta__ = PluginMetadata(
    name='转发来源',
    description='获取转发消息的详情信息, 如聊天记录内出现的人的QQ号, 群号',
    usage='''使用方法: 回复聊天记录, 使用.formsg指令(只需要指令)'''
)


@formsg.handle()
async def _handle(bot: Bot, event: GroupMessageEvent):
    if not event.reply:
        return
    if not "id" in event.reply.message[0].get("data"):
        return
    forward_id = event.reply.message[0].get("data")["id"]
    forward_msg: dict = await bot.get_forward_msg(id=forward_id)
    qq_nickname: dict = {}
    for item in forward_msg["messages"]:
        qq_nickname[item["sender"]["user_id"]] = item["sender"]["nickname"]
    qq_msg = "".join(f"{i}: {qq_nickname[i]}\n" for i in qq_nickname)
    send_msg = f"群号: {forward_msg['messages'][0]['group_id']}(可能为二手转发) \n" \
               f"出现的人: \n{qq_msg}"
    await formsg.finish(MessageSegment.text(send_msg))
