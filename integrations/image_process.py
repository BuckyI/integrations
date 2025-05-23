"image process based on https://www.iloveimg.com/"
from io import BytesIO
from pathlib import Path

import requests
from cachetools import TTLCache, cached
from loguru import logger

from .utils import Config

cfg = Config()


def init(public_key: str):
    "public_key: iloveimg public key"
    cfg.public_key = public_key
    cfg.mark_initialized()


@cached(cache=TTLCache(maxsize=10, ttl=3600))  # signed tokens expire after 2 hours
def request_signed_token(public_key: str):
    url = "https://api.iloveimg.com/v1/auth"
    payload = {"public_key": public_key}
    headers = {"content-type": "application/json"}

    response = requests.post(url, json=payload, headers=headers)
    token = response.json()["token"]
    return token


@cfg.check_initialized
def compress_image(image: bytes, ext=".png") -> bytes:
    """
    image: image file object, eg. open("image.jpg", "rb").read(), or download from url
    ext: image file extension, inconsistency with true image type may leads to bad compression result (especially for png)
    return: processed image bytes, you may save it to a file by `open("output.jpg", "wb").write(img)`
    """
    token = request_signed_token(cfg.public_key)
    headers = {"Authorization": f"Bearer {token}"}

    # step1: start
    logger.debug("start compress image")
    res = requests.get("https://api.iloveimg.com/v1/start/compressimage", headers=headers).json()
    server, task = res["server"], res["task"]

    # step2: upload
    logger.debug("upload image")
    res = requests.post(
        f"https://{server}/v1/upload",
        headers=headers,
        files={"file": ("filename" + ext, BytesIO(image))},  # here specify a filename, not important
        data={"task": task},
    ).json()
    server_filename = res["server_filename"]

    # step3: process
    logger.debug("process image")
    url = f"https://{server}/v1/process"
    data = {
        "task": task,
        "tool": "compressimage",
        "files": [{"server_filename": server_filename, "filename": "filename" + ext}],  # filename should match above
    }
    res = requests.post(url, headers=headers, json=data).json()
    # download_filename = res["download_filename"]  # by default, it is the same as file.name

    # step4: download
    logger.debug("download image")
    url = f"https://{server}/v1/download/{task}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 检查请求是否成功
    return response.content


def download_image_as_bytes(url):
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功
    return response.content


def ext(path: str):
    "get file extension"
    return Path(path).suffix
