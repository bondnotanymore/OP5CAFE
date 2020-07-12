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

        1) Add a new host(some real virtual server on the cloud)
                    to be monitored by OP5
        2) Add relevant checks (check_command=check_ssh in our case) so that
        OP5 can run the relevant plugin for that check within the stipulated
        check intervals set by user and report back the results.
        3) Add couple of services to our server, one which would never fail
        like : check_ping and one which we would like to manipulate and test
        OP5 results with : check_http (checks the status of a webserver)
        3) Set up the server for test, in our case, we need to install a simple
        apache web server on the remote host using Ansible
        4) Let the first check run and verify the reports are good and
        presenting correct data of successful connection to the server/host and
        the apache page can load.
        Verify the state and state_type values and plugin_output is accurate
        as well. We use the /filter api to fetch and verify the results this
        time instead of /reports
        5) Run a Ansible script to manipulate the remote host to bring down
        the apache server or kill its server before the next scheduled
        check.
        6) Let the OP5 do the next check and verify the reports of
        failed connection as the apache web server is down.
        7) Based on maxcheckattempts, let the final check fail as well, when
        the remote host enters a HARD state.
        8) Acknowledge the service problem with proper comments and disable
        the active_checks for the remote host in OP5 till we fix the issue.
        9) Fix the problem using another Ansible script that sets up the
         apache web server on the remote server again so that OP5 can access
         it/connect to it in the next check
        10) Enable the active checks.
        11) Lets the OP5 do the next check and verify the report of successful
        connection this time around. Verify that service is reported as up and
        state,state_type, plugin_output values are correct.
        
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
        description = self.random_string(prefix='Ping services')
        displayname = f'Ping services for host: {host_name}'
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
        time.sleep(next_check_in + 10)

        # Get report in terms of list views from the filter API
        full_query = ''.join([object_type, query])
        logging.info(full_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)

        r = self.fb.get_filter_query_data(query=full_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(
            f'Check results report of service:{description} for host: '
            f'{host_name}  after after 2 min and first check'
            f'post addition of the service: {list_view_data}'
        )
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 0
        assert list_view_data['state_type'] == 1
        assert list_view_data['state_text'] == 'ok'
        assert list_view_data['state_type_text'] == 'hard'
        assert 'HTTP OK' in list_view_data['plugin_output']

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
        time.sleep(next_check_in + 10)

        # Get report in terms of list views from the filter API
        full_query = ''.join([object_type, query])
        logging.info(full_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)

        r = self.fb.get_filter_query_data(query=full_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(
            f'Check results report of service:{description} for host: '
            f'{host_name} for attempt no: {maxcheckattempts-1} after '
            f'{checkinterval} minutes and '
            f'first check post bringing down the service: {list_view_data}'
        )
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 2
        assert list_view_data['state_type'] == 0
        assert list_view_data['state_text'] == 'critical'
        assert list_view_data['state_type_text'] == 'soft'
        assert any(('Connection refused' in list_view_data['plugin_output'],
                    'HTTP CRITICAL' in list_view_data['plugin_output']))

        # This was the first check failed. Following will be
        # maxcheckattempts-1 more checks before the hosts reaches
        # hard state.

        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 10)

        # Get report in terms of list views from the filter API
        full_query = ''.join([object_type, query])
        logging.info(full_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)

        r = self.fb.get_filter_query_data(query=full_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(
            f'Check results report of service:{description} for host: '
            f'{host_name} for attempt no: {maxcheckattempts} after '
            f'{checkinterval} minutes and '
            f'second check post bringing down the service: {list_view_data}'
        )
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 2
        assert list_view_data['state_type'] == 1
        assert list_view_data['state_text'] == 'critical'
        assert list_view_data['state_type_text'] == 'hard'
        assert any(('Connection refused' in list_view_data['plugin_output'],
                    'HTTP CRITICAL' in list_view_data['plugin_output']))

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
        time.sleep(next_check_in + 10)

        # Get report in terms of list views from the filter API
        full_query = ''.join([object_type, query])
        logging.info(full_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)

        r = self.fb.get_filter_query_data(query=full_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(
            f'Default host report after after 2 min and first check post '
            f'acknowledgement and fixing the issue: {list_view_data}'
        )
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 0
        assert list_view_data['state_type'] == 1
        assert list_view_data['state_text'] == 'ok'
        assert list_view_data['state_type_text'] == 'hard'
        assert 'HTTP OK' in list_view_data['plugin_output']

        self.stop_apache()

    def stop_apache(self):
        # Lets bring down the http apache web server on the remote host
        # so that it can be reused for other tests and doesn't cause
        # any discrepancy with the output.

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
