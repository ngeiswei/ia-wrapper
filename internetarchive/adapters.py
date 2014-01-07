import os

import requests.adapters

from internetarchive.auth import S3Auth


class S3Adapter(requests.adapters.HTTPAdapter):

    # __init__()
    def __init__(self, config):
        super(S3Adapter, self).__init__()
        self.config = config

    # add_s3_auth()
    #_____________________________________________________________________________________
    def add_s3_auth(self, request, access_key=None, secret_key=None):
        if not access_key or not secret_key:
            s3_config = self.config.get('s3', {})
            access_key = s3_config.get(('access_key'), os.environ.get('IA_S3_ACCESS_KEY'))
            secret_key = s3_config.get(('secret_key'), os.environ.get('IA_S3_SECRET_KEY'))
        request.prepare_auth(S3Auth(access_key, secret_key))

    # add_headers()
    #_____________________________________________________________________________________
    def send(self, request, access_key=None, secret_key=None, **kwargs):
        self.add_s3_auth(request, access_key, secret_key)
        return super(S3Adapter, self).send(request, **kwargs)
