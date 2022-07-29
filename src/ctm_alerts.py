#!/usr/bin/env python3
# Filename: ctm_alerts.py
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
20220715      Volker Scheithauer    BMC Helix Operation Management Integration

"""

import time
import logging
import sys
import getopt
import platform
import argparse
import os
import json
from collections import OrderedDict
import collections
from xml.sax.handler import ContentHandler
from xml.sax import make_parser

# handle dev environment vs. production
try:
    import w3rkstatt as w3rkstatt
    import core_ctm as ctm
    import core_itsm as itsm
    import core_tsim as tsim
    import core_bhom as bhom
except:
    # fix import issues for modules
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstatt
    from src import core_ctm as ctm
    from src import core_itsm as itsm
    from src import core_tsim as tsim
    from src import core_bhom as bhom

# Get configuration from bmcs_core.json
jCfgData = w3rkstatt.getProjectConfig()
cfgFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",
                                   data=jCfgData)
logFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder", data=jCfgData)
tmpFolder = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",
                                   data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",
                                    data=jCfgData)

data_folder = logFolder
ctm_host = w3rkstatt.getJsonValue(path="$.CTM.host", data=jCfgData)
ctm_port = w3rkstatt.getJsonValue(path="$.CTM.port", data=jCfgData)

integration_itsm_enabled = w3rkstatt.getJsonValue(path="$.CTM.itsm.enabled",
                                                  data=jCfgData)
integration_tsim_enabled = w3rkstatt.getJsonValue(path="$.CTM.tsim.enabled",
                                                  data=jCfgData)
integration_bhom_enabled = w3rkstatt.getJsonValue(path="$.CTM.bhom.enabled",
                                                  data=jCfgData)

# Extract CTM job log & details
# Level: full, mini
ctm_job_log_level = w3rkstatt.getJsonValue(path="$.CTM.jobs.log_level",
                                           data=jCfgData)
ctm_job_detail_level = w3rkstatt.getJsonValue(path="$.CTM.jobs.detail_level",
                                              data=jCfgData)

ctmCoreData = None
ctmJobData = None

# Assign module defaults
_localDebug = jCfgData["DEFAULT"]["debug"]["api"]
_localDebugFunctions = jCfgData["DEFAULT"]["debug"]["functions"]
_localDebugData = jCfgData["DEFAULT"]["debug"]["data"]
_localDebugAdvanced = jCfgData["DEFAULT"]["debug"]["advanced"]
_localQA = jCfgData["DEFAULT"]["debug"]["qa"]
_localDebugBHOM = jCfgData["BHOM"]["debug"]
_localDebugITSM = jCfgData["ITSM"]["debug"]

_FutureUse = False

_localInfo = False
_modVer = "3.0"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_ctmActiveApi = False

logger = w3rkstatt.logging.getLogger(__name__)
logFile = w3rkstatt.getJsonValue(path="$.DEFAULT.log_file", data=jCfgData)
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
hostName = w3rkstatt.getHostName()
hostIP = w3rkstatt.getHostIP(hostName)
hostFqdn = w3rkstatt.getHostFqdn(hostName)
domain = w3rkstatt.getHostDomain(hostFqdn)
epoch = time.time()
parser = argparse.ArgumentParser(prefix_chars=':')
sUuid = w3rkstatt.sUuid


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
    sAlert = str(list).replace("',", "").replace("'", "")
    sCustom = ""

    try:
        if w3rkstatt.sPlatform == "Linux":
            if _localDebugFunctions or _localDebugData:
                logger.debug('Function = "%s" ', "ctmAlert2Dict")
                # logger.debug('Script Arguments for Linux ')
                # logger.debug('Script Arguments #     = %s ', len(list))
                # logger.debug('Script Arguments Start = %s ', start)
                # logger.debug('Script Arguments End   = %s ', end)
                # logger.debug('Script Arguments List  = %s ', str(list))
                logger.debug('Script Arguments Str   = %s ', str(sAlert))

            for counter in range(start, end):
                entry = str(list[counter])

                if entry[-1] == ":":
                    param = list[counter].replace(":", "")
                    sCustom = str(sCustom) + "," + param + ":"
                else:
                    value = str(list[counter]).strip().replace(",", " ")
                    sCustom = str(sCustom) + str(value) + " "

                # res_dct[param] = value

            sCustom = str(sCustom)  # + "'"
            sCustom = sCustom[1:]

            res_dct = dict(item.split(":") for item in sCustom.split(","))

            for (key, value) in res_dct.items():

                if len(value) < 1:
                    value = None
                else:
                    value = value.replace('"', '').strip()
                    if len(value) < 1:
                        value = None

                res_dct[key] = value
                if _localDebugFunctions or _localDebugData:
                    logger.debug('Arguments %s=%s ', key, value)

        else:

            for counter in range(start, end, 2):
                list[counter] = list[counter].replace(":", "")
                value = str(list[counter + 1]).strip()
                param = list[counter]

                if len(value) < 1:
                    value = None
                if _localDebugFunctions or _localDebugData:
                    logger.debug('%s="%s" ', param, value)

                res_dct[param] = value
    except:
        pass

    return res_dct


def getCtmJobInfo(ctmApiClient, data):
    # Get Job Info via CTM API
    ctmData = data
    ctmDataCenter = w3rkstatt.getJsonValue(path="$.data_center", data=ctmData)
    ctmOrderId = w3rkstatt.getJsonValue(path="$.order_id", data=ctmData)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobInfo")
        logger.info('CTM Get Job Info: "%s:%s"', ctmDataCenter, ctmOrderId)
    jData = ctm.getCtmJobInfo(ctmApiClient=ctmApiClient,
                              ctmServer=ctmDataCenter,
                              ctmOrderID=ctmOrderId)

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "jData")
    return jData


def getCtmJobRunLog(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter", data=data)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobRunLog")
        logger.info('CTM Get Job Run Log: "%s # %s"', ctmJobID,
                    ctmJobRunCounter)

    sLogData = ctm.getCtmJobLog(ctmApiClient=ctmApiClient, ctmJobID=ctmJobID)
    if _localDebugFunctions:
        logger.info('CMT QA Get Job Run Log: %s', sLogData)

    # Based on config, extract level of details
    if ctm_job_log_level == "full":
        jCtmJobLog = ctm.transformCtmJobLog(data=sLogData)
    else:
        jCtmJobLog = ctm.transformCtmJobLogMini(data=sLogData,
                                                runCounter=ctmJobRunCounter)

    if _localDebugFunctions or _localDebugData:
        logger.debug('CMT Job Run Log Raw: %s', jCtmJobLog)

    sCtmJobLog = str(jCtmJobLog)

    return sCtmJobLog


def getCtmJobLog(ctmApiClient, data):
    # Get CTM job log after 30 sec - wait for archive server to have log
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobLog")
        logger.debug('CMT Job Log: First attempt to retrieve data')
    time.sleep(2)
    sCtmJobLog = getCtmJobRunLog(ctmApiClient, data)

    if _localDebugFunctions or _localDebugData:
        logger.debug('CMT Job Log Raw: %s', sCtmJobLog)

    jCtmJobLog = json.loads(sCtmJobLog)
    ctmStatus = w3rkstatt.getJsonValue(path="$.status", data=jCtmJobLog)

    if ctmStatus != True:
        if _localDebugFunctions:
            logger.debug('CMT Job Log: Second attempt to retrieve data')
        time.sleep(2)
        jCtmJobLog = getCtmJobRunLog(ctmApiClient, data)
        sCtmJobLog = w3rkstatt.dTranslate4Json(data=jCtmJobLog)

    return sCtmJobLog


def getCtmJobConfig(ctmApiClient, data):
    jCtmJobInfo = data
    ctmFolderInfo = getCtmFolder(ctmApiClient=ctmApiClient, data=jCtmJobInfo)
    jCtmFolderInfo = json.loads(ctmFolderInfo)
    iCtmFolderInfo = w3rkstatt.getJsonValue(path="$.count",
                                            data=jCtmFolderInfo)
    sStatus = w3rkstatt.getJsonValue(path="$.status", data=jCtmFolderInfo)

    if ctm_job_detail_level == "full" or iCtmFolderInfo == 1:
        jCtmJobDetail = ctmFolderInfo
        sCtmJobDetail = w3rkstatt.dTranslate4Json(data=jCtmJobDetail)
    else:
        if _localDebugData:
            logger.debug('Function = "%s" ', "getCtmJobConfig")
            logger.debug('CMT Job Config: "%s"', jCtmJobInfo)
        if sStatus:
            jCtmJobName = w3rkstatt.getJsonValue(path="$.name",
                                                 data=jCtmJobInfo)
            jCtmFolderName = w3rkstatt.getJsonValue(path="$.folder",
                                                    data=jCtmJobInfo)
            jQl = "$." + str(jCtmFolderName) + "." + str(jCtmJobName)
            jData = json.loads(ctmFolderInfo)
            jCtmJobDetail = w3rkstatt.getJsonValue(path=jQl, data=jData)
            sCtmJobDetail = w3rkstatt.dTranslate4Json(data=jCtmJobDetail)
        else:
            sCtmJobDetail = ctmFolderInfo

    return sCtmJobDetail


def getCtmArchiveJobLog(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                              data=ctmData)
    value = ctm.getCtmArchiveJobLog(ctmApiClient=ctmApiClient,
                                    ctmJobID=ctmJobID,
                                    ctmJobRunCounter=ctmJobRunCounter)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmArchiveJobLog")
        logger.debug('CMT Job Log Raw: %s', value)
    return value


def getCtmJobRunOutput(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                              data=ctmData)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobRunOutput")
        logger.info('CTM Get Job Run Output: "%s # %s"', ctmJobID,
                    ctmJobRunCounter)

    value = ctm.getCtmJobOutput(ctmApiClient=ctmApiClient,
                                ctmJobID=ctmJobID,
                                ctmJobRunId=ctmJobRunCounter)
    if _localDebugFunctions:
        logger.debug('CMT Job Output Raw: %s', value)

    ctmJobOutput = ctm.transformCtmJobOutput(data=value)

    if _localDebugFunctions or _localDebugData:
        logger.debug('CMT Job Run Output: %s', ctmJobOutput)
    return ctmJobOutput


def getCtmArchiveJobRunOutput(ctmApiClient, data):
    ctmData = data
    ctmJobID = w3rkstatt.getJsonValue(path="$.job_id", data=ctmData)
    ctmJobRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                              data=ctmData)
    value = ctm.getCtmArchiveJobOutput(ctmApiClient=ctmApiClient,
                                       ctmJobID=ctmJobID,
                                       ctmJobRunId=ctmJobRunCounter)
    ctmJobOutput = ctm.transformCtmJobOutput(data=value)
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmArchiveJobRunOutput")
        logger.debug('CMT Job Output Raw: %s', ctmJobOutput)
    return ctmJobOutput


def getCtmJobOutput(ctmApiClient, data):
    # Get CTM job log after 30 sec - wait for archive server to have log
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmJobOutput")
        logger.debug('CMT Job Output: First attempt to retrieve data')
    time.sleep(2)
    jCtmJobOutput = getCtmJobRunOutput(ctmApiClient, data)
    ctmStatus = w3rkstatt.getJsonValue(path="$.status", data=jCtmJobOutput)

    if ctmStatus != True:
        if _localDebugFunctions:
            logger.debug('CMT Job Output: Second attempt to retrieve data')
        time.sleep(2)
        jCtmJobOutput = getCtmJobRunOutput(ctmApiClient, data)

    # transform to JSON string
    sCtmJobOutput = w3rkstatt.dTranslate4Json(data=jCtmJobOutput)

    return sCtmJobOutput


def createITSM(data):

    data = '{"uuid":"22365c5e-6f18-4412-95a9-38c708661fee","raw":[{"call_type": "I", "alert_id": "280", "data_center": "ctm-srv.trybmc.com", "memname": null, "order_id": "0000q", "severity": "V", "status": "Not_Noticed", "send_time": "20220729164416", "last_user": null, "last_time": null, "message": "Ended not OK", "run_as": "dbus", "sub_application": "Integration", "application": "ADE", "job_name": "Agent Health", "host_id": "ctm-net.trybmc.com", "alert_type": "R", "closed_from_em": null, "ticket_number": null, "run_counter": "00015", "notes": null}],"jobAlert":[{"alert_id": "280", "alert_type": "Regular", "application": "ADE", "call_type": "New", "closed_from_em": null, "data_center": "ctm-srv.trybmc.com", "data_center_dns": "trybmc.com", "data_center_fqdn": "ctm-srv.trybmc.com", "data_center_ip": "192.168.100.62", "host_id": "ctm-net.trybmc.com", "host_ip": "192.168.100.39", "host_ip_dns": "trybmc.com", "host_ip_fqdn": "ctm-net.trybmc.com", "job_id": "ctm-srv.trybmc.com:0000q", "job_name": "Agent Health", "job_script": null, "job_uri": "https://ctm-em.trybmc.com:8443/ControlM/#Search:id=Search_2&search=0000q&date=20220729&controlm=ctm-srv.trybmc.com", "last_time": null, "last_user": null, "memname": null, "message": "Ended not OK", "message_notes": "CTRL-M Job Agent Health failed. Job ID: ctm-srv.trybmc.com:0000q with Job Run Count: 00015", "message_summary": "Job Agent Health failed", "notes": null, "order_id": "0000q", "run_as": "dbus", "run_counter": "00015", "send_time": "2022-07-29 16:44:16", "severity": "CRITICAL", "status": "OPEN", "sub_application": "Integration", "system_category": "job", "system_class": null, "system_status": "failed", "ticket_number": null}],"jobInfo":[{"count":2,"status":true,"entries":[{"job_id": "ctm-srv.trybmc.com:0000q", "folder_id": "ctm-srv.trybmc.com:0000p", "number_of_runs": 15, "name": "Agent Health", "folder": "BHOM", "type": "Command", "status": "Ended Not OK", "held": false, "deleted": false, "cyclic": false, "start_time": "2022-07-29 16:44:14", "end_time": "2022-07-29 16:44:14", "estimated_start_time": "2022-07-29 16:44:14", "estimated_end_time": "2022-07-29 16:44:24", "order_date": "2022-07-28", "ctm": "ctm-srv.trybmc.com", "description": "ADE Integration Test: Agent Health", "host": "ctm-net.trybmc.com", "library": null, "application": "ADE", "sub_application": "Integration", "job_json": null, "output_uri": "https://ctm-em.trybmc.com:8443/automation-api/run/job/ctm-srv.trybmc.com:0000q/output", "log_uri": "https://ctm-em.trybmc.com:8443/automation-api/run/job/ctm-srv.trybmc.com:0000q/log", "count": 24}]}],"jobConfig":[{"count":1,"status":true,"entries":[{"BHOM": {"Type": "Folder", "ControlmServer": "ctm-srv.trybmc.com", "Description": "ADE Integration Test", "ActiveRetentionPolicy": "CleanEndedOK", "RunAs": "ctmem", "SubApplication": "Integration", "CreatedBy": "ctmem", "Application": "ADE", "When": {"RuleBasedCalendars": {"Included": ["EVERYDAY"], "EVERYDAY": {"Type": "Calendar:RuleBased", "When": {"DaysRelation": "OR", "WeekDays": ["NONE"], "MonthDays": ["ALL"]}}}}, "Agent Health": {"Type": "Job:Command", "SubApplication": "Integration", "Host": "ctm-net.trybmc.com", "CreatedBy": "ctmem", "Description": "ADE Integration Test: Agent Health", "RunAs": "dbus", "Application": "ADE", "Command": "ls -latr /", "When": {"WeekDays": ["NONE"], "MonthDays": ["NONE"], "DaysRelation": "OR"}}}}]}],"jobLog":[{"count": 0,"status": "experimental"}],"jobOutput":[{"count": 0,"status": "unknown"}]}'
    jCtmAlert = json.loads(data)

    # ITSM Login
    authToken = itsm.authenticate()

    # ToDO: Update Incident data
    # Add Logic to map CTM Alerts to Incident Support Groups

    sCtmAppMain = w3rkstatt.getJsonValue(path="$.jobAlert.[0].application",
                                         data=jCtmAlert)
    sCtmAppSub = w3rkstatt.getJsonValue(path="$.jobAlert.[0].sub_application",
                                        data=jCtmAlert)
    sCtmJobName = w3rkstatt.getJsonValue(path="$.jobAlert.[0].job_name",
                                         data=jCtmAlert)
    sCtmJobCyclic = w3rkstatt.getJsonValue(path="$.jobInfo.[0].cyclic",
                                           data=jCtmAlert)
    sCtmJobID = w3rkstatt.getJsonValue(path="$.jobAlert.[0].job_id",
                                       data=jCtmAlert)
    sCtmJobRunCount = w3rkstatt.getJsonValue(path="$.jobAlert.[0].run_counter",
                                             data=jCtmAlert)
    sCtmAlertID = w3rkstatt.getJsonValue(path="$.jobAlert.[0].alert_id",
                                         data=jCtmAlert)
    sCtmJobDescSum = w3rkstatt.getJsonValue(
        path="$.jobAlert.[0].message_summary", data=jCtmAlert)
    sCtmJobDescDetail = w3rkstatt.getJsonValue(
        path="$.jobAlert.[0].message_notes", data=jCtmAlert)

    if sCtmJobCyclic:
        sCtmVendorTicket = "#" + sCtmJobID + "#Cyclic#"
    else:
        sCtmVendorTicket = "#" + sCtmJobID + "#Regular#" + \
            sCtmJobRunCount + "#" + sCtmAlertID + "#"

    jIncidentData = {
        "values": {
            "z1D_Action":
            "CREATE",
            "First_Name":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-first",
                                   data=jCfgData),
            "Last_Name":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.name-last",
                                   data=jCfgData),
            "Description":
            sCtmJobDescSum,
            "Detailed_Decription":
            sCtmJobDescDetail,
            "Impact":
            w3rkstatt.getJsonValue(path="$.ITSM.incident.impact",
                                   data=jCfgData),
            "Urgency":
            w3rkstatt.getJsonValue(path="$.ITSM.incident.urgency",
                                   data=jCfgData),
            "Status":
            w3rkstatt.getJsonValue(path="$.ITSM.incident.status",
                                   data=jCfgData),
            "Reported Source":
            w3rkstatt.getJsonValue(path="$.ITSM.incident.reported-source",
                                   data=jCfgData),
            "Service_Type":
            w3rkstatt.getJsonValue(path="$.ITSM.incident.service-type",
                                   data=jCfgData),
            "ServiceCI":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.service-ci",
                                   data=jCfgData),
            # "Assigned Group":
            # w3rkstatt.getJsonValue(path="$.ITSM.defaults.assigned-group",
            #                        data=jCfgData),
            # "Assigned Support Company":
            # w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-company",
            #                        data=jCfgData),
            # "Assigned Support Organization":
            # w3rkstatt.getJsonValue(path="$.ITSM.defaults.support-organization",
            #                        data=jCfgData),
            "Categorization Tier 1":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_1",
                                   data=jCfgData),
            "Categorization Tier 2":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_2",
                                   data=jCfgData),
            "Categorization Tier 3":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.op_cat_3",
                                   data=jCfgData),
            "Product Categorization Tier 1":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_1",
                                   data=jCfgData),
            "Product Categorization Tier 2":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_2",
                                   data=jCfgData),
            "Product Categorization Tier 3":
            w3rkstatt.getJsonValue(path="$.ITSM.defaults.prod_cat_3",
                                   data=jCfgData),
            # "Product Name":
            # w3rkstatt.getJsonValue(path="$.ITSM.defaults.product_name",
            #                        data=jCfgData),
            "Vendor Ticket Number":
            sCtmVendorTicket
            # "AWW Custom Field Name":
            # sCtmJobName + "#" + sCtmAppMain + "#" + sCtmAppSub
        }
    }

    if _localDebugITSM:
        sIncidentData = w3rkstatt.jsonTranslateValues(data=jIncidentData)
        logger.debug('')

    incidentId = itsm.createIncident(token=authToken, data=jIncidentData)

    if _localDebugITSM:
        logger.debug('Function = "%s" ', "createITSM")
        sIncidentData = w3rkstatt.jsonTranslateValues(data=jIncidentData)
        logger.debug('')
        logger.debug('ITSM Integration Data = %s ', sIncidentData)
        logger.debug('')
        logger.debug('ITSM Incident: "%s" ', incidentId)

    # Worklog entry for CTM Alert
    jWorklogData = w3rkstatt.getJsonValue(path="$.jobAlert", data=jCtmAlert)
    createWorklog(token=authToken, data=jWorklogData, incident=incidentId)

    if _localDebugITSM:
        sIncidentData = w3rkstatt.jsonTranslateValues(data=jWorklogData)
        logger.debug('')
        logger.debug('ITSM Worklog Data = %s ', sIncidentData)
        logger.debug('')

    # Worklog entry for CTM Job Info
    jWorklogData = w3rkstatt.getJsonValue(path="$.jobInfo", data=jCtmAlert)
    createWorklog(token=authToken, data=jWorklogData, incident=incidentId)

    # Worklog entry for CTM Job Config
    jWorklogData = w3rkstatt.getJsonValue(path="$.jobConfig", data=jCtmAlert)
    createWorklog(token=authToken, data=jWorklogData, incident=incidentId)

    # Worklog entry for CTM Job Output
    jWorklogData = w3rkstatt.getJsonValue(path="$.jobLog", data=jCtmAlert)
    createWorklog(token=authToken, data=jWorklogData, incident=incidentId)

    # Worklog entry for CTM Job Output
    jWorklogData = w3rkstatt.getJsonValue(path="$.jobOutput", data=jCtmAlert)
    createWorklog(token=authToken, data=jWorklogData, incident=incidentId)

    # ITSM Logoff
    # itsm.itsmLogout(token=authToken)
    logger.info('ITSM Incident: %s', incidentId)
    return incidentId


def createWorklog(token, data, incident):
    authToken = token
    jCtmAlert = json.dumps(data[0], indent=4)
    worklog = {
        "values": {
            "Work Log Submitter": "user",
            "Status": "Enabled",
            "Description": "Control-M Log",
            "Detailed Description": "" + jCtmAlert + "",
            "Incident Number": "" + str(incident) + "",
            "Work Log Type": "Working Log",
            "View Access": "Public",
            "Secure Work Log": "No"
        }
    }
    result = itsm.createIncidentWorklog(token=authToken, data=worklog)
    return result


def getCtmFolder(ctmApiClient, data):
    ctmData = data
    ctmFolderID = ctmData["entries"][0]["folder_id"]
    ctmFolder = ctmData["entries"][0]["folder"]
    ctmServer = ctmData["entries"][0]["ctm"]
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "getCtmFolder")
        logger.info('CTM Get Job Folder: "%s @ %s"', ctmFolder, ctmServer)
    value = ctm.getCtmDeployedFolder(ctmApiClient=ctmApiClient,
                                     ctmServer=ctmServer,
                                     ctmFolder=ctmFolder)

    # adjust new ctm aapi result
    sCtmDeployedFolderTmp = w3rkstatt.dTranslate4Json(str(value))
    jCtmDeployedFolderTmp = json.loads(sCtmDeployedFolderTmp)
    jCtmDeployedFolder = jCtmDeployedFolderTmp

    # adjust if CTM API access failed
    sJobLogStatus = True
    # Failed to get
    if "Failed to get" in str(sCtmDeployedFolderTmp):
        sJobLogStatus = False
        sEntry = ""
        i = 0
    else:
        sEntry = sCtmDeployedFolderTmp[1:-1]
        i = 1

    # Check future use?
    # if "." in value:
    #     xTemp = value.split(".")
    #     for xLine in xTemp:
    #         zValue = xLine.strip()
    #         # construct json string
    #         if i == 0:
    #             sEntry = '"entry-' + str(i).zfill(4) + '":"' + zValue + '"'
    #         else:
    #             sEntry = sEntry + ',"entry-' + \
    #                 str(i).zfill(4) + '":"' + zValue + '"'
    #         i += 1
    # else:
    #     sEntry = '"entry-0000": "' + value + '"'

    jData = '{"count":' + str(i) + ',"status":' + \
        str(sJobLogStatus) + ',"entries":[{' + str(sEntry) + '}]}'
    sData = w3rkstatt.dTranslate4Json(data=jData)

    return sData


def analyzeAlert4Job(ctmApiClient, raw, data):
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "analyzeAlert4Job")
        logger.info('CTM: Analyze Alert for Jobs - Start')

    jCtmAlert = data
    ctmOrderId = w3rkstatt.getJsonValue(path="$.order_id", data=jCtmAlert)
    ctmJobData = None
    jCtmAlertData = json.dumps(jCtmAlert)
    sCtmAlertData = str(jCtmAlertData)
    jCtmAlertRaw = raw

    sCtmJobInfo = '{"count": 0,"status": "unknown"}'
    sCtmJobOutput = '{"count": 0,"status": "unknown"}'
    sCtmJobLog = '{"count": 0,"status": "unknown"}'
    sCtmJobConfig = '{"count": 0,"status": "unknown"}'

    if not ctmOrderId == "00000" and ctmOrderId is not None:

        if "New" in ctmAlertCallType:
            # Get CTM Job Info
            ctmJobId = w3rkstatt.getJsonValue(path="$.job_id", data=jCtmAlert)
            ctmJobName = w3rkstatt.getJsonValue(path="$.job_name",
                                                data=jCtmAlert)

            if _ctmActiveApi:
                # Get job information
                sCtmJobInfo = getCtmJobInfo(ctmApiClient=ctmApiClient,
                                            data=jCtmAlert)

                if _FutureUse:
                    # Get job output
                    sCtmJobOutput = getCtmJobOutput(ctmApiClient=ctmApiClient,
                                                    data=jCtmAlert)

                    jCtmJobOutput = json.loads(sCtmJobOutput)
                    sCtmJobOutputStatus = jCtmJobOutput["status"]

                    # Get job log
                    # if sCtmJobOutputStatus:
                    #     sCtmJobLog = getCtmJobLog(
                    #         ctmApiClient=ctmApiClient, data=jCtmAlert)
                    # else:
                    #    sCtmJobLog = '{"collection":"no accessible"}'
                    sCtmJobLog = getCtmJobLog(ctmApiClient=ctmApiClient,
                                              data=jCtmAlert)
                    jCtmJobLog = json.loads(sCtmJobLog)
                else:
                    sCtmJobLog = '{"count": 0,"status": "experimental"}'

                # Create JSON object
                jCtmJobInfo = json.loads(sCtmJobInfo)

                # Folder / Job Details
                ctmJobInfoCount = w3rkstatt.getJsonValue(path="$.count",
                                                         data=jCtmJobInfo)

                if ctmJobInfoCount >= 1:
                    sCtmJobConfig = getCtmJobConfig(ctmApiClient=ctmApiClient,
                                                    data=jCtmJobInfo)
                else:
                    xData = '{"count":0,"status":' + \
                        str(None) + ',"entries":[]}'
                    sCtmJobConfig = w3rkstatt.dTranslate4Json(data=xData)

            # Prep for str concat
            sCtmAlertRaw = str(jCtmAlertRaw)
            ctmJobData = '{"uuid":"' + sUuid + '","raw":[' + sCtmAlertRaw + '],"jobAlert":[' + sCtmAlertData + '],"jobInfo":[' + \
                sCtmJobInfo + '],"jobConfig":[' + sCtmJobConfig + '],"jobLog":[' + \
                sCtmJobLog + '],"jobOutput":[' + sCtmJobOutput + ']}'
            ctmJobData = w3rkstatt.dTranslate4Json(data=ctmJobData)

        # Convert event data to the JSON format required by the API.
    else:
        sCtmAlertRaw = str(jCtmAlertRaw)
        sjCtmAlert = w3rkstatt.dTranslate4Json(data=jCtmAlert)
        # defaults
        sCtmJobInfo = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) +
                                                ',"status":' + str(None) +
                                                ',"entries":[]}')
        sCtmJobOutput = w3rkstatt.dTranslate4Json(data='{"count":' +
                                                  str(None) + ',"status":' +
                                                  str(None) + ',"entries":[]}')
        sCtmJobLog = w3rkstatt.dTranslate4Json(data='{"count":' + str(None) +
                                               ',"status":' + str(None) +
                                               ',"entries":[]}')
        sCtmJobConfig = w3rkstatt.dTranslate4Json(data='{"count":' +
                                                  str(None) + ',"status":' +
                                                  str(None) + ',"entries":[]}')
        ctmJobData = '{"uuid":"' + sUuid + '","raw":[' + sCtmAlertRaw + '],"jobAlert":[' + sCtmAlertData + '],"jobInfo":[' + \
            sCtmJobInfo + '],"jobConfig":[' + sCtmJobConfig + '],"jobLog":[' + \
            sCtmJobLog + '],"jobOutput":[' + sCtmJobOutput + ']}'

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "ctmJobData")
        logger.info('CTM: Analyze Alert for Jobs - End')
    return ctmJobData


def analyzeAlert4Core(raw, data):
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "analyzeAlert4Core")
        logger.info('CTM: Analyze Alert for Core - Start')

    jCtmAlert = data
    ctmCoreData = None
    jCtmAlertData = json.dumps(jCtmAlert)
    jCtmAlertRaw = raw

    # Prep for str concat
    sCtmAlertRaw = str(jCtmAlertRaw)
    sCtmAlertData = str(jCtmAlertData)

    ctmCoreData = '{"uuid":"' + sUuid + \
        '","raw":[' + sCtmAlertRaw + '],"coreAlert":[' + sCtmAlertData + ']}'
    ctmCoreData = w3rkstatt.jsonTranslateValues(ctmCoreData)
    ctmCoreData = w3rkstatt.jsonTranslateValuesAdv(ctmCoreData)

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "ctmCoreData")
        logger.info('CTM: Analyze Alert for Core - End')
    return ctmCoreData


def analyzeAlert4Infra(raw, data):
    if _localDebugFunctions:
        logger.debug('Function = "%s" ', "analyzeAlert4Infra")
        logger.info('CTM: Analyze Alert for Infra - Start')

    jCtmAlert = data
    ctmCoreData = None
    jCtmAlertData = json.dumps(jCtmAlert)
    jCtmAlertRaw = raw

    # Prep for str concat
    sCtmAlertRaw = str(jCtmAlertRaw)
    sCtmAlertData = str(jCtmAlertData)

    ctmCoreData = '{"uuid":"' + sUuid + \
        '","raw":[' + sCtmAlertRaw + '],"infraAlert":[' + sCtmAlertData + ']}'
    ctmCoreData = w3rkstatt.jsonTranslateValues(ctmCoreData)
    ctmCoreData = w3rkstatt.jsonTranslateValuesAdv(ctmCoreData)

    if _localDebugFunctions or _localDebugData:
        logger.debug('Data = "%s" ', "ctmCoreData")
        logger.info('CTM: Analyze Alert for Infra - End')
    return ctmCoreData


def writeAlertFile(data, alert, type="job"):
    fileStatus = False
    ctmJobData = data
    if _ctmActiveApi:
        fileType = "ctm-enriched-" + type + "-"
    else:
        fileType = "ctm-basic-" + type + "-"

    fileContent = json.loads(ctmJobData)
    fileJsonStatus = w3rkstatt.jsonValidator(data=ctmJobData)

    if fileJsonStatus:
        fileName = fileType + \
            alert.zfill(8) + "-" + str(epoch).replace(".", "") + ".json"
        filePath = w3rkstatt.concatPath(path=data_folder, folder=fileName)
        fileRsp = w3rkstatt.writeJsonFile(file=filePath, content=fileContent)
        fileStatus = w3rkstatt.getFileStatus(path=filePath)

        if _localDebugFunctions:
            logger.info('Function = "%s" ', "writeAlertFile")
            logger.info('CTM QA Alert File: "%s" ', filePath)

    return fileStatus


if __name__ == "__main__":
    logging.basicConfig(filename=logFile,
                        filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')

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
    sCtmArgDict = ctmAlert2Dict(list=sCtmArguments,
                                start=0,
                                end=len(sCtmArguments))
    jCtmArgs = json.dumps(sCtmArgDict)
    jCtmAlert = json.loads(jCtmArgs)
    ctmAlertId = str(w3rkstatt.getJsonValue(path="$.alert_id",
                                            data=jCtmAlert)).strip()
    ctmRunCounter = None

    # Test integration with sample data
    if not len(ctmAlertId) > 0:
        if _localQA:
            jCtmAlert = {
                "call_type": "I",
                "alert_id": "279",
                "data_center": "ctm-srv.trybmc.com",
                "memname": None,
                "order_id": "0000q",
                "severity": "V",
                "status": "Not_Noticed",
                "send_time": "20220729163544",
                "last_user": None,
                "last_time": None,
                "message": "Ended not OK",
                "run_as": "dbus",
                "sub_application": "Integration",
                "application": "ADE",
                "job_name": "Agent Health",
                "host_id": "ctm-net.trybmc.com",
                "alert_type": "R",
                "closed_from_em": None,
                "ticket_number": None,
                "run_counter": "00014",
                "notes": None
            }

    if len(jCtmAlert) > 0:

        if _localDebugData:
            logger.debug('Function = "%s" ', "__main__")
            logger.debug('CTM Initial Alert JSON: %s', jCtmAlert)

        # Transform CTM Alert
        jCtmAlertRaw = json.dumps(jCtmAlert)
        sCtmAlert = ctm.trasnformtCtmAlert(data=jCtmAlert)
        jCtmAlert = json.loads(sCtmAlert)
        ctmEventType = ctm.extractCtmAlertType(jCtmAlert)
        ctmAlertId = str(
            w3rkstatt.getJsonValue(path="$.alert_id", data=jCtmAlert)).strip()
        ctmAlertCallType = w3rkstatt.getJsonValue(path="$.call_type",
                                                  data=jCtmAlert).strip()
        ctmDataCenter = w3rkstatt.getJsonValue(path="$.data_center",
                                               data=jCtmAlert).strip()
        ctmOrderId = w3rkstatt.getJsonValue(path="$.order_id",
                                            data=jCtmAlert).strip()
        ctmRunCounter = w3rkstatt.getJsonValue(path="$.run_counter",
                                               data=jCtmAlert).strip()
        ctmAlertCat = w3rkstatt.getJsonValue(path="$.system_category",
                                             data=jCtmAlert).strip()
        ctmAlertSev = w3rkstatt.getJsonValue(path="$.severity",
                                             data=jCtmAlert).strip()
        sCtmJobCyclic = w3rkstatt.getJsonValue(path="$.jobInfo.[0].cyclic",
                                               data=jCtmAlert).strip()
        ctmAlertNotes = w3rkstatt.getJsonValue(path="$.notes", data=jCtmAlert)

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

            if _localDebugData:
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

                logger.info('')
                jCtmAlertRawTemp = jCtmAlertRaw.replace('null', 'None')
                logger.info('CMT QA Alert JSON Format 03: %s',
                            jCtmAlertRawTemp)
                logger.info('')

            # xAlert ID
            if not ctmAlertId:
                ctmAlertId = str(
                    w3rkstatt.getJsonValue(path="$.Serial",
                                           data=jCtmAlert)).strip()

            # CTM Login
            try:
                ctmApiObj = ctm.getCtmConnection()
                ctmApiClient = ctmApiObj.api_client
                _ctmActiveApi = True
            except:
                _ctmActiveApi = False
                ctmApiClient = None
                logger.error('CTM Login Status: %s', _ctmActiveApi)

            # Analyze alert
            ctmAlertDataFinal = {}
            if ctmAlertCat == "infrastructure":
                ctmAlertDataFinal = analyzeAlert4Infra(raw=jCtmAlertRaw,
                                                       data=jCtmAlert)
                fileStatus = writeAlertFile(data=ctmAlertDataFinal,
                                            alert=ctmAlertId,
                                            type="infra")

                # Update CTM Alert staus if file is written
                if _ctmActiveApi and fileStatus:
                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")
                    logger.debug('CTM Alert Update Status: "%s"',
                                 ctmAlertsStatus)
            elif ctmAlertCat == "job":
                ctmAlertDataFinal = analyzeAlert4Job(ctmApiClient=ctmApiClient,
                                                     raw=jCtmAlertRaw,
                                                     data=jCtmAlert)
                fileStatus = writeAlertFile(data=ctmAlertDataFinal,
                                            alert=ctmAlertId,
                                            type="job")

                if ctmOrderId == "00000" and ctmRunCounter == 0:
                    # do not create file
                    fileStatus = True
                    if _ctmActiveApi:
                        ctmAlertsStatus = ctm.updateCtmAlertStatus(
                            ctmApiClient=ctmApiClient,
                            ctmAlertIDs=ctmAlertId,
                            ctmAlertStatus="Reviewed")
                        logger.debug('CTM Alert Update Status: "%s"',
                                     ctmAlertsStatus)
                else:
                    # Update CTM Alert staus if file is written
                    fileStatus = writeAlertFile(data=ctmAlertDataFinal,
                                                alert=ctmAlertId,
                                                type="job")

                if _ctmActiveApi and fileStatus:
                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")
                    logger.debug('CTM Alert Update Status: "%s"',
                                 ctmAlertsStatus)
            else:

                ctmAlertDataFinal = analyzeAlert4Core(raw=jCtmAlertRaw,
                                                      data=jCtmAlert)
                fileStatus = writeAlertFile(data=ctmAlertDataFinal,
                                            alert=ctmAlertId,
                                            type="core")

                # Update CTM Alert staus if file is written
                if _ctmActiveApi and fileStatus:
                    ctmAlertsStatus = ctm.updateCtmAlertStatus(
                        ctmApiClient=ctmApiClient,
                        ctmAlertIDs=ctmAlertId,
                        ctmAlertStatus="Reviewed")
                    logger.debug('CTM Alert Update Status: "%s"',
                                 ctmAlertsStatus)

            incident = "INC-0000"
            if integration_itsm_enabled:
                logger.debug('CTM ITSM Integration: "%s"', "Start")
                logger.debug('CTM ITSM Debug: "%s"', _localDebugITSM)
                # Create Incident only once
                # Catch Cyclic Jobs
                if ctmRunCounter == 1 and sCtmJobCyclic:
                    if _localDebugITSM:
                        logger.debug(
                            'CTM ITSM Integration Cyclic Job Run: "%s"',
                            ctmRunCounter)
                    incident = createITSM(data=ctmAlertDataFinal)
                elif ctmRunCounter >= 1 and sCtmJobCyclic:
                    if _localDebugITSM:
                        logger.debug(
                            'CTM ITSM Integration Cyclic Job Run: "%s"',
                            ctmRunCounter)
                    # Update Incident Worklog only
                    incident = "WRK-0000"
                elif ctmRunCounter >= 1 and not sCtmJobCyclic:
                    if _localDebugITSM:
                        logger.debug(
                            'CTM ITSM Integration Normal Job Run: "%s"',
                            ctmRunCounter)
                    incident = createITSM(data=ctmAlertDataFinal)
                elif ctmRunCounter == 0 and not sCtmJobCyclic:
                    incident = "INC-9999"

                else:
                    incident = "INC-0000"

                logger.debug('CTM ITSM Integration: "%s"', "End")

            bhom_event_id = "BHOM-0000"
            if integration_bhom_enabled:
                # translate ctm alert to BHOM format
                # ctmAlertDataFinal = json.dumps(ctmAlertDataFinal)
                jBhomEvent = ctm.transformCtmBHOM(data=ctmAlertDataFinal,
                                                  category=ctmAlertCat)

                # future enhancements -> keep token for 24 hours
                authToken = bhom.authenticate()
                if authToken != None:
                    bhom_event_id = bhom.createEvent(token=authToken,
                                                     event_data=jBhomEvent)
                    time.sleep(10)
                    bhom_assigned_user = w3rkstatt.getJsonValue(
                        path="$.BHOM.user", data=jCfgData)
                    bhom.assignEvent(
                        token=authToken,
                        event_id=bhom_event_id,
                        assigned_user=bhom_assigned_user,
                        event_note="Control-M Alert Integration via: " +
                        hostFqdn)

                    time.sleep(10)
                    bhom_event_note = ctmAlertDataFinal
                    bhom.addNoteEvent(token=authToken,
                                      event_id=bhom_event_id,
                                      event_note=bhom_event_note)

                if _localDebugBHOM:
                    logger.debug('CTM BHOM: Event      : %s', jBhomEvent)
                    logger.debug('CTM BHOM: Event Note : "%s"',
                                 bhom_event_note)
                    logger.debug('CTM BHOM: Event ID   : %s', bhom_event_id)
                    logger.debug('CTM BHOM: Auth Token : %s', authToken)

            # update CTM Alert
            if _ctmActiveApi:
                sAlertNotes = "Processed Alert: #" + incident + "#" + bhom_event_id + "#"
                ctmAlertSev = "Normal"
                ctmAlertsStatus = ctm.updateCtmAlertCore(
                    ctmApiClient=ctmApiClient,
                    ctmAlertIDs=ctmAlertId,
                    ctmAlertComment=sAlertNotes,
                    ctmAlertUrgency=ctmAlertSev)

            # Close cTM AAPI connection
            if _ctmActiveApi:
                ctm.delCtmConnection(ctmApiObj)

            sSysOutMsg = "Processed New Alert: #" + str(
                ctmAlertId) + "#" + incident + "#" + bhom_event_id + "#"

        # Process only 'update' alerts
        if "Update" in ctmAlertCallType:
            if _localDebugData:
                logger.debug('- CTM Alert Update: "%s"', "Start")
                logger.debug('- CTM Alert Notes : "%s"', "ctmAlertNotes")

            sSysOutMsg = "Processed Update Alert: " + str(ctmAlertId)

    if _localInfo:
        logger.info('CTM: end event management - %s', w3rkstatt.sUuid)

    logging.shutdown()

    print(f"Message: {sSysOutMsg}")
