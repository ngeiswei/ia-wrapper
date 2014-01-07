import os
import sys
try:
    import ujson as json
except ImportError:
    import json
from fnmatch import fnmatch
import httplib
from six.moves.urllib.parse import urlencode
import six

import jsonpatch
from requests.exceptions import ConnectionError, HTTPError
from requests import Request

from . import __version__


# Item class
#_________________________________________________________________________________________
class Item(object):
    """This class represents an archive.org item. You can use this
    class to access item metadata::

        >>> import internetarchive
        >>> item = internetarchive.Item('stairs')
        >>> print item.metadata

    Or to modify the metadata for an item::

        >>> metadata = dict(title='The Stairs')
        >>> item.modify(metadata)
        >>> print item.metadata['metadata']['title']
        u'The Stairs'

    This class also uses IA's S3-like interface to upload files to an
    item. You need to supply your IAS3 credentials in environment
    variables in order to upload::

        >>> import os
        >>> os.environ['AWS_ACCESS_KEY_ID'] = 'Y6oUrAcCEs4sK8ey'
        >>> os.environ['AWS_SECRET_ACCESS_KEY'] = 'youRSECRETKEYzZzZ'
        >>> item.upload('myfile.tar')
        True

    You can retrieve S3 keys here: `https://archive.org/account/s3.php
    <https://archive.org/account/s3.php>`__

    """
    # init()
    #_____________________________________________________________________________________
    def __init__(self, session, identifier, **kwargs):
        """
        :type identifier: str
        :param identifier: The globally unique Archive.org identifier
                           for a given item.

        """
        self.session = session
        self.protocol = 'https:' if self.session.secure else 'http:'
        self.identifier = identifier
        self._metadata = self.get_metadata(**kwargs)
        self.exists = True if self._metadata else False

    # __repr__()
    #_____________________________________________________________________________________
    def __repr__(self):
        return ('Item(identifier={identifier!r}, '
                'exists={exists!r}, '
                'item_size={item_size!r}, '
                'files_count={files_count!r})'.format(**self.__dict__))

    # get_metadata()
    #_____________________________________________________________________________________
    def get_metadata(self, **kwargs):
        """Get an item's metadata from the `Metadata API
        <http://blog.archive.org/2013/07/04/metadata-api/>`__

        :type identifier: str
        :param identifier: Globally unique Archive.org identifier.

        :type target: bool
        :param target: (optional) Metadata target to retrieve.

        :rtype: dict
        :returns: Metadat API response.

        """
        url = '{protocol}//archive.org/metadata/{identifier}'.format(**self.__dict__)
        resp = self.session.get(url, **kwargs)
        if resp.status_code != 200:
            raise ConnectionError("Unable connect to Archive.org "
                                  "({0})".format(resp.status_code))
        metadata = resp.json()
        for key in metadata:
            setattr(self, key, metadata[key])
        return metadata

    # iter_files()
    #_____________________________________________________________________________________
    def iter_files(self):
        """Get a :class:`File <File>` object for the named file.

        :rtype: :class:`internetarchive.File <File>`
        :returns: An :class:`internetarchive.File <File>` object.

        """
        for f in self.files:
            yield File(self, f.get('name'))

    # get_file()
    #_____________________________________________________________________________________
    def get_file(self, filename):
        for f in self.files:
            if f.get('name') == filename: 
                return File(self, f.get('name'))

    # get_files()
    #_____________________________________________________________________________________
    def get_files(self, files=[], source=None, formats=None, glob_pattern=None):
        if not isinstance(files, (list, tuple, set)):
            files = [files]
        _files = [f for f in list(self.iter_files()) if f.name in files]
        if source:
            if not isinstance(source, (list, tuple, set)):
                source = [source]
            _files = [f for f in _files if f.source in source]
        if formats:
            if not isinstance(formats, (list, tuple, set)):
                formats = [formats]
            _files = [f for f in _files if f.format in formats]
        if glob_pattern:
            _files = [f for f in _files if fnmatch(f.name, glob_pattern)]
        return _files

    # modify_metadata()
    #_____________________________________________________________________________________
    def modify_metadata(self, metadata, target='metadata', append=False, **kwargs):
        """Modify the metadata of an existing item on Archive.org.

        Note: The Metadata Write API does not yet comply with the
        latest Json-Patch standard. It currently complies with `version 02
        <https://tools.ietf.org/html/draft-ietf-appsawg-json-patch-02>`__.

        :type metadata: dict
        :param metadata: Metadata used to update the item.

        :type target: str
        :param target: (optional) Set the metadata target to update.

        Usage::

            >>> import internetarchive
            >>> item = internetarchive.Item('mapi_test_item1')
            >>> md = dict(new_key='new_value', foo=['bar', 'bar2'])
            >>> item.modify_metadata(md)

        :rtype: dict
        :returns: A dictionary containing the status_code and response
                  returned from the Metadata API.

        """
        self.session.add_s3_auth(access_key=kwargs.get('access_key'),
                                 secret_key=kwargs.get('secret_key'))
        access_key = self.session.auth.access_key
        secret_key = self.session.auth.secret_key

        src = self.metadata.get(target, {})
        dest = src.copy()
        dest.update(metadata)

        # Prepare patch to remove metadata elements with the value: "REMOVE_TAG".
        for key, val in metadata.items():
            if val == 'REMOVE_TAG' or not val:
                del dest[key]
            if append:
                dest[key] = '{0} {1}'.format(src[key], val)

        json_patch = jsonpatch.make_patch(src, dest).patch

        data = {
            '-patch': json.dumps(json_patch),
            '-target': target,
            'access': access_key,
            'secret': secret_key,
        }

        host = 'archive.org'
        path = '/metadata/{0}'.format(self.identifier)
        http = httplib.HTTP(host)
        http.putrequest("POST", path)
        http.putheader("Host", host)
        data = urlencode(data)
        http.putheader("Content-Type", 'application/x-www-form-urlencoded')
        http.putheader("Content-Length", str(len(data)))
        http.endheaders()
        http.send(data)
        status_code, error_message, headers = http.getreply()
        resp_file = http.getfile()
        self.get_metadata()
        return dict(
            status_code=status_code,
            content=json.loads(resp_file.read()),
        )

    # _upload_file()
    #_____________________________________________________________________________________
    def _upload_file(self, body, key=None, metadata={}, headers={}, verbose=False,
                     debug=False, **kwargs):
        """Upload a single file to an item. The item will be created
        if it does not exist.

        :type body: Filepath or file-like object.
        :param body: File or data to be uploaded.

        :type key: str
        :param key: (optional) Remote filename.

        :type metadata: dict
        :param metadata: (optional) Metadata used to create a new item.

        :type headers: dict
        :param headers: (optional) Add additional IA-S3 headers to request.

        :type queue_derive: bool
        :param queue_derive: (optional) Set to False to prevent an item from
                             being derived after upload.

        :type ignore_preexisting_bucket: bool
        :param ignore_preexisting_bucket: (optional) Destroy and respecify the
                                          metadata for an item

        :type verbose: bool
        :param verbose: (optional) Print progress to stdout.

        :type debug: bool
        :param debug: (optional) Set to True to print headers to stdout, and
                      exit without sending the upload request.

        Usage::

            >>> import internetarchive
            >>> item = internetarchive.Item('identifier')
            >>> item._upload_file('/path/to/image.jpg',
            ...                  key='photos/image1.jpg')
            True

        """
        if not hasattr(body, 'read'):
            body = open(body, 'rb')
        if not metadata.get('scanner'):
            scanner = 'Internet Archive Python library {0}'.format(__version__)
            metadata['scanner'] = scanner
        try:
            body.seek(0, os.SEEK_END)
            headers['x-archive-size-hint'] = body.tell()
            body.seek(0, os.SEEK_SET)
        except IOError:
            pass

        key = body.name.split('/')[-1] if key is None else key
        base_url = '{protocol}//s3.us.archive.org/identifier'.format(**self.__dict__)
        url = '{base_url}/{key}'.format(base_url=base_url, key=key)
        request = S3Request(
            method='PUT', 
            url=url, 
            headers=headers, 
            data=body,
            metadata=metadata,
            queue_derive=queue_derive,
        )
        if debug:
            return request
        else:
            if verbose:
                sys.stdout.write(' uploading: {id}\n'.format(id=key))
            prepared_request = request.prepare()
            return self.session.send(prepared_request, stream=True, access_key=access_key,
                                     secret_key=secret_key)

    # upload()
    #_____________________________________________________________________________________
    def upload(self, files, **kwargs):
        """Upload files to an item. The item will be created if it
        does not exist.

        :type files: list
        :param files: The filepaths or file-like objects to upload.

        :type kwargs: dict
        :param kwargs: The keyword arguments from the call to
                       _upload_file().

        Usage::

            >>> import internetarchive
            >>> item = internetarchive.Item('identifier')
            >>> md = dict(mediatype='image', creator='Jake Johnson')
            >>> item.upload('/path/to/image.jpg', metadata=md, queue_derive=False)
            True

        :rtype: bool
        :returns: True if the request was successful and all files were
                  uploaded, False otherwise.

        """
        if not isinstance(files, (dict, list, tuple, set)):
            files = [(None, files)]
        if isinstance(files, dict):
            files = files.items()

        responses = []
        for key, body in files:
            if isinstance(body, six.string_types) and os.path.isdir(body):
                for path, __, files in os.walk(body):
                    for f in files:
                        filepath = os.path.join(path, f)
                        key = os.path.relpath(filepath, body)
                        responses.append(self._upload_file(filepath, key=key, **kwargs))
            else:
                responses = self._upload_file(body, key=key, **kwargs)
        return responses

    # download()
    #_____________________________________________________________________________________
    def download(self, concurrent=False, source=None, formats=None, glob_pattern=None,
                 dry_run=False, verbose=False, ignore_existing=False):
        """Download the entire item into the current working directory.

        :type concurrent: bool
        :param concurrent: Download files concurrently if ``True``.

        :type source: str
        :param source: Only download files matching given source.

        :type formats: str
        :param formats: Only download files matching the given Formats.

        :type glob_pattern: str
        :param glob_pattern: Only download files matching the given glob
                             pattern

        :type ignore_existing: bool
        :param ignore_existing: Overwrite local files if they already
                                exist.

        :rtype: bool
        :returns: True if if files have been downloaded successfully.

        """
        if concurrent:
            try:
                from gevent import monkey
                monkey.patch_socket()
                from gevent.pool import Pool
                pool = Pool()
            except ImportError:
                raise ImportError(
                    """No module named gevent

                    Downloading files concurrently requires the gevent neworking library.
                    gevent and all of it's dependencies can be installed with pip:

                    \tpip install cython git+git://github.com/surfly/gevent.git@1.0rc2#egg=gevent

                    """)

        # Filter files, first by source, then by formats, finally by glob_pattern.
        files = list(self.iter_files())
        if source:
            if not isinstance(source, (list, tuple, set)):
                source = [source]
            files = [f for f in files if f.source in source]
        if formats:
            if not isinstance(formats, (list, tuple, set)):
                formats = [formats]
            files = [f for f in files if f.format in formats]
        if glob_pattern:
            files = [f for f in files if fnmatch(f.name, glob_pattern)]

        responses = []
        for f in files:
            fname = f.name.encode('utf-8')
            path = os.path.join(self.identifier, fname)
            if dry_run:
                sys.stdout.write(f.url + '\n')
                continue
            if verbose:
                sys.stdout.write(' downloading: {0}\n'.format(fname))
            if concurrent:
                responses.append(
                    pool.spawn(f.download, path, ignore_existing=ignore_existing))
            else:
                responses.append(f.download(path, ignore_existing=ignore_existing))
        if concurrent:
            pool.join()
        return responses

    # delete()
    #_____________________________________________________________________________________
    def delete(self, files, glob_pattern=None, **kwargs):
        if not isinstance(files, (list, set, tuple)):
            _file = File(self, files)
            return _file.delete(**kwargs)
        if glob_pattern:
            files = [
                f.get('name') for f in self.files if fnmatch(f.get('name'), glob_pattern)
            ]
        responses = []
        for f in files:
            _file = File(self, f)
            responses.append(_file.delete(**kwargs))
        return responses

