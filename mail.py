from email.mime.text import MIMEText
from smtplib import SMTP_SSL
from typing import List, NamedTuple

from .utils import Config

cfg = Config()


def init(send_server: str, send_port: int, user: str, password: str):
    """
    send_server: smtp server address, eg. "smtp.qq.com"
    send_port: smtp server port, eg. 465
    user: email address, eg. "xxx@qq.com"
    password: email password
    """
    global cfg
    cfg.update({"SEND_SERVER": send_server, "SEND_PORT": send_port, "USER": user, "PASSWORD": password})
    cfg.mark_initialized()


@cfg.check_initialized
def send_mail(subject: str, message: str, to: List[str], msg_type="html"):
    """
    to: list of email address send to, must be valid. (you may use `[mail.cfg.USER]`)
    """
    try:
        with SMTP_SSL(host=cfg.SEND_SERVER, port=cfg.SEND_PORT) as smtp:
            msg = MIMEText(message, msg_type, _charset="utf-8")
            msg["Subject"] = subject
            msg["from"] = cfg.USER
            msg["to"] = ", ".join(to)  # Optional

            smtp.login(user=cfg.USER, password=cfg.PASSWORD)  # (235, b'Authentication successful')
            smtp.sendmail(from_addr=cfg.USER, to_addrs=to, msg=msg.as_string())
    except Exception as e:
        print("send mail failed:", e)
