"""The base client class for all the methods of
/report endpoint of OP5 monitor"""

from dynaconf import settings as conf


class FilterBaseClient(object):

    _suffix = 'filter'

    def __init__(self, client, base_url=None):

        self.base_url = base_url
        if base_url is None:
            self.base_url = conf.OP5_BASE_URL
        self.url = f'{self.base_url}/{self._suffix}'
        self.client = client

    _QUERY = 'query'

    def get_filter_query_data(self, query, columns=None, **kwargs):

        params = dict(query=query, columns=columns, **kwargs)
        full_url = f'{self.url}/{self._QUERY}'
        return self.client.get(url=full_url, params=params)

    _COUNT = 'count'

    def get_filter_query_count(self, query, **kwargs):

        params = dict(query=query, **kwargs)
        full_url = f'{self.url}/{self._COUNT}'
        return self.client.get(url=full_url, params=params)
