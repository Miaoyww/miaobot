from pathlib import Path
from typing import List, Literal, Optional, Union

from nonebot import get_driver, on_command
from pydantic import BaseModel, Extra

cf = on_command("config")


class Config(BaseModel, extra=Extra.ignore):
    bot_path: Path = Path(__file__).parent.parent.parent
    text_path: Path = bot_path / "resource" / "text"
    record_path: Path = bot_path / "resource" / "record"
    proxy: str = ""


config = Config.parse_obj(get_driver().config)


@cf.handle()
async def _():
    pass
