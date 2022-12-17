from nonebot import get_driver
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.log import logger
from .config import Config
from httpx import AsyncClient

plugin_config = Config.parse_obj(get_driver().config.dict())


async def get_setu(matcher: Matcher, event: MessageEvent, r18_on: bool, tags: list):
    logger.info(f"收到来自{event.user_id}的指令, r18:{r18_on}|tags:{tags}")
    data = {
        "r18": 0,
        "tag": [],
        "size": [plugin_config.setu_size]
    }
    for item in tags:
        data["tag"].append(item)

    headers = {"Content-Type": "application/json"}
    async with AsyncClient() as client:
        res = await client.post(plugin_config.setu_api_url, json=data, headers=headers, timeout=60)
    data = res.json()
    try:
        download_url = data["data"][0]["urls"]["regular"]
        logger.info("成功获取到图片下载链接")
    except TypeError:
        logger.info("无法匹配到相应tag")
        await matcher.finish("你发送的内容无法匹配相应内容喵~请尝试其它内容~", at_sender=True)
        return
    async with AsyncClient() as client:
        res = await client.get(download_url, timeout=60)
        logger.info("图片下载成功")
        await matcher.finish(message=MessageSegment.image(res.content))
        logger.info("图片发送成功")
