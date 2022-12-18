import json
from dataclasses import dataclass
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


class BangumiHttp(BaseModel):
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
class Bangumi:
    title: str = ""
    media_id: int = 0
    now_ep: int = 0
    now_ep_id: int = 0
    now_ep_show: str = ""
    now_play_url: str = ""
    cover: str = ""
    share_url: str = ""

    def __init__(self, input_: dict | Response, media_id: int = 0):
        if type(input_) is dict:
            self.read_from_file(input_, media_id)
        else:
            self.read_from_response(input_)

    def read_from_file(self, read_body: dict, media_id: int):

        self.title = read_body["title"]
        self.media_id = media_id
        self.now_ep = read_body["now_ep"]
        self.now_ep_id = read_body["now_ep_id"]
        self.now_ep_show = read_body["now_ep_show"]
        self.cover = read_body["cover"]
        self.share_url = read_body["share_url"]
        self.now_play_url = self.get_play_url()

    def read_from_response(self, bangumi_obj: Response):
        bangumi_obj = bangumi_obj.json()
        self.title = bangumi_obj["result"]["media"]["title"]
        self.media_id = bangumi_obj["result"]["media"]["media_id"]
        self.now_ep = bangumi_obj["result"]["media"]["new_ep"]["index"]
        self.now_ep_id = bangumi_obj["result"]["media"]["new_ep"]["id"]
        self.now_ep_show = bangumi_obj["result"]["media"]["new_ep"]["index_show"]
        self.cover = bangumi_obj["result"]["media"]["cover"]
        self.share_url = bangumi_obj["result"]["media"]["share_url"]
        self.now_play_url = self.get_play_url()

    def get_play_url(self):
        return f"https://www.bilibili.com/bangumi/play/ep{self.now_ep_id}"

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


class BangumiManager:

    def __init__(self):
        self.bangumi_list: List[Bangumi] = []
        self.group_list: List[int] = []
        self.file_path = config.data_path / "bangumi_sub.json"
        self.read()

    def auto_save(func):
        def wrapper(self, *args):
            logger.info("已执行自动保存")
            ret = func(self, *args)
            self.save()
            return ret

        return wrapper

    @auto_save
    def update(self, bangumi: Bangumi):
        for item in self.bangumi_list:
            if str(item.media_id) == str(bangumi.media_id):
                self.bangumi_list[self.bangumi_list.index(item)] = bangumi
                return
        self.bangumi_list.append(bangumi)

    @auto_save
    def del_bangumi(self, bangumi: Bangumi | int) -> Bangumi | None:
        if type(bangumi) is Bangumi:
            if self.bangumi_list.count(bangumi) > 0:
                self.bangumi_list.remove(bangumi)
                self.save()
                logger.info(f"BangumiManager 已删除订阅: {bangumi.title}({bangumi.media_id})")
                return bangumi
            else:
                return None
        else:
            if len(self.bangumi_list) < bangumi - 1:
                return None
            else:
                del_result = self.bangumi_list.pop(bangumi)
                logger.info(f"BangumiManager 已删除订阅: {del_result.title}({del_result.media_id})")
                return del_result

    @auto_save
    def add_group(self, group_id: int) -> Message:
        if group_id not in self.group_list:
            self.group_list.append(group_id)
            logger.info(f"BangumiManager 新的群通知: {group_id}")
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

    def get_bangumi_lst(self) -> None | List[Bangumi]:
        if len(self.bangumi_list) == 0:
            return None
        else:
            return self.bangumi_list

    def get(self, media_id: int) -> None | Bangumi:
        for item in self.bangumi_list:
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
        for item in self.bangumi_list:
            result["subs"][str(item.media_id)] = item.json()
        logger.info(f"BangumiManager 即将复写{str(self.file_path)}")
        json.dump(result, open(self.file_path, "w+", encoding="utf-8"), sort_keys=True, indent=4,
                  separators=(',', ':'),
                  ensure_ascii=False)

    def read(self):
        if not self.file_path.exists():
            result = {
                "sub_groups": [],
                "subs": {}
            }
            json.dump(result, open(self.file_path, "r+", encoding="utf-8"), sort_keys=True, indent=4,
                      separators=(',', ':'),
                      ensure_ascii=False)
        try:
            sub_list = json.load(open(self.file_path, "r", encoding="utf-8"))
            for key in sub_list["subs"].keys():
                self.bangumi_list.append(Bangumi(sub_list["subs"][key], key))
            for group_item in sub_list["sub_groups"]:
                self.group_list.append(group_item)
        except JSONDecodeError as e:
            logger.error(f"读取文件失败: {e}")


