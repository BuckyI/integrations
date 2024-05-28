"sm.ms image host"
from io import BytesIO
from os.path import exists
from typing import Generator

import requests

from utils import Config

cfg = Config()


def init(token: str) -> None:
    """token: your sm.ms token"""
    global cfg
    cfg.token = token
    cfg.mark_initialized()


@cfg.check_initialized
def upload_image(source: str | BytesIO | bytes, name: str) -> str:
    """
    upload image from BytesIO or file path or raw bytes
    you may use `BytesIO(open("image.jpg", "rb").read())` if it is a file
    """
    if isinstance(source, str):
        assert exists(source), "image does not exist"
        image = BytesIO(open(source, "rb").read())
    elif isinstance(source, bytes):
        image = BytesIO(source)
    else:
        assert isinstance(source, BytesIO), "invalid source type"
        image = source
    image.name = name
    headers = {"Authorization": cfg.token}
    files = {"smfile": image}
    response = requests.post("https://sm.ms/api/v2/upload", files=files, headers=headers)

    res = response.json()
    match res["code"]:
        case "success":
            return res["data"]["url"]
        case "image_repeated":
            return res["images"]  # previously uploaded url
        case _:  # unsupported conditions
            # "invalid_size": "Image size should less than 5MB"
            raise Exception(f"{res['code']}: {res['message']}\ndata:\n {res}")


@cfg.check_initialized
def image_list() -> Generator[dict, None, None]:
    "get all uploaded images"
    headers = {"Authorization": cfg.token}
    url = "https://sm.ms/api/v2/upload_history"
    payload = {"page": 1}
    res = requests.get(url, data=payload, headers=headers).json()
    yield from res["data"]

    for i in range(2, res["TotalPages"] + 1):
        payload["page"] = i
        res = requests.get(url, data=payload, headers=headers).json()
        yield from res["data"]
