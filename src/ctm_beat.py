#!/usr/bin/env python3
#Filename: ctm_alerts.py

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

Werkstatt Python Core Tools 
Provide core functions for Werkstatt related python scripts

Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20210527      Volker Scheithauer    Tranfer Development from other projects
20211224      Volker Scheithauer    Simplify control-M Alerts, write to local file for use with filebeat

"""

# handle dev environment vs. production 
try:
    import w3rkstatt as w3rkstatt
except:
    # fix import issues for modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstatt


import time, logging
import sys, getopt, platform, argparse
import os, json
from collections import OrderedDict 
import collections
from xml.sax.handler import ContentHandler
from xml.sax import make_parser


# Get configuration from bmcs_core.json

# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)

data_folder = logFolder
ctm_host    = w3rkstatt.getJsonValue(path="$.CTM.host",data=jCfgData)
ctm_port    = w3rkstatt.getJsonValue(path="$.CTM.port",data=jCfgData)

integration_itsm_enabled    = w3rkstatt.getJsonValue(path="$.CTM.itsm.enabled",data=jCfgData)
integration_tsim_enabled    = w3rkstatt.getJsonValue(path="$.CTM.tsim.enabled",data=jCfgData)

# Extract CTM job log & details
# Level: full, mini
ctm_job_log_level           = w3rkstatt.getJsonValue(path="$.CTM.jobs.log_level",data=jCfgData)
ctm_job_detail_level        = w3rkstatt.getJsonValue(path="$.CTM.jobs.detail_level",data=jCfgData)

# Assign module defaults
_localDebug = False
_localDebugAdv = False
_localInfo = False
_localQA = False
_localQAlert = True
_localDebugITSM = False
_modVer = "3.0"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_ctmActiveApi = False

logger   = w3rkstatt.logging.getLogger(__name__) 
logFile  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file",data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel",data=jCfgData)
epoch    = time.time()
hostName = w3rkstatt.getHostName()
hostIP   = w3rkstatt.getHostIP(hostName)
hostFqdn = w3rkstatt.getHostFqdn(hostName)
domain   = w3rkstatt.getHostDomain(hostFqdn)
epoch    = time.time()
parser   = argparse.ArgumentParser(prefix_chars=':')
sUuid    = w3rkstatt.sUuid


def ctmAlert2Dict(list, start, end):    
    """    Converts list to dicts        
    Added start and end to function parms to allow for 0 or 1 start and custom end.        
    first parm is key, second value, and so on.        
    :type lst: list        
    :type start: int        
    :type end: int    
    """    

    # Linux arguments
    # '/opt/ctmexpert/ctm-austin/bmcs_crust_ctm_alert.py', 'call_type:', 'I', 'alert_id:', '208905', 'data_center:', 'psctm', 'memname:', 'order_id:', '00000', 'severity:', 'R', 'status:', 'Not_Noticed', 'send_time:', '20210413165844', 'last_user:', 'last_time:', 'message:', 'STATUS', 'OF', 'AGENT', 'PLATFORM', 'vl-aus-ctm-ap01.ctm.bmc.com', 'CHANGED', 'TO', 'AVAILABLE', 'run_as:', 'sub_application:', 'application:', 'job_name:', 'host_id:', 'alert_type:', 'R', 'closed_from_em:', 'ticket_number:', 'run_counter:', '00000000000', 'notes:'
    res_dct = {}    
    param = None
    value = None
    sAlert = str(list).replace("',","").replace("'","")
    sCustom = ""

    try:
        if w3rkstatt.sPlatform == "Linux":
            if _localDebug:
                # logger.debug('Script Arguments for Linux ')
                # logger.debug('Script Arguments #     = %s ', len(list))
                # logger.debug('Script Arguments Start = %s ', start)
                # logger.debug('Script Arguments End   = %s ', end)    
                # logger.debug('Script Arguments List  = %s ', str(list))  
                logger.debug('Script Arguments Str   = %s ', str(sAlert))           


            for counter in range(start, end):  
                entry = str(list[counter])

                if entry[-1] == ":" :
                    param = list[counter].replace(":", "")
                    sCustom = str(sCustom) + "," + param + ":"
                else:
                    value = str(list[counter]).strip().replace(",", " ")
                    sCustom = str(sCustom) + str(value) + " " 

                # res_dct[param] = value

            sCustom = str(sCustom) # + "'"
            sCustom = sCustom[1:]

            res_dct = dict(item.split(":") for item in sCustom.split(","))

            for (key, value) in res_dct.items():

                    if len(value) < 1:
                        value = None
                    else:
                        value = value.replace('"','').strip()
                        if len(value) < 1:
                            value = None

                    res_dct[key] = value
                    if _localDebug:
                        logger.debug('Arguments %s=%s ', key,value)

        else:

            for counter in range(start, end, 2):  
                list[counter] = list[counter].replace(":", "")
                value = str(list[counter + 1]).strip()
                param = list[counter]
                
                if len(value) < 1:
                    value = None
                if _localDebugAdv:  
                    logger.debug('%s="%s" ', param, value)

                res_dct[param] = value
    except:
        pass

    return res_dct

def analyzeAlert4Job(ctmApiClient, raw, data):
    if _localInfo: 
        logger.info('CTM: Analyze Alert for Jobs - Start')

    jCtmAlert         = data
    ctmOrderId        = w3rkstatt.getJsonValue(path="$.order_id",data=jCtmAlert)
    ctmJobData        = None
    jCtmAlertData     = json.dumps(jCtmAlert)
    sCtmAlertData     = str(jCtmAlertData)
    jCtmAlertRaw      = raw

    if not ctmOrderId == "00000" and  ctmOrderId is not None:
        if "New" in ctmAlertCallType:
            # Get CTM Job Info
            ctmJobId      = w3rkstatt.getJsonValue(path="$.job_id",data=jCtmAlert)
            ctmJobName    = w3rkstatt.getJsonValue(path="$.job_name",data=jCtmAlert)

            sCtmJobInfo = '{"ctm_api":"simplified monitoring"}'
            sCtmJobOutput = '{"ctm_api":"simplified monitoring"}'
            sCtmJobLog = '{"ctm_api":"simplified monitoring"}'
            sCtmJobConfig ='{"ctm_api":"simplified monitoring"}'

            # Prep for str concat
            sCtmAlertRaw  = str(jCtmAlertRaw)
            ctmJobData = '{"uuid":"'  + sUuid  + '","raw":[' + sCtmAlertRaw + '],"jobAlert":[' + sCtmAlertData + '],"jobInfo":[' + sCtmJobInfo + '],"jobConfig":[' + sCtmJobConfig  + '],"jobLog":[' + sCtmJobLog + '],"jobOutput":[' + sCtmJobOutput + ']}'
            ctmJobData = w3rkstatt.dTranslate4Json(data=ctmJobData)
    
        # Convert event data to the JSON format required by the API.
    else:
            sCtmAlertRaw  = str(jCtmAlertRaw)
            sjCtmAlert    = w3rkstatt.dTranslate4Json(data=jCtmAlert)
            # defaults
            sCtmJobInfo   = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) + ',"status":' + str(None) + ',"entries":[]}')
            sCtmJobOutput = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) + ',"status":' + str(None) + ',"entries":[]}')
            sCtmJobLog    = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) + ',"status":' + str(None) + ',"entries":[]}')
            sCtmJobConfig = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) + ',"status":' + str(None) + ',"entries":[]}')
            ctmJobData = '{"uuid":"'  + sUuid  + '","raw":[' + sCtmAlertRaw + '],"jobAlert":[' + sCtmAlertData + '],"jobInfo":[' + sCtmJobInfo + '],"jobConfig":[' + sCtmJobConfig  + '],"jobLog":[' + sCtmJobLog + '],"jobOutput":[' + sCtmJobOutput + ']}'

    if _localInfo: 
        logger.info('CTM: Analyze Alert for Jobs - End')    
    return ctmJobData

def analyzeAlert4Core(ctmApiClient, raw, data):
    if _localInfo: 
        logger.info('CTM: Analyze Alert for Core - Start')

    jCtmAlert         = data
    ctmCoreData       = None
    jCtmAlertData     = json.dumps(jCtmAlert)
    jCtmAlertRaw      = raw

    if _localInfo: 
        logger.info('CTM: Analyze Alert - Core Info')
    # Prep for str concat
    sCtmAlertRaw  = str(jCtmAlertRaw)
    sCtmAlertData = str(jCtmAlertData)

    ctmCoreData = '{"uuid":"'  + sUuid  + '","raw":[' + sCtmAlertRaw + '],"coreAlert":[' + sCtmAlertData + ']}'
    ctmCoreData = w3rkstatt.jsonTranslateValues(ctmCoreData)
    ctmCoreData =w3rkstatt.jsonTranslateValuesAdv(ctmCoreData) 

    if _localInfo: 
        logger.info('CTM: Analyze Alert for Core - End')
    return ctmCoreData

def analyzeAlert4Infra(ctmApiClient, raw, data):
    if _localInfo: 
        logger.info('CTM: Analyze Alert for Infra - Start')

    jCtmAlert         = data
    ctmCoreData       = None
    jCtmAlertData     = json.dumps(jCtmAlert)
    jCtmAlertRaw      = raw

    if _localInfo: 
        logger.info('CTM: Analyze Alert - Infra Info')
    # Prep for str concat
    sCtmAlertRaw  = str(jCtmAlertRaw)
    sCtmAlertData = str(jCtmAlertData)

    ctmCoreData = '{"uuid":"'  + sUuid  + '","raw":[' + sCtmAlertRaw + '],"infraAlert":[' + sCtmAlertData + ']}'
    ctmCoreData = w3rkstatt.jsonTranslateValues(ctmCoreData)
    ctmCoreData =w3rkstatt.jsonTranslateValuesAdv(ctmCoreData) 

    if _localInfo: 
        logger.info('CTM: Analyze Alert for Infra - End')
    return ctmCoreData

def writeAlertFile(data,alert,type="job"):
    fileStatus = False
    ctmJobData = data
    if _ctmActiveApi:
        fileType = "ctm-enriched-" + type +"-"
    else:
        fileType = "ctm-basic-" + type +"-"

    fileContent = json.loads(ctmJobData)
    fileJsonStatus = w3rkstatt.jsonValidator(data=ctmJobData)

    if fileJsonStatus:
        fileName    = fileType + alert.zfill(8) + "-" + str(epoch).replace(".","") + ".json"
        filePath    = w3rkstatt.concatPath(path=data_folder,folder=fileName)
        fileRsp     = w3rkstatt.writeJsonFile(file=filePath,content=fileContent)  
        fileStatus  = w3rkstatt.getFileStatus(path=filePath)

        if _localQA: 
            logger.info('CTM QA Alert File: "%s" ', filePath)

    return fileStatus


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='a', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    
    sSysOutMsg = ""

    if _localInfo: 
        logger.info('CTM: start event management - %s', w3rkstatt.sUuid)
        logger.info('Version: %s ', _modVer)
        logger.info('System Platform: %s ', w3rkstatt.sPlatform)
        logger.info('Log Level: %s', loglevel)
        logger.info('Epoch: %s', epoch)
        logger.info('Host Name: %s', w3rkstatt.sHostname)
        logger.info('UUID: %s', w3rkstatt.sUuid)

    # Extract script arguments
    sCtmArguments = sys.argv[1:]
    sCtmArgDict   = ctmAlert2Dict(list=sCtmArguments,start=0,end=len(sCtmArguments))
    jCtmArgs      = json.dumps(sCtmArgDict)
    jCtmAlert     = json.loads(jCtmArgs)
    ctmAlertId    = str(w3rkstatt.getJsonValue(path="$.alert_id",data=jCtmAlert)).strip()
    ctmRunCounter = None

    if _localDebug:
        logger.debug('CMT Initial Alert JSON: %s', jCtmAlert)

     # Test integration with sample data
    if not len(ctmAlertId) > 0:
        if _localQAlert: 
            # jCtmAlert = {"alert_id": "166", "alert_type": "Regular", "application": None, "call_type": "New", "closed_from_em": None, "data_center": "bmcs-ctm-srv", "data_center_dns": "shytwr.net", "data_center_fqdn": "bmcs-ctm-srv.shytwr.net", "data_center_ip": "172.16.29.125", "host_id": None, "host_ip": "172.16.32.22", "host_ip_dns": "shytwr.net", "host_ip_fqdn": "bmcs-ctm-agt.shytwr.net", "job_name": None, "last_time": None, "last_user": None, "memname": None, "message": "STATUS OF AGENT PLATFORM bmcs-ctm-agt CHANGED TO AVAILABLE", "message_notes": "CTRL-M Agent on bmcs-ctm-agt.shytwr.net availabble. Managed by: bmcs-ctm-srv", "message_summary": "Agent on bmcs-ctm-agt availabble", "notes": None, "order_id": "00000", "run_as": None, "run_counter": "00000000000", "send_time": "2021-04-05 22:39:36", "severity": "OK", "status": "OPEN", "sub_application": None, "ticket_number": None}
            # jCtmAlert = {"call_type": "I", "alert_id": "168", "data_center": "bmcs-ctm-srv", "memname": None, "order_id": "00000", "severity": "R", "status": "Not_Noticed", "send_time": "20210405232831", "last_user": None, "last_time": None, "message": "STATUS OF AGENT PLATFORM bmcs-ctm-agt CHANGED TO AVAILABLE", "run_as": None, "sub_application": None, "application": None, "job_name": None, "host_id": None, "alert_type": "R", "closed_from_em": None, "ticket_number": None, "run_counter": "00000000000", "notes": None}
            # jCtmAlert = {"call_type": "I", "alert_id": "182", "data_center": "bmcs-ctm-srv", "memname": None, "order_id": None, "severity": "V", "status": "Not_Noticed", "send_time": "20210406092918", "last_user": None, "last_time": None, "message": "DATA CENTER bmcs-ctm-srv WAS DISCONNECTED", "run_as": "Gateway", "sub_application": None, "application": None, "job_name": None, "host_id": None, "alert_type": "R", "closed_from_em": None, "ticket_number": None, "run_counter": None, "notes": None}
            # jCtmAlert = {"call_type": "I", "Serial": "46", "Component_type": "9", "Component_machine": "bmcs-ctm-em", "Component_name": "bmcs-ctm-em", "Message_id": "20004", "Xseverity": "3", "Message": "Failed to send e-mail notification to <undefined> from sender <undefined> via e-mail server <undefined> Error: : Empty mail server : Empty mail from : Empty destination mail address .", "Xtime": "20210406165204", "Xtime_of_last": "20210406165204", "Counter": "1", "Status": "1", "Note": None, "Key1": "<undefined>", "Key2": "<undefined>", "Key3": "<undefined>", "Key4": ": Empty mail server : Empty mail from : Empty destination mail address", "Key5": None}
            # Mainframe Alert
            jCtmAlert = {"call_type": "I", "alert_id": "209525", "data_center": "bmcbzos", "memname": "COBCOMP", "order_id": "0314Y", "severity": "V", "status": "Not_Noticed", "send_time": "20210416120024", "last_user": None, "last_time": None, "message": "Ended not OK", "run_as": "RDWDXC", "sub_application": "DCO_SORT", "application": "DCO", "job_name": "COBCOMP", "host_id": None, "alert_type": "R", "closed_from_em": None, "ticket_number": None, "run_counter": "00000", "notes": None}
            jCtmAlert = {"call_type": "I", "alert_id": "210561", "data_center": "psctm", "memname": None, "order_id": "0c4ib", "severity": "V", "status": "Not_Noticed", "send_time": "20210419103327", "last_user": None, "last_time": None, "message": "Ended not OK", "run_as": "ctmagent", "sub_application": "VFS_Alert_Management", "application": "VFS_Integration", "job_name": "VFS_OS", "host_id": "vl-aus-ctm-em01.ctm.bmc.com", "alert_type": "R", "closed_from_em": None, "ticket_number": None, "run_counter": "00001", "notes": None}
            jCtmAlert = {'call_type': 'I', 'alert_id': '212069', 'data_center': 'psctm', 'memname': None, 'order_id': '00000', 'severity': 'R', 'status': 'Not_Noticed', 'send_time': '20210420163225', 'last_user': None, 'last_time': None, 'message': 'Failed to order SAP Job CHILD_1 by template job y_SAP-Childjob in Table DCO_SAP_Basic_Jobs  please verify template job definition', 'run_as': None, 'sub_application': None, 'application': None, 'job_name': None, 'host_id': None, 'alert_type': 'R', 'closed_from_em': None, 'ticket_number': None, 'run_counter': '00000000000', 'notes': None}
            jCtmAlert = {'call_type': 'I', 'alert_id': '212166', 'data_center': 'bmcbzos', 'memname': 'COBCOMP', 'order_id': '031BH', 'severity': 'V', 'status': 'Not_Noticed', 'send_time': '20210420181108', 'last_user': None, 'last_time': None, 'message': 'Ended not OK', 'run_as': 'RDWDXC', 'sub_application': 'DCO_SORT', 'application': 'DCO', 'job_name': 'COBCOMP', 'host_id': None, 'alert_type': 'R', 'closed_from_em': None, 'ticket_number': None, 'run_counter': '00002', 'notes': None}
            jCtmAlert = {"call_type": "I", "alert_id": "212721", "data_center": "psctm", "memname": None, "order_id": "00000", "severity": "R", "status": "Not_Noticed", "send_time": "20210421013938", "last_user": None, "last_time": None, "message": "Failed to order SAP Job CHILD_2 by template job y_SAP-Childjob in Table DCO_SAP_Basic_Jobs  please verify template job definition", "run_as": None, "sub_application": None, "application": None, "job_name": None, "host_id": None, "alert_type": "R", "closed_from_em": None, "ticket_number": None, "run_counter": "00000000000", "notes": None}
            # jCtmAlert = {"call_type": "I", "alert_id": "212760", "data_center": "psctm", "memname": None, "order_id": "0c5w5", "severity": "V", "status": "Not_Noticed", "send_time": "20210421020203", "last_user": None, "last_time": None, "message": "Ended not OK", "run_as": "ctmagent", "sub_application": "VFS_Alert_Management", "application": "VFS_Integration", "job_name": "VFS_OS", "host_id": "vl-aus-ctm-em01.ctm.bmc.com", "alert_type": "R", "closed_from_em": None, "ticket_number": None, "run_counter": "00001", "notes": None}


    if len(jCtmAlert) > 0:

        # Transform CTM Alert
        jCtmAlertRaw      = json.dumps(jCtmAlert) 
        sCtmAlert         = ctm.trasnformtCtmAlert(data=jCtmAlert)
        jCtmAlert         = json.loads(sCtmAlert)
        ctmEventType      = ctm.extractCtmAlertType(jCtmAlert)
        ctmAlertId        = str(w3rkstatt.getJsonValue(path="$.alert_id",data=jCtmAlert)).strip()
        ctmAlertCallType  = w3rkstatt.getJsonValue(path="$.call_type",data=jCtmAlert).strip()
        ctmDataCenter     = w3rkstatt.getJsonValue(path="$.data_center",data=jCtmAlert).strip()
        ctmOrderId        = w3rkstatt.getJsonValue(path="$.order_id",data=jCtmAlert).strip()
        ctmRunCounter     = w3rkstatt.getJsonValue(path="$.run_counter",data=jCtmAlert).strip()
        ctmAlertCat       = w3rkstatt.getJsonValue(path="$.system_category",data=jCtmAlert).strip()
        ctmAlertSev       = w3rkstatt.getJsonValue(path="$.severity",data=jCtmAlert).strip()
        sCtmJobCyclic     = w3rkstatt.getJsonValue(path="$.jobInfo.[0].cyclic",data=jCtmAlert).strip()

        # Process only 'new' alerts
        if "New" in ctmAlertCallType: 
            logger.info('')
            logger.info('CMT New Alert: %s', jCtmAlertRaw)
            logger.info('')
            if ctmAlertCat == "infrastructure":
                pass
            else:
                if ctmRunCounter == None:
                    ctmRunCounter = 0
                elif len(ctmRunCounter) < 1:
                    ctmRunCounter = 0
                else: 
                    ctmRunCounter = int(ctmRunCounter)


            # logger.debug('CMT Alert JSON Raw: %s', jCtmAlertRaw)
            # logger.debug('CMT Alert JSON Formatted: %s', jCtmAlert)

            if _localDebug: 
                # sCtmAlert = w3rkstatt.jsonTranslateValues(data=jCtmAlert)
                sCtmAlert = json.dumps(jCtmAlert)
                logger.info('CMT QA Alert JSON Raw: %s', jCtmAlertRaw)
                logger.info('')
                logger.info('CMT QA Alert JSON Format 01: %s', jCtmAlert)
                logger.info('')
                logger.info('CMT QA Alert JSON Format 02: %s', sCtmAlert)
                logger.info('')
                logger.info('CTM QA Alert ID: %s', ctmAlertId)
                logger.info('CTM QA Alert Type: "%s"', ctmEventType)
                logger.info('CTM QA Alert Category: "%s"', ctmAlertCat)
                logger.info('CTM QA Job Datacenter: %s', ctmDataCenter)
                logger.info('CTM QA Job ID: %s', ctmOrderId)
                logger.info('CTM QA Run Counter: %s', ctmRunCounter)
                logger.info('CTM QA Alert Call: "%s"', ctmAlertCallType)
                logger.info('CTM QA ITSM Integration: "%s"', integration_itsm_enabled)

            # xAlert ID
            if not ctmAlertId:
                ctmAlertId = str(w3rkstatt.getJsonValue(path="$.Serial",data=jCtmAlert)).strip()
                
            if ctmAlertCat == "infrastructure":
                ctmCoreData  = ""
                fileStatus   = writeAlertFile(data=ctmCoreData,alert=ctmAlertId,type="infra")
            elif ctmAlertCat == "job":
                ctmJobData  = ""
                if ctmOrderId == "00000" and ctmRunCounter == 0:
                    # do not create file
                    fileStatus = True
                else:
                    # Update CTM Alert staus if file is written
                    fileStatus  = writeAlertFile(data=ctmJobData,alert=ctmAlertId,type="job") 
            else:
                ctmCoreData  = ""
                fileStatus   = writeAlertFile(data=ctmCoreData,alert=ctmAlertId,type="core")

            
            sSysOutMsg = "Processed New Alert: " + str(ctmAlertId)

        # Process only 'update' alerts             
        if "Update" in ctmAlertCallType: 
            if _localDebugAdv: 
                logger.debug('- CTM Alert Update: "%s"', "Start")
            sSysOutMsg = "Processed Update Alert: " + str(ctmAlertId)

    if _localInfo: 
        logger.info('CTM: end event management - %s', w3rkstatt.sUuid)

    logging.shutdown()

    print (f"Message: {sSysOutMsg}")