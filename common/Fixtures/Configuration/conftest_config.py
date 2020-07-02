import logging
# import random
# import time

import pytest
from dynaconf import settings as conf

from common.Clients.Configuration.Config_client import ConfigBaseClient


for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)

_hosts_to_delete = []


@pytest.fixture(scope='class')
def my_config_root_fixture(request, op5_client_auth_fix,):

    logging.info('In Config Set up')

    cb = ConfigBaseClient(op5_client_auth_fix, conf.OP5_BASE_URL)

    calling_class = request.cls.__name__
    logging.info(f'Class_name:{calling_class}')

    # inject class variables

    request.cls.cb = cb

    yield

    logging.info('In Config tear down')

    logging.info(f'Hosts accumulated for deleting : {_hosts_to_delete}')

    for host_name in _hosts_to_delete:

        logging.info('Now lets delete the hosts one after the other')
        r = cb.delete_host(host_name)
        logging.info(r.text)


@pytest.mark.usefixtures('my_config_root_fixture')
class ConfigBaseFixture:
    pass
