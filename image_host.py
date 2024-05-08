"sm.ms image host"
from io import BytesIO
from os.path import exists
from typing import NamedTuple

import requests


class Config(NamedTuple):
    token: str
    user: str = ""  # optional
    password: str = ""  # optional


CONFIG = None


def init(token: str) -> None:
    global CONFIG
    CONFIG = Config(token)


def upload_image(image: str | BytesIO, name: str) -> str:
    """
    upload image from BytesIO or file path
    you may use `BytesIO(open("image.jpg", "rb").read())` if it is a file
    """
    assert CONFIG is not None, "use init to initialize image host config first"
    if isinstance(image, str):
        assert exists(image), "image does not exist"
        image = BytesIO(open(image, "rb").read())
    image.name = name
    headers = {"Authorization": CONFIG.token}
    files = {"smfile": image}
    response = requests.post("https://sm.ms/api/v2/upload", files=files, headers=headers)

    res = response.json()
    if not res["success"]:
        raise Exception(res["message"])

    return res["data"]["url"]
