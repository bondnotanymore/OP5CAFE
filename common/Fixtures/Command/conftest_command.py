import logging
# import random
# import time

import pytest
from dynaconf import settings as conf

from common.Clients.Command.Command_client import CommandBaseClient

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


@pytest.fixture(scope='class')
def my_command_root_fixture(request, op5_client_auth_fix, ):
    logging.info('In Command Set up')

    cmb = CommandBaseClient(op5_client_auth_fix, conf.OP5_BASE_URL)

    calling_class = request.cls.__name__
    logging.info(f'Class_name:{calling_class}')

    # inject class variables

    request.cls.cmb = cmb

    yield

    logging.info('In Command tear down')


@pytest.mark.usefixtures('my_command_root_fixture')
class CommandBaseFixture:
    pass