# File class
#_________________________________________________________________________________________
class File(object):
    """:todo: document ``internetarchive.File`` class."""
    # init()
    #_____________________________________________________________________________________
    def __init__(self, item, name):
        _file = {}
        for f in item.files:
            if f.get('name') == name:
                _file = f
                break

        self._item = item
        self.identifier = item.identifier
        self.name = name
        self.size = None
        self.source = None
        self.format = None

        for key in _file:
            setattr(self, key, _file[key])

        self.base_url = ('{protocol}//archive.org'
                         '/download/{identifier}'.format(**item.__dict__))
        self.url = '{base_url}/{name}'.format(**self.__dict__)

    # __repr__()
    #_____________________________________________________________________________________
    def __repr__(self):
        return ('File(identifier={identifier!r}, '
                'filename={name!r}, '
                'size={size!r}, '
                'source={source!r}, '
                'format={format!r})'.format(**self.__dict__))

    # download()
    #_____________________________________________________________________________________
    def download(self, file_path=None, ignore_existing=False):
        """:todo: document ``internetarchive.File.download()`` method"""
        file_path = self.name if not file_path else file_path
        if os.path.exists(file_path) and not ignore_existing:
            raise IOError('File already exists: {0}'.format(file_path))

        parent_dir = os.path.dirname(file_path)
        if parent_dir != '' and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        self._item.session.add_cookies()

        try:
            response = self._item.session.get(self.url, stream=True)
            response.raise_for_status()
        except HTTPError as e:
            raise HTTPError('Error downloading {0}, {1}'.format(self.url, e))

        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
        return response

    # delete()
    #_____________________________________________________________________________________
    def delete(self, cascade_delete=False, headers={}, verbose=False, debug=False):
        cascade_delete = 0 if False else 1
        headers['cascade_delete'] = cascade_delete
        url = 'http://s3.us.archive.org/{0}/{1}'.format(self.identifier, self.name)
        request = Request(
            method='DELETE',
            url=url,
            headers=headers,
        )
        if debug:
            return request
        else:
            if verbose:
                sys.stdout.write(' deleting file: {0}\n'.format(self.name))
            prepared_request = request.prepare()
            return self._item.session.send(prepared_request)
