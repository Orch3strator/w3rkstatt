#!/usr/bin/env python3
#Filename: core_tsim.py

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

w3rkstatt Python TrueSight Operations MAnager Integration


Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20210513      Volker Scheithauer    Tranfer Development from other projects


See also: https://realpython.com/python-send-email/
"""

import os, json, logging
import requests, urllib3
import time, datetime
import sys, getopt

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from src import w3rkstatt as w3rkstatt

# Define global variables from w3rkstatt.ini file
# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)

tsim_host    = w3rkstatt.getJsonValue(path="$.TSIM.host",data=jCfgData)
tsws_api_ver = w3rkstatt.getJsonValue(path="$.TSPS.api_version",data=jCfgData)
tsps_host    = w3rkstatt.getJsonValue(path="$.TSPS.host",data=jCfgData)
tsom_user    = w3rkstatt.getJsonValue(path="$.TSIM.user",data=jCfgData)
tsom_pwd     = w3rkstatt.getJsonValue(path="$.TSIM.pwd",data=jCfgData)
tsom_tenant  = w3rkstatt.getJsonValue(path="$.TSIM.tenant",data=jCfgData)
tsps_ssl_ver = w3rkstatt.getJsonValue(path="$.TSPS.ssl_ignore",data=jCfgData)
# routingId - Name of the cell to send events to
tsim_cell    = w3rkstatt.getJsonValue(path="$.TSIM.cell",data=jCfgData)
# routingType
tsim_routing = w3rkstatt.getJsonValue(path="$.TSIM.routing",data=jCfgData)

# Compute Url's
tsps_url     = 'https://' + tsps_host + '/tsws/api/' + tsws_api_ver + '/'
tsim_url     = 'https://' + tsim_host + '/bppmws/api/'

# ITSM configuration
itsm_operational_category1 = w3rkstatt.getJsonValue(path="$.ITSM.opcat_1",data=jCfgData)
itsm_operational_category2 = w3rkstatt.getJsonValue(path="$.ITSM.opcat_2",data=jCfgData)
itsm_operational_category3 = w3rkstatt.getJsonValue(path="$.ITSM.opcat_3",data=jCfgData)

# Ignore HTTPS Insecure Request Warnings
if tsps_ssl_ver:
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Assign module defaults
_modVer = "20.21.05.00"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = True
logger   = w3rkstatt.logging.getLogger(__name__) 
logFile  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file",data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
epoch    = time.time()
hostName = w3rkstatt.getHostName()
hostIP   = w3rkstatt.getHostIP(hostName)
domain   = w3rkstatt.getHostDomain(w3rkstatt.getHostFqdn(hostName))
  

def tsimAuthenticate():
  url = tsps_url + 'token'
  tsom_pwd_decrypted = w3rkstatt.decryptPwd(data=tsom_pwd,sKeyFileName=cryptoFile)

  # Create a dictionary for the request body
  request_body = {}
  request_body['username'] = tsom_user
  request_body['password'] = tsom_pwd_decrypted
  request_body['tenantName'] = tsom_tenant

  # Create a dictionary for the loging of the request body
  log_request_body = {}
  log_request_body['username'] = tsom_user
  log_request_body['password'] = "***********"
  log_request_body['tenantName'] = tsom_tenant
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
    json_data = json.loads(response.text)
    authToken = json_data['response']['authToken']
    if _localDebug:
      logger.info('TSPS: Response: %s', json_data)
      logger.info('TSPS: authToken: %s', authToken)
    return authToken
  else:
      logger.error('Authentication Failure Response Code: %s', response)
      # exit()
  # end of get_authToken() function

def tsimCreateEvent(event_data):
  tsim_event_id = ""
  # Authenticate first.
  authToken = tsimAuthenticate()
  url = tsim_url + 'Event/create?routingId=' + tsim_cell + '&routingType=' + tsim_routing
  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
      'Authorization': 'authtoken ' + authToken,
  }

  # Payload is the complete event definition in JSON format
  payload = event_data

  # Make the call to the API
  if _localDebug:  
    logger.debug('HTTP API Url: %s', url)
    logger.debug('HTTP Headers: %s', headers)
    logger.debug('HTTP Payload: %s', payload)

  try:
    response = requests.post(url, data=payload, headers=headers, verify=False)
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
      tsim_data = rst 
      tsim_event_id = tsimGetEventID(tsim_data)
      if _localDebug:
        logger.info('TSIM: event created: %s', tsim_event_id)
  else:
    logger.error('TSIM: failed to create the event: %s', response)
  return tsim_event_id

def tsimUpdateEvent(event_data):
  status = False
  # Authenticate first.
  authToken = tsimAuthenticate()
  url = tsim_url + 'Event/update?routingId=' + tsim_cell + '&routingType=' + tsim_routing
  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
      'Authorization': 'authtoken ' + authToken,
  }

  # Payload is the complete event definition in JSON format
  payload = event_data

  # Make the call to the API
  if _localDebug:
    logger.debug('HTTP API Url: %s', url)
    logger.debug('HTTP Headers: %s', headers)
    logger.debug('HTTP Payload: %s', payload)

  try:
    response = requests.put(url, data=payload, headers=headers, verify=False)
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
    logger.error('TSIM: failed to create the event: %s', response)
  return status

def tsimSearchEvent(tsimEventIdentifier,tsimEventValue):
  tsim_event_id = ""
  # Authenticate first.
  # https://docs.bmc.com/docs/TSInfrastructure/113/listing-events-774797826.html

  authToken = tsimAuthenticate()
  url = tsim_url + 'Event/search?routingId=' + tsim_cell + '&routingType=' + tsim_routing
  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
      'Authorization': 'authtoken ' + authToken,
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
              "value": tsimEventValue,
              "identifier": tsimEventIdentifier,
              "operator": "EQUALS"            
        }
  }
  

  # Make the call to the API
  if _localDebug:
    logger.debug('HTTP API Url: %s', url)
    logger.debug('HTTP Headers: %s', headers)
    logger.debug('HTTP Payload: %s', payload)

  try:
    response = requests.post(url, json=payload, headers=headers, verify=False)
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
      tsim_data = rst  
      tsim_event_id = tsimGetEventID(tsim_data)
      if _localDebug:
        logger.debug('TSIM: event search: %s', tsim_event_id)
  else:
    logger.error('TSIM: failed to search the event: %s', response)
  return tsim_event_id
 
def tsimGetEventID(data):
  # {'responseTimeStamp': '2020-05-23T20:11:30', 'statusCode': '200', 'statusMsg': 'OK', 'responseList': [{'mc_ueid': 'mc.pncell_bmcs-ts-om.1ec98372.0', 'statusCode': '200', 'statusMsg': 'OK'}]}
  key     = "mc_ueid"
  mc_ueid = ""
  values  = {}

  if key in data:
    vJson = json.loads(data)
    values = w3rkstatt.jsonExtractValues(vJson,key)
    mc_ueid = values[0]
    if _localDebug:
      logger.debug('TSIM: Extract Event ID: %s', values)
  return mc_ueid

# Main function

def tsimEvent(data):
  tsim_event_id = ""
  # Define the TSOM event slots and create a JSON object.
  logger.info('TSIM: define event')
  # json_data = tsimDefineEvent()

  # Make the call to the API to create the event,
  logger.info('TSIM: invoke event creation')
  tsim_event_id = tsimCreateEvent(data)
  return tsim_event_id

def tsimSearchCI(tsimCiIdentifier,tsimCiValue):
  # Authenticate first.
  # https://docs.bmc.com/docs/TSInfrastructure/113/listing-events-774797826.html

  authToken = tsimAuthenticate()
  url = tsim_url + 'CI/search'
  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
      'Authorization': 'authtoken ' + authToken,
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
              "value": tsimCiValue,
              "identifier": tsimCiIdentifier,
              "operator": "EQUALS"            
        }
  }
  # Make the call to the API
  if _localDebug:
    logger.debug('HTTP API Url: %s', url)
    logger.debug('HTTP Headers: %s', headers)
    logger.debug('HTTP Payload: %s', payload)

  try:
    response = requests.post(url, json=payload, headers=headers, verify=False)
  except requests.RequestException as e:
    logger.error('HTTP Response Error: %s', e)

  rsc = response.status_code
  if rsc == 501:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc != 200:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc == 200:
    rst = response.text
    tsim_data = rst  
    if _localDebug:
      logger.debug('HTTP Response Text: %s', rst)      
      logger.info('TSIM: CI search: %s', tsim_data)
  else:
    logger.error('TSIM: failed to search for CI: %s', response)
  return tsim_data  

def tsimSearchCiAdvanced(tsimCiSearchFilter):
  tsim_data = {}
  # Authenticate first.
  # https://docs.bmc.com/docs/TSInfrastructure/113/listing-events-774797826.html

  authToken = tsimAuthenticate()
  url = tsim_url + 'CI/search'
  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
      'Authorization': 'authtoken ' + authToken,
  }

  # Payload is the complete event definition in JSON format
  payload = str(tsimCiSearchFilter)
  # Make the call to the API
  if _localDebug:
    logger.debug('HTTP API Url: %s', url)
    logger.debug('HTTP Headers: %s', headers)
    logger.debug('HTTP Payload: %s', payload)

  try:
    response = requests.post(url, data=payload, headers=headers, verify=False)
  except requests.RequestException as e:
    logger.error('HTTP Response Error: %s', e)

  rsc = response.status_code
  if rsc == 501:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc != 200:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc == 200:
    rst = response.text
    tsim_data = rst  
    if _localDebug:
      logger.debug('HTTP Response Text: %s', rst)  
      logger.info('TSIM: CI search: %s', tsim_data)
  else:
    logger.error('TSIM: failed to search for CI: %s', response)
  return tsim_data  

def tsimCreateCI(data,ciType="CI"):
  tsim_data = ""
  # Authenticate first.
  authToken = tsimAuthenticate()
  # http://bppmwsserver:80/bppmws/api/CI/create?routingIdKeyParam=CI_ID&routingId=ci5&routingIdType=CACHE_KEY&ciType=CI
  # routingIdType=SERVER_NAME
  url = tsim_url + 'CI/create?routingIdKeyParam=NAME&routingIdType=SERVER_NAME&routingId=' + tsim_cell + '&ciType=' + ciType
  # url = tsim_url + 'CI/create?ciType=CI'

  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
      'Authorization': 'authtoken ' + authToken,
  }

  # Payload is the complete event definition in JSON format
  payload = data

  # Make the call to the API
  if _localDebug:
    logger.debug('HTTP API Url: %s', url)
    logger.debug('HTTP Headers: %s', headers)
    logger.debug('HTTP Payload: %s', payload)

  try:
    response = requests.post(url, data=payload, headers=headers, verify=False)
  except requests.RequestException as e:
    logger.error('HTTP Response Error: %s', e)

  rsc = response.status_code
  if rsc == 501:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc != 200:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc == 200:
    rst = response.text
    tsim_data = rst 
    if _localDebug:
      logger.debug('HTTP Response Text: %s', rst)      
      logger.info('TSIM: CI created: %s', tsim_data)
  else:
    logger.error('TSIM: failed to create the CI: %s', response)
  return tsim_data

def tsimComputeCI(data):

    ci_name = data
    ci_attributeMap = {}
    ci_attributeMap['Name'] = ci_name
    ci_attributeMap['CLASS'] = ""
    ci_attributeMap['Description'] = "CTM Application"
    ci_attributeMap['Priority'] = "PRIORITY_5"
    ci_attributeMap['HomeCell'] = tsim_cell
    ci_attributeMap['ReadSecurity'] = "[Full Access]"
    ci_attributeMap['WriteSecurity'] = "[Full Access]"
    ci_attributeMap['status'] = "OK"
    ci_attributeMap['maintenance_mode'] = "NO"
    ci_attributeMap['ComponentAliases'] = "[ctm-em:TryBMC:Business Service Automation:TryBMC Payroll:]"
    ci_attributeMap['HomePageURI'] = "http://www.trybmc.com"
    ci_attributeMap['ManufacturerName'] = "BMC Software"
    ci_attributeMap['TokenId'] = "ctm-em:TryBMC:Business Service Automation:TryBMC Payroll:"
    
     

    # Define the dictionary that wraps each event.
    ci_wrapper = {}
    ci_wrapper["id"] = ci_name
    ci_wrapper["className"] = "BMC_ApplicationService"
    ci_wrapper["attributeMap"] = ci_attributeMap
    json_data = '{"cilist":[' + w3rkstatt.jsonTranslateValues(str(ci_wrapper)) + ']}'
    if _localDebug:
      logger.debug('CTM: CI json payload: %s', json_data)  
    return json_data
    


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('TSIM: start event management')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: %s ', w3rkstatt.platform.system())
    logger.info('Log Level: %s', loglevel)
    logger.info('Host Name: %s', hostName)
    logger.info('Host IP: %s', hostIP)
    logger.info('TrueSight Operations Manager: %s', tsim_host)
    logger.info('TrueSight Web Service: %s', tsps_host)
    logger.info('TSIM API Version: %s', tsws_api_ver)
    logger.info('TSIM Url: %s', tsim_url)
    logger.info('TSIM Cell: %s', tsim_cell)
    logger.info('Tenant: %s', tsom_tenant)
    logger.info('User: %s', tsom_user)
    logger.info('TSIM Token: %s', tsimAuthenticate())
    logger.info('Epoch: %s', epoch)
    

    logging.shutdown()
    print (f"Version: {_modVer}")