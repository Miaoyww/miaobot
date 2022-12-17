import nonebot
from nonebot.adapters.onebot.v11 import Adapter

nonebot.init()
driver = nonebot.get_driver()
driver.register_adapter(Adapter)
config = driver.config
# 加载插件
nonebot.load_plugins("basic_plugins")

nonebot.load_plugins("plugins")

if __name__ == "__main__":
    nonebot.run()
