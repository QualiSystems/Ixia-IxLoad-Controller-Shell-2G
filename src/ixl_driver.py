

from cloudshell.traffic.tg import TgControllerDriver, write_to_reservation_out

from .ixl_handler import IxlHandler


class IxLoadControllerShell2GDriver(TgControllerDriver):

    def __init__(self):
        self.handler = IxlHandler()

    def load_config(self, context, config_file_location):
        """ Load configuration and reserve ports. """
        return super(self.__class__, self).load_config(context, config_file_location)

    def start_traffic(self, context, blocking):
        """ Start IxLoad test.

        :param blocking: True - return after test is finished, False - return immediately.
        """
        return super(self.__class__, self).start_traffic(context, blocking)

    def stop_traffic(self, context):
        """ Stop IxLoad test. """
        return super(self.__class__, self).stop_traffic(context)

    def get_statistics(self, context, view_name, output_type):
        """ Get view statistics.

        :param view_name: port, traffic item, flow group etc.
        :param output_type: CSV or JSON.
        """
        return super(self.__class__, self).get_statistics(context, view_name, output_type)

    #
    # Parent commands are not visible so we re define them in child.
    #

    def initialize(self, context):
        super(self.__class__, self).initialize(context)

    def cleanup(self):
        super(self.__class__, self).cleanup()

    def keep_alive(self, context, cancellation_context):
        super(self.__class__, self).keep_alive(context, cancellation_context)
