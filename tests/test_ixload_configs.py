
from shellfoundry.releasetools.test_helper import get_namespace_from_cloudshell_config


namespace = get_namespace_from_cloudshell_config()

windows_840 = '192.168.65.68'
windows_850 = '192.168.65.94'
linux_850 = '192.168.65.87'
windows_900 = '192.168.65.54'
linux_900 = '192.168.65.23'
localhost_900 = 'localhost'

originate_840 = 'IxVM 8.40 1/Module1/Port1'
terminate_840 = 'IxVM 8.40 2/Module1/Port1'
originate_850 = 'IxVM 8.50 1/Module1/Port1'
terminate_850 = 'IxVM 8.50 2/Module1/Port1'
originate_900 = 'IxVM 9.00 1/Module1/Port1'
terminate_900 = 'IxVM 9.00 2/Module1/Port1'

server_properties = {windows_840: {'ports': [originate_840, terminate_840], 'ixversion': '8.40.0.277',
                                   'apikey': None},
                     windows_850: {'ports': [originate_850, terminate_850], 'ixversion': '',
                                   'apikey': None},
                     linux_850: {'ports': [originate_850, terminate_850], 'ixversion': '8.50.115.333',
                                 'apikey': None},
                     windows_900: {'ports': [originate_900, terminate_900], 'ixversion': '9.00.0.347',
                                   'apikey': 'YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ=='},
                     linux_900: {'ports': [originate_900, terminate_900], 'ixversion': '9.00.0.347',
                                 'apikey': None},
                     localhost_900: {'ports': [originate_900, terminate_900], 'ixversion': '9.00.0.347',
                                     'apikey': 'YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ=='}}
