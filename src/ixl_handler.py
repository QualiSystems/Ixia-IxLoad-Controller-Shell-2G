"""
IxLoad controller handler.
"""
import csv
import io
import json
import logging
import os
from collections import OrderedDict
from typing import Union

from cloudshell.shell.core.driver_context import InitCommandContext, ResourceCommandContext
from cloudshell.traffic.helpers import get_family_attribute, get_location, get_resources_from_reservation
from cloudshell.traffic.tg import IXIA_CHASSIS_MODEL, PERFECT_STORM_CHASSIS_MODEL, attach_stats_csv, is_blocking
from ixload.ixl_app import IxlApp, init_ixl
from ixload.ixl_statistics_view import IxlStatView
from trafficgenerator.tgn_utils import TgnError

from ixl_data_model import IxLoadControllerShell2G

IXIA_PORT_MODELS = [
    f"{PERFECT_STORM_CHASSIS_MODEL}.GenericTrafficGeneratorPort",
    f"{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort",
]


class IxlHandler:
    """IxLoad controller shell business logic."""

    def __init__(self) -> None:
        """Initialize object variables, actual initialization is performed in initialize method."""
        self.ixl: IxlApp = None
        self.logger: logging.Logger = None

    def initialize(self, context: InitCommandContext, logger: logging.Logger) -> None:
        """Init IxlApp and connect to IxLoad API server."""
        self.logger = logger

        service = IxLoadControllerShell2G.create_from_context(context)

        self.ixl = init_ixl(self.logger)

        ixload_gw = service.address if service.address not in ["", "na"] else "localhost"
        version = service.controller_version
        apikey = service.apikey
        auth = {"apikey": apikey, "crt": None}

        self.logger.info(f"connecting to server {ixload_gw} version {version} using default port")
        self.ixl.connect(version=version, ip=ixload_gw, port=None, auth=auth)
        if service.license_server:
            license_server = service.license_server
            licensing_mode = service.licensing_mode
            self.ixl.controller.set_licensing(license_server, licensing_mode)
        if not self.ixl.is_remote:
            log_file_name = self.logger.handlers[0].baseFilename  # type: ignore
            results_dir = (os.path.splitext(log_file_name)[0] + "--Results").replace("\\", "/")
            self.ixl.controller.set_results_dir(results_dir)

    def cleanup(self) -> None:
        """Disconnect from IxLoad API server."""
        self.ixl.disconnect()

    def load_config(self, context: ResourceCommandContext, ixia_config_file_name: str) -> None:
        """Load IxNetwork configuration file, and map and reserve ports."""
        self.ixl.load_config(ixia_config_file_name)
        self.ixl.repository.test.set_attributes(enableForceOwnership=False)
        config_elements = self.ixl.repository.get_elements().values()

        reservation_ports = {}
        for port in get_resources_from_reservation(context, *IXIA_PORT_MODELS):
            reservation_ports[get_family_attribute(context, port.Name, "Logical Name").strip()] = port

        perfectstorms = [ps.FullAddress for ps in get_resources_from_reservation(context, PERFECT_STORM_CHASSIS_MODEL)]

        for element in config_elements:
            if element.name in reservation_ports:
                location = get_location(reservation_ports[element.name])
                ip, module, port = location.split("/")
                if ip in perfectstorms:
                    location = f"{ip}/{module}/{int(port) + 1}"
                self.logger.debug(f"Logical Port {element.name} will be reserved on Physical location {location}")
                if "offline-debug" not in reservation_ports[element.name].Name.lower():
                    element.reserve(location)
                else:
                    self.logger.debug(f"Offline debug port {location} - no actual reservation")
            else:
                elements = reservation_ports.keys()
                raise TgnError(f'Configuration element "{element}" not found in reservation elements {elements}')

        self.logger.info("Port Reservation Completed")

    def start_traffic(self, blocking: str) -> None:
        """Start IxLoad test."""
        self.ixl.start_test(is_blocking(blocking))

    def stop_traffic(self) -> None:
        """Start IxLoad test."""
        self.ixl.stop_test()

    def get_statistics(self, context: ResourceCommandContext, view_name: str, output_type: str) -> Union[dict, str]:
        """Get statistics for the requested view."""
        stats_obj = IxlStatView(view_name)
        stats_obj.read_stats()
        statistics = stats_obj.get_all_stats()
        if output_type.lower().strip() == "json":
            statistics_str = json.dumps(statistics, indent=4, sort_keys=True, ensure_ascii=False)
            return json.loads(statistics_str)
        if output_type.lower().strip() == "csv":
            output = io.StringIO()
            csv_writer = csv.DictWriter(output, ["Timestamp"] + stats_obj.captions)
            csv_writer.writeheader()
            for time_stamp in statistics:
                line = OrderedDict({"Timestamp": time_stamp})
                line.update(statistics[time_stamp])
                csv_writer.writerow(line)
            attach_stats_csv(context, self.logger, view_name, output.getvalue().strip())
            return output.getvalue().strip()
        raise TgnError(f'Output type should be CSV/JSON - got "{output_type}"')
