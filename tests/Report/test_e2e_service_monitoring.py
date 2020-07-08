"""Test OP5 check ssh plugin."""
import logging
from datetime import datetime as dt, timedelta as td
import time

import pytest
from dynaconf import settings as conf

from tests.Report.test_e2e_host_monitoring import OP5Fixture

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    filemode='w',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


@pytest.mark.e2e
class TestHostReport(OP5Fixture):

    def test_e2e_check_http(self):
        """Test to verify the end-to-end OP5 check_http plugin
        functionality.
        """

        # Add a new custom host to the OP5 monitor.

        host_info = self.create_new_host(name=self.random_string(),
                                         maxcheckattempts=2,
                                         hostaddress=conf.PLUGIN_HOST_ADDR,
                                         command='check_ssh',
                                         commandargs=20, checkinterval=2,
                                         retryinterval=2, activechecks=True)

        host_name = host_info['host_name']
        checkinterval = host_info['check_interval']
        self._hosts_to_delete.append(host_name)

        # Adding a new service to the host

        # Lets prepare the new service parameters first that we would
        # like to send to the config API endpoint

        command = 'check_ping'
        checkinterval = 2
        hostname = host_name
        maxcheckattempts = 3
        retryinterval = 2
        description = 'Ping services'
        displayname = f'Ping services for host: {host_name}'
        activechecks = True

        r = self.cb.add_service(command=command,
                                checkinterval=checkinterval,
                                hostname=hostname,
                                maxcheckattempts=maxcheckattempts,
                                retryinterval=retryinterval,
                                description=self.random_string(),
                                displayname=displayname,
                                activechecks=activechecks,
                                )

        assert r.status_code == 201

        # Adding another service to check the status of a webserver
        # on the remote host.

        # As part of setup for this service, we need to install the apache
        # web server on the host

        ansible_start = dt.now()
        logging.info(f'Ansible started at :{ansible_start}')
        runner = self.prepare_ansible_runner(
            inv_location=conf.INVENTORY_FILE,
            pb_location=conf.PATH_TO_ANSIBLE,
            pb_name=conf.START_APACHE
        )

        runner.playbook_runner()
        ansible_end = dt.now()
        logging.info(f'Ansible finished at :{ansible_end}')

        command = 'check_http'
        checkinterval = 2
        hostname = host_name
        maxcheckattempts = 2
        retryinterval = 2
        description = self.random_string(prefix='ApacheService')
        displayname = f'Check http service on host: {host_name}'
        activechecks = True

        r = self.cb.add_service(command=command,
                                checkinterval=checkinterval,
                                hostname=hostname,
                                maxcheckattempts=maxcheckattempts,
                                retryinterval=retryinterval,
                                description=description,
                                displayname=displayname,
                                activechecks=activechecks,
                                )

        # Lets confirm these changes to register in the config files
        # and the monitor service to restart

        self.commit_to_configuration(change_type='new', object_type='service',
                                     object_name=f'{hostname};{description}')
        time.sleep(5)

        # For this test, we would be testing the check_http service

        # Sleeping till the first check of the service.

        object_type = '[services]'
        query = f'description="{description}"'
        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 45)

        # Get report in terms of events

        r = self.rb.get_state_report_all_events(
            service_description=description,
            # start_time=int(start_time),
            # end_time=int(end_time)
        )

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items
        logging.info(
            f'Default service report after {checkinterval} minutes: {r.json()}'
        )
        assert r.status_code == 200

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'service_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['service_description'] == description
        assert ultimate_event['state'] == 'ok'
        assert ultimate_event['hard'] == '1'
        assert 'HTTP OK' in ultimate_event['output']

        # Lets bring down the http apache web server on the remote host

        ansible_start = dt.now()
        logging.info(f'Ansible started at :{ansible_start}')
        runner = self.prepare_ansible_runner(
            inv_location=conf.INVENTORY_FILE,
            pb_location=conf.PATH_TO_ANSIBLE,
            pb_name=conf.STOP_APACHE
        )

        runner.playbook_runner()
        ansible_end = dt.now()
        logging.info(f'Ansible finished at :{ansible_end}')
        time_for_ansible = (ansible_end - ansible_start).total_seconds()

        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 45)

        # Get report in terms of events

        r = self.rb.get_state_report_all_events(
            service_description=description,
            # start_time=int(start_time),
            # end_time=int(end_time)
        )

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items
        logging.info(
            f'Default service report after {checkinterval} minutes: {r.json()}'
        )
        assert r.status_code == 200

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'service_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['service_description'] == description
        assert ultimate_event['state'] == 'critical'
        assert ultimate_event['hard'] == '0'
        assert any(('Connection refused' in ultimate_event['output'],
                    'HTTP CRITICAL' in ultimate_event['output']))

        # This is the first check failed. Following will be
        # maxcheckattempts-1 more checks before the hosts reaches
        # hard state.

        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 45)

        # Get report in terms of events

        r = self.rb.get_state_report_all_events(
            host_name=host_info['host_name'],
            # start_time=int(start_time),
            # end_time=int(end_time)
        )
        logging.info(
            f'Default host report after next 2 checks failure: {r.json()}'
        )
        assert r.status_code == 200

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'service_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['state'] == 'critical'
        assert ultimate_event['hard'] == '1'
        assert any(('Connection refused' in ultimate_event['output'],
                    'SSH CRITICAL' in ultimate_event['output']))

        # Lets now acknowledge the event of service failure
        # and also disable active checks since the service is now a hardened
        # failure wrt to connection

        r = self.cb.patch_service_details(description=description,
                                          active_checks_enabled=False)
        self.commit_to_configuration(change_type='change',
                                     object_type='service',
                                     object_name=f'{hostname};{description}')

        ack_comments = f'Looking into the issue. Looks like the service for ' \
                       f'{host_name} is failing HTTP connection to the' \
                       f'default 80 port.\n' \
                       f'Kapil Mathur(OP5 support team)'

        r = self.cmb.acknowledge_svc_problem(hostname=host_name,
                                             description=description, sticky=1,
                                             notify=True, persistent=True,
                                             comment=ack_comments)

        assert r.status_code == 200
        result = r.json()['result']
        assert result == f'Successfully submitted ACKNOWLEDGE_SVC_PROBLEM'

        # Lets bring up the apache2 server back on the remote host

        runner = self.prepare_ansible_runner(
            inv_location=conf.INVENTORY_FILE,
            pb_location=conf.PATH_TO_ANSIBLE,
            pb_name=conf.START_APACHE
        )
        logging.info(f'Ansible started at :{dt.now().timestamp()}')
        results = runner.playbook_runner()
        logging.info(f'Ansible finished at :{dt.now().timestamp()}')

        # Post the action to restore the apache service,
        # now the HTTP connection to port 80 should be success again.
        # Lets verify that
        # But first lets enable the active checks.

        r = self.cb.patch_service_details(description=description,
                                          active_checks_enabled=True)
        self.commit_to_configuration(change_type='change',
                                     object_type='service',
                                     object_name=f'{hostname};{description}')

        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 45)

        # Get report in terms of events

        r = self.rb.get_state_report_all_events(
            service_description=description,
            # start_time=int(start_time),
            # end_time=int(end_time)
        )

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items
        logging.info(
            f'Default service report after {checkinterval} min and first check'
            f' post acknowledgement and fixing the issue: {r.json()}'
        )
        assert r.status_code == 200

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'service_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['service_description'] == description
        assert ultimate_event['state'] == 'ok'
        assert ultimate_event['hard'] == '1'
        assert 'HTTP OK' in ultimate_event['output']
