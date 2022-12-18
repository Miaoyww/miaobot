import nonebot
from datetime import datetime
from nonebot.log import logger, logger_id, default_format
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
app = nonebot.get_asgi()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)
# 加载插件
nonebot.load_plugin("nonebot_plugin_apscheduler")
nonebot.load_plugins("basic_plugins")
nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
