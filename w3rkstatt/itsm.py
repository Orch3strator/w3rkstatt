#!/usr/bin/python
# itsm.py

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
20210513      Volker Scheithauer    Tranfer Development from other projects

"""

# import bmcs_core as bmcs
import w3rkstatt
import os, json, logging
import time, datetime
import sys, getopt
import requests, urllib3
import subprocess
import urllib3
from urllib3 import disable_warnings
from urllib3.exceptions import NewConnectionError, MaxRetryError, InsecureRequestWarning

import json
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse
import jsonpath_rw_ext as jp

# Get configuration from bmcs_core.json
# jCfgFile     = os.path.join( w3rkstatt.getCurrentFolder(), "bmcs_core.json")
# jCfgData     = w3rkstatt.getFileJson(jCfgFile)

jCfgFile     = w3rkstatt.jCfgFile
jCfgData     = w3rkstatt.jCfgData

itsm_host    = w3rkstatt.getJsonValue(path="$.ITSM.host",data=jCfgData)
itsm_port    = w3rkstatt.getJsonValue(path="$.ITSM.port",data=jCfgData)
itsm_ssl     = w3rkstatt.getJsonValue(path="$.ITSM.ssl",data=jCfgData)
itsm_ssl_ver = w3rkstatt.getJsonValue(path="$.ITSM.ssl_verification",data=jCfgData)
itsm_user    = w3rkstatt.getJsonValue(path="$.ITSM.user",data=jCfgData)
itsm_pwd     = w3rkstatt.getJsonValue(path="$.ITSM.pwd",data=jCfgData)
itsm_api_ns  = w3rkstatt.getJsonValue(path="$.ITSM.api_namespace",data=jCfgData)
itsm_api_ver = w3rkstatt.getJsonValue(path="$.ITSM.api_version",data=jCfgData)

# ITSM form names
itsm_form_crq   = w3rkstatt.getJsonValue(path="$.ITSM.change.form_name",data=jCfgData)
itsm_form_inc   = w3rkstatt.getJsonValue(path="$.ITSM.incident.form_name",data=jCfgData)
itsm_form_wlog  = w3rkstatt.getJsonValue(path="$.ITSM.worklog.form_name",data=jCfgData)
itsm_search_inc = w3rkstatt.getJsonValue(path="$.ITSM.incident.form_search",data=jCfgData)
itsm_form_ci    = w3rkstatt.getJsonValue(path="$.ITSM.cmdb.form_name",data=jCfgData)

# ITSM template IDs
itsm_tmpl_crq = w3rkstatt.getJsonValue(path="$.ITSM.change.template_id",data=jCfgData)
itsm_tmpl_inc = w3rkstatt.getJsonValue(path="$.ITSM.incident.template_id",data=jCfgData)

# ITSM field mappings
itsm_map_file = w3rkstatt.getJsonValue(path="$.ITSM.mappings_file",data=jCfgData)


# ITSM REST API
# https://<localhost>:<port>/api/{namespace}/{version} 
if itsm_ssl:
    itsm_protocol = "https://"
else:
    itsm_protocol = "http://"

itsm_url     = itsm_protocol + itsm_host + ":" + itsm_port + "/api/" + itsm_api_ns + "/" + itsm_api_ver
itsm_jwt     = itsm_protocol + itsm_host + ":" + itsm_port + "/api/jwt"

# ITSM Field mappings
jCfgMapFile  = os.path.join( w3rkstatt.pFolder,"configs", itsm_map_file)
jCfgMapData  = w3rkstatt.getFileJson(jCfgMapFile)

# Assign module defaults
_modVer = "1.0"
_timeFormat  = '%Y-%m-%dT%H:%M:%S'
_localDebug  = False
_localDbgAdv = False
logger   = logging.getLogger(__name__) 
logFile  = w3rkstatt.logFile
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
epoch    = time.time()
hostName = w3rkstatt.getHostName()
hostIP   = w3rkstatt.getHostIP(hostName)

# Ignore HTTPS Insecure Request Warnings
if itsm_ssl_ver == False:
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def itsmAuthenticate():
    url = itsm_jwt + '/login'
    itsm_pwd = w3rkstatt.decrypt(itsm_pwd,"")
    response = ""

    # Create a dictionary for the request body
    request_body = {}
    request_body['username'] = itsm_user
    request_body['password'] = itsm_pwd

    # Create a dictionary for the loging of the request body
    log_request_body = {}
    log_request_body['username'] = itsm_user
    log_request_body['password'] = "***********"
    log_payload = json.dumps(log_request_body)

    # Load the request body into the payload in JSON format.
    payload = request_body
    headers = {
        'content-type': "application/x-www-form-urlencoded",
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
        authToken = response.text
        if _localDebug:
            logger.debug('ITSM: authToken: "%s"', authToken)
        return authToken
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

def itsmLogout(token):
    url = itsm_jwt + '/logout'
    authToken = token

    # Create a dictionary for the request body
    request_body = {}

    # Create a dictionary for the loging of the request body
    log_payload = json.dumps(request_body)

    # Load the request body into the payload in JSON format.
    payload = request_body
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'cache-control': 'no-cache',
        'Authorization': 'AR-JWT {}'.format(authToken)
    }

    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)
        logger.debug('HTTP Payload: %s', log_payload)

    # Execute the API call.
    try:
        response = requests.post(url, data=payload, headers=headers, verify=False )
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
        return False
    elif rsc != 204:
        logger.error('HTTP Response Status: %s', rsc)
        logger.error('HTTP Response Reason: "%s"', response.reason)
        return False
    elif rsc == 204:
        rshd = response.headers
        if _localDbgAdv:
            logger.info('HTTP Response Headers: %s', rshd)
        return True
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        return False
        # exit()


# http://serverName:port/api/arsys/v1/entry/HPD:IncidentInterface_Create?fields=values(Incident Number)  
# https://docs.bmc.com/docs/ars2008/date-and-time-formats-929628201.html

def itsmFormGet(form,headers,entry=""):
    if len(entry) > 1:
        if "?" in entry:
            url = itsm_url + '/entry/' + form + entry
        else:
            url = itsm_url + '/entry/' + form + '/' + entry
    else:
        url = itsm_url + '/entry/' + form 

    if _localDebug:
        logger.debug('HTTP API Url: %s', url)
        logger.debug('HTTP Headers: %s', headers)

    # Execute the API call.
    try:
        response = requests.get(url, headers=headers, verify=False)

    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    if rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
    elif rsc == 401:
        rst = response.text
        logger.error('ITSM: Error: %s', rst)     
        data = {}   
    elif rsc == 404:
        rst = response.text
        rsd = response.content
        logger.error('ITSM: Error: %s', rst)     
        data = {}          
    elif rsc != 200:
        logger.error('HTTP Response Status: %s', rsc)        
    elif rsc == 200:
        rst = response.text
        rsd = response.content
        data = rst
        if _localDbgAdv:
            logger.debug('HTTP Response Text: %s', rst)  
            logger.debug('HTTP Response Content: %s', rsd) 
        return data
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

def itsmFormPost(form,headers,body="",fields=""):
    if len(fields) > 1:
        url = itsm_url + '/entry/' + form + '/?' + fields
    else:
        url = itsm_url + '/entry/' + form 

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
            response = requests.get(url, headers=headers, verify=False)
        else:
            response = requests.post(url, data=payload, headers=headers, verify=False)
    except requests.RequestException as e:
        logger.error('HTTP Response Error: %s', e)

    # Capture the authentication token
    rsc = response.status_code
    rst = response.text
    if rsc == 500:
        logger.error('HTTP Response Status: %s', rsc)
        logger.error('HTTP Response Text: %s', rst)
        data = "Error"
        if _localDebug:
            logger.debug('ITSM: Text: %s', rst) 
        return data
    elif rsc == 501:
        logger.error('HTTP Response Status: %s', rsc)
        data = "Error"
        if _localDebug:
            logger.debug('ITSM: Text: %s', rst) 
        return data
    elif rsc == 400:
        logger.error('HTTP Response Status: %s', rsc)     
        logger.error('HTTP Response Text: %s', rst)    
        data = rst
        if _localDebug:
            logger.debug('ITSM: Text: %s', rst) 
        return data         
    elif rsc != 201:
        logger.error('HTTP Response Status: %s', rsc)
        data = "Error"
        if _localDebug:
            logger.debug('ITSM: Text: %s', rst) 
        return data        
    elif rsc == 201:
        # rshd = response.headers
        rst  = response.text
        data = rst
        if _localDebug:
            logger.debug('ITSM: Text: %s', rst) 
        return data
    else:
        logger.error('Authentication Failure Response Code: %s', response)
        # exit()

def createIncident(token,data):
    authToken = "AR-JWT " + token
    headers = {
        'content-type': 'application/json',
        'cache-control': "no-cache" ,
        'Authorization': authToken
    }    
   
    entryFields  = "fields=values(Incident Number)"
    entryRespone = itsmFormPost(form=itsm_form_inc,headers=headers,body=data,fields=entryFields).replace(" ","")
    entryJson    = json.loads(entryRespone)
    entryID      = w3rkstatt.getJsonValue(path="$.*.IncidentNumber",data=entryJson)

    return entryID

# http://<server_name>:<port>/api/arsys/v1/entry/HPD:IncidentInterface_Create/Incident Number
def getIncident(token,incident):
    entryJson = {}
    authToken = "AR-JWT " + token
    headers = {
        'content-type': 'application/json',
        'cache-control': "no-cache" ,
        'Authorization': authToken
    }    
    
    entryID      = incident
    entryRespone = itsmFormGet(form=itsm_search_inc,headers=headers,entry=entryID)
    logger.debug('ITSM: Entry: %s', entryRespone) 

    return entryRespone

def getIncidentStatus(token,incident):
    incInfo = json.loads(getIncident(token=token,incident=incident))
    status  = w3rkstatt.getJsonValue(path="$.values.Status",data=incInfo)

    return status

def createChange(token,data):
    authToken = "AR-JWT " + token
    headers = {
        'content-type': 'application/json',
        'cache-control': "no-cache" ,
        'Authorization': authToken
    }    
    entryFields  = "fields=values(Infrastructure Change Id)"
    entryRespone = itsmFormPost(form=itsm_form_crq,headers=headers,body=data,fields=entryFields)

    entryRespone = entryRespone.replace(" ","")
    if entryRespone == "Error":
        entryID = "0"
    else: 
        entryJson    = json.loads(entryRespone)
        entryID      = w3rkstatt.getJsonValue(path="$.*.InfrastructureChangeId",data=entryJson)
    return entryID

def createChangeWorklog(token,data):
    authToken = "AR-JWT " + token
    headers = {
        'content-type': 'application/json',
        'cache-control': "no-cache" ,
        'Authorization': authToken
    }    
    entryFields  = "fields=values(Infrastructure Change Id)"
    entryRespone = itsmFormPost(form=itsm_form_crq,headers=headers,body=data,fields=entryFields).replace(" ","")
    entryJson    = json.loads(entryRespone)
    entryID      = w3rkstatt.getJsonValue(path="$.*.InfrastructureChangeId",data=entryJson)
    return entryID

def createIncidentWorklog(token,data):
    authToken = "AR-JWT " + token
    headers = {
        'content-type': 'application/json',
        'cache-control': "no-cache" ,
        'Authorization': authToken
    }    
    entryRespone = itsmFormPost(form=itsm_form_wlog,headers=headers,body=data)
    
    return entryRespone

def getChange(token,change):
    authToken = "AR-JWT " + token
    headers = {
        'content-type': 'application/json',
        'cache-control': "no-cache" ,
        'Authorization': authToken
    }    
    # ?q=('Request ID'="entryID") 

    itsm_form    = itsm_form_crq.split("_")[0]
    entryID      = '/?q=(' + "'Infrastructure Change ID'" + '="' + change + '")' 
    entryRespone = itsmFormGet(form=itsm_form,headers=headers,entry=entryID)
    logger.debug('ITSM: Entry: %s', entryRespone) 

    return entryRespone

def extractChangeState(change):
    status = ""
    jData   = json.loads(change)
    crqInfo = w3rkstatt.getJsonValue(path="$.entries..values",data=jData)

    if len(crqInfo) > 1:
        stateId = int(w3rkstatt.getJsonValue(path="$.ChangeRequestStatusString",data=crqInfo))
    else:
        stateId = 99

    # jQl    = "$.*.change-request-status.mapping.[?id='" + stateId + "')].name"
    if(stateId == 0):
        status = "Draft"
    elif(stateId == 1):
        status = "Request For Authorization"
    elif(stateId == 2):
        status = "Request For Change"
    elif(stateId == 3):
        status = "Planning In Progress"
    elif(stateId == 4):
        status = "Scheduled For Review"
    elif(stateId == 5):
        status = "Scheduled For Approval"
    elif(stateId == 6):
        status = "Scheduled"
    elif(stateId == 7):
        status = "Implementation In Progress"
    elif(stateId == 8):
        status = "Pending"
    elif(stateId == 9):
        status = "Rejected"
    elif(stateId == 10):
        status = "Completed"
    elif(stateId == 11):
        status = "Closed"
    elif(stateId == 12):
        status = "Cancelled"
    else:
        status = "Unknown"

    return status

def testIncidentCreate(token):
    data =  {
                "values": {
                    "z1D_Action" : "CREATE",
                    "First_Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-first",data=jCfgData),
                    "Last_Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-last",data=jCfgData),
                    "Description": "CTM WCM: Incident Creation " + str(epoch),
                    "Impact": w3rkstatt.getJsonValue(path="$.ITSM.incident.impact",data=jCfgData),
                    "Urgency": w3rkstatt.getJsonValue(path="$.ITSM.incident.urgency",data=jCfgData),
                    "Status": w3rkstatt.getJsonValue(path="$.ITSM.incident.status",data=jCfgData),
                    "Reported Source": w3rkstatt.getJsonValue(path="$.ITSM.incident.reported-source",data=jCfgData),
                    "Service_Type": w3rkstatt.getJsonValue(path="$.ITSM.incident.service-type",data=jCfgData),
                    "ServiceCI": w3rkstatt.getJsonValue(path="$.ITSM.defaults.service-ci",data=jCfgData),
                    "Assigned Group": w3rkstatt.getJsonValue(path="$.ITSM.defaults.assigned-group",data=jCfgData),
                    "Assigned Support Company": w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-company",data=jCfgData),
                    "Assigned Support Organization": w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-organization",data=jCfgData),
                    "Categorization Tier 1": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_1",data=jCfgData),
                    "Categorization Tier 2": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_2",data=jCfgData),
                    "Categorization Tier 3": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_3",data=jCfgData),
                    "Product Categorization Tier 1": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_1",data=jCfgData),
                    "Product Categorization Tier 2": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_2",data=jCfgData),
                    "Product Categorization Tier 3": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_3",data=jCfgData),
                    "Product Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.product_name",data=jCfgData),
                    "TemplateID": "AGGAA5V0GO2Y0APMV93LPLY5FREVV1"
                    # "Urgency" : "3-Medium",
                    # "Vendor Ticket Number" : "INC9969625",
                    # "z1D_View_Access":"Internal",
                    # "z1D_WorklogDetails": "Test",
                    # "z1D_Activity_Type": "General Information",
                    # "z1D_CommunicationSource": "Other",
                    # "z1D_Secure_Log": "Locked",
                    # "z1D_Details": "Adding Work notes"                                   
                }
            } 
    result = createIncident(token,data)
    return result 

def testIncidentWorklog(token,incident):
    data =  {
                "values": {
                    "Work Log Submitter": "user",
                    "Status": "Enabled",
                    "Description": "Integration Demo",
                    "Detailed Description": "Added via Python REST API",
                    "Incident Number": "" + str(incident) + "",
                    "Work Log Type": "Incident Task / Action",
                    "View Access": "Public",
                    "Secure Work Log": "No"
                }
            } 
    result = createIncidentWorklog(token,data)
    return result 

def testChangeCreate(token):
    timeDelta  = w3rkstatt.getJsonValue(path="$.ITSM.defaults.timedelta",data=jCfgData)
    startDate  = w3rkstatt.getCurrentDate(timeFormat=_timeFormat)
    endDate    = w3rkstatt.addTimeDelta(date=startDate,timeFormat=_timeFormat,delta=timeDelta)

    data =  {
                "values": {
                    "z1D_Action" : "CREATE",
                    "First Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-first",data=jCfgData),
                    "Last Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-last",data=jCfgData),
                    "Description": "CTM WCM: Change Creation " + str(epoch),
                    "Impact": w3rkstatt.getJsonValue(path="$.ITSM.change.impact",data=jCfgData),
                    "Urgency": w3rkstatt.getJsonValue(path="$.ITSM.change.urgency",data=jCfgData),
                    "Status": w3rkstatt.getJsonValue(path="$.ITSM.change.status",data=jCfgData),
                    "Status Reason": w3rkstatt.getJsonValue(path="$.ITSM.change.status_reason",data=jCfgData),
                    "Vendor Ticket Number": "CMT 99",
                    "ServiceCI": w3rkstatt.getJsonValue(path="$.ITSM.defaults.service-ci",data=jCfgData),
                    "Company3": w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-company",data=jCfgData),
                    "Support Organization": w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-organization",data=jCfgData),
                    "Support Group Name": w3rkstatt.getJsonValue(path="$.ITSM.defaults.assigned-group",data=jCfgData),
                    "Location Company": w3rkstatt.getJsonValue(path="$.ITSM.defaults.location-company",data=jCfgData),
                    "Region": w3rkstatt.getJsonValue(path="$.ITSM.defaults.region",data=jCfgData),
                    "Site Group": w3rkstatt.getJsonValue(path="$.ITSM.defaults.site-group",data=jCfgData),
                    "Site": w3rkstatt.getJsonValue(path="$.ITSM.defaults.site",data=jCfgData),
                    "Categorization Tier 1": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_1",data=jCfgData),
                    "Categorization Tier 2": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_2",data=jCfgData),
                    "Categorization Tier 3": w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_3",data=jCfgData),
                    "Product Cat Tier 1(2)": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_1",data=jCfgData),
                    "Product Cat Tier 2 (2)": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_2",data=jCfgData),
                    "Product Cat Tier 3 (2)": w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_3",data=jCfgData),
                    "Scheduled Start Date": startDate, 
                    "Scheduled End Date": endDate,
                    "TemplateID": itsm_tmpl_crq               
                }
            } 
    result = createChange(token,data)
    return result 

def demoITSM():
    itsm_demo_crq   = w3rkstatt.getJsonValue(path="$.ITSM.change.demo",data=jCfgData)
    itsm_demo_inc   = w3rkstatt.getJsonValue(path="$.ITSM.incident.demo",data=jCfgData)
    
    authToken    = itsmAuthenticate()

    # Demo ITSM Change Integration
    if itsm_demo_crq:
        changeID     = testChangeCreate(token=authToken)
        logger.info('ITSM: Change   ID: "%s"', changeID) 

        crqInfo      = getChange(token=authToken,change=changeID)
        logger.info('ITSM: Change Info: %s', crqInfo) 

        crqStatus    = extractChangeState(change=crqInfo)
        logger.info('ITSM: Change State: "%s"', crqStatus) 
    
    # Demo ITSM Incident Integration
    if itsm_demo_inc:
        incidentID   = testIncidentCreate(token=authToken)
        logger.info('ITSM: Incident ID: "%s"', incidentID) 

        incInfo    = getIncident(token=authToken,incident=incidentID)
        logger.info('ITSM: Incident: %s', incInfo) 

        incStatus  = getIncidentStatus(token=authToken,incident=incidentID)
        logger.info('ITSM: Incident State: "%s"', incStatus) 

        incWLogStatus = testIncidentWorklog(token=authToken,incident=incidentID)
        logger.info('ITSM: Incident Worklog Status: "%s"', incWLogStatus) 



    itsmLogout(token=authToken)


if __name__ == "__main__":
  logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
  logger.info('Helix: ITSM Management Start')
  logger.info('Version: %s ', _modVer)
  logger.info('System Platform: "%s" ', w3rkstatt.platform.system())
  logger.info('Log Level: "%s"', loglevel)
  logger.info('Host Name: "%s"', hostName)
  logger.info('Host IP: "%s"', hostIP)
  logger.info('ITSM Url: "%s"', itsm_url)
  logger.info('User: "%s"', itsm_user)
  logger.info('Secure Pwd: "%s"', itsm_pwd)
  logger.info('Epoch: %s', epoch)

  # Demo Integration
  if w3rkstatt.getJsonValue(path="$.DEFAULT.demo",data=jCfgData):
      demoITSM()

  logger.info('Helix: ITSM Management End')
  logging.shutdown()
  print (f"Version: {_modVer}")