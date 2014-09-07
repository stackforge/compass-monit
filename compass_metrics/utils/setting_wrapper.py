# Copyright 2014 Huawei Technologies Co. Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""comapss setting wrapper.

   .. moduleauthor:: Xiaodong Wang ,xiaodongwang@huawei.com>
"""
import datetime
import logging
import os
import os.path


# default setting
CONFIG_DIR = '/etc/compass_monit'
DEFAULT_LOGLEVEL = 'debug'
DEFAULT_LOGDIR = '/tmp'
DEFAULT_LOGINTERVAL = 1
DEFAULT_LOGINTERVAL_UNIT = 'h'
DEFAULT_LOGFORMAT = (
    '%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s')
WEB_LOGFILE = 'compass_monit.log'
ROOT_URL = 'http://localhost:8080'

if (
    'COMPASS_METRICS_IGNORE_SETTING' in os.environ and
    os.environ['COMPASS_METRICS_IGNORE_SETTING']
):
    pass
else:
    if 'COMPASS_METRICS_SETTING' in os.environ:
        SETTING = os.environ['COMPASS_METRICS_SETTING']
    else:
        SETTING = '/etc/compass_monit/setting'

    try:
        logging.info('load setting from %s', SETTING)
        execfile(SETTING, globals(), locals())
    except Exception as error:
        logging.exception(error)
        raise error
