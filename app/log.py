import logging
from logging.handlers import TimedRotatingFileHandler
import os
from app.config import root_path

log_dir = root_path / "logs"
os.makedirs(str(log_dir), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志级别

log_file = os.path.join(log_dir, "app.log")
file_handler = TimedRotatingFileHandler(
    filename=log_file,
    when="midnight",  # 每天午夜分片
    interval=1,  # 每天一个文件
    backupCount=7,  # 保留最近7天的日志
    encoding="utf-8"
)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
