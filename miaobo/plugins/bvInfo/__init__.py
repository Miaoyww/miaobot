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

bvf = on_command("bvf", aliases={"bvinfo"})
buffer = {
}


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
    matched_bvid = re.findall("(?<=BV)\w*", input_arg)
    bvid: str
    if len(matched_bvid) == 1:
        bvid = f"BV{matched_bvid[0]}"
        logger.info(f"得到bvid: {bvid}")
    else:
        await bot.send_group_msg(group_id=event.group_id, message=f"[CQ:at,qq={event.user_id}] 你输入的内容有误",
                                 auto_escape=False)
        return
    logger.debug(buffer)
    if bvid in buffer:
        if time.time() - buffer[bvid] < 20:
            logger.debug(f"{bvid}的请求被拒绝，短时间内请求过量")
            return
        else:
            buffer.pop(bvid)
    response_body: dict
    try:
        response_body = json.loads(
            requests.get(f"http://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=headers).content.decode(
                encoding="UTF-8"))["data"]
    except KeyError:
        await bot.send_group_msg(group_id=event.group_id, message=f"[CQ:at,qq={event.user_id}] 你输入的视频不存在",
                                 auto_escape=False)
        return
    video_info = {
        "title": response_body["title"],
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
    save_path = Path(__file__).parent / "img.png"
    os.remove(save_path) if os.path.exists(save_path) else None
    with open(save_path, 'wb') as w:
        w.write(requests.get(video_info["cover_url"], headers=headers).content)
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
    text = f"————标题———— \n{video_info['title']}\n" \
           f"————UP主———— \n{video_info['owner']} ({video_info['upload_time']}上传 -时长: {video_info['duration']})\n" \
           f"————信息———— \n{detail_text}\n" \
           f"————简介———— \n{video_info['desc']}" if video_info['desc'] != "" else None
    image_message = MessageSegment.image(save_path)
    text_message = MessageSegment.text(text)
    buffer[f"{bvid}"] = time.time()
    await bot.send(event=event, message=(image_message + text_message))
