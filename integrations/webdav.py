import io
import tempfile
from pathlib import Path

import requests
from webdav3.client import Client


class JGY:
    def __init__(
        self, hostname: str, username: str, password: str, root: str = "Files"
    ) -> None:
        """
        坚果云 jianguoyun WebDAV client
        manage files in specified remote root folder.
        Note: avoid subfolder related operations (not tested thoroughly)
        """

        options = {
            "webdav_hostname": hostname,
            "webdav_login": username,
            "webdav_password": password,
            "disable_check": True,  # 坚果云不支持 check，会无法访问资源
            "verbose": True,
        }
        self.client = Client(options)
        self.root = root
        if not any(
            i["name"] == self.root and i["isdir"]
            for i in self.client.list(get_info=True)
        ):
            self.client.mkdir(self.root)  # init

    @property
    def resources(self):
        # 默认存在根目录，去掉它
        return self.client.list(remote_path=self.root, get_info=True)[1:]

    def exists(self, filename: str) -> bool:
        return any(r["name"] == filename for r in self.resources)

    def upload_file(
        self, source: str, filename: str | None = None, overwrite: bool = False
    ) -> None:
        """
        source: local file path
        filename: upload file name, default the same as local file
        overwrite: if True, overwrite existing file
        """
        assert Path(source).is_file(), "file to be uploaded does not exist"
        if filename is None:  # default keep original filename
            filename = Path(source).name

        if not overwrite:
            assert not self.exists(filename), "file already exists in remote"

        dest = f"{self.root}/{filename}"
        self.client.upload(dest, source)

    def upload_file_obj(self, file: io.BytesIO, filename: str) -> None:
        assert not self.exists(filename), "file already exists in remote"
        dest = f"{self.root}/{filename}"

        # WARNING: Windows 系统执行此步骤会报错，需要额外设定 delete=False，但会导致文件残留
        with tempfile.NamedTemporaryFile() as temp_file:
            with temp_file.file as f:
                f.write(file.read())
            self.client.upload(dest, temp_file.name)

    def upload_url(self, url: str, filename: str) -> None:
        assert not self.exists(filename), "file already exists in remote"
        response = requests.get(url)
        response.raise_for_status()
        dest = f"{self.root}/{filename}"
        self.client.upload_to(buff=response.content, remote_path=dest)
