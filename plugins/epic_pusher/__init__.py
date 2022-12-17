from nonebot import *
from nonebot.plugin import PluginMetadata


__plugin_meta__ = PluginMetadata(
    name='epic每日限免',
    description='推送epic每日限免',
    usage='''使用.epic add指令将本群加入到推送
    使用.epic today指令立即推送目前限免'''
)

epic = on_command("epic")
# https://github.com/DIYgod/RSSHub/blob/master/lib/v2/epicgames/index.js
# https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=zh-CN&country=CN&allowCountries=CN


# TODO 将epic推送完善
