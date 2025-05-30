import logging
from datetime import datetime as dt
import time

import pytest
from dynaconf import settings as conf

from common.Clients.Filter.Filter_client import FilterBaseClient

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


@pytest.fixture(scope='class')
def my_filter_root_fixture(request, op5_client_auth_fix, ):
    logging.info('In Filter Set up')

    fb = FilterBaseClient(op5_client_auth_fix, conf.OP5_BASE_URL)

    calling_class = request.cls.__name__
    logging.info(f'Class_name:{calling_class}')

    # inject class variables

    request.cls.fb = fb

    yield

    logging.info('In Filter tear down')


@pytest.mark.usefixtures('my_filter_root_fixture')
class FilterBaseFixture:

    @classmethod
    def how_much_to_sleep(cls, object_type, query):

        current_time = dt.now().timestamp()
        logging.info(f'current_time: {current_time}')
        final_query = ''.join([object_type, query])
        columns = 'next_check'
        logging.info(f'final query is : {final_query}')
        r = cls.fb.get_filter_query_data(query=final_query, columns=columns)
        assert r.status_code == 200
        logging.info(r.json())
        next_check_time = r.json()[0]['next_check']
        logging.info(f'next check timestamp: {next_check_time}')
        return next_check_time-current_time

    @classmethod
    def verify_host_up(cls, r):

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 0
        assert list_view_data['state_type'] == 1
        assert list_view_data['state_text'] == 'up'
        assert list_view_data['state_type_text'] == 'hard'

    @classmethod
    def verify_host_down(cls, r, hard=True):

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 1
        if hard:
            assert list_view_data['state_type'] == 1
        else:
            assert list_view_data['state_type'] == 0
        assert list_view_data['state_text'] == 'down'
        if hard:
            assert list_view_data['state_type_text'] == 'hard'
        else:
            assert list_view_data['state_type_text'] == 'soft'

    @classmethod
    def verify_host_unreachable(cls, r, hard=True):

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 2
        if hard:
            assert list_view_data['state_type'] == 1
        else:
            assert list_view_data['state_type'] == 0
        assert list_view_data['state_text'] == 'unreachable'
        if hard:
            assert list_view_data['state_type_text'] == 'hard'
        else:
            assert list_view_data['state_type_text'] == 'soft'
