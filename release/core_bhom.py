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
20230522      Volker Scheithauer    Update API key issues

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
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstat

# Define global variables from w3rkstatt.ini file
# Get configuration from bmcs_core.json
jCfgData = w3rkstatt.getProjectConfig()
cfgFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",
                                   data=jCfgData)
logFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder", data=jCfgData)
tmpFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",
                                   data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",
                                    data=jCfgData)

bhom_host = w3rkstatt.getJsonValue(path="$.BHOM.host", data=jCfgData)
bhom_api_ver = w3rkstatt.getJsonValue(path="$.BHOM.api_version", data=jCfgData)
bhom_api_ns = w3rkstatt.getJsonValue(path="$.BHOM.api_namespace",
                                     data=jCfgData)
bhom_ssl_ver = w3rkstatt.getJsonValue(path="$.BHOM.ssl_ignore", data=jCfgData)

bhom_api_key = w3rkstatt.getJsonValue(path="$.BHOM.api_key", data=jCfgData)
bhom_api_secret = w3rkstatt.getJsonValue(path="$.BHOM.api_secret",
                                         data=jCfgData)
bhom_tenant = w3rkstatt.getJsonValue(path="$.BHOM.tenant", data=jCfgData)

# Compute Url's
# /ims/api/v1
bhom_url_ims = 'https://' + bhom_host + '/ims/api/v1/'

# /events-service/api/v1.0/events
bhom_url_event = 'https://' + bhom_host + '/events-service/api/v1.0/'

# ITSM configuration
itsm_operational_category1 = w3rkstatt.getJsonValue(path="$.ITSM.opcat_1",
                                                    data=jCfgData)
itsm_operational_category2 = w3rkstatt.getJsonValue(path="$.ITSM.opcat_2",
                                                    data=jCfgData)
itsm_operational_category3 = w3rkstatt.getJsonValue(path="$.ITSM.opcat_3",
                                                    data=jCfgData)

# Ignore HTTPS Insecure Request Warnings
if bhom_ssl_ver:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Assign module defaults
_modVer = "20.23.05.00"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = jCfgData["BHOM"]["debug"]
logger = w3rkstatt.logging.getLogger(__name__)
logFile = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file", data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)
domain = w3rkstatt.getHostDomain(w3rkstatt.getHostFqdn(hostName))


def createEvent(token, event_data):
    # https://{{server}}:{{port}}/events-service/api/v1.0/events
    bhom_event_id = ""
    authToken = token
    url = bhom_url_event + 'events'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'Bearer ' + authToken,
    }

    # Payload is the complete event definition in JSON format
    payload = event_data

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        json_data = json.loads(rst)
        bhom_event_id = json_data['resourceId'][0]
        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('BHOM: event created: %s', bhom_event_id)
    else:
        logger.error('BHOM: failed to create the event: %s', response)
    return bhom_event_id


def acknowledgeEvent(token, event_id, event_note=""):
    # https://{{server}}:{{port}}/events-service/api/v1.0/events/operations/acknowledge
    bhom_event_status = False
    authToken = token
    url = bhom_url_event + 'events/operations/acknowledge'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'Bearer ' + authToken,
    }

    # Create a dictionary for the request body
    request_body = {'eventIds': [event_id], 'slots': {'notes': event_note}}

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 202:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 202:
        rst = response.text
        json_data = json.loads(rst)
        bhom_event_passed_id = json_data['passedIds'][0]

        if event_id == bhom_event_passed_id:
            bhom_event_status = True

        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('BHOM: event status: %s', bhom_event_status)
    else:
        logger.error('BHOM: failed to acknowledge the event: %s', response)
    return bhom_event_status


def setPriorityEvent(token,
                     event_id,
                     event_priority="PRIORITY_5",
                     event_note=""):
    # https://{{server}}:{{port}}/events-service/api/v1.0/events/operations/setPriority
    # PRIORITY_5 (lowest priority)
    # PRIORITY_4
    # PRIORITY_3
    # PRIORITY_2
    # PRIORITY_1 (highest priority)

    # CTM Alert:
    # INFO = PRIORITY_5
    # MAJOR = PRIORITY_2
    # CRITICAL = PRIORITY_1

    bhom_event_status = False
    authToken = token
    url = bhom_url_event + 'events/operations/setPriority'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'Bearer ' + authToken,
    }

    # Create a dictionary for the request body
    request_body = {
        'eventIds': [event_id],
        'slots': {
            "priority": event_priority,
            'notes': event_note
        }
    }

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 202:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 202:
        rst = response.text
        json_data = json.loads(rst)
        bhom_event_passed_id = json_data['passedIds'][0]

        if event_id == bhom_event_passed_id:
            bhom_event_status = True

        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('BHOM: event status: %s', bhom_event_status)
    else:
        logger.error('BHOM: failed to set priority: %s', response)
    return bhom_event_status


