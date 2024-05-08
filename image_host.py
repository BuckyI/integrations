"sm.ms image host"
from io import BytesIO
from os.path import exists

import requests

from utils import Config

cfg = Config()


def init(token: str) -> None:
    """token: your sm.ms token"""
    global cfg
    cfg.token = token
    cfg.mark_initialized()


@cfg.check_initialized
def upload_image(image: str | BytesIO, name: str) -> str:
    """
    upload image from BytesIO or file path
    you may use `BytesIO(open("image.jpg", "rb").read())` if it is a file
    """
    if isinstance(image, str):
        assert exists(image), "image does not exist"
        image = BytesIO(open(image, "rb").read())
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
