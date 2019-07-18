
from os import path
import sys
import logging

from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_deployment, create_command_context

from src.driver import IxLoadControllerShell2GDriver
import test_ixload_configs
from test_ixload_configs import namespace, server_properties


controller = test_ixload_configs.windows_840

attributes = {'{}.Address'.format(namespace): controller,
              '{}.Controller Version'.format(namespace): server_properties[controller]['ixversion'],
              '{}.ApiKey'.format(namespace): server_properties[controller]['apikey'],
              '{}.License Server'.format(namespace): '192.168.42.61'}


class TestIxLoadControllerDriver(object):

    def setup(self):
        self.session = create_session_from_deployment()
        self.context = create_command_context(self.session, server_properties[controller]['ports'],
                                              namespace, attributes)
        self.driver = IxLoadControllerShell2GDriver()
        self.driver.initialize(self.context)
        self.driver.logger.addHandler(logging.StreamHandler(sys.stdout))
        self.driver.logger.info('logfile = {}'.format(self.driver.logger.handlers[0].baseFilename))

    def teardown(self):
        self.driver.cleanup()
        self.session.EndReservation(self.context.reservation.reservation_id)

    def test_init(self):
        pass

    def test_load_config(self):
        self._load_config('test_config')

    def test_run_traffic(self):
        self.test_load_config()
        self.driver.start_traffic(self.context, 'True')
        print(self.driver.get_statistics(self.context, 'Test_Client', 'json'))
        print(self.driver.get_statistics(self.context, 'Test_Client', 'csv'))

    def _load_config(self, config_name):
        config_file = path.join(path.dirname(__file__), '{}.rxf'.format(config_name))
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Traffic1@Network1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic2@Network2')
        self.driver.load_config(self.context, path.join(path.dirname(__file__), config_file))