def assignEvent(token, event_id, assigned_user, event_note=""):
    # https://{{server}}:{{port}}/events-service/api/v1.0/events/operations/assign

    bhom_event_status = False
    authToken = token
    url = bhom_url_event + 'events/operations/assign'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'Bearer ' + authToken,
    }

    # Create a dictionary for the request body
    request_body = {
        'eventIds': [event_id],
        'slots': {
            "assigned_user": assigned_user,
            'notes': event_note
        }
    }

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 202:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 202:
        rst = response.text
        json_data = json.loads(rst)
        bhom_event_passed_id = json_data['passedIds'][0]

        if event_id == bhom_event_passed_id:
            bhom_event_status = True

        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('BHOM: event status: %s', bhom_event_status)
    else:
        logger.error('BHOM: failed to assign event: %s', response)
    return bhom_event_status


def createIncidentEvent(token, event_id):
    # https://{{server}}:{{port}}/events-service/api/v1.0/events/operations/incident

    bhom_event_status = False
    authToken = token
    url = bhom_url_event + 'events/operations/incident'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'Bearer ' + authToken,
    }

    # Create a dictionary for the request body
    request_body = {'eventIds': [event_id]}

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 202:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 202:
        rst = response.text
        json_data = json.loads(rst)
        bhom_event_passed_id = json_data['passedIds'][0]

        if event_id == bhom_event_passed_id:
            bhom_event_status = True

        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('BHOM: event status: %s', bhom_event_status)
    else:
        logger.error('BHOM: failed to create incident for event: %s', response)
    return bhom_event_status


def addNoteEvent(token, event_id, event_note):
    # https://{{server}}:{{port}}/events-service/api/v1.0/events/operations/addNote

    bhom_event_status = False
    authToken = token
    url = bhom_url_event + 'events/operations/addNote'
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'Authorization': 'Bearer ' + authToken,
    }

    # Create a dictionary for the request body
    request_body = {'eventIds': [event_id], 'slots': {'notes': event_note}}

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 202:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 202:
        rst = response.text
        json_data = json.loads(rst)
        bhom_event_passed_id = json_data['passedIds'][0]

        if event_id == bhom_event_passed_id:
            bhom_event_status = True

        if _localDebug:
            logger.debug('HTTP Response Text: %s', rst)
            logger.info('BHOM: event status: %s', bhom_event_status)
    else:
        logger.error('BHOM: failed to add note to the event: %s', response)
    return bhom_event_status


# Main function


def authenticate():
    """login

    Login to BMC Helix Operations Manager
    :param str key: BHOM API Access Key
    :param str secret: BHOM API Secret
    :param str tenant: BHOM Tenant ID
    :return: JWT                
    """
    # https://{{server}}:{{port}}/ims/api/v1/access_keys/login
    authToken = None
    logger.info('bhom: login')
    url = bhom_url_ims + 'access_keys/login'
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}

    bhom_key_decrypted = bhom_api_key
    bhom_secret_decrypted = bhom_api_secret

    # Create a dictionary for the request body
    request_body = {}
    request_body['access_key'] = bhom_key_decrypted
    request_body['access_secret_key'] = bhom_secret_decrypted
    request_body['tenant_id'] = bhom_tenant

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)

    # Make the call to the API
    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', payload)

    try:
        response = requests.post(url,
                                 data=payload,
                                 headers=headers,
                                 verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        json_data = json.loads(rst)
        authToken = json_data['json_web_token']
        if _localDebug:
            logger.info('BHOM: Response: %s', json_data)
            logger.info('BHOM: authToken: %s', authToken)
    else:
        logger.error('Authentication Failure Response Code: %s', response)
    return authToken


if __name__ == "__main__":
    logging.basicConfig(filename=logFile,
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')
    logger.info('BHOM: start event management')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: %s ', w3rkstatt.platform.system())
    logger.info('Log Level: %s', loglevel)
    logger.info('Host Name: %s', hostName)
    logger.info('Host IP: %s', hostIP)
    logger.info('BMC Helix Operation Manager: %s', bhom_host)
    logger.info('BHOM API Version: %s', bhom_api_ver)
    logger.info('BHOM Url Login: %s', bhom_url_ims)
    logger.info('BHOM Url Event: %s', bhom_url_event)
    logger.info('BHOM API Key: %s', bhom_api_key)
    logger.info('Epoch: %s', epoch)

    logging.shutdown()
    print(f"Version: {_modVer}")
