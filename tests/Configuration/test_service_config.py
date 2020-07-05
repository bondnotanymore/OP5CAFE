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
@pytest.mark.service
class TestServiceConfig(ConfigBaseFixture):

    def test_list_default_service(self):
        """Test to verify the default service
         running on default host after installation
        """

        r = self.cb.list_all_services()

        assert r.status_code == 200
        default_service_list = r.json()
        default_service = default_service_list[0]
        default_service_name = default_service['name']
        assert default_service_name == 'op5_monitor_servers;SSH Server'

        # Get details of the default host

        r = self.cb.get_service_details(description=default_service_name)

        assert r.status_code == 200
        default_service_details = r.json()
        logging.info(f'Default service details: {default_service_details}')

    def test_service_crud(self):
        """Test to verify the crud operations for a new service"""

        # Lets prepare the new service parameters first that we would
        # like to send to the config API endpoint

        # If there is no host other than the default host available
        # we will have to link it to the default host itself.

        command = 'check_ssh'
        commandargs = 25
        checkinterval = 3
        hostname = 'monitor'
        maxcheckattempts = 3
        retryinterval = 2
        description = 'Custom-ssh'
        displayname = 'New service for monitor'
        activechecks = 1

        r = self.cb.add_service(command=command,
                                commandargs=commandargs,
                                checkinterval=checkinterval,
                                hostname=hostname,
                                maxcheckattempts=maxcheckattempts,
                                retryinterval=retryinterval,
                                description=description,
                                displayname=displayname,
                                activechecks=activechecks,
                                )

        assert r.status_code == 201

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='new', object_type='service',
                                     object_name=f'{hostname};{description}')

        # Verify that the newly added service is now part of the existing
        # service list monitored by OP5

        r = self.cb.list_all_services()

        assert r.status_code == 200

        service_list_data = r.json()
        service_name_list = [service['name'] for service in service_list_data]
        assert f'{hostname};{description}' in service_name_list

        # Patch a single config for the service

        checkinterval = 1

        r = self.cb.patch_service_details(description=description,
                                          check_interval=checkinterval
                                          )

        assert r.status_code == 200

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='change',
                                     object_type='service',
                                     object_name=f'{hostname};{description}')

        # Delete the host

        r = self.cb.delete_service(description=description)

        assert r.status_code == 200

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='delete',
                                     object_type='service',
                                     object_name=f'{hostname};{description}')

        # Verify that the deleted service is now not part of the existing
        # host list monitored by OP5

        r = self.cb.list_all_services()

        assert r.status_code == 200

        service_list_data = r.json()
        service_name_list = [service['name'] for service in service_list_data]
        assert f'{hostname};{description}' not in service_name_list
