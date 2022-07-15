#!/usr/bin/env python3
# Filename: core_bhom.py

"""
(c) 2022 Volker Scheithauer
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

https://opensource.org/licenses/GPL-3.0
# SPDX-License-Identifier: GPL-3.0-or-later
For information on SDPX, https://spdx.org/licenses/GPL-3.0-or-later.html

w3rkstatt Python BMC Helix Operation Manager [BHOM] Integration


Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20220715      Volker Scheithauer    Initial Development


See also: https://realpython.com/python-send-email/
"""

import os
import json
import logging
import requests
import urllib3
import time
import datetime
import sys
import getopt

# handle dev environment vs. production
try:
    import w3rkstatt as w3rkstatt
except:
    # fix import issues for modules
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstat

# Define global variables from w3rkstatt.ini file
# Get configuration from bmcs_core.json
jCfgData = w3rkstatt.getProjectConfig()
cfgFolder = w3rkstatt.getJsonValue(
    path="$.DEFAULT.config_folder", data=jCfgData)
logFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder", data=jCfgData)
tmpFolder = w3rkstatt.getJsonValue(
    path="$.DEFAULT.template_folder", data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(
    path="$.DEFAULT.crypto_file", data=jCfgData)

bhom_host = w3rkstatt.getJsonValue(path="$.BHOM.host", data=jCfgData)
bhom_api_ver = w3rkstatt.getJsonValue(path="$.BHOM.api_version", data=jCfgData)
bhom_api_ns = w3rkstatt.getJsonValue(
    path="$.BHOM.api_namespace", data=jCfgData)
bhom_api_key = w3rkstatt.getJsonValue(path="$.BHOM.api_Key", data=jCfgData)
bhom_ssl_ver = w3rkstatt.getJsonValue(path="$.BHOM.ssl_ignore", data=jCfgData)


# Compute Url's
bhom_url = 'https://' + bhom_host + '/' + \
    bhom_api_ns + '/api/' + bhom_api_ver + '/'

# ITSM configuration
itsm_operational_category1 = w3rkstatt.getJsonValue(
    path="$.ITSM.opcat_1", data=jCfgData)
itsm_operational_category2 = w3rkstatt.getJsonValue(
    path="$.ITSM.opcat_2", data=jCfgData)
itsm_operational_category3 = w3rkstatt.getJsonValue(
    path="$.ITSM.opcat_3", data=jCfgData)

# Ignore HTTPS Insecure Request Warnings
if bhom_ssl_ver:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Assign module defaults
_modVer = "20.22.07.00"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = True
logger = w3rkstatt.logging.getLogger(__name__)
logFile = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file", data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)
domain = w3rkstatt.getHostDomain(w3rkstatt.getHostFqdn(hostName))


def createEvent(token, event_data):
    bhom_event_id = ""
    authToken = token
    url = bhom_url + 'events'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'apiKey ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = event_data

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(
            url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
        if w3rkstatt.jsonValidator(rst):
            bhom_data = rst
            bhom_event_id = getEventID(bhom_data)
            if _localDebug:
                logger.info('bhom: event created: %s', bhom_event_id)
    else:
        logger.error('bhom: failed to create the event: %s', response)
    return bhom_event_id


def updateEvent(token, event_data):
    status = False
    authToken = token
    url = bhom_url + 'Event/update?routingId=' + \
        bhom_cell + '&routingType=' + bhom_routing
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'apiKey ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = event_data

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.put(
            url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
        if w3rkstatt.jsonValidator(rst):
            status = True
    else:
        logger.error('bhom: failed to create the event: %s', response)
    return status


def searchEvent(token, bhomEventIdentifier, bhomEventValue):
    bhom_event_id = ""
    # Authenticate first.
    # https://docs.bmc.com/docs/TSInfrastructure/113/listing-events-774797826.html
    authToken = token
    url = bhom_url + 'Event/search?routingId=' + \
        bhom_cell + '&routingType=' + bhom_routing
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'apiKey ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = {
        "sortCriteria": [
              {
                  "sortOrder": 1,
                  "attributeName": "date_reception"
              }
        ],
        "criteria": {
            "value": bhomEventValue,
            "identifier": bhomEventIdentifier,
            "operator": "EQUALS"
        }
    }

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(
            url, json=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
        if w3rkstatt.jsonValidator(rst):
            bhom_data = rst
            bhom_event_id = bhomGetEventID(bhom_data)
            if _localDebug:
                logger.debug('bhom: event search: %s', bhom_event_id)
    else:
        logger.error('bhom: failed to search the event: %s', response)
    return bhom_event_id


def getEventID(data):
    # {'responseTimeStamp': '2020-05-23T20:11:30', 'statusCode': '200', 'statusMsg': 'OK', 'responseList': [{'mc_ueid': 'mc.pncell_bmcs-ts-om.1ec98372.0', 'statusCode': '200', 'statusMsg': 'OK'}]}
    key = "mc_ueid"
    mc_ueid = ""
    values = {}

    if key in data:
        vJson = json.loads(data)
        values = w3rkstatt.jsonExtractValues(vJson, key)
        mc_ueid = values[0]
        if _localDebug:
            logger.debug('bhom: Extract Event ID: %s', values)
    return mc_ueid

# Main function


def bhomEvent(token, data):
    authToken = token
    bhom_event_id = None
    # Define the TSOM event slots and create a JSON object.
    logger.info('bhom: define event')
    # json_data = bhomDefineEvent()

    # Make the call to the API to create the event,
    logger.info('bhom: invoke event creation')
    bhom_event_id = createEvent(token=authToken, data=data)
    return bhom_event_id


def searchCI(token, bhomCiIdentifier, bhomCiValue):
    # Authenticate first.
    # https://docs.bmc.com/docs/TSInfrastructure/113/listing-events-774797826.html

    authToken = token
    url = bhom_url + 'CI/search'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'apiKey ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = {
        "sortCriteria": [
              {
                  "sortOrder": 1,
                  "attributeName": "Name"
              }
        ],
        "criteria": {
            "value": bhomCiValue,
            "identifier": bhomCiIdentifier,
            "operator": "EQUALS"
        }
    }
    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(
            url, json=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        bhom_data = rst
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('bhom: CI search: %s', bhom_data)
    else:
        logger.error('bhom: failed to search for CI: %s', response)
    return bhom_data


def searchCIAdvanced(token, bhomCiSearchFilter):
    bhom_data = {}
    # Authenticate first.
    # https://docs.bmc.com/docs/TSInfrastructure/113/listing-events-774797826.html

    authToken = token
    url = bhom_url + 'CI/search'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'apiKey ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = str(bhomCiSearchFilter)
    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(
            url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        bhom_data = rst
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('bhom: CI search: %s', bhom_data)
    else:
        logger.error('bhom: failed to search for CI: %s', response)
    return bhom_data


def createCI(token, data, ciType="CI"):
    bhom_data = None
    # Authenticate first.
    authToken = token
    # http://bppmwsserver:80/bppmws/api/CI/create?routingIdKeyParam=CI_ID&routingId=ci5&routingIdType=CACHE_KEY&ciType=CI
    # routingIdType=SERVER_NAME
    url = bhom_url + 'CI/create?routingIdKeyParam=NAME&routingIdType=SERVER_NAME&routingId=' + \
        bhom_cell + '&ciType=' + ciType
    # url = bhom_url + 'CI/create?ciType=CI'

    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'apiKey ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = data

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(
            url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        bhom_data = rst
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('bhom: CI created: %s', bhom_data)
    else:
        logger.error('bhom: failed to create the CI: %s', response)
    return bhom_data


def decryptApiKey():
    if bhom_api_key != None:
        api_key = w3rkstatt.decryptPwd(
            data=bhom_api_key, sKeyFileName=cryptoFile)

    return api_key


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('BHOM: start event management')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: %s ', w3rkstatt.platform.system())
    logger.info('Log Level: %s', loglevel)
    logger.info('Host Name: %s', hostName)
    logger.info('Host IP: %s', hostIP)
    logger.info('BMC Helix Operation Manager: %s', bhom_host)
    logger.info('BHOM API Version: %s', bhom_api_ver)
    logger.info('BHOM Url: %s', bhom_url)
    logger.info('BHOM API Key: %s', bhom_api_key)
    logger.info('Epoch: %s', epoch)

    logging.shutdown()
    print(f"Version: {_modVer}")
