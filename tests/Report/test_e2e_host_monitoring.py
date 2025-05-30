"""Test Spark check ssh plugin."""
import logging
from datetime import datetime as dt, timedelta as td
import time

import pytest
from dynaconf import settings as conf

from common.Fixtures.Configuration.conftest_config import ConfigBaseFixture
from common.Fixtures.Report.conftest_report import ReportBaseFixture
from common.Fixtures.Command.conftest_command import CommandBaseFixture
from common.Fixtures.Filter.conftest_filter import FilterBaseFixture

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    filemode='w',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)


@pytest.mark.usefixtures('my_config_root_fixture',
                         'my_report_root_fixture',
                         'my_command_root_fixture',
                         'my_filter_root_fixture',
                         )
class OP5Fixture(
    ConfigBaseFixture,
    ReportBaseFixture,
    CommandBaseFixture,
    FilterBaseFixture
):
    pass


@pytest.mark.e2e
class TestHostReport(OP5Fixture):

    def test_e2e_check_ssh(self):
        """Test to verify the end-to-end OP5 check_ssh plugin
        functionality.

        1) Add a new host(some real virtual server on the cloud)
                    to be monitored by OP5
        2) Add relevant checks (check_command=check_ssh in our case) so that
        OP5 can run
        the relevant plugin for that check within the stipulated
        check intervals set by user and report back the results.
        3) Set up the server for test, in our case, we need to make sure
        that the ssh port of the server is set to default: 22
        4) Let the first check run and verify the reports are good and
        presenting correct data of successful connection to the server/host.
        Verify the state and state_type values and plugin_output is accurate
        as well.
        5) Run a Ansible script to manipulate the remote host to change its
        default ssh port to some other random value before the next scheduled
        check.
        6) Let the OP5 do the next check and verify the reports of
        failed connection as the port has now changed and OP5 doesn't know
        that.Host is determined as down now in the reports.
        7) Based on maxcheckattempts, let the final check fail as well, when
        the remote host enters a HARD state.
        8) Acknowledge the remote host problem with proper comments and disable
         the active_checks
        for the remote host in OP5 till we fix the issue
        9) Fix the problem using another Ansible script that sets the ssh
        default port back to 22 so that OP5 can access it in the next check
        10) Enable the active checks.
        11) Lets the OP5 do the next check and verify the report of successful
        connection this time around. Verify that host is reported as up and
        state,state_type, plugin_output values are correct

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
        time.sleep(10)
        # Sleeping till the first check.

        object_type = '[hosts]'
        query = f'name="{host_name}"'
        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 45)

        # Get report in terms of events

        r = self.rb.get_state_report_all_events(
            host_name=host_name,
            # start_time=int(start_time),
            # end_time=int(end_time)
        )

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items
        logging.info(
            f'Default host report after {checkinterval} minutes: {r.json()}'
        )
        assert r.status_code == 200

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'host_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['state'] == 'up'
        assert ultimate_event['hard'] == '1'
        assert 'SSH OK' in ultimate_event['output']

        ansible_start = dt.now()
        logging.info(f'Ansible started at :{ansible_start}')
        runner = self.prepare_ansible_runner(
            inv_location=conf.INVENTORY_FILE,
            pb_location=conf.PATH_TO_ANSIBLE,
            pb_name=conf.CHANGE_SSH_PORT
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
            host_name=host_info['host_name'],
            # start_time=int(start_time),
            # end_time=int(end_time)
        )
        logging.info(
            f'Default host report after {checkinterval} minute: {r.json()}'
        )
        assert r.status_code == 200

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'host_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['state'] == 'down'
        assert ultimate_event['hard'] == '0'
        assert any(('Connection refused' in ultimate_event['output'],
                    'SSH CRITICAL' in ultimate_event['output']))

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
        assert ultimate_event['event_type'] == 'host_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['state'] == 'down'
        assert ultimate_event['hard'] == '1'
        assert any(('Connection refused' in ultimate_event['output'],
                    'SSH CRITICAL' in ultimate_event['output']))

        # Lets now acknowledge the event of host connection failure
        # and also disable active checks since the host is now a hardened
        # failure wrt to connection

        r = self.cb.patch_host_details(host_name=host_name,
                                       active_checks_enabled=False)
        self.commit_to_configuration(change_type='change',
                                     object_name=host_name, object_type='host')

        ack_comments = f'Looking into the issue. Looks like the host ' \
                       f'{host_name} is refusing SSH connection to the' \
                       f'default 22 port.\n' \
                       f'Kapil Mathur(OP5 support team)'

        r = self.cmb.acknowledge_host_problem(hostname=host_name, sticky=1,
                                              notify=True, persistent=True,
                                              comment=ack_comments)

        assert r.status_code == 200
        result = r.json()['result']
        assert result == f'Successfully submitted ACKNOWLEDGE_HOST_PROBLEM'

        runner = self.prepare_ansible_runner(
            inv_location=conf.INVENTORY_FILE,
            pb_location=conf.PATH_TO_ANSIBLE,
            pb_name=conf.DEFAULT_SSH_PORT
        )
        logging.info(f'Ansible started at :{dt.now().timestamp()}')
        results = runner.playbook_runner()
        logging.info(f'Ansible finished at :{dt.now().timestamp()}')

        # Post the action to restore the ssh port to default: 22
        # Now the connection should be success again. Lets verify that
        # But first lets enable the active checks.

        r = self.cb.patch_host_details(host_name=host_name,
                                       active_checks_enabled=True)
        self.commit_to_configuration(change_type='change',
                                     object_name=host_name, object_type='host')

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
            f'Default host report after {checkinterval} min and first check'
            f' post acknowledgement and fixing the issue: {r.json()}'
        )
        assert r.status_code == 200

        # Lets collect the events data

        events_data = r.json()['data']  # List of events dictionary items

        # Validate that the last event generated presents correct data

        ultimate_event = events_data[-1]
        assert ultimate_event['event_type'] == 'host_alert'
        assert ultimate_event['host_name'] == host_name
        assert ultimate_event['state'] == 'up'
        assert ultimate_event['hard'] == '1'
        assert 'SSH OK' in ultimate_event['output']
