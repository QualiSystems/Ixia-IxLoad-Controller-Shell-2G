
from os import path
import unittest
import time
import json

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import create_session_from_deployment, create_command_context

import test_ixload_configs
from test_ixload_configs import server_properties, namespace


controller = test_ixload_configs.linux_900

attributes = [AttributeNameValue('{}.Address'.format(namespace), controller),
              AttributeNameValue('{}.Controller Version'.format(namespace), server_properties[controller]['ixversion']),
              AttributeNameValue('{}.ApiKey'.format(namespace), server_properties[controller]['apikey']),
              AttributeNameValue('{}.License Server'.format(namespace), '192.168.42.61')]


class TestIxLoadControllerShell(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_deployment()
        self.context = create_command_context(self.session, server_properties[controller]['ports'], namespace,
                                              attributes)

    def tearDown(self):
        reservation_id = self.context.reservation.reservation_id
        self.session.EndReservation(reservation_id)
        while self.session.GetReservationDetails(reservation_id).ReservationDescription.Status != 'Completed':
            time.sleep(1)
        self.session.DeleteReservation(reservation_id)

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config'))

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config'))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, namespace, 'Service',
                                    'start_traffic', [InputNameValue('blocking', 'True')])
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id, namespace, 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Test_Client'),
                                                               InputNameValue('output_type', 'JSON')])
        print(json.loads(stats.Output))

    def _load_config(self, config_name):
        config_file = path.join(path.dirname(__file__), '{}.rxf'.format(config_name))
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Traffic1@Network1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic2@Network2')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, namespace, 'Service',
                                    'load_config', [InputNameValue('config_file_location', config_file)])
