#!/usr/bin/python
# core_snow.py

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
import sys
import getopt
import requests
import urllib3
import subprocess
import urllib3
from urllib3 import disable_warnings
from urllib3.exceptions import NewConnectionError, MaxRetryError, InsecureRequestWarning

import json
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
import jsonpath_rw_ext as jp

# Get configuration from bmcs_core.json
jCfgFile = os.path.join(w3rkstatt.getCurrentFolder(), "bmcs_core.json")
jCfgData = w3rkstatt.getFileJson(jCfgFile)
snow_host = w3rkstatt.getJsonValue(path="$.SNOW.host", data=jCfgData)
snow_port = w3rkstatt.getJsonValue(path="$.SNOW.port", data=jCfgData)
snow_ssl = w3rkstatt.getJsonValue(path="$.SNOW.ssl", data=jCfgData)
snow_ssl_ver = w3rkstatt.getJsonValue(
    path="$.SNOW.ssl_verification", data=jCfgData)
snow_user = w3rkstatt.getJsonValue(path="$.SNOW.user", data=jCfgData)
snow_pwd_sec = w3rkstatt.getJsonValue(path="$.SNOW.pwd_secure", data=jCfgData)
snow_api_ns = w3rkstatt.getJsonValue(
    path="$.SNOW.api_namespace", data=jCfgData)
snow_api_ver = w3rkstatt.getJsonValue(path="$.SNOW.api_version", data=jCfgData)

# SNOW template IDs
snow_tmpl_req = w3rkstatt.getJsonValue(
    path="$.SNOW.request.template_id", data=jCfgData)

# SNOW REST API
# https://<localhost>:<port>/api/{namespace}/{version}
if snow_ssl:
    snow_protocol = "https://"
else:
    snow_protocol = "http://"
# SNOW Base Url
snow_base_url = snow_protocol + snow_host + ":" + snow_port + "/api"

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

# Ignore HTTPS Insecure Request Warnings
if snow_ssl_ver == False:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Versioned URL: /api/now/{api_version}/table/{tableName}/{sys_id}
# Default URL: /api/now/table/{tableName}/{sys_id}

# Versioned URL: /api/sn_sc/{api_version}/servicecatalog/items/{sys_id}/order_now
# Default URL: /api/sn_sc/servicecatalog/items/{sys_id}/order_now


