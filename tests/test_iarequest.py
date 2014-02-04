# -*- coding: utf-8 -*-
import os, sys
inc_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, inc_path)

import internetarchive.iarequest

def test_build_headers():
    r = internetarchive.iarequest.S3Request(url='https://s3.us.archive.org/iacli-test-item')

    r.metadata = {
        'collection': 'test_collection',
        'foo': u'தமிழ்',
        'subject': ['foo', 'bar', 'baz'],
        'bar': 13,
        'boo': {'test': 'dict'},
        'none': None,
        'none2': False,
        'test_foo': 'underscore',
    }
    r.headers = {
        'x-archive-size-hint': 19327352832,
        'x-archive-test-header': 'test value',
    }

    p = r.prepare()
    s3_headers = p.headers

    test_output = {
            # str test.
            'x-archive-meta00-collection': 'test_collection',

            # unicode test.
            'x-archive-meta00-foo': u'தமிழ்',

            # int test
            'x-archive-meta00-bar': 13,
            
            # list test.
            'x-archive-meta00-subject':'foo',
            'x-archive-meta01-subject': 'bar',
            'x-archive-meta02-subject': 'baz',

            # convert "_" to "--" test (S3 converts "--" to "_").
            'x-archive-meta00-test--ddd': 'sdfsdf',
             
            # dict test.
            'x-archive-meta00-boo': '{"test": "dict"}',
            'x-archive-meta00-test--foo': 'underscore',

            # prepared HTTP headers test.
            'x-archive-size-hint': 19327352832,
            'x-archive-test-header': 'test value',

            # Automatically added.
            'x-archive-meta-scanner': 'Internet Archive Python library {0}'.format(internetarchive.__version__),
            'x-archive-auto-make-bucket': 1,
            'Content-Length': '0',
    }

    for key, value in s3_headers.items():
        if key == 'Authorization':
            continue
        assert test_output[key] == value
