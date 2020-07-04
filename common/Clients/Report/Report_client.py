"""The base client class for all the methods of
/report endpoint of OP5 monitor"""

from dynaconf import settings as conf


class ReportBaseClient(object):

    _suffix = 'report'

    def __init__(self, client, base_url=None):

        self.base_url = base_url
        if base_url is None:
            self.base_url = conf.OP5_BASE_URL
        self.url = f'{self.base_url}/{self._suffix}'
        self.client = client

    _STATE = 'state'

    def get_current_state_report(self, **kwargs):

        params = dict(**kwargs)
        full_url = f'{self.url}/{self._STATE}'
        return self.client.get(url=full_url, params=params)

    _EVENT = 'event'

    def get_state_report_all_events(self, **kwargs):

        params = dict(**kwargs)
        full_url = f'{self.url}/{self._EVENT}'
        return self.client.get(url=full_url, params=params)
