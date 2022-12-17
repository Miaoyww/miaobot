from pathlib import Path
from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    bot_path: Path = Path(__file__).parent.parent
    text_path: Path = bot_path / "resource" / "text"
    record_path: Path = bot_path / "resource" / "record"
    data_path: Path = bot_path / "data"
    log_path: Path = bot_path / "logs"
    proxy: str = ""


config = Config.parse_obj(get_driver().config)
