"""Base conftest.py."""
import logging
import pytest

from Authentication.Auth.auth_api import Authorize

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG,
)

pytest_plugins = [
    'common.Fixtures.Configuration.conftest_config',
    'common.Fixtures.Report.conftest_report',
    'common.Fixtures.Command.conftest_command',
]


@pytest.fixture(scope='session')
def op5_client_auth_fix():
    """
    Client fixture for OP5.
    The scope of the fixture is for the entire session of a test run.
    """

    return Authorize()
