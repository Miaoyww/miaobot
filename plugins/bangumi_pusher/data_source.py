import asyncio
import json
import os
from dataclasses import dataclass
from json import JSONDecodeError
from configs.path_config import *
from nonebot.adapters.onebot.v11 import Message, MessageSegment
import aiohttp
from pydantic import BaseModel
from nonebot import require, logger, get_bot
from typing import List
import requests

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


class SeasonHttp(BaseModel):
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


@dataclass()
class Season:
    title: str = ""
    media_id: str = ""
    now_ep: int = 0
    now_ep_id: int = 0
    now_ep_show: str = ""
    now_play_url: str = ""
    cover: str = ""
    share_url: str = ""

    def __init__(self, input_: dict | aiohttp.ClientResponse, media_id: str = ""):
        if type(input_) is dict:
            self.read_from_file(input_, media_id)
        else:
            self.read_from_response(input_)

    def read_from_file(self, read_body: dict, media_id: str):

        self.title = read_body["title"]
        self.media_id = media_id
        self.now_ep = read_body["now_ep"]
        self.now_ep_id = read_body["now_ep_id"]
        self.now_ep_show = read_body["now_ep_show"]
        self.cover = read_body["cover"]
        self.share_url = read_body["share_url"]
        self.now_play_url = self.get_play_url()

    async def read_from_response(self, season_obj: aiohttp.ClientResponse):
        season_obj = await season_obj.json()
        self.title = season_obj["result"]["media"]["title"]
        self.media_id = season_obj["result"]["media"]["media_id"]
        self.now_ep = season_obj["result"]["media"]["new_ep"]["index"]
        self.now_ep_id = season_obj["result"]["media"]["new_ep"]["id"]
        self.now_ep_show = season_obj["result"]["media"]["new_ep"]["index_show"]
        self.cover = season_obj["result"]["media"]["cover"]
        self.share_url = season_obj["result"]["media"]["share_url"]
        self.now_play_url = self.get_play_url()

    def get_play_url(self):
        return f"https://www.bilibili.com/season/play/ep{self.now_ep_id}"

    def json(self):
        return {
            "title": self.title,
            "now_ep": self.now_ep,
            "now_ep_show": self.now_ep_show,
            "now_ep_id": self.now_ep_id,
            "now_play_url": self.now_play_url,
            "cover": self.cover,
            "share_url": self.share_url
        }


class SeasonManager:

    def __init__(self):
        self.season_list: List[Season] = []
        self.group_list: List[int] = []
        self.file_path = DATA_PATH / "season_sub.json"
        self.read()

    def auto_save(func):
        def wrapper(self, *args):
            logger.info("已执行自动保存")
            ret = func(self, *args)
            self.save()
            return ret

        return wrapper

    @auto_save
    def update(self, season: Season):
        for item in self.season_list:
            if str(item.media_id) == str(season.media_id):
                self.season_list[self.season_list.index(item)] = season
                return
        self.season_list.append(season)

    @auto_save
    def del_season(self, season: Season | int) -> Season | None:
        if type(season) is Season:
            if self.season_list.count(season) > 0:
                self.season_list.remove(season)
                self.save()
                logger.info(f"SeasonManager 已删除订阅: {season.title}({season.media_id})")
                return season
            else:
                return None
        else:
            if len(self.season_list) < season - 1:
                return None
            else:
                del_result = self.season_list.pop(season)
                logger.info(f"SeasonManager 已删除订阅: {del_result.title}({del_result.media_id})")
                return del_result

    @auto_save
    def add_group(self, group_id: int) -> Message:
        if group_id not in self.group_list:
            self.group_list.append(group_id)
            logger.info(f"SeasonManager 新的群通知: {group_id}")
            return Message(MessageSegment.text("本群添加通知成功"))
        else:
            return Message(MessageSegment.text("本群已添加通知"))

    @auto_save
    def del_group(self, group_id: int) -> Message:
        if group_id not in self.group_list:
            return Message(MessageSegment.text("本群未在通知列表中"))
        else:
            self.group_list.remove(group_id)
            return Message(MessageSegment.text("已移除本群通知"))

    def get_season_lst(self) -> None | List[Season]:
        if len(self.season_list) == 0:
            return None
        else:
            return self.season_list

    def get(self, media_id: int) -> None | Season:
        for item in self.season_list:
            if media_id == item.media_id:
                return item
        return None

    def get_group_lst(self) -> None | List[int]:
        if len(self.group_list) == 0:
            return None
        else:
            return self.group_list

    def save(self):
        result = {
            "sub_groups": self.group_list,
            "subs": {}
        }
        for item in self.season_list:
            result["subs"][str(item.media_id)] = item.json()
        logger.info(f"SeasonManager 即将复写{str(self.file_path)}")
        json.dump(result, open(self.file_path, "w+", encoding="utf-8"), sort_keys=True, indent=4,
                  separators=(',', ':'),
                  ensure_ascii=False)

    def read(self):
        if not self.file_path.exists():
            result = {
                "sub_groups": [],
                "subs": {}
            }
            if not os.path.exists(self.file_path.parent):
                os.mkdir(self.file_path.parent)
            json.dump(result, open(self.file_path, "x", encoding="utf-8"), sort_keys=True, indent=4,
                      separators=(',', ':'),
                      ensure_ascii=False)
        try:
            sub_list = json.load(open(self.file_path, "r", encoding="utf-8"))
            for key in sub_list["subs"].keys():
                self.season_list.append(Season(sub_list["subs"][key], key))
            for group_item in sub_list["sub_groups"]:
                self.group_list.append(group_item)
        except JSONDecodeError as e:
            logger.error(f"读取文件失败: {e}")


