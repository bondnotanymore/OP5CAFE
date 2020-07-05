import logging
import random
import string

import pytest
from dynaconf import settings as conf

from common.Clients.Configuration.Config_client import ConfigBaseClient
from common.tools.Ansible.Ansible import ansible_runner

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)

_hosts_to_delete = []


@pytest.fixture(scope='class')
def my_config_root_fixture(request, op5_client_auth_fix, ):
    logging.info('In Config Set up')

    cb = ConfigBaseClient(op5_client_auth_fix, conf.OP5_BASE_URL)

    calling_class = request.cls.__name__
    logging.info(f'Class_name:{calling_class}')

    # inject class variables

    request.cls.cb = cb
    request.cls._hosts_to_delete = _hosts_to_delete

    yield

    logging.info('In Config tear down')

    logging.info(f'Hosts accumulated for deleting : {_hosts_to_delete}')

    for host_name in _hosts_to_delete:
        logging.info('Now lets delete the hosts one after the other')
        for name in _hosts_to_delete:
            r = cb.delete_host(host_name=name)

            assert r.status_code == 200

            # Lets confirm this change to register in the config files
            # and the monitor service to restart

            r = cb.get_config_changes_to_save()
            assert r.status_code == 200
            r = cb.save_config_changes()
            assert r.status_code == 200


@pytest.mark.usefixtures('my_config_root_fixture')
class ConfigBaseFixture:

    @classmethod
    def prepare_ansible_runner(cls, inv_location, pb_location, pb_name):
        return ansible_runner(inv_location=inv_location,
                              pb_location=pb_location,
                              pb_name=pb_name
                              )

    @classmethod
    def commit_to_configuration(cls, change_type, object_type, object_name):
        r = cls.cb.get_config_changes_to_save()
        assert r.status_code == 200

        changes = r.json()[0]
        assert changes['type'] == change_type
        assert changes['object_type'] == object_type
        assert changes['name'] == object_name
        assert changes['user'] == conf.USER

        # Confirming the change to make the changes transfer from
        # nacoma to nachos to config files for naemon to read them
        # and reload its services

        r = cls.cb.save_config_changes()
        assert r.status_code == 200

        # Verify that there are no changes left to save now

        r = cls.cb.get_config_changes_to_save()

        assert r.status_code == 200
        changes = r.json()
        assert not changes

    @classmethod
    def create_new_host(cls, name, maxcheckattempts, hostaddress,
                        command, commandargs, checkinterval, retryinterval,
                        activechecks, **kwargs):

        r = cls.cb.add_host(name=name, maxcheckattempts=maxcheckattempts,
                            activechecks=activechecks,
                            hostaddress=hostaddress,
                            command=command, commandargs=commandargs,
                            checkinterval=checkinterval,
                            retryinterval=retryinterval
                            )

        assert r.status_code == 201

        # Lets confirm this change to register in the config files
        # and the monitor service to restart

        cls.commit_to_configuration(change_type='new', object_type='host',
                                    object_name=name)

        return cls.cb.get_host_details(host_name=name).json()

    @staticmethod
    def random_string(prefix='HOST', size=4, suffix='OP5'):
        """
        Return a random string of alphanumeric characters of 'size' length.
        The string would be embedded with the current timestamp in isoformat
        at the time of being called.

        For eg : 'Server_SyvHL5IX_SPARK_2019-06-03T17:44:42.856788'
        """
        if size <= 0:
            return '{}{}'.format(prefix or '', suffix or '')

        charpool = tuple(string.ascii_letters + string.digits)
        final_string = ''
        while size > 0:
            segment_size = min(int(len(charpool) / 2), size)
            size = size - segment_size
            final_string += ''.join(random.sample(charpool, segment_size))
        return '{}_{}_{}'.format(prefix, final_string, suffix)
