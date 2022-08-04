"""
Test IxLoadController2GDriver.
"""
# pylint: disable=redefined-outer-name
from pathlib import Path
from typing import Iterable

import pytest
from _pytest.fixtures import SubRequest
from cloudshell.api.cloudshell_api import AttributeNameValue, CloudShellAPISession, InputNameValue
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.traffic.helpers import get_reservation_id, get_resources_from_reservation, set_family_attribute
from cloudshell.traffic.tg import IXIA_CHASSIS_MODEL, IXLOAD_CONTROLLER_MODEL
from shellfoundry_traffic.test_helpers import TestHelpers, create_session_from_config  # noqa: F401

from src.ixl_driver import IxLoadController2GDriver

ALIAS = "IxLoad Controller"

WINDOWS_910 = "localhost"
LINUX_910 = "192.168.65.25"

ORIGINATE_910 = "ixia/Module1/Port1"
TERMINATE_910 = "ixia/Module1/Port2"

server_properties = {
    "windows_910": {
        "server": WINDOWS_910,
        "version": "9.10.115.94",
        "ports": [ORIGINATE_910, TERMINATE_910],
        "apikey": "YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ==",
    },
    "linux_910": {
        "server": LINUX_910,
        "version": "9.10.115.94",
        "ports": [ORIGINATE_910, TERMINATE_910],
        "apikey": "YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ==",
    },
}


@pytest.fixture(scope="session")
def session() -> CloudShellAPISession:
    """Yield session."""
    return create_session_from_config()


@pytest.fixture()
def test_helpers(session: CloudShellAPISession) -> Iterable[TestHelpers]:
    """Yield initialized TestHelpers object."""
    test_helpers = TestHelpers(session)
    test_helpers.create_reservation()
    yield test_helpers
    test_helpers.end_reservation()


@pytest.fixture(params=["windows_910"])
def server(request: SubRequest) -> list:
    """Yield server information."""
    controller_address = server_properties[request.param]["server"]
    version = server_properties[request.param]["version"]
    apikey = server_properties[request.param]["apikey"]
    ports = server_properties[request.param]["ports"]
    return [controller_address, version, apikey, ports]


@pytest.fixture()
def driver(test_helpers: TestHelpers, server: list) -> Iterable[IxLoadController2GDriver]:
    """Yield initialized IxLoadController2GDriver."""
    controller_address, controller_version, apikey, _ = server
    attributes = {
        f"{IXLOAD_CONTROLLER_MODEL}.Address": controller_address,
        f"{IXLOAD_CONTROLLER_MODEL}.Controller Version": controller_version,
        f"{IXLOAD_CONTROLLER_MODEL}.ApiKey": apikey,
        f"{IXLOAD_CONTROLLER_MODEL}.License Server": "192.168.42.61",
        f"{IXLOAD_CONTROLLER_MODEL}.Licensing Mode": "Perpetual",
    }
    init_context = test_helpers.service_init_command_context(IXLOAD_CONTROLLER_MODEL, attributes)
    driver = IxLoadController2GDriver()
    driver.initialize(init_context)
    yield driver
    driver.cleanup()


@pytest.fixture()
def context(session: CloudShellAPISession, test_helpers: TestHelpers, server: list) -> ResourceCommandContext:
    """Yield ResourceCommandContext for shell command testing."""
    controller_address, controller_version, apikey, ports = server
    attributes = [
        AttributeNameValue(f"{IXLOAD_CONTROLLER_MODEL}.Address", controller_address),
        AttributeNameValue(f"{IXLOAD_CONTROLLER_MODEL}.Controller Version", controller_version),
        AttributeNameValue(f"{IXLOAD_CONTROLLER_MODEL}.ApiKey", apikey),
        AttributeNameValue(f"{IXLOAD_CONTROLLER_MODEL}.License Server", "192.168.42.61"),
        AttributeNameValue(f"{IXLOAD_CONTROLLER_MODEL}.Licensing Mode", "Perpetual"),
    ]
    session.AddServiceToReservation(test_helpers.reservation_id, IXLOAD_CONTROLLER_MODEL, ALIAS, attributes)
    context = test_helpers.resource_command_context(service_name=ALIAS)
    session.AddResourcesToReservation(test_helpers.reservation_id, ports)
    reservation_ports = get_resources_from_reservation(context, f"{IXIA_CHASSIS_MODEL}.GenericTrafficGeneratorPort")
    set_family_attribute(context, reservation_ports[0].Name, "Logical Name", "Traffic1@Network1")
    set_family_attribute(context, reservation_ports[1].Name, "Logical Name", "Traffic2@Network2")
    return context


class TestIxLoadControllerDriver:
    """Test direct driver calls."""

    def test_load_config(self, driver: IxLoadController2GDriver, context: ResourceCommandContext) -> None:
        """Test load configuration command."""
        self._load_config(driver, context, "test_config")

    def test_run_traffic(self, driver: IxLoadController2GDriver, context: ResourceCommandContext) -> None:
        """Test complete cycle - from load_config to get_statistics."""
        self._load_config(driver, context, "test_config")
        driver.start_traffic(context, "True")
        driver.get_statistics(context, "Test_Client", "json")
        driver.get_statistics(context, "Test_Client", "csv")

    def _load_config(self, driver: IxLoadController2GDriver, context: ResourceCommandContext, config_name: str) -> None:
        """Get full path to the requested configuration file based on fixture and run load_config."""
        config_file = Path(__file__).parent.joinpath(f"{config_name}.rxf")
        driver.load_config(context, config_file.as_posix())


class TestIxLoadControllerShell:
    """Test indirect Shell calls."""

    def test_load_config(self, session: CloudShellAPISession, context: ResourceCommandContext) -> None:
        """Test load configuration command."""
        self._load_config(session, context, ALIAS, "test_config")

    def test_run_traffic(self, session: CloudShellAPISession, context: ResourceCommandContext) -> None:
        """Test complete cycle - from load_config to get_statistics."""
        self._load_config(session, context, ALIAS, "test_config")
        cmd_inputs = [InputNameValue("blocking", "True")]
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "start_traffic", cmd_inputs)
        cmd_inputs = [InputNameValue("view_name", "Test_Client"), InputNameValue("output_type", "JSON")]
        session.ExecuteCommand(get_reservation_id(context), ALIAS, "Service", "get_statistics", cmd_inputs)

    @staticmethod
    def _load_config(session: CloudShellAPISession, context: ResourceCommandContext, alias: str, config_name: str) -> None:
        """Get full path to the requested configuration file based on fixture and run load_config."""
        config_file = Path(__file__).parent.joinpath(f"{config_name}.rxf")
        cmd_inputs = [InputNameValue("config_file_location", config_file.as_posix())]
        session.ExecuteCommand(get_reservation_id(context), alias, "Service", "load_config", cmd_inputs)
