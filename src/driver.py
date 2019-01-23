from cloudshell.traffic.driver import TrafficControllerDriver

from ixl_handler import IxlHandler


class IxiaIxloadControllerShell2GDriver(TrafficControllerDriver):
    SHELL_TYPE = "CS_TrafficGeneratorController"
    SHELL_NAME = "Ixia IxLoad Controller Shell 2G"

    def __init__(self):
        super(IxiaIxloadControllerShell2GDriver, self).__init__()
        self.handler = IxlHandler(shell_name=self.SHELL_NAME)

    def initialize(self, context):
        """

        :param context: ResourceCommandContext,ReservationContextDetailsobject with all Resource Attributes inside
        :type context:  context: cloudshell.shell.core.driver_context.ResourceRemoteCommandContext
        """
        super(IxiaIxloadControllerShell2GDriver, self).initialize(context)
        return 'Finished initializing'

    def load_config(self, context, config_file_location):
        """Reserve ports and load configuration

        :param context:
        :param str config_file_location: configuration file location
        :return:
        """
        super(IxiaIxloadControllerShell2GDriver, self).load_config(context)
        self.handler.load_config(context, config_file_location)

        return config_file_location + ' loaded, ports reserved'

    def start_traffic(self, context, blocking):
        """Start traffic on all ports

        :param context: the context the command runs on
        :param bool blocking: True - return after traffic finish to run, False - return immediately
        """
        self.handler.start_test(blocking)

    def stop_traffic(self, context):
        """Stop traffic on all ports

        :param context: the context the command runs on
        """
        self.handler.stop_test()

    def get_statistics(self, context, view_name, output_type):
        """Get real time statistics as sandbox attachment

        :param context:
        :param str view_name: requested view name
        :param str output_type: CSV or JSON
        :return:
        """
        return self.handler.get_statistics(context, view_name, output_type)

    def cleanup(self, context=None):
        """

        :param context:
        :return:
        """
        return super(IxiaIxloadControllerShell2GDriver, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        """

        :param context:
        :param cancellation_context:
        :return:
        """
        return super(IxiaIxloadControllerShell2GDriver, self).keep_alive(context, cancellation_context)


if __name__ == "__main__":
    import mock
    from cloudshell.shell.core.driver_context import ResourceCommandContext, ResourceContextDetails, ReservationContextDetails

    address = '192.168.85.10'
    port = 8080
    ctrl_version = "8.40.0.277"

    auth_key = 'h8WRxvHoWkmH8rLQz+Z/pg=='
    api_port = 8029

    context = ResourceCommandContext(*(None, ) * 4)
    context.resource = ResourceContextDetails(*(None, ) * 13)
    context.resource.name = "IxLoad"
    context.resource.fullname = "IxLoad"
    context.reservation = ReservationContextDetails(*(None, ) * 7)
    context.resource.attributes = {}

    for attr, value in [("Controller Address", address),
                        ("Controller TCP Port", port),
                        ("Controller Version", ctrl_version)]:

        context.resource.attributes["{}.{}".format(IxiaIxloadControllerShell2GDriver.SHELL_NAME, attr)] = value

    context.resource.address = address

    context.connectivity = mock.MagicMock()
    context.connectivity.server_address = "192.168.85.14"

    dr = IxiaIxloadControllerShell2GDriver()
    dr.initialize(context)

    out = dr.load_config(context, "C:\\config.rxf")
    # out = dr.keep_alive(context, mock.MagicMock())
    # out = dr.start_traffic(context)
    # out = dr.stop_traffic(context)
    # out = dr.get_results(context)
    # out = dr.cleanup_reservation(context)
