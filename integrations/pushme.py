"""
Notification service based on https://push.i-i.me/
"""

from enum import Enum

import requests

from .utils import Config

cfg = Config()


def init(push_key: str):
    global cfg
    cfg.push_key = push_key
    cfg.mark_initialized()


class Theme(Enum):
    info = "[i]"
    success = "[s]"
    warning = "[w]"
    failure = "[f]"

    def __str__(self):
        return self.value  # 直接返回字符串值


@cfg.check_initialized
def push(title: str, content: str, type: str = "markdown", theme: Theme = Theme.info):
    """Push a notification to your device.

    - type: markdown | text
    - theme: Theme (info, success, warning, failure)

    docs: https://push.i-i.me/docs/index
    """
    url = "https://push.i-i.me"
    data = {
        "push_key": cfg.push_key,
        "title": str(theme) + title,
        "content": content,
        "type": type,
    }
    # headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, timeout=5)
    response.raise_for_status()
    return
