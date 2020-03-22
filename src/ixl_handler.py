import json
import csv
import io
import os
from collections import OrderedDict

from cloudshell.traffic.tg import TrafficHandler, attach_stats_csv
from cloudshell.traffic.common import get_reservation_id, get_resources_from_reservation
from cloudshell.traffic.tg_helper import get_address, is_blocking, get_family_attribute

from ixload.ixl_app import init_ixl
from ixload.ixl_statistics_view import IxlStatView

from ixl_data_model import IxLoad_Controller_Shell_2G


class IxlHandler(TrafficHandler):

    def initialize(self, context, logger):

        service = IxLoad_Controller_Shell_2G.create_from_context(context)
        super(self.__class__, self).initialize(service, logger)

        self.ixl = init_ixl(self.logger)

        ixload_gw = self.resource.address if self.resource.address not in ['', 'na'] else 'localhost'
        version = self.service.controller_version
        apikey = self.service.apikey
        auth = {'apikey': apikey, 'crt': None}

        self.logger.info('connecting to server {} version {} using default port'.format(ixload_gw, version))
        self.ixl.connect(version=version, ip=ixload_gw, port=None, auth=auth)
        if self.service.license_server:
            self.ixl.controller.set_licensing(self.service.license_server)
        if not self.ixl.is_remote:
            log_file_name = self.logger.handlers[0].baseFilename
            results_dir = (os.path.splitext(log_file_name)[0] + '--Results').replace('\\', '/')
            self.ixl.controller.set_results_dir(results_dir)

    def cleanup(self):
        self.ixl.disconnect()

    def load_config(self, context, ixia_config_file_name):
        reservation_id = get_reservation_id(context)

        self.ixl.load_config(ixia_config_file_name)
        self.ixl.repository.test.set_attributes(enableForceOwnership=False)
        config_elements = self.ixl.repository.get_elements()


        reservation_ports = {}
        for port in  get_resources_from_reservation(context,
                                                    'Generic Traffic Generator Port',
                                                    'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                    'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                    'IxVM Virtual Traffic Chassis 2G.VirtualTrafficGeneratorPort'):
            reservation_ports[get_family_attribute(context, port.Name, 'Logical Name').strip()] = port

        perfectstorms = [ps.FullAddress for ps in get_resources_from_reservation(context,
                                                                                'PerfectStorm Chassis Shell 2G')]

        for name, element in config_elements.items():
            if name in reservation_ports:
                address = get_address(reservation_ports[name])
                ip_address, module, port = address.split('/')
                if ip_address in perfectstorms:
                    address = '{}/{}/{}'.format(ip_address, module, int(port) + 1)
                self.logger.debug('Logical Port {} will be reserved on Physical location {}'.format(name, address))
                element.reserve(address)
            else:
                self.logger.error('Configuration element "{}" not found in reservation elements {}'.
                                  format(element, reservation_ports.keys()))
                raise Exception('Configuration element "{}" not found in reservation elements {}'.
                                format(element, reservation_ports.keys()))

        self.logger.info("Port Reservation Completed")

    def start_traffic(self, context, blocking):
        self.ixl.start_test(is_blocking(blocking))

    def stop_traffic(self, context):
        self.ixl.stop_test()

    def get_statistics(self, context, view_name, output_type):

        stats_obj = IxlStatView(view_name)
        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == 'json':
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        elif output_type.lower().strip() == 'csv':
            output = io.BytesIO()
            w = csv.DictWriter(output, ['Timestamp'] + stats_obj.captions)
            w.writeheader()
            for time_stamp in statistics:
                w.writerow(OrderedDict({'Timestamp': time_stamp}.items() + statistics[time_stamp].items()))
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise Exception('Output type should be CSV/JSON - got "{}"'.format(output_type))
