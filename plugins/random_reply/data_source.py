import difflib
import json
import os
import random
from miaobo.basic_plugins.config import Config
from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageSegment, Message

replies = json.load(open(Config.TEXT_PATH / "reply" / "reply.json", "r", encoding='utf-8'))
voice_lst = os.listdir(Config.RECORD_PATH / "dingzhen")


async def record(voice_name: str, path: str = None) -> MessageSegment | None:
    """
    说明:
        生成一个 MessageSegment.record 消息
    参数:
        :param voice_name: 音频文件名称，默认在 resource/voice 目录下
        :param path: 音频文件路径，默认在 resource/voice 目录下
    """
    if len(voice_name.split(".")) == 1:
        voice_name += ".mp3"
    file = Config.RECORD_PATH / path / voice_name
    if file.exists():
        result = MessageSegment.record(f"file:///{file.absolute()}")
        return result
    else:
        logger.warning(f"语音{file.absolute()}缺失...")
        return None


async def get_reply_result(text: str) -> Message | MessageSegment | None:
    result = await get_text_reply_result(text)
    if result is not None:
        return result
    return await get_special_reply_result(text)


async def get_special_reply_result(text: str) -> Message | MessageSegment | None:
    rand = random.random()
    if 0.3 < rand < 0.9:
        if len(text.replace(" ", "")) == 0:
            rand_choice = random.choice(replies[" "])
            if type(rand_choice) is list:
                rand_choice = random.choice(rand_choice)
                if type(rand_choice) is dict:
                    rply_text = MessageSegment.text(rand_choice["text"])
                    rply_song = record(rand_choice["path"], "songs")
                    return rply_text + await rply_song
                else:
                    return MessageSegment.text(rand_choice)
            else:
                return MessageSegment.text(rand_choice)

    if f"{text}.mp3" not in voice_lst:
        rand = random.random()
        if 0.3 < rand < 0.9:
            matches = await get_close_matches(text, voice_lst)
            return await record(random.choice(matches), "dingzhen") if len(matches) >= 1 else None
    else:
        return await record(text, "dingzhen")


async def get_close_matches(arg: str, lst: list) -> list:
    match_list = []
    for cf in range(20):
        match = difflib.get_close_matches(arg, lst, cutoff=1.0 - cf / 20.0, n=20)
        if len(match) > 0:
            match_list.append(match[0])
    return match_list


async def get_text_reply_result(text: str) -> MessageSegment | None:
    if len(text.replace(" ", "")) == 0:
        return None
    else:
        text.replace(" ", "")
    keys = replies.keys()
    for key in keys:
        if text.find(key) != -1:
            result = MessageSegment.text(random.choice(replies[key]))
            return result
