"""
(only) common utils for Notion API
"""

import html
import re
from typing import Generator

import notion_client


def init(token: str) -> None:
    "token: Notion integration token"
    global client
    client = notion_client.Client(auth=token)


def require_client(func):
    def wrapper(*args, **kwargs):
        if "client" not in globals():
            raise Exception("use init to initialize notion client first")
        return func(*args, **kwargs)

    return wrapper


@require_client
def retrieve_database_pages(database_id: str, start_cursor=None, **kwargs) -> Generator[dict, None, None]:
    "retrieve ALL pages inside a database"
    data: dict = client.databases.query(database_id=database_id, start_cursor=start_cursor)  # type: ignore
    yield from data["results"]
    while data["has_more"]:
        data: dict = client.databases.query(database_id, start_cursor=data["next_cursor"])  # type: ignore
        yield from data["results"]


@require_client
def retrieve_block_children(block_id: str, start_cursor=None) -> Generator[dict, None, None]:
    "retrieve ALL children blocks inside a page"
    data: dict = client.blocks.children.list(block_id=block_id, start_cursor=start_cursor)  # type: ignore
    yield from data["results"]
    while data["has_more"]:
        start_cursor = data["next_cursor"]
        data: dict = client.blocks.children.list(block_id=block_id, start_cursor=start_cursor)  # type: ignore
        yield from data["results"]


@require_client
def create_database_page(database_id: str, properties: dict = {}) -> dict:
    "create a new empty page inside a database, return the created page"
    # properties must be specified (`{}` for empty)
    # otherwise would raise body failed validation error
    return client.pages.create(parent={"database_id": database_id}, properties=properties)  # type: ignore


def rich_text2html(rich_text: list):
    "parse Notion rich_text to html format"
    result = ""
    for text in rich_text:
        # text part
        match text["type"]:
            case "text":
                content = text["text"]["content"]
            case "equation":
                content = f' ${text["equation"]["expression"]}$ '
            case "mention":
                content = f' @{text["plain_text"]} '
                text["annotations"]["code"] = True
            case _:
                raise Exception("unexpected rich text type: %s" % text["type"])
        content: str = html.escape(content)
        content = content.replace("\n", "<br>")
        # link and style part
        annotations = text["annotations"]
        if text["href"]:
            content = f'<a href="{text["href"]}">{content}</a>'
        if annotations["bold"]:
            content = f"<b>{content}</b>"
        if annotations["italic"]:
            content = f"<i>{content}</i>"
        if annotations["strikethrough"]:
            content = f"<s>{content}</s>"
        if annotations["underline"]:
            content = f"<u>{content}</u>"
        if annotations["code"]:
            content = f"<code>{content}</code>"
        if annotations["color"] != "default":
            color = annotations["color"]
            if color.endswith("_background"):  # background color
                style = f'style="background-color: {color[:-11]};"'
            else:  # font color
                style = f'style="color: {color};"'
            content = f'<span {style}">{content}</span>'
        result += content
    return result


def rich_text2plain_text(rich_text: list) -> str:
    return "".join(text["plain_text"] for text in rich_text)


def rich_text2markdown(rich_text: list):
    "parse Notion rich_text to markdown format"
    result = ""
    for text in rich_text:
        # text part
        match text["type"]:
            case "text":
                content = text["text"]["content"]
            case "equation":
                content = f' ${text["equation"]["expression"]}$ '
            case "mention":
                content = f'`@{text["plain_text"]}`'
            case _:
                raise Exception("unknown text type: " + text["type"])
        # TODO: markdown escape
        content = content.replace("\n", "  \n")  # add 2 spaces before new line
        # link and style part
        annotations = text["annotations"]
        if text["href"]:
            content = f"[{content}]({text['href']})"
        if annotations["bold"]:
            content = f"**{content}**"
        if annotations["italic"]:
            content = f"*{content}*"
        if annotations["strikethrough"]:
            content = f"~~{content}~~"
        if annotations["underline"]:
            content = f"<u>{content}</u>"
        if annotations["code"]:
            content = f"`{content}`"
        result += content
    return result


def id2url(page_id: str) -> str:
    page_id = page_id.replace("-", "")
    return f"https://www.notion.so/{page_id}"


def url2id(url: str) -> str:
    match = re.search(r"[0-9a-z]{32}$", re.sub(r"\?.*$", "", url))
    return match.group() if match else ""


def get_page_title(page: dict) -> str:
    title = ""
    for p in page["properties"].values():
        if p["id"] == "title":
            title = rich_text2plain_text(p["title"])
            break
    return title
