"""Test Spark Volumes."""
import logging
import random
from os import environ

import pytest
from dynaconf import settings as conf

from common.Fixtures.Configuration.conftest_config import ConfigBaseFixture

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    filemode='w',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


class TestHostConfig(ConfigBaseFixture):

    @pytest.mark.smoke
    @pytest.mark.host
    def test_list_default_hosts(self):
        """Test to verify that OP5 monitor itself
        is added as a default host after installation
        """

        r = self.cb.list_all_hosts()

        assert r.status_code == 200
        default_host_list = r.json()
        default_host = default_host_list[0]
        default_host_name = default_host['name']
        assert default_host_name == 'monitor'

        # Get details of the default host

        r = self.cb.get_host_details(host_name=default_host_name)

        assert r.status_code == 200
        default_host_details = r.json()
        logging.info(f'Default host details: {default_host_details}')
