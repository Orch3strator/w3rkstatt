#!/usr/bin/python
#Filename: ctm.py

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
20210311      Volker Scheithauer    Tranfer Development from bmcs_core project

"""

import w3rkstatt
import os, json, logging
import re
import time, datetime
import sys, getopt
import requests, urllib3
from collections import OrderedDict 



# Control-M Python support
# python3 -m pip install git+https://github.com/dcompane/controlm_py.git

import controlm_py as ctm
from controlm_py.rest import ApiException
# from controlm_py.models.run_report_info import RunReportInfo

import urllib3
from urllib3 import disable_warnings
from urllib3.exceptions import NewConnectionError, MaxRetryError, InsecureRequestWarning

# To Handle CTM JSON with '
# https://pypi.org/project/demjson/


# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)

ctm_host    = w3rkstatt.getJsonValue(path="$.CTM.host",data=jCfgData)
ctm_port    = w3rkstatt.getJsonValue(path="$.CTM.port",data=jCfgData)
ctm_aapi    = w3rkstatt.getJsonValue(path="$.CTM.aapi",data=jCfgData)
ctm_user    = w3rkstatt.getJsonValue(path="$.CTM.user",data=jCfgData)
ctm_pwd     = w3rkstatt.getJsonValue(path="$.CTM.pwd",data=jCfgData)
ctm_ssl     = w3rkstatt.getJsonValue(path="$.CTM.ssl",data=jCfgData)
ctm_ssl_ver = w3rkstatt.getJsonValue(path="$.CTM.ssl_verification",data=jCfgData)
ctm_url     = 'https://' + ctm_host + ':' + ctm_port + ctm_aapi + '/'
ctm_rpt_jsm = w3rkstatt.getJsonValue(path="$.CTM.service_model_rpt_job",data=jCfgData)
# CTM Report Name to get job definitions for service model


# Compute CTM Server Name
ctm_server = w3rkstatt.getHostFromFQDN(ctm_host)
ctm_agent  = ctm_server

# Assign module defaults
_modVer = "3.0"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = False
_localDebugAdv = False
_localQA = False

logger   = logging.getLogger(__name__) 
logFile  = w3rkstatt.logFile
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
epoch    = time.time()
hostName = w3rkstatt.getHostName()
hostIP   = w3rkstatt.getHostIP(hostName)

# Ignore HTTPS Insecure Request Warnings
if ctm_ssl_ver == 'true':
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CtmConnection(object):
    """
    Implements persistent connectivity for the Control-M Automation API
    :property api_client Implements the connection to the Control-M AAPI endpoint
    """
    logged_in = False

    def __init__(self, host='', port='', endpoint='/automation-api',
                 user='', password='',
                 ssl=True, verify_ssl=False,
                 additional_login_header={}):
        """
        Initializes the CtmConnection object and provides the Automation API client.
        :param host: str: Control-M web server host name (preferred fqdn) serving the Automation API.
                               Could be a load balancer or API Gateway
        :param port: str: Control-M web server port serving the Automation API.
        :param endpoint: str: The serving point for the AAPI (default='/automation-api')
        :param ssl: bool: If the web server uses https (default=True)
        :param user: str: Login user
        :param password: str: Password for the login user
        :param verify_ssl: bool: If the web server uses self signed certificates (default=False)
        :param additionalLoginHeader: dict: login headers to be added to the AAPI headers
        :return None
        """
        #
        configuration = ctm.Configuration()
        if ssl:
            configuration.host = 'https://'
            # Only use verify_ssl = False if the cert is self-signed.
            configuration.verify_ssl = verify_ssl
            if not verify_ssl:
                # This urllib3 function disables warnings when certs are self-signed
                disable_warnings(InsecureRequestWarning)
        else:
            configuration.host = 'http://'

        configuration.host = configuration.host + host + ':' + port + endpoint

        self.api_client = ctm.api_client.ApiClient(configuration=configuration)
        self.session_api = ctm.api.session_api.SessionApi(api_client=self.api_client)
        credentials = ctm.models.LoginCredentials(username=user, password=password)

        if additional_login_header is not None:
            for header in additional_login_header.keys():
                self.api_client.set_default_header(header, additional_login_header[header])

        try:
            api_token = self.session_api.do_login(body=credentials)
            self.api_client.default_headers.setdefault('Authorization', 'Bearer ' + api_token.token)
            self.logged_in = True
            if _localDebug:
                logger.debug('CTM: API Login: %s', True)
                logger.debug('CTM: API Bearer: %s', api_token.token)
        except (NewConnectionError, MaxRetryError, ctm.rest.ApiException) as exp:
            logger.error('CTM: connection error occurred: %s', exp)
            exit(42)


    def __del__(self):
        if self.session_api is not None:
            try:
                self.logout()
            except ImportError:
                logger.error('CTM: Network access for Logout unavailable due to python shutdown.')
                logger.error('CTM: Program termination occurred before deleting ApiClient object, which performs logout')
                logger.error('CTM: SECURITY RISK: Token will still be available to continue operations.')
                exit(50)

    def logout(self):
        if self.logged_in:
            try:
                self.session_api.do_logout()
                self.logged_in = False
                if _localDebug:
                    logger.debug('CTM: API Logout: %s', True)
            except ctm.rest.ApiException as exp:
                logger.error('CTM: Exception when calling SessionAp => do_logout: %s', exp)
                raise("Exception when calling SessionApi => do_logout: %s\n" % exp)
                

# Main function

def getCtmAgents(ctmApiClient,ctmServer):
    """
    Simple function that uses the get_agents service to get all the agents of the specified Control-M Server.

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """

    # Instantiate the AAPI object
    ctmCfgAapi = ctm.api.config_api.ConfigApi(api_client=ctmApiClient)
    logger.debug('CTM: API object: %s', ctmCfgAapi)
    results = ""

    # Call CTM AAPI
    try:
        logger.debug('CTM: API Function: %s', "get_agents")
        results = ctmCfgAapi.get_agents(server=ctmServer, _return_http_data_only=True )
        results = str(results).replace("'",'"')
        results = str(results).replace("None",'"None"')

        logger.debug('CTM: API Result:\n%s', results)
        results = json.loads(results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: API Error: %s', exp)
    return results

def getCtmJobOutput(ctmApiClient,ctmJobID, ctmJobRunId):
    """
    Get the output returned from a job

    :param async_req bool
    :param str job_id: The job ID (required)
    :param int run_no: The execution number in case of multiple executions (0 will get the last execution's output)
    :return: str
                If the method is called asynchronously, returns the request thread.
    """
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.RunApi(api_client=ctmApiClient)
    if _localDebugAdv: 
        logger.debug('CTM: AAPI object: %s', ctmCfgAapi)

    # Call CTM AAPI
    results = ""
    try:
        if _localDebugAdv: 
            logger.debug('CTM: AAPI Function: %s', "get_job_output")
        results = ctmCfgAapi.get_job_output(job_id=ctmJobID, run_no=ctmJobRunId )
        if _localDebugAdv: 
            logger.debug('CTM: AAPI Result: %s', results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: AAPI Function: %s', "get_job_output")
        sBody = str(exp).split("HTTP response body:")[1]
        sMessage = str(sBody)#.replace("\\n","").replace("\n","").strip()
        jMessage = json.loads(sMessage)
        sNote    = str(w3rkstatt.getJsonValue(path="$.errors.[0].message",data=jMessage)).strip()
        logger.error('CTM: AAPI Error: %s', sNote)
        results = sNote
    return results

def getCtmArchiveJobLog(ctmApiClient,ctmJobID, ctmJobRunCounter):
    # ctm_pwd = w3rkstatt.decrypt(ctm_pwd_sec,"")
    # aapi_client = CtmConnection(host=ctm_host,port=ctm_port, ssl=ctm_ssl, verify_ssl=ctm_ssl_ver,
    #                         user=ctm_user,password=ctm_pwd,
    #                         additional_login_header={'accept': 'application/json'})
    """
    Simple function that uses the get_agents service to get all the agents of the specified Control-M Server.

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.ArchiveApi(api_client=ctmApiClient)
    logger.debug('CTM: AAPI object: %s', ctmCfgAapi)

    # Call CTM AAPI
    results = ""
    try:
        logger.debug('CTM: AAPI Function: %s', "get_archive_job_log")
        results = ctmCfgAapi.get_archive_job_log(ctmJobID, ctmJobRunCounter )
        logger.debug('CTM: AAPI Result: %s', results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: AAPI Function: %s', "get_archive_job_log")
        logger.error('CTM: AAPI Error: %s', exp)
        logger.error('CTM: AAPI Result: %s', results)
        results = {}
        logger.error('CTM: AAPI Continue ....',)
    return results

def getCtmArchiveJobOutput(ctmApiClient,ctmJobID, ctmJobRunId):
    """
    Get job output by unique job key

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.ArchiveApi(api_client=ctmApiClient)
    logger.debug('CTM: AAPI object: %s', ctmCfgAapi)

    # Call CTM AAPI
    results = ""
    try:
        logger.debug('CTM: AAPI Function: %s', "get_archive_job_output")
        results = ctmCfgAapi.get_archive_job_output(job_id=ctmJobID, run_no=ctmJobRunId )
        logger.debug('CTM: AAPI Result: %s', results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: AAPI Function: %s', "get_archive_job_output")
        logger.error('CTM: AAPI Error: %s', exp)
        logger.error('CTM: AAPI Result: %s', results)
        results = {}
        logger.error('CTM: AAPI Continue ....',)
    return results

def getCtmJobLog(ctmApiClient,ctmJobID):
    # ctm_pwd = w3rkstatt.decrypt(ctm_pwd_sec,"")
    # aapi_client = CtmConnection(host=ctm_host,port=ctm_port, ssl=ctm_ssl, verify_ssl=ctm_ssl_ver,
    #                         user=ctm_user,password=ctm_pwd,
    #                         additional_login_header={'accept': 'application/json'})
    """
    Get the job execution log. 

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.RunApi(api_client=ctmApiClient)

    # Call CTM AAPI
    results = ""
    try:            
        results = ctmCfgAapi.get_job_log(ctmJobID )
        if _localDebugAdv: 
            logger.debug('CTM: AAPI Function: %s', "get_archive_job_output")
            logger.debug('CTM: AAPI Result: %s', results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: AAPI Function: %s', "get_job_output")
        sBody = str(exp).split("HTTP response body:")[1]
        sMessage = str(sBody)#.replace("\\n","").replace("\n","").strip()
        jMessage = json.loads(sMessage)
        sNote    = str(w3rkstatt.getJsonValue(path="$.errors.[0].message",data=jMessage)).strip()
        logger.error('CTM: AAPI Error: %s', sNote)
        results = sNote
    return results

def getCtmJobStatus(ctmApiClient, ctmServer, ctmOrderID):
    """
    Simple function that uses the ConfigApi service retrieve the job status.

    :param api_cli: property from CTMConnection object
    :param ctm_server: logical name of the ctm server
    :param order_id: order_id of the job
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """

    # Instantiate the service aapi_client.api_client
    # ctmCfgAapi = ctm.api.config_api.ConfigApi(api_client=ctmApiCli)
    ctmCfgAapi = ctm.api.run_api.RunApi(api_client=ctmApiClient)
    results = ""
    if ctmOrderID == "00000":
        if _localDebugAdv: 
            logger.debug('CTM: Order ID: %s', ctmOrderID)
    else:
        #Call the service
        cmtJobID = ctmServer + ":" + ctmOrderID
        try:
            results  = ctmCfgAapi.get_jobs_status_by_filter(jobid=cmtJobID)
            if len(str(results)) > 0:
                # Tranform to JSON, require result as dict 
                dResults = results.to_dict()
                jResults = w3rkstatt.dTranslate4Json(data=dResults)
                if _localDebugAdv:
                    logger.debug('CTM: API Function: %s', "get_job_status")
                    logger.debug('CTM: API Result: %s', results)
            else:
                jResults = {}
                if _localDebugAdv:
                    logger.debug('CTM: API Function: %s', "get_job_status")                
                    logger.debug('CTM: API Result: %s', "no data")

        except ctm.rest.ApiException as exp:
            logger.error('CTM: AAPI Function: %s', "get_job_output")
            sBody = str(exp).split("HTTP response body:")[1]
            sMessage = str(sBody)#.replace("\\n","").replace("\n","").strip()
            jMessage = json.loads(sMessage)
            sNote    = str(w3rkstatt.getJsonValue(path="$.errors.[0].message",data=jMessage)).strip()
            logger.error('CTM: AAPI Error: %s', sNote)
            jResults = sNote

    return jResults

def getCtmAgentStatus(ctmApiClient,ctmAgent):

    ctmAgentInfo = getCtmAgents(ctmApiClient, ctm_server)
    # ctmAgentInfoJson = json.loads(ctmAgentInfo)
    ctmAgentStatus = w3rkstatt.jsonExtractValues(ctmAgentInfo,"status")
    return ctmAgentStatus

def getCtmConnection():
    ctm_pwd_decrypted  = w3rkstatt.decryptPwd(data=ctm_pwd,sKeyFileName=cryptoFile)
    ctmApiCli = CtmConnection(host=ctm_host,port=ctm_port, ssl=ctm_ssl, verify_ssl=ctm_ssl_ver,
                            user=ctm_user,password=ctm_pwd_decrypted,
                            additional_login_header={'accept': 'application/json'})    
    return ctmApiCli

def delCtmConnection(ctmApiObj): 
    ctmApiObj.logout()
        
def ctmTest(ctmApiClient):
    ctmReportInfo   = runCtmReport(ctmApiClient=ctmApiClient,ctmReportName=ctm_rpt_jsm)
    ctmReportID     = w3rkstatt.jsonExtractSimpleValue(ctmReportInfo,"id")
    ctmReportInfo   = getCtmReportStatus(ctmApiClient=ctmApiClient,ctmReportID=ctmReportID)
    ctmReportStatus = w3rkstatt.jsonExtractSimpleValue(ctmReportInfo,"status")

    while (ctmReportStatus == "PROCESSING") or (ctmReportStatus == "PENDING") or (ctmReportStatus != "SUCCEEDED"):
        ctmReportInfo   = getCtmReportStatus(ctmApiClient=ctmApiClient,ctmReportID=ctmReportID)
        ctmReportStatus = w3rkstatt.jsonExtractSimpleValue(ctmReportInfo,"status")
        time.sleep(10)

    # ToDo: Review loop
    # max_attempts = 6
    # attempts = 0
    # sleeptime = 10 #in seconds, no reason to continuously try if network is down
    # while attempts < max_attempts:
    #     time.sleep(sleeptime)
    #     try:
    #         ctmReportInfo   = getCtmReportStatus(ctmApiClient=ctmApiClient,ctmReportID=ctmReportID)
    #         ctmReportStatus = w3rkstatt.jsonExtractSimpleValue(ctmReportInfo,"status")
    #         if (ctmReportStatus == "SUCCEEDED"):
    #             break
    #     except:
    #         attempts += 1
    #         logger.debug('CTM: Report Status Loop: %s', attempts)

    ctmReportUrl  = w3rkstatt.jsonExtractSimpleValue(ctmReportInfo,"url")
    ctmReportData = getCtmReportData(ctmReportUrl)
    ctmReportJson = w3rkstatt.convertCsv2Json(data=ctmReportData,keepDuplicate="last")

    logger.info('CTM Report ID: %s', ctmReportID)
    logger.info('CTM Report Status: %s', ctmReportStatus)
    logger.info('CTM Report Url: %s', ctmReportUrl)
    logger.info('CTM Report JSON: %s', ctmReportJson)

    return 
    
def runCtmReport(ctmApiClient,ctmReportName):
    """
    Simple function that uses the ABC service to get a the report of the specified Control-M Server.

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """
    # Instantiate the AAPI object
    ctmRptAapi = ctm.api.reporting_api.ReportingApi(api_client=ctmApiClient)
    logger.debug('CTM: API object: %s', ctmRptAapi)
    ctmReportRun = ctm.RunReport(name=ctmReportName,format="csv") # RunReport | The report generation parameters
    # Call CTM AAPI
    try:
        logger.debug('CTM: API Function: %s', "RunReport")
        results = ctmRptAapi.run_report(body=ctmReportRun,async_req=True,_return_http_data_only=True)

        ctmRptInfo   = results.get()
        ctmRptId     = ctmRptInfo.report_id
        ctmRptName   = ctmRptInfo.name
        ctmRptStatus = ctmRptInfo.status

        logger.debug('CTM: Report ID: %s', ctmRptId)
        logger.debug('CTM: Report Name: %s', ctmRptName)
        logger.debug('CTM: Report Status: %s', ctmRptStatus)

        report_data = {}
        report_data['type'] = "CTM Report Info"
        report_data['id'] = ctmRptId
        report_data['name'] = ctmRptName
        report_data['status'] = ctmRptStatus
        json_data = json.dumps(report_data)
        logger.debug('CTM: Report JSON: %s', json_data)        

    except ctm.rest.ApiException as exp:
        logger.error('CTM: API Error: %s', exp)
    return json_data

def getCtmReportStatus(ctmApiClient,ctmReportID):
    """
    Simple function that uses the ABC service to get a the report of the specified Control-M Server.

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """
    # Instantiate the AAPI object
    ctmRptAapi = ctm.api.reporting_api.ReportingApi(api_client=ctmApiClient)
    logger.debug('CTM: API object: %s', ctmRptAapi)
    # Call CTM AAPI
    try:
        logger.debug('CTM: API Function: %s', "RunReport")
        results = ctmRptAapi.get_report_status(report_id=ctmReportID,_return_http_data_only=True)

        ctmRptInfo   = results
        ctmRptId     = ctmRptInfo.report_id
        ctmRptName   = ctmRptInfo.name
        ctmRptFormat = ctmRptInfo.format
        ctmRptUrl    = ctmRptInfo.url
        ctmRptStatus = ctmRptInfo.status

        logger.debug('CTM: Report ID: %s', ctmRptId)
        logger.debug('CTM: Report Status: %s', ctmRptStatus)

        report_data = {}
        report_data['type'] = "CTM Report Info"
        report_data['id'] = ctmRptId
        report_data['name'] = ctmRptName
        report_data['format'] = ctmRptFormat
        report_data['url'] = ctmRptUrl
        report_data['status'] = ctmRptStatus
        json_data = json.dumps(report_data)
        logger.debug('CTM: Report JSON: %s', json_data)        

    except ctm.rest.ApiException as exp:
        logger.error('CTM: API Error: %s', exp)
    return json_data

def getCtmReportData(ctmReportUrl):
  url = ctmReportUrl

  # Create a dictionary for the request body
  request_body = {}

  # Load the request body into the payload in JSON format.
  payload = json.dumps(request_body)
  headers = {
      'content-type': "application/json",
      'cache-control': "no-cache" ,
  }

  logger.debug('HTTP API Url: %s', url)
  logger.debug('HTTP Headers: %s', headers)
  logger.debug('HTTP Payload: %s', payload)

  # Execute the API call.
  try:
    response = requests.get(url, data=payload, headers=headers, verify=False)
  except requests.RequestException as e:
    logger.error('HTTP Response Error: %s', e)

  # Capture the authentication token
  rsc = response.status_code
  if rsc == 501:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc != 200:
    logger.error('HTTP Response Status: %s', rsc)
  elif rsc == 200:
    csv_data = response.text
    # logger.debug('CTM: Report Data: %s', csv_data)
    return csv_data
  else:
      logger.error('HTTP Response Code: %s', response)
      # exit()

def getCtmHostGroupMembers(ctmApiClient,ctmServer,ctmHostGroup):
    """
    Simple function that uses the get_agents service to get all the agents of the specified Control-M Server.

    :param api_client: property from CTMConnection object
    :return: list of named tuple: [{'key': 'value'}] access as list[0].key
    """

    # Instantiate the AAPI object
    ctmCfgAapi = ctm.api.config_api.ConfigApi(api_client=ctmApiClient)
    logger.debug('CTM: API object: %s', ctmCfgAapi)
    results = ""

    # Call CTM AAPI
    try:
        logger.debug('CTM: API Function: %s', "get_hosts_in_group")
        results = ctmCfgAapi.get_hosts_in_group(server=ctmServer, hostgroup=ctmHostGroup , _return_http_data_only=True )
        results = str(results).replace("'",'"')
        logger.debug('CTM: API Result: %s', results)
        results = json.loads(results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: API Error: %s', exp)
    return results

def getCtmJobInfo(ctmApiClient, ctmServer, ctmOrderID):
    ctmJobInfo = getCtmJobStatus(ctmApiClient=ctmApiClient, ctmServer=ctmServer, ctmOrderID=ctmOrderID)
    if _localQA: 
        logger.info('CMT QA Get Job Status: %s', ctmJobInfo)

    # Get counter of CTM Job Info
    ctmJobId   = ctmServer + ":" + ctmOrderID
    jPath      = "$.statuses[?(@.job_id=='" + ctmJobId + "')]"
    jData      = json.loads(ctmJobInfo)
    jRecords   = int(w3rkstatt.getJsonValue(path="$.total",data=jData))
    sStatus    = False
    iCounter   = None

    # Assign default
    jJobInfo  = '{"count":' +  str(None) + '}'

    if jRecords >= 1:
        sStatus  = True
        iCounter = int(jRecords)
        # Extract CTM Job Info
        jJobInfo  = w3rkstatt.getJsonValue(path=jPath,data=jData)
        # beutify job info
        for (key, value) in jJobInfo.items():
            if key == "start_time":
                if value is not None or not "None" in str(value):
                    value = extractCtmAlertDate(data=value)
                jJobInfo[key] = value         
            if key == "end_time":
                if value is not None or not "None" in str(value):
                    value = extractCtmAlertDate(data=value)
                jJobInfo[key] = value    
            if key == "estimated_end_time":
                if value is not None or not "None" in str(value):
                    value = value[0]
                    value = extractCtmAlertDate(data=value)
                jJobInfo[key] = value  
            if key == "estimated_start_time":
                if value is not None or not "None" in str(value):
                    value = value[0]
                    value = extractCtmAlertDate(data=value)
                jJobInfo[key] = value                          
            if key == "order_date":
                if value is not None or not "None" in str(value):
                    value = extractCtmOrderDate(data=value)
                jJobInfo[key] = value     

        jJobInfo["count"] = len(jJobInfo)
    
    elif jRecords == 0:
        sStatus   = True
        iCounter  = 0
        jJobInfo  = ctmJobInfo


    xData = '{"count":' + str(iCounter) + ',"status":' + str(sStatus) + ',"entries":[' + str(jJobInfo) + ']}'   
    sData = w3rkstatt.dTranslate4Json(data=xData)
    # jData = json.loads(sData)

    if _localDebugAdv: 
        logger.debug('CTM Job Info: %s', sData)

    return sData

def getCtmJobStatusAdv(ctmApiClient, ctmServer, ctmOrderID):
    ctmJobStatus = {}
    ctmJobStatuses = getCtmJobStatus(ctmApiClient=ctmApiClient, ctmServer=ctmServer, ctmOrderID=ctmOrderID)
    ctmJobStatusList =  json.loads(ctmJobStatuses)

    
    ctmJobs = ctmJobStatusList["statuses"]
    ctmJobIDTemp = ctmServer + ":" + ctmOrderID

    if ctmJobs:
        for ctmJob in ctmJobs:
            ctmJobApp  = ctmJob["application"]
            ctmJobID   = ctmJob["job_id"]
            
            if ctmJobID == ctmJobIDTemp:
                ctmJobStatus = w3rkstatt.jsonTranslateValues(ctmJob)
                ctmFolder    = ctmJob["folder"]
                logger.debug('CTM: Job Application: "%s"', ctmJobApp)
                logger.debug('CTM: Job ID: "%s"', ctmJobID)
                logger.debug('CTM: Job Folder: "%s"', ctmFolder)
                logger.debug('CTM: Job Status: %s', ctmJobStatus)

    return ctmJobStatus

def getCtmDeployedFolder(ctmApiClient, ctmServer, ctmFolder):
    """Get deployed jobs that match the search criteria.  # noqa: E501
        Get definition of jobs and folders (in the desired format - JSON or XML) that match the requested search criteria.  # noqa: E501
        This method makes a synchronous HTTP request by default. To make an
        asynchronous HTTP request, please pass async_req=True

        :param async_req bool
        :param str format: Output format (json or xml)
        :param str folder:
        :param str ctm:
        :param str server:
        :return: str
                 If the method is called asynchronously,
                 returns the request thread.
        """
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.DeployApi(api_client=ctmApiClient)
    if _localDebugAdv: 
        logger.debug('CTM: AAPI object: %s', ctmCfgAapi)

    # Call CTM AAPI
    results = ""
    try:    
        results = ctmCfgAapi.get_deployed_folders_new(format="json",folder=ctmFolder,server=ctmServer)
        if _localDebugAdv: 
            logger.debug('CTM: AAPI Function: %s', "get_deployed_folders_new")
            logger.debug('CTM: AAPI Result: %s', results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: AAPI Function: %s', "get_job_output")
        sBody = str(exp).split("HTTP response body:")[1]
        sMessage = str(sBody)#.replace("\\n","").replace("\n","").strip()
        jMessage = json.loads(sMessage)
        sNote    = str(w3rkstatt.getJsonValue(path="$.errors.[0].message",data=jMessage)).strip().replace('"',"")
        logger.error('CTM: AAPI Error: "%s"', sNote)
        results = sNote
    return results

def translateCtmAlertStatus (data):   
    # http://documents.bmc.com/supportu/9.0.19/help/Main_help/en-US/index.htm#45731.htm
    if "Not_Noticed" in data:
        value = "OPEN"
    elif  "Noticed" in data:
        value = "ACK"
    elif "Handled" in data:
        value = "CLOSED"
    else:
        value = "OPEN"
    
    return value 

def translateCtmAlertSeverity (data):
    # https://docs.bmc.com/docs/display/tsim107/Understanding+event+states
    if "R" in data:
        value = "INFO"
    elif  "U" in data:
        value = "MAJOR"
    elif "V" in data:
        value = "CRITICAL"
    else:
        value = "INFO"
    
    return value

def translateCtmAlertOpCat3 (data):
    if "Ended not OK" in data:
        value = "Failed Job"
    else:
        value = "Information"
    
    return value

def translateCtmAlertUpdateType (data):   
    # http://documents.bmc.com/supportu/9.0.19/help/Main_help/en-US/index.htm#45731.htm
    if "I" in data:
        value = "New"
    elif  "U" in data:
        value = "Update"
    else:
        value = "New"
    
    return value 

def extractCtmAlertId(data):
    jsonEvent = data
    value = ""
    if "run_counter" in jsonEvent:
        value = jsonEvent['alert_id']  

    ctmAlertId = value
    return ctmAlertId

def extractCtmAlertType (data):   
    # http://documents.bmc.com/supportu/9.0.19/help/Main_help/en-US/index.htm#45731.htm
    if "R" in data:
        value = "Regular"
    elif  "B" in data:
        value = "BMC Batch Impact Manager"
    else:
        value = "Regular"
    
    return value

def extractCtmAlertDate (data):
    # 2020-05-26 22:57:36
    sYear   = data[0:4]
    sMonth  = data[4:6]
    sDay    = data[6:8]
    sHour   = data[8:10]
    sMin    = data[10:12]
    sSec    = data[12:]
    sDate   = sYear + "-" + sMonth + "-" + sDay  + " " + sHour + ":" + sMin + ":" + sSec
    return sDate

def extractCtmDate (data):
    # 2020-05-26 22:57:36
    sYear   = data[0:4]
    sMonth  = data[4:6]
    sDay    = data[6:8]
    sHour   = data[8:10]
    sMin    = data[10:12]
    sDate   = sYear + "-" + sMonth + "-" + sDay  + " " + sHour + ":" + sMin 
    return sDate

def extractCtmAlertCal (data):
    # 20200525
    sDate   = data[0:8]
    return sDate

def extractCtmAlertDataCenter(data):
    jsonEvent = data
    value = ""
    if "data_center" in jsonEvent:
        value = jsonEvent['data_center']   
    return value

def extractCtmOrderDate (data):
    # 2020-05-26 22:57:36
    sYear   = data[0:2]
    sMonth  = data[2:4]
    sDay    = data[4:6]
    sDate   = "20" + sYear + "-" + sMonth + "-" + sDay
    return sDate

def trasnformtCtmAlert(data):
    alias = None
    cdmclass = "BMC_ApplicationService"
    ctmJobRunId = None
    ctmOrderId = None
    ctmJobId = None
    ctmJobPlatform = None
    ctmJobScript = None
    data_center_ip = None
    data_center_fqdn = None
    data_center_dns = None
    host_ip = None
    host_ip_fqdn = None
    host_ip_dns = None
    summary = None
    notes = None
    sAgentStatus = None
    sDataCenterStatus = None
    ctmUpdateDate = None
    sAlertCat = None
    sSystemStatus = None
    
    

    jCtmAlert = data
    ctmDataCenter = w3rkstatt.getJsonValue(path="$.data_center",data=jCtmAlert)
    for (key, value) in jCtmAlert.items():
        
        if key == "call_type":
            value = translateCtmAlertUpdateType(data=value)
            jCtmAlert[key] = value
        if key == "send_time":
            data = value
            value = extractCtmAlertDate(data=data)
            jCtmAlert[key] = value
            ctmUpdateDate = extractCtmAlertCal(data)
        if key == "last_time":
            if value is not None:
                data = value
                value = extractCtmAlertDate(data=data)
                jCtmAlert[key] = value
                ctmUpdateDate = extractCtmAlertCal(data)
        # Mainframe job type
        if key == "memname":
            if value is not None:
                logger.debug('CTM Alert Entry: %s=%s' , key,value)
                if value == "None":
                    ctmJobScript = None
                elif value != "None": 
                    ctmJobScript = value


        # X-Alert
        if key == "Xtime":
            value = extractCtmAlertDate(data=value)
            jCtmAlert[key] = value
            sAlertCat = "infrastructure"
        if key == "Xtime_of_last":
            value = extractCtmAlertDate(data=value)
            jCtmAlert[key] = value            
 
 
 
        if key == "alert_type":
            value = extractCtmAlertType(data=value)
            jCtmAlert[key] = value
        if key == "severity":
            value = translateCtmAlertSeverity(data=value)
            jCtmAlert[key] = value      
        if key == "status":
            value = translateCtmAlertStatus(data=value)
            jCtmAlert[key] = value        
        if key == "run_counter":
             if value is not None:
                ctmOrderId    = w3rkstatt.getJsonValue(path="$.order_id",data=jCtmAlert)
                ctmJobId      = ctmDataCenter + ":" + ctmOrderId
        if key == "data_center":
            # get data center details from config josn
            # $.CTM.datacenter[?(@.name=='bmcbzos')].host
            jQl              = "$.CTM.datacenter[?(@.name=='" + str(value) + "')].host" 
            data_center      = w3rkstatt.getJsonValue(path=jQl,data=jCfgData)
            if len(data_center) > 1:
                data_center_ip   = w3rkstatt.getHostIP(hostname=data_center)
                data_center_fqdn = w3rkstatt.getHostFqdn(hostname=data_center)
                data_center_dns  = w3rkstatt.getHostDomain(hostname=data_center)
            else:
                data_center_ip   = None
                data_center_fqdn = None
                data_center_dns  = None
        if key == "host_id":
            if value is not None:
                if len(value) > 0:
                    host_ip = w3rkstatt.getHostIP(hostname=value)
                    host_ip_fqdn = w3rkstatt.getHostFqdn(hostname=value)
                    host_ip_dns  = w3rkstatt.getHostDomain(hostname=value)

        if key == "Component_machine":
            host_ip = w3rkstatt.getHostIP(hostname=value)
            host_ip_fqdn = w3rkstatt.getHostFqdn(hostname=value)
            host_ip_dns  = w3rkstatt.getHostDomain(hostname=value)
            alias = cdmclass + ":" + value  + ":" + host_ip_dns

        if key == "message":
            if "STATUS OF AGENT PLATFORM" in value:
                sTemp = value.split()
                host_name = sTemp[4]
                host_ip = w3rkstatt.getHostIP(hostname=host_name)
                host_ip_fqdn = w3rkstatt.getHostFqdn(hostname=host_name)
                host_ip_dns  = w3rkstatt.getHostDomain(hostname=host_name)
                alias = cdmclass + ":" + host_name  + ":" + host_ip_dns
                sAgentStatus = sTemp[7]
                sAlertCat = "agent"
            elif "DATA CENTER" in value:
                sTemp = value.split()
                host_name = sTemp[2]
                host_ip = w3rkstatt.getHostIP(hostname=host_name)
                host_ip_fqdn = w3rkstatt.getHostFqdn(hostname=host_name)
                host_ip_dns  = w3rkstatt.getHostDomain(hostname=host_name)
                alias = cdmclass + ":" + host_name  + ":" + host_ip_dns
                sDataCenterStatus = sTemp[4]
                sAlertCat = "datacenter"
            elif "Distributed Control-M/EM Configuration Agent" in value:
                sTemp = value.split()
                host_name = sTemp[2]
                host_ip = w3rkstatt.getHostIP(hostname=host_name)
                host_ip_fqdn = w3rkstatt.getHostFqdn(hostname=host_name)
                host_ip_dns  = w3rkstatt.getHostDomain(hostname=host_name)
                alias = cdmclass + ":" + host_name  + ":" + host_ip_dns
                # sCtmComponenttatus = sTemp[4]
                sAlertCat = "infrastructure"                
            elif "Ended not OK" in value:
                ctmOrderId    = w3rkstatt.getJsonValue(path="$.order_id",data=jCtmAlert)
                ctmJobRunId   = ctmDataCenter + ":" + ctmOrderId
                job_name      = w3rkstatt.getJsonValue(path="$.job_name",data=jCtmAlert)
                run_counter   = w3rkstatt.getJsonValue(path="$.run_counter",data=jCtmAlert)
                summary  = "Job " + job_name + " failed"
                notes = "CTRL-M Job " + job_name + " failed. Job ID: " + ctmJobRunId + " with Job Run Count: " + run_counter
                sAlertCat = "job"
                sSystemStatus = "failed"
            elif "Failed to order" in value:
                ctmOrderId    = w3rkstatt.getJsonValue(path="$.order_id",data=jCtmAlert)
                ctmJobRunId   = ctmDataCenter + ":" + ctmOrderId
                job_name      = w3rkstatt.getJsonValue(path="$.job_name",data=jCtmAlert)
                run_counter   = w3rkstatt.getJsonValue(path="$.run_counter",data=jCtmAlert)

                if job_name is None:
                    summary = value
                    notes = "CTRL-M Job failed. Job ID: " + ctmJobRunId + " with Job Run Count: " + run_counter
                else:
                    summary  = "Job " + job_name + " failed"
                    notes = "CTRL-M Job " + job_name + " failed. Job ID: " + ctmJobRunId + " with Job Run Count: " + run_counter
                sAlertCat = "job"
                sSystemStatus = "failed"
            elif "BIM / SIM" in value:
                ctmOrderId    = w3rkstatt.getJsonValue(path="$.order_id",data=jCtmAlert)
                ctmJobRunId   = ctmDataCenter + ":" + ctmOrderId
                job_name      = w3rkstatt.getJsonValue(path="$.job_name",data=jCtmAlert)
                run_counter   = w3rkstatt.getJsonValue(path="$.run_counter",data=jCtmAlert)

                if job_name is None:
                    summary = value
                    notes = "CTRL-M Job failed. Job ID: " + ctmJobRunId + " with Job Run Count: " + run_counter
                else:
                    summary  = "Job " + job_name + " failed"
                    notes = "CTRL-M Job " + job_name + " failed. Job ID: " + ctmJobRunId + " with Job Run Count: " + run_counter
                sAlertCat = "job"
                sSystemStatus = "failed"                
            else:
                summary = value
                notes = value

        if key == "Message":
                summary  = value
                notes = "CTRL-M Component " + value + ". Managed by: " + host_ip_dns
                
              
                

    if not ctmOrderId == "00000" and  ctmOrderId is not None:
        job_uri =  "https://" + ctm_host + ":" + ctm_port + "/ControlM/#Search:id=Search_2&search=" + ctmOrderId + "&date=" + ctmUpdateDate + "&controlm=" + ctmDataCenter
        jCtmAlert["job_id"] = ctmJobId
        jCtmAlert["job_uri"] = job_uri


    if sAgentStatus is not None:
        if "UNAVAILABLE" in sAgentStatus:
            jCtmAlert["severity"] =  "MAJOR"
            summary  = "Agent on " + host_name + " not availabble"
            notes = "CTRL-M Agent on " + host_ip_fqdn + " down or not availabble. Managed by: " + ctmDataCenter
            sSystemStatus = "unavailabble"

        elif "AVAILABLE" in sAgentStatus:
            jCtmAlert["severity"] =  "OK"
            summary  = "Agent on " + host_name + " availabble"
            notes = "CTRL-M Agent on " + host_ip_fqdn + " availabble. Managed by: " + ctmDataCenter  
            sSystemStatus = "availabble"

    if sDataCenterStatus is not None:
        if "DISCONNECTED" in sDataCenterStatus:
            jCtmAlert["severity"] =  "CRITICAL"
            summary  = "Data Center " + ctmDataCenter + " was disconnected"
            notes = "CTRL-M Data Center " + ctmDataCenter + " on " + host_ip_fqdn + " down or disconnected."
            sSystemStatus = "disconnected"
        elif "CONNECTED" in sDataCenterStatus:
            jCtmAlert["severity"] =  "OK"
            summary  = "Data Center on " + host_name + " availabble"
            notes = "CTRL-M Data Center " + ctmDataCenter + " on " + host_ip_fqdn + " availabble or connected."
            sSystemStatus = "connected"

    jCtmAlert["data_center_ip"] = data_center_ip
    jCtmAlert["data_center_fqdn"] = data_center_fqdn
    jCtmAlert["data_center_dns"] = data_center_dns
    jCtmAlert["host_ip"] = host_ip
    jCtmAlert["host_ip_fqdn"] = host_ip_fqdn
    jCtmAlert["host_ip_dns"] = host_ip_dns
    jCtmAlert["system_category"] = sAlertCat
    jCtmAlert["system_status"] = sSystemStatus
    jCtmAlert["system_class"] = alias
    jCtmAlert["job_script"] = ctmJobScript
    
    
    # CTM Agent issues
    jCtmAlert["message_summary"] = summary
    jCtmAlert["message_notes"] = notes

    jCtmAlert = OrderedDict(sorted(jCtmAlert.items()))

    for (key, value) in jCtmAlert.items():
        if _localDebugAdv: 
            logger.debug('CTM Alert Entry: %s=%s' , key,value)

    # Tweak final json
    jCtmAlertData = json.dumps(jCtmAlert)
    tCtmAlertData = w3rkstatt.jsonTranslateValues(jCtmAlertData)
    xCtmAlertData = json.loads(tCtmAlertData)
    jCtmAlert     = jCtmAlertData
    
    return jCtmAlert

def transformCtmJobStatus(data):
    pass
        
def transformCtmJobOutput(data):
    jValue = {}
    s = "\n"
    xList = [s for s in data.splitlines(True) if s.strip("\r\n")]
    yList = list(map(str.strip,xList))
    sStatus = False

    i = 0
    for item in yList:
        jValue["entry-" + str(i).zfill(4)] = item.replace("'","")
        i += 1

    # {"count":2,"entries":[{"entry-0000": "Request  rejected by Data Center", "entry-0001": "ECS3010 USER NOT AUTHORIZED"}]}
    xValue   = json.dumps(jValue)
    iCounter = int(len(jValue)) 

    if iCounter == 0:
        sStatus = None
    elif iCounter == 1:
        sY1 = yList[0]
        if "Failed" in sY1:
            sStatus = False
    elif iCounter == 2:
        sY1 = yList[0]
        sY2 = yList[1]
        if "rejected" in sY1 and "USER NOT AUTHORIZED" in sY2:
            sStatus = False
        else:
            sStatus = True
    else:
        sStatus = True
    
    xData = '{"count":' + str(iCounter) + ',"status":' + str(sStatus) + ',"entries":[' + str(xValue) + ']}'   
    sData = w3rkstatt.dTranslate4Json(data=xData)
    jData = json.loads(sData)
            
    if _localDebugAdv: 
        logger.debug('CMT Job Output Transform Raw: %s', sData)
  
    return jData
  

def transformCtmJobLog(data):
    lgo = []
    log_list = []
    jValue = {}
    s = "\n"
    xList = [s for s in data.splitlines(True) if s.strip("\r\n")]
    yList = list(map(str.strip,xList))
    sJobLogStatus = False


    i = 0
    # Extract Data from line
    # 12:48:07 2-Apr-2021  ORDERED JOB:24; DAILY FORCED, ODATE 20210402   	5065
    for item in yList:
        log_data = {}

        sTemp    = re.split(r'\s{2,}', item)
        sTime    = item.split()[0]
        sDate    = item.split()[1]
        sMessage = sTemp[1].split("\t")[0]
        sCtmCode =  item.split("\t")[1]

        if sCtmCode == "5100":
            xTemp = sMessage.split()
            log_data['oscompstat'] = xTemp[4].replace(".","")
            log_data['run_count'] = xTemp[6]
            log_data['ended'] = extractCtmAlertDate (data=xTemp[2].replace(".",""))
                   
        log_data['time'] = sTime
        log_data['date'] = sDate
        log_data['message'] = sMessage
        log_data['code'] = sCtmCode

        log_wrapper = {}
        log_wrapper['entry-' + str(i).zfill(4)] = log_data
        log_list.append(log_wrapper)
        i += 1

    # Convert event data to the JSON format required by the API.
    jData = json.dumps(log_list)
    if i == 0:
        sJobLogStatus = None
        jData = '{"count":0,"status":' + str(sJobLogStatus) + ',"entries":[]}'
    else:
        sJobLogStatus = True
        jData = '{"count":' + str(i) + ',"status":' + str(sJobLogStatus) + ',"entries":[' + str(jData) + ']}'    

    # json_data = json.dumps(log_list)
    jStatus = w3rkstatt.jsonValidator(data=jData)
    if jStatus:   
        jData = json.loads(jData)
        return jData
    else:
        jData = '{"count":1,"status":' + str(sJobLogStatus) + ',"entries":[' + str(jData) + ']}'
        sData = w3rkstatt.dTranslate4Json(data=jData)
        return sData

def transformCtmJobLogMini(data,runCounter):
    ctmJobRunCounter = runCounter.strip("0")
    log_list = []
    jValue = {}
    s = "\n"
    xList = [s for s in data.splitlines(True) if s.strip("\r\n")]
    yList = list(map(str.strip,xList))
    sStatus  = yList[0]
    sJobLogStatus = False

    i = 0
    # Extract Data from line
    # 12:48:07 2-Apr-2021  ORDERED JOB:24; DAILY FORCED, ODATE 20210402   	5065
    for item in yList:
        log_data = {}

        sTemp    = re.split(r'\s{2,}', item)
        sTime    = item.split()[0]
        sDate    = item.split()[1]

        if "Failed to get job log" in sStatus:
            sMessage = sTemp[0]
            # Build JSON
            # log_wrapper = {}
            # log_wrapper['entry-' + str(i).zfill(4)] = sMessage
            # log_list.append(log_wrapper)

            # construct json string
            if i == 0:
                sEntry = '"entry-' + str(i).zfill(4) + '":"' +  sMessage + '"'
            else:
                sEntry = sEntry + ',"entry-' + str(i).zfill(4) + '":"' +  sMessage + '"'

            i += 1
        else:
            sJobLogStatus = True
            sMessage = sTemp[1].split("\t")[0]
            sCtmCode =  item.split("\t")[1]

            if sCtmCode == "5100":
                xTemp = sMessage.split()
                zTemp = xTemp[6]
                if zTemp == ctmJobRunCounter:
                    log_data['oscompstat'] = xTemp[4].replace(".","")
                    log_data['run_count'] = xTemp[6]
                    log_data['ended'] = extractCtmAlertDate (data=xTemp[2].replace(".",""))                   
                    log_data['time'] = sTime
                    log_data['date'] = sDate
                    log_data['message'] = sMessage
                    log_data['code'] = sCtmCode

                    # Build JSON
                    log_wrapper = {}
                    log_wrapper['entry-' + str(i).zfill(4)] = log_data
                    log_list.append(log_wrapper)
                
                i += 1

    # custom json in case no access to CTM API
    if sJobLogStatus:
        xData = json.dumps(log_list)
        jData = '{"count":' + str(i) + ',"status":' + str(sJobLogStatus) + ',"entries":[' + str(xData) + ']}'
    else:
        xData = '{' + sEntry + '}'
        jData = '{"count":' + str(i) + ',"status":' + str(sJobLogStatus) + ',"entries":[' + str(xData) + ']}'
    
    sData = w3rkstatt.dTranslate4Json(data=jData)

    return sData

def updateCtmAlertCore(ctmApiClient,ctmAlertIDs, ctmAlertComment, ctmAlertUrgency="Normal"):
    """Update alert.  # noqa: E501
    Update alert.  # noqa: E501
    This method makes a synchronous HTTP request by default. To make an
    asynchronous HTTP request, please pass async_req=True

    :param async_req bool
    :param AlertParam body: File that contains the alert propery that want to be update. (required)
    :return: SuccessData
                If the method is called asynchronously,
                returns the request thread.
    """
    # https://docs.bmc.com/docs/automation-api/monthly/run-service-989443409.html#Runservice-alerts_updaterunalerts::update
    sCtmAlertData = '{"alertIds":[' + ctmAlertIDs + '],"urgency":"' + ctmAlertUrgency + '","comment":"' + ctmAlertComment + '"}'
    sCtmAlertData = json.loads(sCtmAlertData)
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.api.run_api.RunApi(api_client=ctmApiClient)
    results = ""

    # Call CTM AAPI
    try:
        results = ctmCfgAapi.update_alert(body=sCtmAlertData,_return_http_data_only=True )
        results = str(results).replace("'",'"')
        results = str(results).replace("None",'"None"')
        if _localDebugAdv:
            logger.debug('CTM: API Function: %s', "update_alert")
            logger.debug('CTM: API Result:\n%s', results)
        results = json.loads(results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: API Error: %s', exp)
    return results    

def updateCtmAlertStatus(ctmApiClient,ctmAlertIDs, ctmAlertStatus="Reviewed"):
    """Update alert.  # noqa: E501
    Update alert.  # noqa: E501
    This method makes a synchronous HTTP request by default. To make an
    asynchronous HTTP request, please pass async_req=True

    :param async_req bool
    :param AlertParam body: File that contains the alert propery that want to be update. (required)
    :return: SuccessData
                If the method is called asynchronously,
                returns the request thread.
    """
    # https://docs.bmc.com/docs/automation-api/monthly/run-service-989443409.html#Runservice-alerts_status_updaterunalerts:status::update
    sCtmAlertData = '{"alertIds":[' + ctmAlertIDs + '],"status":"' + ctmAlertStatus + '"}'
    sCtmAlertData = json.loads(sCtmAlertData)
    # Instantiate the AAPI object
    ctmCfgAapi = ctm.api.run_api.RunApi(api_client=ctmApiClient)
    results = ""

    # Call CTM AAPI
    try:
        results = ctmCfgAapi.update_alert_status(body=sCtmAlertData,_return_http_data_only=True )
        results = str(results).replace("'",'"')
        results = str(results).replace("None",'"None"')
        if _localDebugAdv:
            logger.debug('CTM: API Function: %s', "update_alert_status")
            logger.debug('CTM: API Result:\n%s', results)
        results = json.loads(results)
    except ctm.rest.ApiException as exp:
        logger.error('CTM: API Error: %s', exp)
    return results   

def updateCtmAlert(ctmApiClient,ctmAlertIDs, ctmAlertComment, ctmAlertUrgency="Normal",ctmAlertStatus="Reviewed"):
    ctmAlertsCore = updateCtmAlertCore(ctmApiClient=ctmApiClient,ctmAlertIDs=ctmAlertIDs, ctmAlertComment=ctmAlertComment, ctmAlertUrgency=ctmAlertUrgency)
    ctmAlertsStatus = updateCtmAlertStatus(ctmApiClient=ctmApiClient,ctmAlertIDs=ctmAlertIDs, ctmAlertStatus=ctmAlertStatus)

    # replace, strip, translate issues
    ctmAlertsStatusMsg = str(w3rkstatt.getJsonValue(path="$.message",data=ctmAlertsStatus)).replace("[","id: ").replace("]","; msg:")
    ctmAlertsCoreMsg   = str(w3rkstatt.getJsonValue(path="$.message",data=ctmAlertsCore)).replace("[","id: ").replace("]","; msg:")

    sCtmAlertData = '{"alert":"' + ctmAlertsCoreMsg + '","status":"' + ctmAlertsStatusMsg + '"}'
    sCtmAlertData = json.loads(sCtmAlertData)
    return sCtmAlertData

def updateCtmITSM(data):
    ctmEventType = w3rkstatt.getJsonValue(path="$.call_type",data=data) 

    jValue = {}
    # For new Incident
    if "New" in ctmEventType:
        jValue["First_Name"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-first",data=jCfgData)
        jValue["Last_Name"] =  w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-last",data=jCfgData)
        jValue["Description"] = w3rkstatt.getJsonValue(path="$.message_summary",data=data)
        jValue["Impact"] = w3rkstatt.getJsonValue(path="$.ITSM.incident.impact",data=jCfgData)
        jValue["Urgency"] = w3rkstatt.getJsonValue(path="$.ITSM.incident.urgency",data=jCfgData)
        jValue["Status"] = w3rkstatt.getJsonValue(path="$.ITSM.incident.status",data=jCfgData)
        jValue["Reported_Source"] = w3rkstatt.getJsonValue(path="$.ITSM.incident.reported-source",data=jCfgData)
        jValue["Service_Type"] = w3rkstatt.getJsonValue(path="$.ITSM.incident.service-type",data=jCfgData)
        jValue["ServiceCI"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.service-ci",data=jCfgData)
        jValue["Assigned_Group"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.assigned-group",data=jCfgData)
        jValue["Assigned_Support_Company"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-company",data=jCfgData)
        jValue["Assigned_Support_Organization"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-organization",data=jCfgData)
        jValue["Categorization_Tier_1"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_1",data=jCfgData)
        jValue["Categorization_Tier_2"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_2",data=jCfgData)
        jValue["Categorization_Tier_3"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_3",data=jCfgData)
        jValue["Product_Categorization_Tier_1"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_1",data=jCfgData)
        jValue["Product_Categorization_Tier_2"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_2",data=jCfgData)
        jValue["Product_Categorization_Tier_3"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_3",data=jCfgData)
        jValue["Product_Name"] = w3rkstatt.getJsonValue(path="$.ITSM.defaults.product_name",data=jCfgData)

    # For worklog entry with incident
    if "Update" in ctmEventType: 
        ctmAlertNotes = str(w3rkstatt.getJsonValue(path="$.notes",data=data))
        ctmAlertStatus = w3rkstatt.getJsonValue(path="$.status",data=data) 

        jValue["Work_Log_Submitter"] = "user"
        jValue["Status"] = "Enabled"
        jValue["Incident_Number"] = w3rkstatt.getJsonValue(path="$.ticket_number",data=data) 
        jValue["Work_Log_Type"] = "Incident Task / Action"
        jValue["View_Access"] = "Public"
        jValue["Secure_Work_Log"] = "No"

        if ctmAlertNotes is not None or "null" in ctmAlertNotes:            
            jValue["Description"] =  ctmAlertStatus + " - Scheduler Notes" 
            jValue["Detailed_Description"] = ctmAlertNotes    
        else:
            jValue["Description"] =  ctmAlertStatus + " - " + w3rkstatt.getJsonValue(path="$.message_summary",data=data) 
            jValue["Detailed_Description"] = w3rkstatt.getJsonValue(path="$.message_notes",data=data)

    
    xValue = json.dumps(jValue)
    logger.debug('CMT Job Output Transform Raw: %s', xValue)
    jStatus = w3rkstatt.jsonValidator(data=xValue)
    if jStatus:   
        return xValue
    else:
        return {'lines': None}

def extractFolderJobDetails(data):
    pass


def demoCTM():
    ctm_demo_agt    = w3rkstatt.getJsonValue(path="$.CTM.ctmag.demo",data=jCfgData)
    ctm_demo_jobs   = w3rkstatt.getJsonValue(path="$.CTM.jobs.demo",data=jCfgData)
    ctm_demo_alerts = w3rkstatt.getJsonValue(path="$.CTM.alerts.demo",data=jCfgData)

    if ctm_demo_alerts:
        ctm_alert_ids = w3rkstatt.getJsonValue(path="$.CTM.alerts.ids",data=jCfgData)
        ctm_alert_msg = w3rkstatt.getJsonValue(path="$.CTM.alerts.comment",data=jCfgData)
        ctm_alert_urgency = w3rkstatt.getJsonValue(path="$.CTM.alerts.urgency",data=jCfgData)
        ctm_alert_status = w3rkstatt.getJsonValue(path="$.CTM.alerts.status",data=jCfgData)

        # Alert Comment
        # ctmAlertsCore   = updateCtmAlertCore(ctmApiClient=ctmApiClient,ctmAlertIDs=ctm_alert_ids, ctmAlertComment=ctm_alert_msg, ctmAlertUrgency=ctm_alert_urgency)
        # logger.info('CTM Alert Core: %s', ctmAlertsCore)
        
        # Alert Status
        ctmAlertsStatus = updateCtmAlertStatus(ctmApiClient=ctmApiClient,ctmAlertIDs=ctm_alert_ids, ctmAlertStatus=ctm_alert_status)
        logger.info('CTM Alert Status: %s', ctmAlertsStatus)
        # ctmAlerts = updateCtmAlert(ctmApiClient=ctmApiClient,ctmAlertIDs=ctm_alert_ids, ctmAlertComment=ctm_alert_msg)
        # ctmAlerts = w3rkstatt.jsonTranslateValues(ctmAlerts)
        


        # logger.info('CTM Alert: %s', ctmAlerts)

    if ctm_demo_agt:
        ctmAgents = getCtmAgents(ctmApiClient=ctmApiClient,ctmServer=ctm_server)
        logger.info('CTM Agents: %s', ctmAgents)
    
    if ctm_demo_jobs:
        ctm_job_oderid  = w3rkstatt.getJsonValue(path="$.CTM.jobs.oderid",data=jCfgData)
        ctm_job_srv     = w3rkstatt.getJsonValue(path="$.CTM.jobs.server",data=jCfgData)
        ctm_job_runid   = ctm_job_srv + ":" + ctm_job_oderid

        ctmJobInfo      = getCtmJobInfo(ctmApiClient=ctmApiClient,ctmServer=ctm_job_srv,ctmOrderID=ctm_job_oderid)
        # ctmJobStatusAdv = getCtmJobStatusAdv(ctmApiClient=ctmApiClient,ctmServer=ctm_job_srv,ctmOrderID=ctm_job_oderid)
        logger.info('CTM Job: %s', ctmJobInfo)


if __name__ == "__main__":

    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('CTM: Workload Management Start')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: %s ', w3rkstatt.platform.system())
    logger.info('Log Level: %s', loglevel)
    logger.info('Host Name: %s', hostName)
    logger.info('Host IP: %s', hostIP)
    logger.info('CTM Url: %s', ctm_url)
    logger.info('CTM User: %s', ctm_user)
    logger.info('Epoch: %s', epoch)

    # Test CTM API login
    ctmApiObj    = getCtmConnection()
    ctmApiClient = ctmApiObj.api_client

    # Demo Integration
    if w3rkstatt.getJsonValue(path="$.DEFAULT.demo",data=jCfgData):
        demoCTM()

    delCtmConnection(ctmApiObj)
    logger.info('CTM: Workload Management End')
    logging.shutdown()
    print (f"Version: {_modVer}")