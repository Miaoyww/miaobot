from datetime import datetime, timedelta
from configs.config import config
from loguru import logger as logger_
from nonebot.log import default_format, default_filter


logger = logger_


logger.add(
    config.log_path / f'{datetime.now().date()}.log',
    level='INFO',
    rotation='00:00',
    format=default_format,
    filter=default_filter,
    retention=timedelta(days=30))

logger.add(
    config.log_path / f'error_{datetime.now().date()}.log',
    level='ERROR',
    rotation='00:00',
    format=default_format,
    filter=default_filter,
    retention=timedelta(days=30))