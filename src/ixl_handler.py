import csv
import json
import io
import os
from collections import OrderedDict

from cloudshell.traffic.helpers import get_location, get_family_attribute, get_resources_from_reservation
from cloudshell.traffic.tg import IXIA_CHASSIS_MODEL, PERFECT_STORM_CHASSIS_MODEL, TrafficHandler, attach_stats_csv, is_blocking

from trafficgenerator.tgn_utils import TgnError
from ixload.ixl_app import init_ixl
from ixload.ixl_statistics_view import IxlStatView

from ixl_data_model import IxLoadControllerShell2G


class IxlHandler(TrafficHandler):

    def initialize(self, context, logger):

        service = IxLoadControllerShell2G.create_from_context(context)
        super().initialize(service, logger)

        self.ixl = init_ixl(self.logger)

        ixload_gw = self.resource.address if self.resource.address not in ['', 'na'] else 'localhost'
        version = self.service.controller_version
        apikey = self.service.apikey
        auth = {'apikey': apikey, 'crt': None}

        self.logger.info(f'connecting to server {ixload_gw} version {version} using default port')
        self.ixl.connect(version=version, ip=ixload_gw, port=None, auth=auth)
        if self.service.license_server:
            license_server = self.service.license_server
            licensing_mode = self.service.licensing_mode
            self.ixl.controller.set_licensing(license_server, licensing_mode)
        if not self.ixl.is_remote:
            log_file_name = self.logger.handlers[0].baseFilename
            results_dir = (os.path.splitext(log_file_name)[0] + '--Results').replace('\\', '/')
            self.ixl.controller.set_results_dir(results_dir)

    def cleanup(self):
        self.ixl.disconnect()

    def load_config(self, context, ixia_config_file_name):

        self.ixl.load_config(ixia_config_file_name)
        self.ixl.repository.test.set_attributes(enableForceOwnership=False)
        config_elements = self.ixl.repository.get_elements()

        reservation_ports = {}
        for port in get_resources_from_reservation(context,
                                                   'Generic Traffic Generator Port',
                                                   f'{PERFECT_STORM_CHASSIS_MODEL}.GenericTrafficGeneratorPort',
                                                   f'{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort',
                                                   'IxVM Virtual Traffic Chassis 2G.VirtualTrafficGeneratorPort'):
            reservation_ports[get_family_attribute(context, port.Name, 'Logical Name').strip()] = port

        perfectstorms = [ps.FullAddress for ps in get_resources_from_reservation(context, PERFECT_STORM_CHASSIS_MODEL)]

        for name, element in config_elements.items():
            if name in reservation_ports:
                location = get_location(reservation_ports[name])
                ip, module, port = location.split('/')
                if ip in perfectstorms:
                    location = f'{ip}/{module}/{int(port) + 1}'
                self.logger.debug(f'Logical Port {name} will be reserved on Physical location {location}')
                element.reserve(location)
            else:
                elements = reservation_ports.keys()
                raise TgnError(f'Configuration element "{element}" not found in reservation elements {elements}')

        self.logger.info('Port Reservation Completed')

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
            output = io.StringIO()
            w = csv.DictWriter(output, ['Timestamp'] + stats_obj.captions)
            w.writeheader()
            for time_stamp in statistics:
                line = OrderedDict({'Timestamp': time_stamp})
                line.update(statistics[time_stamp])
                w.writerow(line)
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        else:
            raise TgnError(f'Output type should be CSV/JSON - got "{output_type}"')
