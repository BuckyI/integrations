from email.mime.text import MIMEText
from smtplib import SMTP_SSL
from typing import List, NamedTuple


class Config(NamedTuple):
    SEND_SERVER: str  # smtp.qq.com
    SEND_PORT: int  # 465
    USER: str  # xxx@qq.com
    PASSWORD: str


CONFIG = None


def init(config: Config):
    global CONFIG
    CONFIG = config


def send_mail(subject: str, message: str, to: List[str], msg_type="html"):
    """
    to: list of email address send to, must be valid. (you may use `[mail.CONFIG.USER]`)
    """
    assert CONFIG is not None, "use init to initialize mail config first"
    try:
        with SMTP_SSL(host=CONFIG.SEND_SERVER, port=CONFIG.SEND_PORT) as smtp:
            msg = MIMEText(message, msg_type, _charset="utf-8")
            msg["Subject"] = subject
            msg["from"] = CONFIG.USER
            msg["to"] = ", ".join(to)  # Optional

            smtp.login(user=CONFIG.USER, password=CONFIG.PASSWORD)  # (235, b'Authentication successful')
            smtp.sendmail(from_addr=CONFIG.USER, to_addrs=to, msg=msg.as_string())
    except Exception as e:
        print("send mail failed:", e)
