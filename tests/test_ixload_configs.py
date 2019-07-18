
from shellfoundry.releasetools.test_helper import get_namespace_from_cloudshell_config


namespace = get_namespace_from_cloudshell_config()

windows_840 = '192.168.65.68'
localhost_850 = 'localhost'
windows_850 = '192.168.65.94'
linux_850 = '192.168.65.87'

originate_840 = '207/Module1/Port1'
terminate_840 = '162/Module1/Port1'
originate_850 = '6553/Module1/Port1'
terminate_850 = '65120/Module1/Port1'

server_properties = {windows_840: {'ports': [originate_840, terminate_840], 'ixversion': '8.40.0.277',
                                   'apikey': None},
                     localhost_850: {'ports': [originate_850, terminate_850], 'ixversion': '8.50.0.465',
                                     'apikey': 'YWRtaW58elR0MTNZR0NPRTYyREpubGFWOXJzT3R6Ry13PQ=='},
                     windows_850: {'ports': [originate_850, terminate_850], 'ixversion': '',
                                   'apikey': None},
                     linux_850: {'ports': [originate_850, terminate_850], 'ixversion': '8.50.115.333',
                                 'apikey': None}}