def snowAppGet(application, action="", namespace="now"):
    '''
    Provide the ability to interact with various ServiceNow functionality within your application. 

    :param str application: ServiceNow Application
    :param str item: Item or Object of ServiceNow Application
    :param str action: Action to be executed for Item or Object of ServiceNow Application
    :param str headers: Request Headers
    :param str body: Request Body

    :return: http repsonse 
    :rtype: str json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    snow_pwd = w3rkstatt.decryptPwd(data=snow_pwd_sec)
    if snow_api_ver == "latest":
        snow_url = snow_protocol + snow_host + ":" + \
            snow_port + "/api/" + namespace + "/" + application
    else:
        snow_url = snow_protocol + snow_host + ":" + snow_port + \
            "/api/" + namespace + "/" + snow_api_ver + "/" + application

    url = snow_url + action

    headers = {
        'cache-control': "no-cache",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)

    # Execute the API call.
    try:
        response = requests.get(url, auth=(
            snow_user, snow_pwd), headers=headers, verify=False)

    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 500:
        rst = response.text
        logger.error('HTTP Response Status: %s', rsc)
        logger.error('HTTP Response Text: %s', rst)
        data = "Internal server error. An unexpected error occurred while processing the request"
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    elif rsc == 400:
        logger.error('HTTP Response Status: %s', rsc)
        data = "Indicates that the quantity value is invalid and the request is not placed."
        if _localDebug:
            logger.debug('SNOW: Text: %s', data)
        return data
    elif rsc == 401:
        rst = response.text
        logger.error('HTTP Response Status: %s', rsc)
        logger.error('HTTP Response Text: %s', rst)
        data = "Unauthorized. The user credentials are incorrect."
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
        data = "Error"
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    elif rsc == 200:
        # rshd = response.headers
        rst = response.text
        data = rst
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()


def snowAppPost(application, item, body="", action="", namespace="now"):
    '''
    Provide the ability to interact with various ServiceNow functionality within your application. 

    :param str application: ServiceNow Application
    :param str item: Item or Object of ServiceNow Application
    :param str action: Action to be executed for Item or Object of ServiceNow Application
    :param str headers: Request Headers
    :param str body: Request Body

    :return: http repsonse 
    :rtype: str json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    snow_pwd = w3rkstatt.decryptPwd(data=snow_pwd_sec)
    if snow_api_ver == "latest":
        snow_url = snow_protocol + snow_host + ":" + \
            snow_port + "/api/" + namespace + "/" + application
    else:
        snow_url = snow_protocol + snow_host + ":" + snow_port + \
            "/api/" + namespace + "/" + snow_api_ver + "/" + application

    if len(action) > 1:
        url = snow_url + "/" + item + "/" + action
    else:
        url = snow_url + "/" + item

    headers = {
        'cache-control': "no-cache",
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    # '/?fields=values(Infrastructure Change Id)'
    # Create a dictionary for the request body
    request_body = body

    # Create a dictionary for the loging of the request body
    log_payload = json.dumps(request_body)

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', log_payload)

    # Execute the API call.
    try:
        if len(request_body) < 0:
            response = requests.get(url, auth=(
                snow_user, snow_pwd), headers=headers, verify=False)
        else:
            response = requests.post(url, auth=(
                snow_user, snow_pwd), data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 500:
        rst = response.text
        logger.error('HTTP Response Status: %s', rsc)
        logger.error('HTTP Response Text: %s', rst)
        data = "Internal server error. An unexpected error occurred while processing the request"
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    elif rsc == 400:
        logger.error('HTTP Response Status: %s', rsc)
        data = "Indicates that the quantity value is invalid and the request is not placed."
        if _localDebug:
            logger.debug('SNOW: Text: %s', data)
        return data
    elif rsc == 401:
        rst = response.text
        logger.error('HTTP Response Status: %s', rsc)
        logger.error('HTTP Response Text: %s', rst)
        data = "Unauthorized. The user credentials are incorrect."
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
        data = "Error"
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    elif rsc == 200:
        # rshd = response.headers
        rst = response.text
        data = rst
        if _localDebug:
            logger.debug('SNOW: Text: %s', rst)
        return data
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

# /api/now/table/{tableName}
# /api/sn_sc/servicecatalog/items/{sys_id}/order_now


def createRequest(sys_id, data):
    sNameSpace = "sn_sc"
    sApplication = "servicecatalog"
    sItem = "/items/" + sys_id
    sAction = "order_now"
    sBody = data

    value = snowAppPost(application=sApplication, item=sItem,
                        namespace=sNameSpace, action=sAction, body=sBody)
    jData = json.loads(value)
    sRequestNum = w3rkstatt.getJsonValue(
        path="$.result.request_number", data=jData)
    sRequestID = w3rkstatt.getJsonValue(path="$.result.request_id", data=jData)

    if _localDebug:
        logger.debug('SNOW Request Number: "%s"', sRequestNum)
        logger.debug('SNOW Request ID: "%s"', sRequestID)

    return sRequestNum


def getSnowOrderScStatus(sc_number):
    sNameSpace = "now"
    sApplication = "table/sc_request"
    sAction = "?sysparm_query=numberSTARTSWITH" + sc_number + "&sysparm_limit=1"

    value = snowAppGet(application=sApplication,
                       namespace=sNameSpace, action=sAction)
    jData = json.loads(value)
    sReqApproval = w3rkstatt.getJsonValue(
        path="$.result[0].approval", data=jData)

    return sReqApproval


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('SNOW: ITSM Management Start')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: "%s" ', w3rkstatt.platform.system())
    logger.info('Log Level: "%s"', loglevel)
    logger.info('Host Name: "%s"', hostName)
    logger.info('Host IP: "%s"', hostIP)
    logger.info('SNOW Base Url: "%s"', snow_base_url)
    logger.info('User: "%s"', snow_user)
    logger.info('Secure Pwd: "%s"', snow_pwd_sec)
    logger.info('Epoch: %s', epoch)

    logger.info('SNOW: ITSM Management End')
    logging.shutdown()
    print(f"Version: {_modVer}")
