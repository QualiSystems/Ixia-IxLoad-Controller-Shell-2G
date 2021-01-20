"""
Test IxLoadController2GDriver.
"""
import json
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue, CloudShellAPISession
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.traffic.helpers import set_family_attribute, get_resources_from_reservation, get_reservation_id
from cloudshell.traffic.tg import IXLOAD_CONTROLLER_MODEL, IXIA_CHASSIS_MODEL
from shellfoundry_traffic.test_helpers import create_session_from_config, TestHelpers

from src.ixl_driver import IxLoadController2GDriver


ALIAS = 'IxLoad Controller'

windows_910 = 'localhost'
linux_910 = '192.168.65.25'

originate_910 = 'ixia-910-1/Module1/Port1'
terminate_910 = 'ixia-910-2/Module1/Port1'

server_properties = {'windows_910': {'server': windows_910, 'version': '9.10.115.94',
                                     'ports': [originate_910, terminate_910],
                                     'apikey': 'YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ=='},
                     'linux_910': {'server': windows_910, 'version': '9.10.115.94',
                                   'ports': [originate_910, terminate_910],
                                   'apikey': 'YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ=='}}


@pytest.fixture(scope='session')
def session() -> CloudShellAPISession:
    yield create_session_from_config()


@pytest.fixture()
def test_helpers(session: CloudShellAPISession) -> TestHelpers:
    test_helpers = TestHelpers(session)
    test_helpers.create_reservation()
    yield test_helpers
    test_helpers.end_reservation()


@pytest.fixture(params=['windows_910', 'linux_910'])
def server(request: SubRequest) -> list:
    controller_address = server_properties[request.param]['server']
    version = server_properties[request.param]['version']
    apikey = server_properties[request.param]['apikey']
    ports = server_properties[request.param]['ports']
    yield controller_address, version, apikey, ports


@pytest.fixture()
def driver(test_helpers: TestHelpers, server: list) -> IxLoadController2GDriver:
    controller_address, controller_version, apikey, _ = server
    attributes = {f'{IXLOAD_CONTROLLER_MODEL}.Address': controller_address,
                  f'{IXLOAD_CONTROLLER_MODEL}.Controller Version': controller_version,
                  f'{IXLOAD_CONTROLLER_MODEL}.ApiKey': apikey,
                  f'{IXLOAD_CONTROLLER_MODEL}.License Server': '192.168.42.61',
                  f'{IXLOAD_CONTROLLER_MODEL}.Licensing Mode': 'Perpetual'}
    init_context = test_helpers.service_init_command_context(IXLOAD_CONTROLLER_MODEL, attributes)
    driver = IxLoadController2GDriver()
    driver.initialize(init_context)
    print(driver.logger.handlers[0].baseFilename)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session: CloudShellAPISession, test_helpers: TestHelpers, server: list) -> ResourceCommandContext:
    controller_address, controller_version, apikey, ports = server
    attributes = [AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.Address', controller_address),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.Controller Version', controller_version),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.ApiKey', apikey),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.License Server', '192.168.42.61'),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.Licensing Mode', 'Perpetual')]
    session.AddServiceToReservation(test_helpers.reservation_id, IXLOAD_CONTROLLER_MODEL, ALIAS, attributes)
    context = test_helpers.resource_command_context(service_name=ALIAS)
    session.AddResourcesToReservation(test_helpers.reservation_id, ports)
    reservation_ports = get_resources_from_reservation(context, f'{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort')
    set_family_attribute(context, reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
    set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Traffic2@Network2')
    yield context


class TestIxLoadControllerDriver:

    def test_load_config(self, driver: IxLoadController2GDriver, context: ResourceCommandContext):
        self._load_config(driver, context, 'test_config')

    def test_run_traffic(self, driver, context):
        self._load_config(driver, context, 'test_config')
        driver.start_traffic(context, 'True')
        print(driver.get_statistics(context, 'Test_Client', 'json'))
        print(driver.get_statistics(context, 'Test_Client', 'csv'))

    def _load_config(self, driver: IxLoadController2GDriver, context: ResourceCommandContext, config_name: str) -> None:
        config_file = Path(__file__).parent.joinpath(f'{config_name}.rxf')
        driver.load_config(context, config_file.as_posix())


class TestIxLoadControllerShell:

    def test_load_config(self, session, context):
        self._load_config(session, context, ALIAS, 'test_config')

    def test_run_traffic(self, session, context):
        self._load_config(session, context, ALIAS, 'test_config')
        session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                               'start_traffic',
                               [InputNameValue('blocking', 'True')])
        stats = session.ExecuteCommand(get_reservation_id(context), ALIAS, 'Service',
                                       'get_statistics',
                                       [InputNameValue('view_name', 'Test_Client'),
                                        InputNameValue('output_type', 'JSON')])
        print(json.loads(stats.Output))

    def _load_config(self, session, context, alias, config_name):
        config_file = Path(__file__).parent.joinpath(f'{config_name}.rxf')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'load_config',
                               [InputNameValue('config_file_location', config_file.as_posix())])