bangumi_manager = BangumiManager()

cookies = requests.get("https://bilibili.com").cookies
cookies = "; ".join([f"{x}={cookies[x]}" for x in cookies.keys()])
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.bilibili.com/",
    "Cookie": cookies
}


# 获取搜索结果
async def get_search_results(keyword: str) -> List[BangumiHttp] | None:
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
                matches.append(BangumiHttp.parse_obj(item))
            return matches
        else:
            return None


# 添加番剧订阅
async def add_bangumi_sub(bangumi_obj: Response) -> Message:
    if bangumi_obj.json()["code"] == 0:
        bangumi = Bangumi(bangumi_obj)
        bangumi_manager.update(bangumi)
        return Message(MessageSegment.image(await get_bytes(bangumi.cover)) + MessageSegment.text(
            f"{bangumi.title}({bangumi.media_id}) 订阅成功\n当前集数: {bangumi.now_ep}"))
    else:
        return Message(MessageSegment.text("您输入的mid有误"))


async def add_group_sub(group_id: int) -> Message:
    return bangumi_manager.add_group(group_id)


# 删除番剧订阅(通过index) 从1开始
async def del_bangumi_sub(input_index: int) -> Message:
    result = bangumi_manager.del_bangumi(input_index)
    if result is None:
        return Message(MessageSegment.text("您输入的索引有误"))
    else:
        return Message(MessageSegment.text(f"{result.title}({result.media_id}) 已移除订阅"))


# 获取已订阅的番剧
async def get_bangumi_lst() -> Message:
    result = bangumi_manager.get_bangumi_lst()
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
async def get_bangumi_obj(mid: str) -> Response:
    async with AsyncClient() as client:
        params = {"media_id": mid}
        return await client.get("https://api.bilibili.com/pgc/review/user", headers=headers, params=params)


# 获取http bytes
async def get_bytes(url: str) -> bytes:
    async with AsyncClient() as client:
        return (await client.get(url, headers=headers)).content


@scheduler.scheduled_job("cron", second=15, id="bangumi")
async def get_bangumi_update():
    if (bangumi_lst := bangumi_manager.get_bangumi_lst()) is not None:
        for bangumi_item in bangumi_lst:
            response_body = (await get_bangumi_obj(str(bangumi_item.media_id)))
            if (new_ep := response_body.json()["result"]["media"]["new_ep"]["index"]) > bangumi_item.now_ep:
                logger.info(f"{bangumi_item.title}({bangumi_item.media_id}) 更新至{new_ep}")
                bangumi_manager.update(Bangumi(response_body))

                if (group_ids := bangumi_manager.get_group_lst()) is not None:
                    logger.info("即将广播群聊")
                    img = MessageSegment.image(await get_bytes(bangumi_item.cover))
                    text = MessageSegment.text(f"——————————————\n"
                                               "更新啦!!!\n"
                                               f"{bangumi_item.share_url}"
                                               f"{bangumi_item.title}({bangumi_item.media_id}) 已更新至第{new_ep}集!!\n"
                                               "——————————————")
                    for group_id in group_ids:
                        await get_bot().send_msg(message=Message(img + text), group_id=group_id)


scheduler.add_job(get_bangumi_update, "interval", seconds=15)
