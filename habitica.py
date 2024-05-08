import time
from functools import lru_cache
from typing import NamedTuple

import requests

from utils import Config

cfg = Config()


def init(user: str, key: str):
    """
    user: habitica user ID, key: habitica api key
    you can get it from 'Settings' -> 'Site Data'
    """
    global cfg
    cfg.headers = {
        "x-client": user + " - habitica.py",
        "x-api-user": user,
        "x-api-key": key,
        "content-type": "application/json",
    }
    cfg.mark_initialized()


@cfg.check_initialized
@lru_cache
def get_bot_tag() -> str:
    """return uuid of 'bot' tag"""
    url = "https://habitica.com/api/v3/tags"
    payload = None
    response = requests.get(url, data=payload, headers=cfg.headers)
    tags = response.json()["data"]
    for tag in tags:
        if tag["name"] == "bot":
            return tag["id"]
    raise Exception("bot tag does not exist!")


class Task(NamedTuple):
    text: str
    notes: str
    type: str = "todo"


@cfg.check_initialized
def create_tasks(tasks: list[Task]):
    """
    create a list of tasks
    """

    url = "https://habitica.com/api/v3/tasks/user"
    bot_tag = get_bot_tag()
    for task in tasks:
        payload = {
            "text": task.text,
            "type": task.type,
            "notes": task.notes,
            "tags": [bot_tag],  # indicate that the task is created by a bot
        }
        response = requests.post(url, json=payload, headers=cfg.headers)
        result = response.json()
        if not result["success"]:
            print(f"{task} created failed")

        if response.headers["X-RateLimit-Remaining"] == "0":
            time.sleep(60)  # sleep 1 minute if rate limit is exceeded


@cfg.check_initialized
def delete_bot_tasks():
    bot_tag = get_bot_tag()
    # get all tasks
    url = "https://habitica.com/api/v3/tasks/user"
    payload = {"type": "todos"}  # 不知道为什么不起作用
    response = requests.get(url, json=payload, headers=cfg.headers)
    tasks = filter(lambda t: bot_tag in t["tags"] and t["type"] == "todo", response.json()["data"])
    for t in tasks:
        url = f"https://habitica.com/api/v3/tasks/{t['id']}"
        response = requests.delete(url, headers=cfg.headers)
        if not response.json()["success"]:
            print(f"Failed to delete task {t}.")

        if response.headers["X-RateLimit-Remaining"] == "0":
            time.sleep(60)  # sleep 1 minute if rate limit is exceeded