class SeasonRequestManager:
    def __init__(self):
        self._session = None
        asyncio.get_event_loop().run_until_complete(self.update_session())

    async def update_session(self):
        if self.session is not None:
            await self.session.close()
        jar = aiohttp.CookieJar()
        self.session = aiohttp.ClientSession(cookie_jar=jar)
        async with self.session.request("GET", "https://www.bilibili.com/") as response:
            jar.update_cookies(response.cookies)

    async def get_season_obj(self, mid: str) -> aiohttp.ClientResponse:
        if self.session is None:
            await self.update_session()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://www.bilibili.com"}
        return await self.session.request("GET", "https://api.bilibili.com/pgc/review/user", params={"media_id": mid},
                                          headers=headers)

    async def get_bytes(self, url: str) -> bytes:
        if self.session is None:
            await self.update_session()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://www.bilibili.com"}
        return (await self.session.request("GET", url, headers=headers)).content.total_bytes

    async def get_season(self, media_id: str) -> tuple[int, aiohttp.ClientResponse]:
        res_body = (await self.get_season_obj(str(media_id)))
        return int((await res_body.json())["result"]["media"]["new_ep"]["index"]), res_body

    @property
    def session(self) -> aiohttp.ClientSession:
        return self._session

    @session.setter
    def session(self, session: aiohttp.ClientSession):
        self._session = session


season_manager = SeasonManager()
request_manager = SeasonRequestManager()


# 获取搜索结果
async def get_search_results(keyword: str) -> List[SeasonHttp] | None:
    params = {"keyword": keyword, "search_type": "media_season"}
    async with request_manager.session.request(
            "GET",
            "https://api.bilibili.com/x/web-interface/search/type",
            params=params) as resp:
        if "result" in (search_result := (await resp.json())):
            matches = []
            for item in search_result["result"]:
                if '<em class="keyword">' and "</em>" not in item["title"]:
                    continue
                item["title"] = item["title"].replace('<em class="keyword">', "").replace("</em>", "")
                matches.append(SeasonHttp.parse_obj(item))
            return matches
        else:
            return None


# 添加番剧订阅
async def add_season_sub(season_obj: aiohttp.ClientResponse) -> Message:
    if (await season_obj.json())["code"] == 0:
        season = Season(season_obj)
        season_manager.update(season)
        return Message(MessageSegment.image(await request_manager.get_bytes(season.cover)) + MessageSegment.text(
            f"{season.title}({season.media_id}) 订阅成功\n当前集数: {season.now_ep}"))
    else:
        return Message(MessageSegment.text("您输入的mid有误"))


async def add_group_sub(group_id: int) -> Message:
    return season_manager.add_group(group_id)


# 删除番剧订阅(通过index) 从1开始
async def del_season_sub(input_index: int) -> Message:
    result = season_manager.del_season(input_index)
    if result is None:
        return Message(MessageSegment.text("您输入的索引有误"))
    else:
        return Message(MessageSegment.text(f"{result.title}({result.media_id}) 已移除订阅"))


# 获取已订阅的番剧
async def get_season_lst() -> Message:
    result = season_manager.get_season_lst()
    if result is not None:
        content = f"\n".join(
            [
                f"+---------{index + 1}---------+\n"
                f"{x.share_url}\n"
                f"{x.title}({x.media_id}) \n"
                f"当前集数:{x.now_ep} | 当前信息:{x.now_ep_show}"
                for index, x in enumerate(result)
            ]
        )
        reply = "* 当前订阅的番剧有 *\n" + content
        return Message(MessageSegment.text(reply))
    else:
        return Message(MessageSegment.text("当前未订阅番剧"))


# 获取番剧obj (Response)


# 获取http bytes


@scheduler.scheduled_job("cron", second=15, id="season")
async def get_season_update():
    if (season_lst := season_manager.get_season_lst()) is not None:
        for season_item in season_lst:
            new_ep, response_body = await request_manager.get_season(season_item.media_id)
            if new_ep > season_item.now_ep:
                logger.info(f"{season_item.title}({season_item.media_id}) 更新至{new_ep}")
                season_manager.update(Season(response_body))

                if (group_ids := season_manager.get_group_lst()) is not None:
                    logger.info("即将广播群聊")
                    img = MessageSegment.image(await request_manager.get_bytes(season_item.cover))
                    text = MessageSegment.text(f"——————————————\n"
                                               "更新啦!!!\n"
                                               f"{season_item.share_url}"
                                               f"{season_item.title}({season_item.media_id}) 已更新至第{new_ep}集!!\n"
                                               "——————————————")
                    for group_id in group_ids:
                        await get_bot().send_msg(message=Message(img + text), group_id=group_id)


scheduler.add_job(get_season_update, "interval", seconds=15)
