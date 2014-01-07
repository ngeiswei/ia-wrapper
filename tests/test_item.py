import os
import sys
import shutil

import internetarchive.session


inc_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, inc_path)

SESSION = internetarchive.session.ArchiveSession()


def test_item():
    item = SESSION.get_item('stairs')
    assert isinstance(item.session, internetarchive.session.ArchiveSession)
    assert any(s == item.protocol for s in ['http:', 'https:'])
    assert item.identifier == 'stairs'
    assert item.exists == True
    metadata_api_keys = [
        'files', 'updated', 'uniq', 'created', 'server', 'reviews', 'item_size', 'dir',
        'metadata', 'd2', 'files_count', 'd1'
    ]
    assert all(k in item.__dict__ for k in metadata_api_keys)
    assert item.metadata['title'] == 'stairs where i worked'

def test_get_metadata():
    item = SESSION.get_item('nasa')
    md = item.get_metadata(timeout=3)
    assert md['metadata']['title'] == item.metadata['title']

def test_get_file():
    item = SESSION.get_item('stairs')
    filename = 'glogo.png'
    file = item.get_file(filename)

    assert not os.path.exists(filename)
    file.download()

    assert unicode(os.stat(filename).st_size) == file.size
    os.unlink(filename)

def test_download():
    item = SESSION.get_item('stairs')
    item_dir = item.identifier
    assert not os.path.exists(item_dir)
    item.download()
    assert os.path.exists(item_dir)
    assert os.path.exists(os.path.join(item_dir, item.identifier+'_meta.xml'))
    shutil.rmtree(item_dir)
