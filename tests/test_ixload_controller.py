
import sys
from os import path
import json
import pytest

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg import IXLOAD_CONTROLLER_MODEL
from cloudshell.traffic.helpers import (set_family_attribute, add_resources_to_reservation,
                                        get_resources_from_reservation, get_reservation_id)
from shellfoundry.releasetools.test_helper import (create_init_command_context, create_session_from_deployment,
                                                   create_service_command_context, end_reservation)

from src.ixl_driver import IxLoadControllerShell2GDriver

windows_840 = '192.168.65.68'
windows_850 = '192.168.65.94'
linux_850 = '192.168.65.87'
windows_900 = '192.168.15.25'
linux_900 = '192.168.65.69'
localhost_900 = 'localhost'

originate_840 = 'ixia-840-1/Module1/Port1'
terminate_840 = 'ixia-840-2/Module1/Port1'
originate_850 = 'ixia-850-1/Module1/Port1'
terminate_850 = 'ixia-850-2/Module1/Port1'
originate_900 = 'ixia-900-1/Module1/Port1'
terminate_900 = 'ixia-900-2/Module1/Port1'

server_properties = {windows_840: {'ports': [originate_840, terminate_840], 'ixversion': '8.40.0.277',
                                   'apikey': None},
                     windows_850: {'ports': [originate_850, terminate_850], 'ixversion': '',
                                   'apikey': None},
                     linux_850: {'ports': [originate_850, terminate_850], 'ixversion': '8.50.115.333',
                                 'apikey': None},
                     windows_900: {'ports': [originate_900, terminate_900], 'ixversion': '9.00.0.347',
                                   'apikey': 'YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ=='},
                     linux_900: {'ports': [originate_900, terminate_900], 'ixversion': '9.00.0.347',
                                 'apikey': None}}


@pytest.fixture()
def alias():
    yield 'IxLoad Controller'


# @pytest.fixture(params=[localhost_900, linux_900],
#                 ids=['windows-900', 'linux-900'])
@pytest.fixture(params=[windows_900])
def server(request):
    controller_address = request.param
    ixversion = server_properties[controller_address]['ixversion']
    apikey = server_properties[controller_address]['apikey']
    ports = server_properties[controller_address]['ports']
    yield controller_address, ixversion, apikey, ports


@pytest.fixture()
def session():
    yield create_session_from_deployment()


@pytest.fixture()
def driver(session, server):
    controller_address, controller_version, apikey, _ = server
    attributes = {f'{IXLOAD_CONTROLLER_MODEL}.Address': controller_address,
                  f'{IXLOAD_CONTROLLER_MODEL}.Controller Version': controller_version,
                  f'{IXLOAD_CONTROLLER_MODEL}.ApiKey': apikey,
                  f'{IXLOAD_CONTROLLER_MODEL}.License Server': '192.168.42.61'}
    init_context = create_init_command_context(session, 'CS_TrafficGeneratorController', IXLOAD_CONTROLLER_MODEL,
                                               'na', attributes, 'Service')
    driver = IxLoadControllerShell2GDriver()
    driver.initialize(init_context)
    print(driver.logger.handlers[0].baseFilename)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session, alias, server):
    controller_address, controller_version, apikey, ports = server
    attributes = [AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.Address', controller_address),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.Controller Version', controller_version),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.ApiKey', apikey),
                  AttributeNameValue(f'{IXLOAD_CONTROLLER_MODEL}.License Server', '192.168.42.61')]
    context = create_service_command_context(session, IXLOAD_CONTROLLER_MODEL, alias, attributes)
    add_resources_to_reservation(context, *ports)
    reservation_ports = get_resources_from_reservation(context,
                                                       'Generic Traffic Generator Port',
                                                       'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
    set_family_attribute(context, reservation_ports[0].Name, 'Logical Name', 'Traffic1@Network1')
    set_family_attribute(context, reservation_ports[1].Name, 'Logical Name', 'Traffic2@Network2')
    yield context
    end_reservation(session, get_reservation_id(context))


class TestIxLoadControllerDriver:

    def test_load_config(self, driver, context):
        self._load_config(driver, context, 'test_config')

    def test_run_traffic(self, driver, context):
        self._load_config(driver, context, 'test_config')
        driver.start_traffic(context, 'True')
        print(driver.get_statistics(context, 'Test_Client', 'json'))
        print(driver.get_statistics(context, 'Test_Client', 'csv'))

    def _load_config(self, driver, context, config_name):
        config_file = path.join(path.dirname(__file__), '{}.rxf'.format(config_name))
        driver.load_config(context, path.join(path.dirname(__file__), config_file))


class TestIxLoadControllerShell:

    def test_load_config(self, session, context, alias):
        self._load_config(session, context, alias, 'test_config')

    def test_run_traffic(self, session, context, alias):
        self._load_config(session, context, alias, 'test_config')
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'start_traffic',
                               [InputNameValue('blocking', 'True')])
        stats = session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                                       'get_statistics',
                                       [InputNameValue('view_name', 'Test_Client'),
                                        InputNameValue('output_type', 'JSON')])
        print(json.loads(stats.Output))

    def _load_config(self, session, context, alias, config_name):
        config_file = path.join(path.dirname(__file__), '{}.rxf'.format(config_name))
        session.ExecuteCommand(get_reservation_id(context), alias, 'Service',
                               'load_config',
                               [InputNameValue('config_file_location', config_file)])
