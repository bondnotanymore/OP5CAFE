"""Test Spark check ssh plugin."""
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
class TestHostParentChild(OP5Fixture):

    def test_host_parent_child_logic(self):
        """Test to verify the reachability logic for a parent-child
        hosts setup in OP5.

        We will add one host: host1 to the OP5 with a certain check and then
        add another host: host2 the parent of which will be: host1.

        As per the reachability logic, if host2 is down and host1 is up, then
        OP5 will determine host2(child) as down.

        But if host2 is down and host1 is down as well, then the actual state
        of host2 doesnt make a difference and OP5 will determine host2 as
        unreachable and NOT down as its parent is down through which OP5 tries
        to reach it.
        """

        # Add a new host(localhost) to the OP5 monitor(as the parent)
        # and then we will add another custom host as a child host to it.

        parent_host_info = self.create_new_host(name=self.random_string(
                                                prefix='ParentHOST'),
                                                maxcheckattempts=2,
                                                hostaddress=conf.CONFIG_HOST_ADDR,
                                                command='check_ping',
                                                checkinterval=1,
                                                retryinterval=2,
                                                activechecks=True)

        parent_host_name = parent_host_info['host_name']
        self._hosts_to_delete.append(parent_host_name)
        time.sleep(5)

        # Sleeping till the next check
        object_type = '[hosts]'
        query = f'name="{parent_host_name}"'
        next_check_in_for_parent = self.how_much_to_sleep(
            object_type=object_type, query=f'name="{parent_host_name}"'
        )
        logging.info(f'OP5 will do next check in : {next_check_in_for_parent}')
        time.sleep(next_check_in_for_parent + 10)

        # Get report in terms of list views from the filter API
        full_parent_query = ''.join(
            [object_type, f'name="{parent_host_name}"']
        )
        logging.info(full_parent_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)

        r = self.fb.get_filter_query_data(query=full_parent_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 0
        assert list_view_data['state_type'] == 1
        assert list_view_data['state_text'] == 'up'
        assert list_view_data['state_type_text'] == 'hard'

        # Lets now patch the parent host with a check
        # that's not going to pass and will make it go down

        r = self.cb.patch_host_details(host_name=parent_host_name,
                                       check_command='check_adam',
                                       )
        assert r.status_code == 200

        self.commit_to_configuration(change_type='change',
                                     object_name=parent_host_name,
                                     object_type='host')

        # Sleeping till the next check
        object_type = '[hosts]'
        query = f'name="{parent_host_name}"'
        next_check_in_for_parent = self.how_much_to_sleep(
            object_type=object_type, query=f'name="{parent_host_name}"'
        )
        logging.info(f'OP5 will do next check in : {next_check_in_for_parent}')
        time.sleep(next_check_in_for_parent + 10)

        # Get report in terms of list views from the filter API
        full_parent_query = ''.join(
            [object_type, f'name="{parent_host_name}"']
        )
        logging.info(full_parent_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)

        r = self.fb.get_filter_query_data(query=full_parent_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 1
        assert list_view_data['state_type'] == 0
        assert list_view_data['state_text'] == 'down'
        assert list_view_data['state_type_text'] == 'soft'

        # Adding a new child, with a valid command so that its first
        # first check passes.

        child_host_info = self.create_new_host(name=self.random_string(
                                               prefix='ChildHOST'),
                                               maxcheckattempts=2,
                                               hostaddress=conf.PLUGIN_HOST_ADDR,
                                               command='check_ping',
                                               checkinterval=2,
                                               retryinterval=2,
                                               activechecks=True,
                                               parents=[f'{parent_host_name}'])

        child_host_name = child_host_info['host_name']

        checkinterval = child_host_info['check_interval']
        self._hosts_to_delete.append(child_host_name)
        time.sleep(5)

        # Sleeping till the first check of child host, which should pass
        # since its a simple ping check and the server is up.

        query = f'name="{child_host_name}"'
        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 10)

        # Get report in terms of list views from the filter API
        full_child_query = ''.join([object_type, query])
        logging.info(full_child_query)
        columns = f'state,state_text,has_been_checked,state_type,' \
                  f'state_type_text,plugin_output'
        logging.info(columns)
        #
        r = self.fb.get_filter_query_data(query=full_child_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 0
        assert list_view_data['state_type'] == 1
        assert list_view_data['state_text'] == 'up'
        assert list_view_data['state_type_text'] == 'hard'

        # Lets now patch the child host with a check
        # that's not going to pass and will make it go down

        r = self.cb.patch_host_details(host_name=child_host_name,
                                       check_command='check_adam')
        assert r.status_code == 200

        self.commit_to_configuration(change_type='change',
                                     object_name=child_host_name,
                                     object_type='host')

        # Sleeping till the next check of child host, which should fail
        # as there is no HTTP service available on it and OP5 should determine
        # it as down.

        next_check_in = self.how_much_to_sleep(
            object_type=object_type, query=query
        )
        logging.info(f'OP5 will do next check in : {next_check_in}')
        time.sleep(next_check_in + 10)

        # Get report in terms of list views from the filter API
        r = self.fb.get_filter_query_data(query=full_child_query,
                                          columns=columns)

        assert r.status_code == 200
        list_view_data = r.json()[0]
        logging.info(list_view_data)
        assert list_view_data['has_been_checked'] == 1
        assert list_view_data['state'] == 2
        assert list_view_data['state_type'] == 0
        assert list_view_data['state_text'] == 'unreachable'
        assert list_view_data['state_type_text'] == 'soft'
