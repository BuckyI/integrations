import time
from functools import lru_cache
from typing import NamedTuple

import requests
from loguru import logger

from .utils import Config

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


def _check(response):
    "check response result and catch rate limit, return status code"
    try:
        # 某些未知情况下 response.json() 会报错，所以这里谨慎一些 (可能是因为 502，返回的是 html)
        if response.status_code == 429:
            retry_after = float(response.headers["Retry-After"])
            logger.warning(f"rate limit exceeded, sleep {retry_after}s")
            time.sleep(retry_after)
            return "TooManyRequests"
        if response.status_code == 502:  # bad gateway
            logger.warning("502 Bad Gateway, sleep 1s")
            time.sleep(1)
            return "BadGateway"
        if response.json()["success"]:
            return "Success"
    except Exception as e:
        logger.exception(e)
    logger.error(f"UnknownError: {response.status_code=}, {response.text=}")
    return "UnknownError"


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
    return tasks that failed to create
    """
    failed: list[Task] = []

    url = "https://habitica.com/api/v3/tasks/user"
    bot_tag = get_bot_tag()
    logger.debug(f"create {len(tasks)} task")
    for task in tasks:
        payload = {
            "text": task.text,
            "type": task.type,
            "notes": task.notes,
            "tags": [bot_tag],  # indicate that the task is created by a bot
        }
        response = requests.post(url, json=payload, headers=cfg.headers)
        result = _check(response)
        if result != "Success":  # retry
            response = requests.post(url, json=payload, headers=cfg.headers)
            result = _check(response)
        if result != "Success":
            logger.error(f"{task} created failed ({result})")
            failed.append(task)
    return failed


@cfg.check_initialized
def delete_bot_tasks():
    "delete bot tasks, return tasks that failed to delete"
    failed = []

    bot_tag = get_bot_tag()
    # get all tasks
    url = "https://habitica.com/api/v3/tasks/user"
    payload = {"type": "todos"}  # 不知道为什么不起作用
    response = requests.get(url, json=payload, headers=cfg.headers)
    tasks = list(filter(lambda t: bot_tag in t["tags"] and t["type"] == "todo", response.json()["data"]))
    logger.debug(f"delete {len(tasks)} task")
    for t in tasks:
        url = f"https://habitica.com/api/v3/tasks/{t['id']}"
        response = requests.delete(url, headers=cfg.headers)
        result = _check(response)
        if result != "Success":  # retry
            response = requests.delete(url, headers=cfg.headers)
            result = _check(response)
        if result != "Success":
            logger.error(f"Failed to delete task {t}. ({result})")
            failed.append(t)
    return failed
