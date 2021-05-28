#!/usr/bin/python
#Filename: uat.py

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
20210521      Volker Scheithauer    Consolidate test cases
20210527      Volker Scheithauer    Update UAT

"""

# Fix module import issues
import sys
import os, json, logging
import time, datetime

# fix import issues for modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from src import w3rkstatt as w3rkstatt
from src import core_ctm as ctm
from src import core_itsm as itsm
from src import core_tsim as tsim
from src import core_tso as tso
from src import core_smtp as smtp




# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)
smtp_ssl   = w3rkstatt.getJsonValue(path="$.MAIL.ssl",data=jCfgData)

logger   = w3rkstatt.logging.getLogger(__name__) 
logFile  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file",data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
epoch    = time.time()
hostName = w3rkstatt.getHostName()
hostIP   = w3rkstatt.getHostIP(hostName)
hostFqdn = w3rkstatt.getHostFqdn(hostName)
domain   = w3rkstatt.getHostDomain(hostFqdn)


# Assign module defaults
_modVer = "20.21.05.00"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = False
_localDebugAdv = False
_localQA = False


# Helix ITSM Sample data
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
    data2log = w3rkstatt.jsonTranslateValuesAdv(data=data)
    logger.info('ITSM Incident Data: %s ', data2log) 
    result = itsm.createIncident(token,data)
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
    result = itsm.createIncidentWorklog(token,data)
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
                    "TemplateID": itsm.itsm_tmpl_crq               
                }
            } 
    result = itsm.createChange(token,data)
    return result 

# TrueSight Operations MAnager Integration
def tsimDefineEvent():
    # Create a dictionary to hold the attributes for the event.
    # Be sure to use valid slot names as the keys.
    event_data = {}
    event_data['severity'] = 'WARNING'
    event_data['CLASS'] = 'EVENT'
    event_data['msg'] = 'This event was created using the TSOM REST API'
    event_data['cdmclass'] = 'BMC_ComputerSystem'
    event_data['componentalias'] = 'BMC_ComputerSystem:' + hostFqdn + "'"
    event_data['instancename'] = hostFqdn
    event_data['itsm_product_name'] = 'Control-M'
    event_data['mc_host'] = 'ctm-em.trybmc.com'
    event_data['mc_host_address'] = hostIP
    event_data['mc_location'] = domain
    event_data['mc_object'] = 'Job'
    event_data['mc_object_class'] = 'Control-M'
    event_data['mc_origin'] = 'Enterprise Manager'
    event_data['mc_origin_class'] = 'Control-M'
    event_data['mc_tool_id'] = 'epoch=' + str(epoch)
    event_data['mc_tool'] = 'Python Script'
    event_data['mc_tool_rule'] = 'uat.py'
    event_data['mc_tool_uri'] = 'git.io'

    # The TSOM create event call expects a list of events,
    # even for just a single event.
    event_list = []

    # Define the dictionary that wraps each event.
    event_wrapper = {}
    event_wrapper['eventSourceHostName'] = hostFqdn
    event_wrapper['attributes'] = event_data

    # Add the event to the list
    event_list.append(event_wrapper)

    # Convert event data to the JSON format required by the API.
    json_data = json.dumps(event_list)
    logger.debug('TSIM: event json payload: %s', json_data)

    return json_data

def computeCI(data):

    ci_name = data
    ci_attributeMap = {}
    ci_attributeMap['Name'] = ci_name
    ci_attributeMap['CLASS'] = ""
    ci_attributeMap['Description'] = "CTM Application"
    ci_attributeMap['Priority'] = "PRIORITY_5"
    ci_attributeMap['HomeCell'] = tsim.tsim_cell
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

# Demo Control-M
def demoCTM():
    # CTM Login
    try:
        ctmApiObj    = ctm.getCtmConnection()
        ctmApiClient = ctmApiObj.api_client
        _ctmActiveApi    = True
    except:
        _ctmActiveApi = False
        ctmApiClient = None

    # Log CTM login state
    logger.info('CTM Login Status: %s', _ctmActiveApi)

    ctm_demo_agt    = w3rkstatt.getJsonValue(path="$.CTM.ctmag.demo",data=jCfgData)
    ctm_demo_jobs   = w3rkstatt.getJsonValue(path="$.CTM.jobs.demo",data=jCfgData)
    ctm_demo_alerts = w3rkstatt.getJsonValue(path="$.CTM.alerts.demo",data=jCfgData)

    if _ctmActiveApi:
        if ctm_demo_alerts:
            ctm_alert_ids = w3rkstatt.getJsonValue(path="$.CTM.alerts.ids",data=jCfgData)
            ctm_alert_msg = w3rkstatt.getJsonValue(path="$.CTM.alerts.comment",data=jCfgData)
            ctm_alert_urgency = w3rkstatt.getJsonValue(path="$.CTM.alerts.urgency",data=jCfgData)
            ctm_alert_status = w3rkstatt.getJsonValue(path="$.CTM.alerts.status",data=jCfgData)

            # Alert Comment
            # ctmAlertsCore   = updateCtmAlertCore(ctmApiClient=ctmApiClient,ctmAlertIDs=ctm_alert_ids, ctmAlertComment=ctm_alert_msg, ctmAlertUrgency=ctm_alert_urgency)
            # logger.info('CTM Alert Core: %s', ctmAlertsCore)
            
            # Alert Status
            ctmAlertsStatus = ctm.updateCtmAlertStatus(ctmApiClient=ctmApiClient,ctmAlertIDs=ctm_alert_ids, ctmAlertStatus=ctm_alert_status)
            logger.info('CTM Alert Status: %s', ctmAlertsStatus)
            # ctmAlerts = updateCtmAlert(ctmApiClient=ctmApiClient,ctmAlertIDs=ctm_alert_ids, ctmAlertComment=ctm_alert_msg)
            # ctmAlerts = w3rkstatt.jsonTranslateValues(ctmAlerts)
            


            # logger.info('CTM Alert: %s', ctmAlerts)

        if ctm_demo_agt:
            ctm_servers = w3rkstatt.getJsonValues(path="$.CTM.datacenter[*].name",data=jCfgData)
            for server in ctm_servers:
                ctmAgents = ctm.getCtmAgents(ctmApiClient=ctmApiClient,ctmServer=server)
                logger.info('CTM Server: %s', server)
                logger.info('CTM Agents: %s', ctmAgents)
    
        if ctm_demo_jobs:
            ctm_job_oderid  = w3rkstatt.getJsonValue(path="$.CTM.jobs.oderid",data=jCfgData)
            ctm_job_srv     = w3rkstatt.getJsonValue(path="$.CTM.jobs.server",data=jCfgData)
            ctm_job_runid   = ctm_job_srv + ":" + ctm_job_oderid

            ctmJobInfo      = ctm.getCtmJobInfo(ctmApiClient=ctmApiClient,ctmServer=ctm_job_srv,ctmOrderID=ctm_job_oderid)
            # ctmJobStatusAdv = getCtmJobStatusAdv(ctmApiClient=ctmApiClient,ctmServer=ctm_job_srv,ctmOrderID=ctm_job_oderid)
            logger.info('CTM Job: %s', ctmJobInfo)

# Demo Helix ITSM
def demoITSM():
    itsm_demo_crq   = w3rkstatt.getJsonValue(path="$.ITSM.change.demo",data=jCfgData)
    itsm_demo_inc   = w3rkstatt.getJsonValue(path="$.ITSM.incident.demo",data=jCfgData)
    
    authToken    = itsm.authenticate()

    # Demo ITSM Change Integration
    if itsm_demo_crq:
        changeID     = testChangeCreate(token=authToken)
        logger.info('ITSM: Change   ID: "%s"', changeID) 

        crqInfo      = itsm.getChange(token=authToken,change=changeID)
        logger.info('ITSM: Change Info: %s', crqInfo) 

        crqStatus    = itsm.extractChangeState(change=crqInfo)
        logger.info('ITSM: Change State: "%s"', crqStatus) 
    
    # Demo ITSM Incident Integration
    if itsm_demo_inc:
        incidentID   = testIncidentCreate(token=authToken)
        logger.info('ITSM: Incident ID: "%s"', incidentID) 

        incInfo    = itsm.getIncident(token=authToken,incident=incidentID)
        logger.info('ITSM: Incident: %s', incInfo) 

        incStatus  = itsm.getIncidentStatus(token=authToken,incident=incidentID)
        logger.info('ITSM: Incident State: "%s"', incStatus) 

        incWLogStatus = testIncidentWorklog(token=authToken,incident=incidentID)
        logger.info('ITSM: Incident Worklog Status: "%s"', incWLogStatus) 



    itsm.itsmLogout(token=authToken)

# Demo TrueSight Operations Manager Integration
def demoTSIM():
  tsim.tsimAuthenticate()
  # data = "Helix Expert"
  # ci_json = tsimComputeCI(data=data)
  # tsim_data = tsimCreateCI(data=ci_json)

  tsim_data     = tsimDefineEvent()
  tsim_event_id = tsim.tsimCreateEvent(event_data=tsim_data)
  logger.debug('TSIM: event id: %s', tsim_event_id)
  return tsim_event_id

# Demo TrueSight Orchestrator Integration
def demoTSO():
    authToken = tso.authenticate()
    logger.info('TSO Login: %s',  authToken)
    if authToken != None:
        workflow    = w3rkstatt.getJsonValue(path="$.TSO.ctm.wcm",data=jCfgData)
        data        = {
                        "inputParameters": [
                                {
                                    "name": "data",
                                    "value": "test"
                                }
                            ]
                    }

        response  = tso.executeTsoProcess(token=authToken,process=workflow,data=data)
        response  = w3rkstatt.jsonTranslateValues(data=response)
        logger.info('TSO Demo: %s', response)

        response = tso.getTsoModulesAdv(token=authToken)
        response = w3rkstatt.jsonTranslateValues(data=response)
        logger.info('TSO Demo: %s', response)

# Demo E-Mail vi SMTP in HTML format
def demoSMTP():

    email_from = None
    email_from_name = None
    email_rcpt = w3rkstatt.getJsonValue(path="$.MAIL.user",data=jCfgData)
    email_subject = "W3rkstatt Community Python Scripts"
    email_message = "User Acceptance Testing in progress"
    email_data = None
    email_template  = None

    # Create E-Mail Body
    email_html_message = smtp.prepareEmail(eml_from=email_from, eml_from_name=email_from_name, eml_to=email_rcpt, eml_subbject=email_subject, eml_message=email_message, eml_data=email_data,eml_template=email_template)

    # Send E-mail
    if smtp_ssl:
        smtp.sendEmailSmtpSSL(eml_from=email_from, eml_to=email_rcpt, eml_message=email_html_message)
    else:
        smtp.sendEmailSmtp(eml_from=email_from, eml_to=email_rcpt, eml_message=email_html_message)

if __name__ == "__main__":
    
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('W3rkstatt: User Acceptance Test')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: %s ', w3rkstatt.platform.system())
    logger.info('Log Level: %s', loglevel)
    logger.info('Host Name: %s', hostName)
    logger.info('Host IP: %s', hostIP)
    logger.info('CTM Url: %s', ctm.ctm_url)
    logger.info('CTM User: %s', ctm.ctm_user)
    logger.info('Epoch: %s', epoch)

    demoStatusCTM  = w3rkstatt.getJsonValue(path="$.CTM.demo",data=jCfgData)
    demoStatusITSM = w3rkstatt.getJsonValue(path="$.ITSM.demo",data=jCfgData)
    demoStatusTSIM = w3rkstatt.getJsonValue(path="$.TSIM.demo",data=jCfgData)
    demoStatusTSO  = w3rkstatt.getJsonValue(path="$.TSO.demo",data=jCfgData)
    demoStatusSMTP = w3rkstatt.getJsonValue(path="$.MAIL.demo",data=jCfgData)

    # Demo Control-M Integration
    if demoStatusCTM:
        demoCTM()

    # Demo Helix ITSM Integration
    if demoStatusITSM:
        demoITSM()

    # Demo TrueSight Operations Manager Integration
    if demoStatusTSIM:
        demoTSIM()

    # Demo TrueSight ORchestrator Integration
    if demoStatusTSO:
        demoTSO()

    # Demo SMTP Integration
    if demoStatusSMTP:
        demoSMTP()

    logger.info('W3rkstatt: User Acceptance Test')
    logging.shutdown()
    print (f"Version: {_modVer}")