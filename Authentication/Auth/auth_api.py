import logging

import requests
# noinspection PyProtectedMember
from dynaconf import settings as conf

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


class Authorize:
    def __init__(self, user=None, password=None):

        self.user = conf.USER if user is None else user
        self.password = conf.PASSWORD if password is None else password
        self.authed_user = (self.user, self.password)
        self.request_std_params = {'auth': self.authed_user, 'verify': False}
        self.headers = {'Content-Type': 'application/json'}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get(self, url, params=None):
        """GET Request."""
        return self.session.get(url, params=params, **self.request_std_params)

    def post(self, url, data=None):
        """POST Request."""

        logging.info(f'Request_payload: {data}')

        return self.session.post(url, json=data, **self.request_std_params)

    def put(self, url, data):
        """PUT Request."""

        logging.info(f'Request_payload: {data}')

        return self.session.put(url, json=data, **self.request_std_params)

    def patch(self, url, data):
        """PUT Request."""

        logging.info(f'Request_payload: {data}')

        return self.session.patch(url, json=data, **self.request_std_params)

    def delete(self, url):
        """DELETE Request."""
        return self.session.delete(url, **self.request_std_params)


if __name__ == '__main__':

    my_basic_auth = Authorize()
