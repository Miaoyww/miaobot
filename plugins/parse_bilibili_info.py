import os
import re
import time
from decimal import Decimal
from pathlib import Path
import requests
import json
from urllib import request
from nonebot import on_command, logger
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import *
from nonebot.plugin import PluginMetadata

bvf = on_command("bvf", aliases={"bvinfo"})

__plugin_meta__ = PluginMetadata(
    name='Bilibili Video Info',
    description='获取Bilibili视频的详情信息',
    usage='''使用方法: .bvf <Bvid>|<Aid>'''
)


def bv2av(x):
    table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'  # 码表
    tr = {}  # 反查码表
    # 初始化反查码表
    for i in range(58):
        tr[table[i]] = i
    s = [11, 10, 3, 8, 4, 6]  # 位置编码表
    XOR = 177451812  # 固定异或值
    ADD = 8728348608  # 固定加法值
    r = 0
    for i in range(6):
        r += tr[x[s[i]]] * 58 ** i
    return (r - ADD) ^ XOR


@bvf.handle()
async def _handle(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/107.0.0.0 Mobile Safari/537.36 Edg/107.0.1418.35 ",
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json;charset=UTF-8"
    }
    input_arg = arg.extract_plain_text()
    matched_b23tv = re.findall("(?<=b23.tv/)\w*", input_arg)
    if len(matched_b23tv) == 1:
        input_arg = request.urlopen(f"https://b23.tv/{matched_b23tv[0]}").geturl()
    matched_acode = re.search("av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})", input_arg)
    if matched_acode is None:
        return

    if matched_acode[0][0:2] == "BV":
        aid = bv2av(matched_acode[0])
    else:
        aid = matched_acode[0].replace("av", "")

    logger.info(f"得到aid: {aid}")
    response_body: dict
    try:
        response_body = json.loads(
            requests.get(f"http://api.bilibili.com/x/web-interface/view?aid={aid}", headers=headers).content.decode(
                encoding="UTF-8"))["data"]
    except KeyError:
        await bot.send_group_msg(group_id=event.group_id, message=f"[CQ:at,qq={event.user_id}] 你输入的视频不存在",
                                 auto_escape=False)
        return
    video_info = {
        "title": response_body["title"],
        "bvid": response_body["bvid"],
        "cover_url": response_body["pic"],
        "upload_time": time.strftime("%Y/%m/%d %H:%M", time.localtime(response_body["pubdate"])),
        "duration": f"{response_body['duration'] // 60}:{response_body['duration'] - response_body['duration'] // 60 * 60}",
        "desc": f"{response_body['desc']}",
        "view": response_body["stat"]["view"],
        "danmu": response_body["stat"]["danmaku"],
        "like": response_body["stat"]["like"],
        "coin": response_body["stat"]["coin"],
        "share": response_body["stat"]["share"],
        "favorite": response_body["stat"]["favorite"],
        "owner": f"{response_body['owner']['name']}",
        "owner_face": f"{response_body['owner']['face']}"
    }
    img_data = requests.get(video_info["cover_url"], headers=headers).content
    logger.debug("图像准备完成, 准备发送")

    if len(video_info['desc'].split("\n")) > 5:
        if len(video_info['desc'].split("\n")) > 5:
            logger.debug("简介过长, 准备取前5行")
            video_info["desc"] = "\n".join(video_info["desc"].split("\n")[:5])
            video_info["desc"] += "...\n  (由于简介过长, 已截取前5行)"
    detail_text = f"{Decimal(video_info['view'] / 10000).quantize(Decimal('0.0')) if video_info['view'] > 10000 else video_info['view']}" \
                  f"{'w' if video_info['view'] > 10000 else ''}次观看 · " \
                  f"{Decimal(video_info['like'] / 10000).quantize(Decimal('0.0')) if video_info['like'] > 10000 else video_info['like']}" \
                  f"{'w' if video_info['like'] > 10000 else ''}点赞 · " \
                  f"{Decimal(video_info['coin'] / 10000).quantize(Decimal('0.0')) if video_info['coin'] > 10000 else video_info['coin']}" \
                  f"{'w' if video_info['coin'] > 10000 else ''}硬币 · " \
                  f"{Decimal(video_info['favorite'] / 10000).quantize(Decimal('0.0')) if video_info['favorite'] > 10000 else video_info['favorite']}" \
                  f"{'w' if video_info['favorite'] > 10000 else ''}收藏"
    text = f"https://www.bilibili.com/video/{video_info['bvid']}\n" \
           f"————标题———— \n{video_info['title']}\n" \
           f"————UP主———— \n{video_info['owner']} ({video_info['upload_time']}上传 -时长: {video_info['duration']})\n" \
           f"————信息———— \n{detail_text}\n" \
           f"————简介———— \n{video_info['desc'] if video_info['desc'] != '' else '来自半夏的消息——暂无简介哦~'}"

    image_message = MessageSegment.image(img_data)
    text_message = MessageSegment.text(text)
    await bot.send(event=event, message=(image_message + text_message))
