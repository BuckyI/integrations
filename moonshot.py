from openai import OpenAI

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
    )
    cfg.update({"api_key": api_key, "client": client})
    cfg.mark_initialized()


@cfg.check_initialized
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
