import os
import sys
import shutil
import time

import pytest
import internetarchive.session


inc_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, inc_path)

SESSION = internetarchive.session.get_session()


def test_item():
    item = SESSION.get_item('nasa')
    assert isinstance(item.session, internetarchive.session.ArchiveSession)
    assert any(s == item.protocol for s in ['http:', 'https:'])
    assert item.identifier == 'nasa'
    assert item.exists == True
    metadata_api_keys = [
        'files', 'updated', 'uniq', 'created', 'server', 'reviews', 'item_size', 'dir',
        'metadata', 'd2', 'files_count', 'd1'
    ]
    assert all(k in item.__dict__ for k in metadata_api_keys)
    assert item.metadata['title'] == 'NASA Images'

def test_get_metadata():
    item = SESSION.get_item('nasa')
    md = item.get_metadata(timeout=3)
    assert md['metadata']['title'] == item.metadata['title']

def test_iter_files():
    item = SESSION.get_item('nasa')
    files = list(item.iter_files())
    item_files = [
        'NASAarchiveLogo.jpg',
        'globe_west_540.jpg',
        'nasa_reviews.xml',
        'nasa_meta.xml',
        'nasa_archive.torrent',
        'nasa_files.xml',
    ]
    for f in files:
        assert f.name in item_files

def test_get_file():
    item = SESSION.get_item('nasa')
    filename = 'NASAarchiveLogo.jpg'
    f = item.get_file(filename)

    assert not os.path.exists(filename)
    f.download()

    assert unicode(os.stat(filename).st_size) == f.size
    os.unlink(filename)

def test_get_files():
    item = SESSION.get_item('nasa')
    files = item.get_files(source='original')
    item_files = ['NASAarchiveLogo.jpg', 'globe_west_540.jpg']
    assert len(files) == len(item_files)
    for f in files:
        assert f.name in item_files 

    files = item.get_files(files=['NASAarchiveLogo.jpg', 'globe_west_540.jpg'])
    item_files = ['NASAarchiveLogo.jpg', 'globe_west_540.jpg']
    assert len(files) == len(item_files)
    for f in files:
        assert f.name in item_files

    files = item.get_files(formats='Metadata')
    item_files = ['nasa_reviews.xml', 'nasa_meta.xml', 'nasa_files.xml']
    assert len(files) == len(item_files)
    for f in files:
        assert f.name in item_files

    files = item.get_files(glob_pattern='*xml')
    item_files = ['nasa_reviews.xml', 'nasa_meta.xml', 'nasa_files.xml']
    assert len(files) == len(item_files)
    for f in files:
        assert f.name in item_files

cookies = SESSION.get_item('iacli-test-item').session.cookies
@pytest.mark.skipif('len(cookies) == 0', reason='requires authorization.')
def test_modify_metadata():
    item = SESSION.get_item('iacli-test-item')

    valid_key = 'foo-{k}'.format(k=int(time.time()))
    resp = item.modify_metadata({valid_key: 'test value'})
    assert resp.status_code == 200

    assert item.get_metadata()['metadata'][valid_key] == 'test value'

    resp = item.modify_metadata({'-illegal-key': 'fail'})
    assert resp.status_code == 400
    assert resp.json()['success'] == False

def test_download():
    item = SESSION.get_item('nasa')
    item_dir = item.identifier
    assert not os.path.exists(item_dir)
    item.download()
    assert os.path.exists(item_dir)
    assert os.path.exists(os.path.join(item_dir, item.identifier+'_meta.xml'))
    shutil.rmtree(item_dir)
