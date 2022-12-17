from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    # copied from https://github.com/kexue-z/nonebot-plugin-setu-now/blob/master/nonebot_plugin_setu_now/config.py
    setu_size: str = "regular"
    setu_api_url: str = "https://api.lolicon.app/setu/v2"
    setu_cd: int = 30
