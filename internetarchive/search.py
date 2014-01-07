try:
    import ujson as json
except ImportError:
    import json
import urllib



# Search class
#_________________________________________________________________________________________
class Search(object):
    """This class represents an archive.org item search. You can use 
    this class to search for archive.org items using the advanced 
    search engine.

    Usage::

        >>> import internetarchive
        >>> search = internetarchive.Search('(uploader:jake@archive.org)')
        >>> for result in search.results:
        ...     print result['identifier']

    """

    # init()
    #_____________________________________________________________________________________
    def __init__(self, query, fields=['identifier'], params={}):
        self._base_url = 'http://archive.org/advancedsearch.php'
        self.query = query
        self.params = dict(dict(
                q = self.query,
                output = params.get('output', 'json'),
                rows = 100,
        ).items() + params.items())
        # Updata params dict with fields.
        for k, v in enumerate(fields):
            key = 'fl[{0}]'.format(k)
            self.params[key] = v
        self.encoded_params = urllib.urlencode(self.params)
        self.search_info = self._get_search_info()
        self.num_found = self.search_info['response']['numFound']


    # __repr__()
    #_____________________________________________________________________________________
    def __repr__(self):
        return ('Search(query={query!r}, '
                'num_found={num_found!r})'.format(**self.__dict__))


    # _get_search_info()
    #_____________________________________________________________________________________
    def _get_search_info(self):
        info_params = self.params.copy()
        info_params['rows'] = 0
        encoded_info_params = urllib.urlencode(info_params)
        f = urllib.urlopen(self._base_url, encoded_info_params)
        results = json.loads(f.read())
        del results['response']['docs']
        return results


    # _iter_results()
    #_____________________________________________________________________________________
    def results(self):
        """Generator for iterating over search results"""
        total_pages = ((self.num_found / self.params['rows']) + 2)
        for page in range(1, total_pages):
            self.params['page'] = page
            encoded_params = urllib.urlencode(self.params)
            f = urllib.urlopen(self._base_url, encoded_params)
            results = json.loads(f.read())
            for doc in results['response']['docs']:
                yield doc
