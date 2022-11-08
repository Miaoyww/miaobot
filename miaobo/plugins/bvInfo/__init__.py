import re
import time
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import requests
import json
from PIL import Image, ImageFont, ImageDraw
from urllib import request
from nonebot import on_command, logger
from nonebot.matcher import Matcher
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
    image = Image.new("RGB", (530, 620), (245, 243, 243))
    image.paste((220, 220, 220), (0, 480, 530, 620))
    cover = Image.open(BytesIO(
        requests.get(video_info["cover_url"], headers=headers).content)).resize((464, 290), Image.ANTIALIAS)
    cover_size = (34, 34, 34 + cover.width, 34 + cover.height)
    image.paste(cover, cover_size)

    face = Image.open(BytesIO(
        requests.get(video_info["owner_face"], headers=headers).content)).resize((80, 80), Image.ANTIALIAS)
    face_size = (34, 510, 34 + face.width, 510 + face.height)
    face_draw = ImageDraw.Draw(image)
    face_draw.text((face.width + 50, face_size[1] + 10), f"{video_info['owner']}\n{video_info['upload_time']} 上传",
                   fill=(20, 20, 20),
                   font=ImageFont.truetype(str(Path(__file__).parent / "fonts/SourceHanSansSC-Heavy-2.otf"), 21))
    image.paste(face, face_size)

    cover_draw = ImageDraw.Draw(image)
    least_text = video_info["title"]
    if len(video_info["title"]) >= 12:
        least_text = "\n".join(re.findall('.{12}', video_info['title']))
        if len(least_text) < len(video_info["title"]):
            least_text += f"..."
    detail_text = f"\n" \
                  f"{Decimal(video_info['view'] / 10000).quantize(Decimal('0.0')) if video_info['view'] > 10000 else video_info['view']}" \
                  f"{'w' if video_info['view'] > 10000 else ''}次观看·" \
                  f"{Decimal(video_info['like'] / 10000).quantize(Decimal('0')) if video_info['like'] > 10000 else video_info['like']}" \
                  f"{'w' if video_info['like'] > 10000 else ''}点赞·" \
                  f"{Decimal(video_info['coin'] / 10000).quantize(Decimal('0')) if video_info['coin'] > 10000 else video_info['coin']}" \
                  f"{'w' if video_info['coin'] > 10000 else ''}硬币·" \
                  f"{Decimal(video_info['favorite'] / 10000).quantize(Decimal('0')) if video_info['favorite'] > 10000 else video_info['favorite']}" \
                  f"{'w' if video_info['favorite'] > 10000 else ''}收藏"
    cover_draw.text((cover_size[0], cover_size[3]), least_text, fill=(20, 20, 20),
                    font=ImageFont.truetype(str(Path(__file__).parent / "fonts/SourceHanSansSC-Heavy-2.otf"), 30))
    cover_draw.text((cover_size[0], 410), detail_text, fill=(50, 50, 50),
                    font=ImageFont.truetype(str(Path(__file__).parent / "fonts/SourceHanSansSC-Heavy-2.otf"), 21))
    image.save(save_path)
    logger.debug("图像准备完成, 准备发送")
    send_image = MessageSegment.image(save_path)
    logger.debug("send_image OK")
    buffer[f"{bvid}"] = time.time()
    await bvf.finish(send_image)
