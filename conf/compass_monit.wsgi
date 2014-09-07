#!/usr/bin/env python
import site
import sys
import os
import os.path


activate_this='$PythonHome/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
site.addsitedir('$PythonHome/lib/python2.6/site-packages')
sys.path.append('$PythonHome')
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.egg'

from compass_metrics.utils import flags
from compass_metrics.utils import logsetting
from compass_metrics.utils import setting_wrapper as setting

flags.init()
flags.OPTIONS.logfile = setting.WEB_LOGFILE
logsetting.init()

from compass_metrics.api import api as compass_metrics_api

compass_metrics_api.init()
application = compass_metrics_api.app
