import time

from filestack import Security, Client, Filelink
from typing import Dict

from common.app_config import config
from common.app_logger import logger


class FileStackClient:
    def __init__(self):
        self.file_stack_api_key = config.FILESTACK_API_KEY
        self.file_stack_app_secret = config.FILESTACK_APP_SECRET
        self.client = Client(self.file_stack_api_key)

    def _get_security(self, policy):
        security = Security(policy, self.file_stack_app_secret)
        return security

    def upload_file(self, file_path, store_params: Dict = None):
        policy = {"expiry": int(time.time() + 3600), "call": ["store"]}
        store_params = store_params or {}
        new_file_link = self.client.upload(
            filepath=file_path,
            store_params=store_params,
            security=self._get_security(policy)
        )
        return new_file_link

    def delete_file(self, filelink: Filelink):
        policy = {"expiry": int(time.time() + 3600), "call": ["remove"]}
        return filelink.delete(security=self._get_security(policy))

    def convert_to_pdf_from_url(self, file_url: str) -> str:
        transform = self.client.transform_external(file_url)
        transform.filetype_conversion(format='pdf')
        return transform.url

    def convert_to_pdf(self, filelink: Filelink):
        transform = filelink.filetype_conversion(format='pdf')
        return transform.url
