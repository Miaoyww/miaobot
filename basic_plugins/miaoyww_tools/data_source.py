from pathlib import Path
from nonebot import logger
from nonebot.internal.matcher import Matcher
from configs.config import config
import os
import shutil
import requests
import zipfile


async def entry_update_plugins(matcher: Matcher):
    await matcher.send("正在更新插件.")
    plugins_path = Path(__file__).parent.parent.parent
    plugins_temp_path = f"{plugins_path}\\plugins_temp"
    if os.path.exists(plugins_temp_path):
        shutil.rmtree(plugins_temp_path)
    logger.info("开始获取插件压缩包")
    if os.path.exists(plugins_temp_path + ".zip"):
        os.remove(plugins_temp_path + ".zip")
    with open(plugins_temp_path + ".zip", "wb") as w:
        resp = requests.get("https://github.com/Miaoyww/miaobot-plugins/archive/refs/heads/main.zip").content
        w.write(resp)
    logger.info("获取成功")
    logger.info("开始解压压缩包")
    file = zipfile.ZipFile(plugins_temp_path + ".zip", )
    file.extractall(plugins_path)
    file.close()
    logger.info("Update Done")
    os.remove(plugins_temp_path + ".zip")
    shutil.rmtree(f"{plugins_path}/plugins")
    while True:
        try:
            os.renames(f"{plugins_path}/miaobot-plugins-main", f"{plugins_path}/plugins")
            break
        except:
            continue
    await matcher.send("插件已更新完毕, bot即将重启")
