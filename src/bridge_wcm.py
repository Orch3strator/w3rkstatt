#!/usr/bin/python
# bridge_wcm.py

"""
(c) 2020 Volker Scheithauer
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice (including the next paragraph) shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

https://opensource.org/licenses/MIT
# SPDX-License-Identifier: MIT
For information on SDPX, https://spdx.org/licenses/MIT.html

BMC Software Python Core Tools 
Provide core functions for BMC Software related python scripts

Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20200501      Volker Scheithauer    Initial Development
20200601      Volker Scheithauer    Update  
20220701      Volker Scheithauer    Migrate to W3rkstatt project
"""

import w3rkstatt
import bmcs_core_tso as tso
import os
import json
import logging
import time
import datetime
import sys
import getopt

# Get configuration from bmcs_core.json
jCfgFile = os.path.join(w3rkstatt.getCurrentFolder(), "bmcs_core.json")
jCfgData = w3rkstatt.getFileJson(jCfgFile)
# tso_proc    = w3rkstatt.jsonExtractValues(jCfgData,"ctm_tso_process")[0]


# Assign module defaults
_modVer = "1.0"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = False
logger = logging.getLogger(__name__)
logFile = w3rkstatt.logFile
loglevel = w3rkstatt.loglevel
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)


def processIncomingWCM(process, data=""):
    authToken = tso.tsoAuthenticate()
    body = {
        "inputParameters": [
            {
                "name": "data",
                        "value": "WCM Integration",
            }
        ]
    }

    tso_data = tso.executeTsoProcess(
        token=authToken, process=process, data=body)
    json_data = w3rkstatt.jsonTranslateValues(tso_data)
    logger.debug('TSO: Process Name: "%s"', process)
    logger.debug('TSO: Process Response: %s', json_data)
    return json_data


if __name__ == "__main__":

    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('CTM: WCM Integration Start')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: %s ', w3rkstatt.platform.system())
    logger.info('Log Level: %s', loglevel)
    logger.info('Host Name: %s', hostName)
    logger.info('Host IP: %s', hostIP)
    logger.info('Epoch: %s', epoch)
    logger.info('TSO: WCM Workflow "%s"', tso_proc)

    processIncomingWCM(process=tso_proc)

    logger.info('CTM: WCM Integration End')
    logging.shutdown()
    print(f"Version: {_modVer}")
