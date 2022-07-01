#!/usr/bin/python
# bmcs_bridge_snow.py

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
20201001      Volker Scheithauer    Initial Development
20220701      Volker Scheithauer    Migrate to W3rkstatt project
"""

import w3rkstatt
import os
import json
import logging
import time
import datetime
import core_snow as snow

import json
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
import jsonpath_rw_ext as jp

# Get configuration from bmcs_core.json
jCfgFile = os.path.join(w3rkstatt.getCurrentFolder(), "bmcs_core.json")
jCfgData = w3rkstatt.getFileJson(jCfgFile)

# SNOW template IDs
snow_tmpl_req = w3rkstatt.getJsonValue(
    path="$.SNOW.request.template_id", data=jCfgData)


# https://dev81866.service-now.com/api/now/table/{tableName}
# https://dev81866.service-now.com/api/now/v1/table/{tableName}


# Assign module defaults
_modVer = "1.0"
_timeFormat = '%Y-%m-%dT%H:%M:%S'
_localDebug = True
_localDbgAdv = True
logger = logging.getLogger(__name__)
logFile = w3rkstatt.logFile
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)


# Versioned URL: /api/now/{api_version}/table/{tableName}/{sys_id}
# Default URL: /api/now/table/{tableName}/{sys_id}

# Versioned URL: /api/sn_sc/{api_version}/servicecatalog/items/{sys_id}/order_now
# Default URL: /api/sn_sc/servicecatalog/items/{sys_id}/order_now

# /api/sn_sc/servicecatalog/items/{sys_id}/order_now


def createSnowReq(data):
    jCtmData = json.loads(data)
    ctmRequestID = w3rkstatt.getJsonValue(path="$.ctmRequestID", data=jCtmData)
    ctmWorkspace = w3rkstatt.getJsonValue(path="$.name", data=jCtmData)
    newState = w3rkstatt.getJsonValue(path="$.newState", data=jCtmData)
    oldState = w3rkstatt.getJsonValue(path="$.oldState", data=jCtmData)
    creationTime = w3rkstatt.getJsonValue(path="$.creationTime", data=jCtmData)
    endUser = w3rkstatt.getJsonValue(path="$.endUser", data=jCtmData)

    jSnowReq = {
        "sysparm_quantity": "1",
        "variables": {
            "description": "Control-M Workoad Change Management Request",
            "short_description": "CTM WCM",
            "ctm_description": "Control-M Workoad Change Management Request"
        }
    }

    if _localDebug:
        logger.info('CTM: Create CRQ: "%s": %s ', "Request ID", ctmRequestID)
        logger.info('CTM: Create CRQ: "%s": %s ', "Workspace", ctmWorkspace)
        logger.info('CTM: Create CRQ: "%s": %s ', "New State", newState)
        logger.info('CTM: Create CRQ: "%s": %s ', "Old State", oldState)
        logger.info('CTM: Create CRQ: "%s": %s ',
                    "Creation Time", creationTime)
        logger.info('CTM: Create CRQ: "%s": %s ', "End User", endUser)

    if _localDebug:
        logger.info('SNOW: REQ JSON: %s ', jSnowReq)

    ctmChangeID = snow.createRequest(sys_id=snow_tmpl_req, data=jSnowReq)

    if _localDebug:
        logger.info('CTM: Create CRQ: "%s": %s ', "Change ID", ctmChangeID)

    return ctmChangeID


def getSnowReqStatus(data):
    sc_number = data
    sNameSpace = "now"
    sApplication = "table/sc_request"
    sAction = "?sysparm_query=numberSTARTSWITH" + sc_number + "&sysparm_limit=1"

    value = snow.snowAppGet(application=sApplication,
                            namespace=sNameSpace, action=sAction)
    jData = json.loads(value)
    sReqApproval = w3rkstatt.getJsonValue(
        path="$.result[0].approval", data=jData)

    return sReqApproval


def translateSnowReqStatus(data):
    # httpResponseCode
    # - 200 = Approved
    # - 400 = Not Approved
    status = data
    if(status == "Draft"):
        httpResponseCode = 400
    elif(status == "approved"):
        httpResponseCode = 200
    else:
        httpResponseCode = 400

    return httpResponseCode


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('SNOW: ITSM Management Start')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: "%s" ', w3rkstatt.platform.system())
    logger.info('Log Level: "%s"', loglevel)
    logger.info('Host Name: "%s"', hostName)
    logger.info('Host IP: "%s"', hostIP)
    logger.info('Epoch: %s', epoch)

    logger.info('SNOW: ITSM Management End')
    logging.shutdown()
    print(f"Version: {_modVer}")
