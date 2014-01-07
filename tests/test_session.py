import os.path
import sys

import requests.cookies

import internetarchive.auth


inc_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, inc_path)


def test_session():
    s = internetarchive.session.ArchiveSession()
    assert isinstance(s.config, dict)
    assert isinstance(s.secure, bool)
    assert isinstance(s.cookies, requests.cookies.RequestsCookieJar)
    assert 'auth' in s.__attrs__

    s.add_cookies({'test-cookie': 'test value'})
    assert s.cookies['test-cookie'] == 'test value'
    assert s.auth == None

    item = s.get_item('nasa')
    assert isinstance(item, internetarchive.item.Item)
    assert isinstance(item.session, internetarchive.session.ArchiveSession)

    s3_auth = internetarchive.auth.S3Auth('testaccesskey', 'testsecretkey')
    s3_auth(s)
    assert s.headers['Authorization'] == 'LOW testaccesskey:testsecretkey'
