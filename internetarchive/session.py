import os

import requests.sessions
import requests.cookies

import internetarchive.config
import internetarchive.item
import internetarchive.catalog
from internetarchive.adapters import S3Adapter


class ArchiveSession(requests.sessions.Session):

    def __init__(self, config=None):
        super(ArchiveSession, self).__init__()
        config = config if config else internetarchive.config.get_config()
        cookies = requests.cookies.cookiejar_from_dict(config.get('cookies', {}))

        self.config = config
        self.secure = config.get('secure', False)
        self.cookies = cookies
        if not self.cookies:
            self.add_cookies()

        self.mount('http://s3', S3Adapter(config=self.config))
        self.mount('https://s3', S3Adapter(config=self.config))

    # add_cookies()
    #_____________________________________________________________________________________
    def add_cookies(self, cookies={}):
        self.cookies.update(cookies)
        if not 'logged-in-user' in self.cookies:
            self.cookies['logged-in-user'] = os.environ.get('IA_LOGGED_IN_USER')
        if not 'logged-in-sig' in self.cookies:
            self.cookies['logged-in-sig'] = os.environ.get('IA_LOGGED_IN_SIG')

    # get_item()
    #_____________________________________________________________________________________
    def get_item(self, identifier, **kwargs):
        return internetarchive.item.Item(self, identifier, **kwargs)

    # get_catalog()
    #_____________________________________________________________________________________
    def get_catalog(self, **kwargs):
        return internetarchive.catalog.Catalog(self, **kwargs)
