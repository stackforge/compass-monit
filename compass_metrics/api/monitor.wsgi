from os import sys, path

sys.path.append(path.dirname(path.abspath(__file__)))

import anapi_v2
application = anapi_v2.app
