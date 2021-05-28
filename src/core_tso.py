#!/usr/bin/python
#Filename: core_tso.py

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

https://opensource.org/licenses/GPL-3.0
# SPDX-License-Identifier: GPL-3.0-or-later
For information on SDPX, https://spdx.org/licenses/GPL-3.0-or-later.html

BMC Software Python Core Tools 
Provide core functions for BMC Software related python scripts

Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20210527      Volker Scheithauer    Tranfer Development from other projects

"""


import os, json, logging
import time, datetime
import sys, getopt
import requests, urllib3
import urllib3
from urllib3 import disable_warnings
from urllib3.exceptions import NewConnectionError, MaxRetryError, InsecureRequestWarning
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
import jsonpath_rw_ext as jp

# fix import issues for modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from src import w3rkstatt as w3rkstatt

# Get configuration from bmcs_core.json
# jCfgFile     = os.path.join( w3rkstatt.getCurrentFolder(), "bmcs_core.json")
# jCfgData     = w3rkstatt.getFileJson(jCfgFile)

# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)

tso_host    = w3rkstatt.getJsonValue(path="$.TSO.host",data=jCfgData)
tso_port    = w3rkstatt.getJsonValue(path="$.TSO.port",data=jCfgData)
tso_ssl     = w3rkstatt.getJsonValue(path="$.TSO.ssl",data=jCfgData)
tso_ssl_ver = w3rkstatt.getJsonValue(path="$.TSO.ssl_verification",data=jCfgData)
tso_user    = w3rkstatt.getJsonValue(path="$.TSO.user",data=jCfgData)
tso_pwd     = w3rkstatt.getJsonValue(path="$.TSO.pwd",data=jCfgData)

# ITSM REST API
# https://<localhost>:<port>/api/{namespace}/{version} 
if tso_ssl:
    tso_protocol = "https://"
else:
    tso_protocol = "http://"

if (tso_port == "443") and (tso_ssl == True):
    tso_url     = tso_protocol + tso_host + "/baocdp"
else:
    tso_url     = tso_protocol + tso_host + ":" + tso_port + "/baocdp"

# Assign module defaults
_modVer = "20.21.05.00"
_timeFormat  = '%Y-%m-%dT%H:%M:%S'
_localDebug  = False
_localDbgAdv = False
logger   = logging.getLogger(__name__) 
logFile  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file",data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
epoch    = time.time()
hostName = w3rkstatt.getHostName()
hostIP   = w3rkstatt.getHostIP(hostName)

# Ignore HTTPS Insecure Request Warnings
if tso_ssl_ver == False:
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



def authenticate():
    '''
    Login to TSO platform

    :return: authentication token
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''  

    authToken = None
    url = tso_url + '/rest/login'
    tso_pwd_decrypted = w3rkstatt.decryptPwd(data=tso_pwd,sKeyFileName=cryptoFile)

    # Create a dictionary for the request body
    request_body = {}
    request_body['username'] = tso_user
    request_body['password'] = tso_pwd_decrypted

    # Create a dictionary for the loging of the request body
    log_request_body = {}
    log_request_body['username'] = tso_user
    log_request_body['password'] = "***********"
    log_payload = json.dumps(log_request_body)

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache" ,
    }

    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', log_payload)

    # Execute the API call.
    try:
        response = requests.post(url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        # Authentication-Token
        rshd = response.headers
        authToken = rshd["Authentication-Token"]
        if _localDebug:
            logger.debug('TSO: authToken: "%s"', authToken)
    else:
        logger.error('Authentication Failure Response Code: %s', response)
    return authToken

def logout(data):
    '''
    Logout from TSO platform

    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''    

    url = tso_url + '/rest/logout'
    authToken = data

    # Create a dictionary for the request body
    request_body = {}

    # Create a dictionary for the loging of the request body
    log_payload = json.dumps(request_body)

    # Load the request body into the payload in JSON format.
    payload = json.dumps(request_body)
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache" ,
        'Authentication-Token': authToken ,
    }

    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', log_payload)

    # Execute the API call.
    try:
        response = requests.post(url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        # rshd = response.headers
        return rsc
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

def apiGet(api,headers,body=""):
    '''
    Execute a TSO API GET

    :param str api: TSO api
    :param str headers: request headers
    :param str body: request body
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''        

    url = tso_url + '/rest/' + api
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
            response = requests.get(url, headers=headers, verify=False)
        else:
            response = requests.get(url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 401:
        rst = response.text
        logger.error('TSO: Error: %s', rst)     
        tso_data = {}   
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        rsd = response.content
        tso_data = json.loads(rst) 
        if _localDbgAdv:
            logger.debug('HTTP Response Text: %s', rst)  
            logger.debug('HTTP Response Content: %s', rsd) 
            logger.info('TSO: Get Data: %s', tso_data)
        return tso_data
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

def apiPost(api,headers,body=""):
    '''
    Execute a TSO API POST

    :param str api: TSO api
    :param str headers: request headers
    :param str body: request body
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''    

    url = tso_url + '/rest/' + api
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
            response = requests.get(url, headers=headers, verify=False)
        else:
            response = requests.post(url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 401:
        rst = response.text
        logger.error('TSO: Error: %s', rst)     
        tso_data = {} 
    elif rsc == 420:
        rst = response.text
        logger.error('TSO: Error: %s', rst)     
        tso_data = rst        
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 200:
        rst = response.text
        rsd = response.content
        tso_data = json.loads(rst) 
        if _localDbgAdv:
            logger.debug('HTTP Response Text: %s', rst)  
            logger.debug('HTTP Response Content: %s', rsd) 
            logger.info('TSO: Get Data: %s', tso_data)
        return tso_data
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

def getTsoModules(token):
    '''
    Get the TSO modules

    :param str token: authentication token
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''      

    # 'repo': "false" , pattern
    tsoApi = "module"
    authToken = token
    headers = {
            'content-type': "application/json",
            'cache-control': "no-cache" ,
            'Authentication-Token': authToken ,
            'repo': "false",
        }
    body = {}
    items01 = apiGet(api=tsoApi,headers=headers,body=body)

    tsoModules = []
    for item01 in items01:
        tsoModule = {}
        tsoModule["name"] = item01["name"]
        tsoModule["version"] = item01["version"]
        tsoModule["revision"] = item01["revision"]
        tsoModules.append(tsoModule)

    json_data = '{"module":' + w3rkstatt.jsonTranslateValues(str(tsoModules)) + '}'
    if _localDebug:
        logger.debug('TSO: Modules: %s', json_data)
    return json_data

def getTsoModulesAdv(token):
    '''
    Get the TSO modules with additional information

    :param str token: authentication token
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       
    # 'repo': "false" , pattern
    tsoApi = "module"
    authToken = token
    headers = {
            'content-type': "application/json",
            'cache-control': "no-cache" ,
            'Authentication-Token': authToken ,
            'repo': "false",
        }
    body = {}
    items01 = apiGet(api=tsoApi,headers=headers,body=body)

    tsoModules = []
    itemsCounter = 0
    for item01 in items01:
        tsoModule = {}
        
        tsoModule["name"] = item01["name"]
        tsoModule["version"] = item01["version"]
        tsoModule["revision"] = item01["revision"]      
        items02 = items01[itemsCounter]["processes"]
        
        tsoProcesses = []
        tsoProcesses.clear()
        for item02 in items02:
            tsoProcess = {}
            tsoProcess["name"] = item02["name"]
            tsoProcesses.append(tsoProcess)

        tsoModule["processes"] = tsoProcesses
        tsoModules.append(tsoModule)
        itemsCounter += 1
        

    json_data = w3rkstatt.jsonTranslateValues(tsoModules)
    if _localDebug:
        logger.debug('TSO: Modules Advanced: %s', json_data)
    return json_data

def getTsoAdapters(token):
    '''
    Get the TSO adapters

    :param str token: authentication token
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''   

    tsoApi = "adapter?configDataType=JSON"
    authToken = token
    headers = {
            'content-type': "application/json",
            'cache-control': "no-cache" ,
            'Authentication-Token': authToken ,
            'configDataType':'JSON'
        }
    body = {}
    items01 = apiGet(api=tsoApi,headers=headers,body=body)
    tsoAdapters = []
    for item01 in items01:
        tsoAdapter = {}
        tsoAdapter["name"] = item01["name"]
        tsoAdapter["version"] = item01["version"]
        tsoAdapter["revision"] = item01["revision"]
        tsoAdapter["adapterType"] = item01["adapterType"]
        tsoAdapter["revision"] = item01["revision"]

        # adapterType
        tsoAdapters.append(tsoAdapter)

    json_data = '{"adapter":' + w3rkstatt.jsonTranslateValues(str(tsoAdapters)) + '}'
    if _localDebug:
        logger.debug('TSO: Adapters: %s', json_data)    
    return json_data

def executeTsoProcess(token,process,data=""):
    '''
    Execute a TSO workflow

    :param str token: authentication token
    :param str process: workflow name
    :param str data: workflow payload
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''       

    # https://<hostname>:<port>/baocdp/rest/process/<process_name>/execute
    # process/<process_name>/execute
    tsoProcess = w3rkstatt.encodeUrl(process)
    tsoApi = "process/" + tsoProcess + "/execute?configDataType=JSON"
    logger.debug('TSO: Process Url: "%s"', tsoProcess)
    authToken = token
    headers = {
            'content-type': "application/json",
            'cache-control': "no-cache" ,
            'Authentication-Token': authToken ,
            'configDataType':'JSON'
        }
    body = data
    tso_data = apiPost(api=tsoApi,headers=headers,body=body)

    return tso_data
    
def executeProcess(process,data=""):
    '''
    Execute a TSO workflow

    :param str process: workflow name
    :param str data: workflow payload
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''        
    if _localDebug:
        logger.debug('TSO Process Name: %s', process)
        logger.debug('TSO Process Data: %s', data)
        
    authToken = authenticate()
    response  = executeTsoProcess(token=authToken,process=process,data=data)
    response  = w3rkstatt.jsonTranslateValues(data=response)
    logout(authToken)
    return response


if __name__ == "__main__":
  logging.basicConfig(filename=logFile, filemode='a', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
  logger.info('TrueSight: Orchestration Start')
  logger.info('Version: %s ', _modVer)
  logger.info('System Platform: "%s" ', w3rkstatt.platform.system())
  logger.info('Log Level: "%s"', loglevel)
  logger.info('Host Name: "%s"', hostName)
  logger.info('Host IP: "%s"', hostIP)
  logger.info('TSO Url: "%s"', tso_url)
  logger.info('User: "%s"', tso_user)
  logger.info('Epoch: %s', epoch)

  logger.info('TrueSight: Orchestration End')
  logging.shutdown()
  print (f"Version: {_modVer}")