import os

import requests.sessions
import requests.cookies

import internetarchive.config
import internetarchive.item


class ArchiveSession(requests.sessions.Session):

    # __init__()
    #_____________________________________________________________________________________
    def __init__(self, config=None):
        super(ArchiveSession, self).__init__()
        config = config if config else internetarchive.config.get_config()
        cookies = requests.cookies.cookiejar_from_dict(config.get('cookies', {}))

        self.config = config
        self.secure = config.get('secure', False)
        self.cookies = cookies
        if not self.cookies:
            self.add_cookies()

        s3_config = self.config.get('s3', {})
        self.access_key = s3_config.get(('access_key'), os.environ.get('IA_S3_ACCESS_KEY'))
        self.secret_key = s3_config.get(('secret_key'), os.environ.get('IA_S3_ACCESS_KEY'))

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


def get_session(config=None):
    """
    Return a new ArchiveSession object

    """
    return ArchiveSession(config)
