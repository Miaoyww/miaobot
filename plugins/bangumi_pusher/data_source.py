import json
from json import JSONDecodeError

from configs.config import config
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from httpx import AsyncClient, Response
from pydantic import BaseModel
from nonebot import require, logger, get_bot
from typing import List
import requests
import shutil

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


class Bangumi(BaseModel):
    title: str = ""  # 标题
    media_id: int = 0  # mid
    index_show: str = ""  # 索引右方, 比如更新到第几集, 总共几集
    cover: str = ""  # 封面url
    goto_url: str = ""  # 播放url
    eps: list = []  # 每集的详细信息
    ep_size: int = 0
    pubtime: int = 0  # 上传时间
    season_type_name: str = ""
    desc: str = ""


file_path = config.data_path / "bangumi_sub.json"
cookies = requests.get("https://bilibili.com").cookies
cookies = "; ".join([f"{x}={cookies[x]}" for x in cookies.keys()])
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.bilibili.com/",
    "Cookie": cookies
}


# 获取搜索结果
async def get_search_results(keyword: str) -> List[Bangumi] | None:
    async with AsyncClient() as client:

        params = {"keyword": keyword, "search_type": "media_bangumi"}
        client.headers = headers
        client.params = params
        if "result" in (search_result := (
                await client.get("https://api.bilibili.com/x/web-interface/search/type")
        ).json()["data"]):
            matches = []
            for item in search_result["result"]:
                if '<em class="keyword">' and "</em>" not in item["title"]:
                    continue
                item["title"] = item["title"].replace('<em class="keyword">', "").replace("</em>", "")
                matches.append(Bangumi.parse_obj(item))
            return matches
        else:
            return None


# 添加番剧订阅
async def add_bangumi_sub(bangumi_obj: Response, sub_user) -> Message:
    bangumi_obj = bangumi_obj.json()
    title = bangumi_obj["result"]["media"]["title"]
    media_id = bangumi_obj["result"]["media"]["media_id"]
    append_content = {
        "title": title,
        "now_ep": bangumi_obj["result"]["media"]["new_ep"]["index"],
        "now_ep_show": bangumi_obj["result"]["media"]["new_ep"]["index_show"],
        "cover": bangumi_obj["result"]["media"]["cover"],
        "share_url": bangumi_obj["result"]["media"]["share_url"]}
    start_content = {"subs": {str(media_id): append_content}}

    async def default() -> Message:
        json.dump(start_content, open(file_path, "r+", encoding="utf-8"), sort_keys=True, indent=4,
                  separators=(',', ':'), ensure_ascii=False)
        return Message(MessageSegment.image(await get_bytes(append_content['cover'])) + MessageSegment.text(
            f"{title}({media_id}) 订阅成功\n当前集数: {append_content['now_ep']}"))

    if not file_path.exists():
        await default()  # 若文件不存在使用开头文本
    try:
        sub_list = json.load(open(file_path, "r", encoding="utf-8"))
    except JSONDecodeError:
        return await default()  # 防止json文件损坏导致不运行
    if str(media_id) not in sub_list["subs"].keys():  # media_id是否已经存在, 存在删除
        sub_list["subs"][str(media_id)] = append_content
        json.dump(sub_list, open(file_path, "w+", encoding="utf-8"), sort_keys=True, indent=4, separators=(',', ':'),
                  ensure_ascii=False)
        return Message(MessageSegment.image(await get_bytes(append_content['cover'])) + MessageSegment.text(
            f"{title}({media_id}) 订阅成功\n当前集数: {append_content['now_ep']}"))
    else:
        return MessageSegment.at(sub_user) + MessageSegment.text(f"{title}({media_id}) 已被订阅")


# 删除番剧订阅(通过index) 从1开始
async def del_bangumi_sub(input_index: int) -> Message:
    try:
        sub_list = json.load(open(file_path, "r", encoding="utf-8"))
    except JSONDecodeError as e:
        return Message(MessageSegment.text(f"读取配置文件错误: {e}"))
    sub_map = {}
    for index, item in enumerate(sub_list["subs"]):
        sub_map[index + 1] = item
    if input_index > len(sub_map.keys()) + 1:
        return Message(MessageSegment.text("不存在的索引"))
    selected_media_id = sub_map[input_index]
    del_sub = sub_list["subs"].pop(selected_media_id)
    json.dump(sub_list, open(file_path, "w+", encoding="utf-8"), sort_keys=True, indent=4, separators=(',', ':'),
              ensure_ascii=False)
    return Message(MessageSegment.text(f"{del_sub['title']}({selected_media_id}) 已移除订阅"))


# 获取已订阅的番剧
async def get_bangumi_lst() -> Message:
    if not file_path.exists():
        return Message(MessageSegment.text("当前未订阅任何番剧"))
    else:
        try:
            sub_list = json.load(open(file_path, "r", encoding="utf-8"))
        except JSONDecodeError as e:
            return Message(MessageSegment.text(f"读取配置文件错误: {e}"))
        content = f"\n".join(
            [
                f"+---------{index + 1}---------+\n"
                f"{sub_list['subs'][x]['share_url']}\n"
                f"{sub_list['subs'][x]['title']}({x}) \n"
                f"当前集数:{sub_list['subs'][x]['now_ep']} | 当前信息:{sub_list['subs'][x]['now_ep_show']}"
                for index, x in enumerate(sub_list["subs"].keys())
            ]
        )
        reply = "* 当前订阅的番剧有 *\n" + content
        return Message(MessageSegment.text(reply))


# 获取番剧obj (Response)
async def get_bangumi_obj(mid: str) -> Response:
    async with AsyncClient() as client:
        params = {"media_id": mid}
        return await client.get("https://api.bilibili.com/pgc/review/user", headers=headers, params=params)


# 获取http bytes
async def get_bytes(url: str) -> bytes:
    async with AsyncClient() as client:
        return (await client.get(url, headers=headers)).content


@scheduler.scheduled_job("cron", minute=1, id="bangumi")
async def get_bangumi_update():
    try:
        sub_list = json.load(open(file_path, "r", encoding="utf-8"))
    except JSONDecodeError as e:
        logger.error(f"读取json文件时出错: {e}")
        return
    for media_id in sub_list["subs"].keys():
        response_body = (await get_bangumi_obj(media_id)).json()
        if (new_ep := response_body["result"]["media"]["new_ep"]["index"]) > sub_list["subs"][media_id]["now_ep"]:
            logger.info(f"{sub_list['subs'][media_id]['title']}({media_id}) 更新至{new_ep}")
            logger.info("即将广播群聊")

            if "sub_groups" in sub_list.keys():
                img = MessageSegment.image(await get_bytes(sub_list["subs"][media_id]["cover"]))
                text = MessageSegment.text(f"——————————————\n"
                                           "更新啦!!!\n"
                                           f"{sub_list['subs'][media_id]['title']}({media_id}) 已更新至第{new_ep}集!!\n"
                                           "——————————————")
                for group_id in sub_list["sub_groups"]:
                    await get_bot().send_msg(message=Message(img + text), group_id=group_id)


scheduler.add_job(get_bangumi_update, "interval", minutes=1)
