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

        # Delete the service

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

    def test_host_deletion_deletes_service(self):
        # Add a new custom host to the OP5 monitor.

        host_info = self.create_new_host(name=self.random_string(),
                                         maxcheckattempts=2,
                                         hostaddress=conf.CONFIG_HOST_ADDR,
                                         command='check_ssh',
                                         commandargs=20, checkinterval=2,
                                         retryinterval=2, activechecks=True)

        host_name = host_info['host_name']

        # Adding 2 new services to the host

        # Lets prepare the new service parameters first that we would
        # like to send to the config API endpoint

        command = 'check_ping'
        checkinterval = 2
        hostname = host_name
        maxcheckattempts = 3
        retryinterval = 2
        description1 = self.random_string(prefix='Ping services')
        displayname = f'Ping services for host: {host_name}'
        activechecks = True

        r = self.cb.add_service(command=command,
                                checkinterval=checkinterval,
                                hostname=hostname,
                                maxcheckattempts=maxcheckattempts,
                                retryinterval=retryinterval,
                                description=description1,
                                displayname=displayname,
                                activechecks=activechecks,
                                )

        assert r.status_code == 201

        # Adding another service to check the status of a webserver
        # on the remote host.

        command = 'check_http'
        checkinterval = 2
        hostname = host_name
        maxcheckattempts = 2
        retryinterval = 2
        description2 = self.random_string(prefix='ApacheService')
        displayname = f'Check http service on host: {host_name}'
        activechecks = True

        r = self.cb.add_service(command=command,
                                checkinterval=checkinterval,
                                hostname=hostname,
                                maxcheckattempts=maxcheckattempts,
                                retryinterval=retryinterval,
                                description=description2,
                                displayname=displayname,
                                activechecks=activechecks,
                                )

        # Lets confirm these changes to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='new', object_type='service',
                                     object_name=f'{host_name};{description2}')

        # Now lets delete the host and that should also delete
        # the associated services.

        r = self.cb.delete_host(host_name=host_name)

        assert r.status_code == 200

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        r = self.cb.get_config_changes_to_save()
        assert r.status_code == 200
        r = self.cb.save_config_changes()
        assert r.status_code == 200

        # Verify that the deleted service is now not part of the existing
        # host list monitored by OP5

        r = self.cb.list_all_services()

        assert r.status_code == 200

        service_list_data = r.json()
        service_name_list = [service['name'] for service in service_list_data]
        assert f'{host_name};{description1}' not in service_name_list
        assert f'{host_name};{description2}' not in service_name_list
