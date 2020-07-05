import logging
# import random
# import time

import pytest
from dynaconf import settings as conf

from common.Clients.Report.Report_client import ReportBaseClient

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


@pytest.fixture(scope='class')
def my_report_root_fixture(request, op5_client_auth_fix, ):
    logging.info('In Report Set up')

    rb = ReportBaseClient(op5_client_auth_fix, conf.OP5_BASE_URL)

    calling_class = request.cls.__name__
    logging.info(f'Class_name:{calling_class}')

    # inject class variables

    request.cls.rb = rb

    yield

    logging.info('In Report tear down')


@pytest.mark.usefixtures('my_report_root_fixture')
class ReportBaseFixture:
    pass
