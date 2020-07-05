"""Test Spark Volumes."""
import logging

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


@pytest.mark.smoke
@pytest.mark.config
@pytest.mark.host
class TestHostConfig(ConfigBaseFixture):

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

    def test_host_crud(self):
        """Test to verify the crud operations for a new host"""

        # Lets prepare the new host parameters first that we would
        # like to send to the config API endpoint

        name = 'First-local'
        maxcheckattempts = 3
        activechecks = 1
        hostaddress = conf.CONFIG_HOST_ADDR
        command = 'check_tcp'
        commandargs = 1156
        checkinterval = 1
        retryinterval = 1
        alias = 'Trying out with localhost first'
        notes = 'Lets have notes'

        r = self.cb.add_host(name=name, maxcheckattempts=maxcheckattempts,
                             activechecks=activechecks, hostaddress=hostaddress,
                             command=command, commandargs=commandargs,
                             checkinterval=checkinterval,
                             retryinterval=retryinterval, alias=alias,
                             notes=notes)

        assert r.status_code == 201

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='new', object_type='host',
                                     object_name=name)

        # Verify that the newly added host is now part of the existing
        # host list monitored by OP5

        r = self.cb.list_all_hosts()

        assert r.status_code == 200

        host_list_data = r.json()
        host_name_list = [host['name'] for host in host_list_data]
        assert name in host_name_list

        # Update multiple config for the host

        checkinterval, retryinterval = 2, 2

        r = self.cb.update_host_details(host_name=name,
                                        check_interval=checkinterval,
                                        retry_interval=retryinterval)

        assert r.status_code == 201

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='change', object_type='host',
                                     object_name=name)

        # Patch a single config for the host

        checkinterval = 1

        r = self.cb.update_host_details(host_name=name,
                                        check_interval=checkinterval,
                                        retry_interval=retryinterval)

        assert r.status_code == 201

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='change', object_type='host',
                                     object_name=name)

        # Delete the host

        r = self.cb.delete_host(host_name=name)

        assert r.status_code == 200

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='delete', object_type='host',
                                     object_name=name)

        # Verify that the deleted host is now not part of the existing
        # host list monitored by OP5

        r = self.cb.list_all_hosts()

        assert r.status_code == 200

        host_list_data = r.json()
        host_name_list = [host['name'] for host in host_list_data]
        assert name not in host_name_list
