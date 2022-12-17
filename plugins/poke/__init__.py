import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from nonebot import on_notice, logger
from nonebot.adapters.onebot.v11 import PokeNotifyEvent, MessageSegment
from miaobo.basic_plugins.config import Config
import random
import os

# Copied From https://github.com/HibiKier/zhenxun_bot/edit/main/plugins/poke/__init__.py
# Rewrite
__zx_plugin_name__ = "戳一戳"

__plugin_usage__ = """
usage：
    戳一戳随机掉落语音或美图萝莉图
""".strip()
__plugin_des__ = "戳一戳发送语音美图萝莉图不美哉？"
__plugin_type__ = ("其他",)
__plugin_version__ = 0.1
__plugin_author__ = "HibiKier"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["戳一戳"],
}

poke__reply = json.load(open(Config.text_path / "poke" / "reply.json", encoding="utf-8"))["replies"]


class CountLimiter:
    """
    次数检测工具，检测调用次数是否超过设定值
    """

    def __init__(self, max_count: int):
        self.count = defaultdict(int)
        self.max_count = max_count

    def add(self, key: Any):
        self.count[key] += 1

    def check(self, key: Any) -> bool:
        if self.count[key] >= self.max_count:
            self.count[key] = 0
            return True
        return False


_clmt = CountLimiter(3)
poke_ = on_notice(priority=5, block=False)


def record(voice_name: str, path: str = None) -> MessageSegment or str:
    """
    说明:
        生成一个 MessageSegment.record 消息
    参数:
        :param voice_name: 音频文件名称，默认在 resource/voice 目录下
        :param path: 音频文件路径，默认在 resource/voice 目录下
    """
    if len(voice_name.split(".")) == 1:
        voice_name += ".mp3"
    file = (
        Path(Config.record_path) / path / voice_name
        if path
        else Path(Config.record_path) / voice_name
    )
    if "http" in voice_name:
        return MessageSegment.record(voice_name)
    if file.exists():
        result = MessageSegment.record(f"file:///{file.absolute()}")
        return result
    else:
        logger.warning(f"语音{file.absolute()}缺失...")
        return ""


def poke(qq: int) -> MessageSegment:
    """
    说明:
        生成一个 MessageSegment.poke 消息
    参数:
        :param qq: qq号
    """
    return MessageSegment("poke", {"qq": qq})


@poke_.handle()
async def _poke_event(event: PokeNotifyEvent):
    await asyncio.sleep(random.randint(10, 20) / 10)
    if event.self_id == event.target_id:
        _clmt.add(event.user_id)
        if _clmt.check(event.user_id) or random.random() < 0.3:
            rst = ""
            if random.random() < 0.15:
                logger.info(f"{event.user_id} 的拍一拍回复被拒")
                return
            await poke_.finish(rst + random.choice(poke__reply), at_sender=True)
        rand = random.random()
        if 0.4 < rand < 0.8:
            voice = random.choice(os.listdir(Config.record_path / "dinggong"))
            result = record(voice, "dinggong")
            await poke_.send(result)
            await poke_.send(voice.split("_")[1])
            logger.info(
                f'USER {event.user_id} 戳了戳我 回复: {result} \n {voice.split("_")[1]}'
            )
        else:
            logger.info(f"戳了戳 {event.user_id}")
            await poke_.send(poke(event.user_id))
