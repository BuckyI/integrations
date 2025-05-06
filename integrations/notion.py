"""
(only) common utils for Notion API
"""

import html
import re
from typing import Generator, Iterable

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


def enrich_data(data: dict | Iterable[dict]):
    "enrich data with additional fields"

    def _enrich(d: dict) -> dict:
        d["token"] = client.options.auth  # for development
        return d

    if isinstance(data, dict):
        return _enrich(data)
    else:
        return map(_enrich, data)


def clean(data: dict) -> dict:
    "remove additional fields"
    for k in ["token"]:
        data.pop(k, None)
    return data


@require_client
def retrieve_general_info(id: str):
    """
    retrieve general info from id, useful for checking type: page, database, blocks...
    Note: "child_page" for page, "child_database" for database, other for general blocks
    """
    data: dict = client.blocks.retrieve(id)  # type: ignore
    for k in ["object", "request_id"]:
        data.pop(k)
    return enrich_data(data)


@require_client
def retrieve_page(page_id: str) -> dict:
    "retrieve a page by id"
    return enrich_data(client.pages.retrieve(page_id))  # type: ignore


@require_client
def retrieve_comments(
    block_id: str, retrieve_all: bool = True, **kwargs
) -> Generator[dict, None, None]:
    """
    Retrieve comments for a given block.
    retrieve_all: if True, try to retrieve all comments by performing query in a loop.
    """
    has_more = True
    start_cursor = None
    if "page_size" in kwargs:
        retrieve_all = False  # force only query once

    while has_more:
        comments: dict = client.comments.list(
            block_id=block_id, start_cursor=start_cursor, **kwargs
        )  # type: ignore
        yield from enrich_data(comments["results"])

        start_cursor = comments["next_cursor"]
        has_more = comments["has_more"] and retrieve_all


@require_client
def retrieve_comments_recursive(block_id: str, **kwargs) -> Generator[dict, None, None]:
    """
    retrieve all comments for a given block/page recursively
    default no limit on page_size (comment size)
    """
    # the root comment
    yield from retrieve_comments(block_id, **kwargs)
    # comments from children blocks
    for block in retrieve_block_children_recursive(block_id, **kwargs):
        yield from retrieve_comments(block["id"], **kwargs)


@require_client
def retrieve_database_pages(
    database_id: str, retrieve_all: bool = True, **kwargs
) -> Generator[dict, None, None]:
    """
    retrieve pages inside a database
    retrieve_all: if True, try to retrieve all pages by performing query in a loop.
    """
    has_more = True
    start_cursor = None
    if "page_size" in kwargs:
        retrieve_all = False  # force only query once

    while has_more:
        data: dict = client.databases.query(
            database_id=database_id, start_cursor=start_cursor, **kwargs
        )  # type: ignore
        yield from enrich_data(data["results"])

        start_cursor = data["next_cursor"]
        has_more = data["has_more"] and retrieve_all


@require_client
def retrieve_block_children(
    block_id: str, retrieve_all: bool = True, **kwargs
) -> Generator[dict, None, None]:
    """
    retrieve children blocks inside a page.
    retrieve_all: if True, try to retrieve all pages by performing query in a loop.
    """
    has_more = True
    start_cursor = None
    if "page_size" in kwargs:
        retrieve_all = False  # force only query once

    while has_more:
        data: dict = client.blocks.children.list(
            block_id=block_id, start_cursor=start_cursor
        )  # type: ignore
        yield from enrich_data(data["results"])

        start_cursor = data["next_cursor"]
        has_more = data["has_more"] and retrieve_all


@require_client
def retrieve_block_children_recursive(
    block_id: str, **kwargs
) -> Generator[dict, None, None]:
    """
    retrieve children blocks inside a page.
    retrieve_all: if True, try to retrieve all pages by performing query in a loop.
    """
    ids = [block_id]
    limit = int(kwargs["page_size"]) if "page_size" in kwargs else float("inf")
    for i in ids:
        for block in retrieve_block_children(i, **kwargs):
            yield block

            limit -= 1
            if limit <= 0:
                return

            if block["has_children"]:
                ids.append(block["id"])


@require_client
def create_database_page(database_id: str, properties: dict = {}) -> dict:
    "create a new empty page inside a database, return the created page"
    # properties must be specified (`{}` for empty)
    # otherwise would raise body failed validation error
    page: dict = client.pages.create(
        parent={"database_id": database_id}, properties=properties
    )  # type: ignore
    return enrich_data(page)  # type: ignore


def rich_text2html(rich_text: list):
    "parse Notion rich_text to html format"
    result = ""
    for text in rich_text:
        # text part
        match text["type"]:
            case "text":
                content = text["text"]["content"]
            case "equation":
                content = f" ${text['equation']['expression']}$ "
            case "mention":
                content = f" @{text['plain_text']} "
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


def property2plain_text(property):
    plain_text = ""
    match _type := property["type"]:
        case (
            "checkbox"
            | "created_time"
            | "email"
            | "last_edited_time"
            | "number"
            | "url"
        ):
            plain_text = property[_type] or ""  # None -> ""
        case "created_by":
            plain_text = property[_type]["id"]
        case "date":
            date = property[_type]
            if date.get("end"):
                plain_text = f"{date['start']} - {date['end']}"
            else:
                plain_text = date["start"]
        case "last_edited_by":
            plain_text = property[_type]["id"]
        case "multi_select":
            plain_text = ", ".join(_s["name"] for _s in property[_type])
        case "relation":
            plain_text = ", ".join(_r["id"] for _r in property[_type])
        case "rich_text" | "title":
            plain_text = "".join(_t["plain_text"] for _t in property[_type])
        case "select" | "status":
            plain_text = property[_type]["name"] if property[_type] else ""
        case "unique_id":
            _unique_id = property[_type]
            plain_text = "{}{}".format(_unique_id["prefix"] or "", _unique_id["number"])
        case "verification":
            plain_text = property[_type]["state"]
        case _:
            # files, formula, people, phone_number, rollup
            raise NotImplementedError(f"Property type {_type} is not implemented")
    return str(plain_text)


def plain_text2rich_text(text: str) -> dict:
    """
    Generate simple rich text to simplify saving text to Notion.
    Use case when creating a page:
    ```
    properties = {
        "content": plain_text2rich_text(text),
        ... # other properties
    }
    ```
    """
    contents = [
        text[i : i + 2000] for i in range(0, len(text), 2000)
    ]  # split into 2000 chunks for Notin's Size limit
    return {"rich_text": [{"text": {"content": c}} for c in contents]}


def rich_text2markdown(rich_text: list):
    "parse Notion rich_text to markdown format"
    result = ""
    for text in rich_text:
        # text part
        match text["type"]:
            case "text":
                content = text["text"]["content"]
            case "equation":
                content = f" ${text['equation']['expression']}$ "
            case "mention":
                content = f"`@{text['plain_text']}`"
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
