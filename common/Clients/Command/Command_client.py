"""The base client class for all the methods of
/command endpoint of OP5 monitor"""

from dynaconf import settings as conf


class CommandBaseClient(object):
    _suffix = 'command'

    def __init__(self, client, base_url=None):
        self.base_url = base_url
        if base_url is None:
            self.base_url = conf.OP5_BASE_URL
        self.url = f'{self.base_url}/{self._suffix}'
        self.client = client

    _command1 = 'ACKNOWLEDGE_HOST_PROBLEM'

    def acknowledge_host_problem(self, hostname, sticky, notify,
                                 persistent, comment):

        host_payload = dict(host_name=hostname, sticky=sticky, notify=notify,
                            persistent=persistent, comment=comment)

        full_url = f'{self.url}/{self._command1}'
        return self.client.post(url=full_url, data=host_payload)

    _command2 = 'ACKNOWLEDGE_SVC_PROBLEM'

    def acknowledge_svc_problem(self, hostname, description, sticky, notify,
                                persistent, comment):
        host_payload = dict(host_name=hostname, service_description=description,
                            sticky=sticky, notify=notify,
                            persistent=persistent, comment=comment)

        full_url = f'{self.url}/{self._command2}'
        return self.client.post(url=full_url, data=host_payload)
