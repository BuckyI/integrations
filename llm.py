import re
import time

from openai import OpenAI, RateLimitError

from .utils import Config

cfg = Config()


def init(api_key: str):
    """
    key: moonshot ai api key
    """
    global cfg
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.moonshot.cn/v1",
        max_retries=0,  # no retry, it makes harder to handle rate limit error
    )
    cfg.update({"api_key": api_key, "client": client})
    cfg.mark_initialized()


def retry_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RateLimitError as e:
            match_res = re.search(r"try again after (\d+) seconds", e.body["message"])
            if not match_res:
                raise e
            # the retry_after time is not accurate, use 60s instead
            retry_after = 60
            print(f"reched rate time limit, sleep {retry_after} seconds")
            time.sleep(retry_after)
            return func(*args, **kwargs)

    return wrapper


@cfg.check_initialized
@retry_wrapper
def ask(query: str, role: str) -> str:
    completion = cfg.client.chat.completions.create(
        model="moonshot-v1-8k",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": query},
        ],
        temperature=0.6,
    )
    return completion.choices[0].message.content
