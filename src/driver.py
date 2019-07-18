from cloudshell.traffic.driver import TrafficControllerDriver

from ixl_handler import IxlHandler


class IxLoadControllerShell2GDriver(TrafficControllerDriver):

    def __init__(self):
        super(IxLoadControllerShell2GDriver, self).__init__()
        self.handler = IxlHandler()

    def load_config(self, context, config_file_location):
        """ Load IxLoad repository and reserve ports.

        :param config_file_location: Full path to IxLoad repository file name
        """
        super(self.__class__, self).load_config(context)
        self.handler.load_config(context, config_file_location)

    def start_traffic(self, context, blocking):
        """ Start test.

        :param bool blocking: True - return after test finish to run, False - return immediately
        """
        self.handler.start_test(blocking)

    def stop_traffic(self, context):
        """ Stop test. """
        self.handler.stop_test()

    def get_statistics(self, context, view_name, output_type):
        """ Get view statistics.

        :param view_name: name of one of the csv result files.
        :param output_type: CSV or JSON.
        """
        return self.handler.get_statistics(context, view_name, output_type)

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def cleanup_reservation(self, context):
        pass

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)
