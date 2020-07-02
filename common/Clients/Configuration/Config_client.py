"""The base client class for all the methods of
/config endpoint of OP5 monitor"""

from dynaconf import settings as conf


class ConfigBaseClient(object):

    _suffix = 'config'

    def __init__(self, client, base_url=None):

        self.base_url = base_url
        if base_url is None:
            self.base_url = conf.OP5_BASE_URL
        self.url = f'{self.base_url}/{self._suffix}'
        self.client = client

    _CHANGE = 'change'

    def get_config_changes_to_save(self,):
        full_url = f'{self.url}/{self._CHANGE}'
        return self.client.get(url=self.url,)

    def revert_config_changes(self,):
        full_url = f'{self.url}/{self._CHANGE}'
        return self.client.post(url=self.url,)

    def save_config_changes(self,):
        full_url = f'{self.url}/{self._CHANGE}'
        return self.client.post(url=self.url,)

    _HOST = 'host'

    def add_host(
        self,
        name,
        maxcheckattempts,
        activechecks,
        hostaddress,
        command,
        commandargs,
        checkinterval,
        retryinterval,
        **kwargs,
    ):

        host_payload = dict(host_name=name,
                            max_check_attempts=maxcheckattempts,
                            active_checks_enabled=activechecks,
                            address=hostaddress, check_command=command,
                            check_command_args=commandargs,
                            check_interval=checkinterval,
                            retry_interval=retryinterval, **kwargs)

        full_url = f'{self.url}/{self._HOST}'
        return self.client.post(url=full_url, data=host_payload)

    def get_host_details(self, host_name):

        full_url = f'{self.url}/{self._HOST}/{host_name}'
        return self.client.get(url=full_url)

    def update_host_details(self, host_name, **kwargs):

        updated_host = dict(**kwargs)
        full_url = f'{self.url}/{self._HOST}/{host_name}'
        return self.client.put(url=full_url, data=updated_host)

    def delete_host(self, host_name):

        full_url = f'{self.url}/{self._HOST}/{host_name}'
        return self.client.delete(url=full_url)

    def list_all_hosts(self):

        full_url = f'{self.url}/{self._HOST}'
        return self.client.get(url=full_url)
