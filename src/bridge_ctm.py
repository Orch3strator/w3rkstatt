#!/usr/bin/python
# bridge_ctm.py

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
20200601      Volker Scheithauer    Initial Development 
20200730      Volker Scheithauer    Modify json handling for WCM
20201009      Volker Scheithauer    Externalize Helix functions
20201009      Volker Scheithauer    Externalize SNOW functions
20201015      Volker Scheithauer    Add Oracle POM Test
20210204      Volker Scheithauer    Remove Oracle POM Test
20210204      Volker Scheithauer    Add TrueSight Orchestrator for WCM
20220701      Volker Scheithauer    Migrate to W3rkstatt project
"""

import logging
import w3rkstatt
import bridge_wcm as wcm
import os
import logging
import time
import datetime
import platform

import bridge_helix as helix
import bridge_tso as tso
import bridge_snow as snow

from werkzeug.serving import WSGIRequestHandler
from flask import Flask, Blueprint, request, render_template, url_for, jsonify, json, Response, make_response
from flask_restx import Resource, Api, reqparse, fields
from flasgger import Swagger
from flasgger.utils import swag_from

# pip install werkzeug flask flask_restful flask-restplus flask-marshmallow flask-restplus-marshmallow flask_restx flasgger

# Define global variables from w3rkstatt.ini file
jCfgFile = w3rkstatt.jCfgFile
jCfgData = w3rkstatt.getFileJson(jCfgFile)
ctm_bridge_host = w3rkstatt.getJsonValue(
    path="$.CTM_BRIDGE.host", data=jCfgData)
ctm_bridge_port = w3rkstatt.getJsonValue(
    path="$.CTM_BRIDGE.port", data=jCfgData)
ctm_bridge_html = w3rkstatt.getJsonValue(
    path="$.CTM_BRIDGE.html", data=jCfgData)
ctm_bridge_api = w3rkstatt.getJsonValue(path="$.CTM_BRIDGE.api", data=jCfgData)
ctm_tso_process = w3rkstatt.getJsonValue(
    path="$.CTM_BRIDGE.tso_process", data=jCfgData)

# itsm_smrtit_host = w3rkstatt.getJsonValue(path="$.SMARTIT.host",data=jCfgData)
# itsm_smrtit_port = w3rkstatt.getJsonValue(path="$.SMARTIT.port",data=jCfgData)
# itsm_smrtit      = "http://" + itsm_smrtit_host + ":" + itsm_smrtit_port + "/smartit/app/#/change/displayid/"

# ITSM template IDs
itsm_tmpl_crq = w3rkstatt.getJsonValue(
    path="$.ITSM.change.template_id", data=jCfgData)


# Assign module defaults
_localDebug = True
_modVer = "1.1"
_timeFormat = '%Y-%m-%dT%H:%M:%S'
logger = logging.getLogger(__name__)
logFile = w3rkstatt.logFile
loglevel = w3rkstatt.getJsonValue(path="$.DEFAULT.loglevel", data=jCfgData)
epoch = time.time()
WSGIRequestHandler.protocol_version = "HTTP/1.1"

# OpenAPI Info
ctmBridgeVersion = "1.2"
ctmBridgeTitle = "CTM ITSM Bridge"
ctmBridgeDesc = "Integrate CTM with IT Service Management"

# CTM WCM variables
STATE_REQUESTER_WORKS = "RequesterWorks"
STATE_SUBMITTED = "Submitted"
STATE_SCHEDULER_WORKS = "SchedulerWorks"
STATE_RETURNED = "Returned"
STATE_APPROVED = "Approved"


# ctm_bridge_api
oApiTempFile = w3rkstatt.getFilePathLocal(ctm_bridge_api)
oApiTempJson = w3rkstatt.getFileJson(oApiTempFile)


ctmBridgeApp = Flask(__name__)
swagger = Swagger(ctmBridgeApp, template=oApiTempJson)


@ctmBridgeApp.route('/')
def home():
    logger.debug('Flask: Get: %s ', "ctmBridgeIndex")
    return render_template(ctm_bridge_html)


# WCM REST API Calls
# WCM - validateChangeState
# WCM - stateChanged
# WCM - getChangeStatus


#
# Support Helix ITSM
#
@ctmBridgeApp.route("/bridge/api/helix/validateChangeState", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.validateChangeState.yml')
def post_validateChangeState():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:

        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "validateChangeState"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            pass
        else:
            ctmChangeID = helix.createHelixCrq(data=ctmDataReq)

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")

        if len(ctmChangeID) > 1:
            ctmChangeStatus = helix.getHelixCrqStatus(data=ctmChangeID)
            ctmResponseCode = helix.translateCrqStatus(status=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        # WCM response json as string in one line
        # ctmDataResp   = '"message":"The change ' + ctmChangeID + ' is in phase: ' + ctmChangeStatus + '"'
        ctmDataResp = '"changeID":"' + ctmChangeID + ' "'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: Validate WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: Validate WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: Validate WCM Workspace: "%s"', ctmWorkspace)
            logger.info('CTM: Validate WCM Response Code: "%s"',
                        ctmResponseCode)
            logger.info('CTM: Validate WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
        return responseFlask

# ./swagger/bridge.ctm.api.stateChanged.yml


@ctmBridgeApp.route("/bridge/api/helix/stateChanged", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.stateChanged.yml')
def post_stateChanged():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = helix.getHelixCrqStatus(data=ctmChangeID)
            ctmResponseCode = helix.translateCrqStatus(status=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmResponseCode = helix.translateCrqStatus(status=ctmChangeStatus)

        if _localDebug:
            logger.info('CTM: State Change WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: State Change WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: State Change WCM Workspace: "%s"', ctmWorkspace)

    # WCM response json as string in one line
        # Helix Smart IT Link
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
        return responseFlask

# ./swagger/bridge.ctm.api.getChangeStatus.yml


@ctmBridgeApp.route("/bridge/api/helix/getChangeStatus", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.getChangeStatus.yml')
def post_getChangeStatus():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = helix.getHelixCrqStatus(data=ctmChangeID)
            ctmResponseCode = helix.translateCrqStatus(status=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmResponseCode = helix.translateCrqStatus(status=ctmChangeStatus)

    # WCM response json as string in one line
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info(
                'CTM: Change Status WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Change Status WCM Change Request ID: "%s"', ctmChangeID)
            logger.info(
                'CTM: Change Status WCM Change Status: "%s"', ctmChangeStatus)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
            logger.info('CTM: Change Status WCM Workspace: "%s"', ctmWorkspace)
            logger.info(
                'CTM: Change Status WCM JSON Response: "%s": %s ', ctmWcmApi, ctmDataResp)
        return responseFlask

#
# Support ServiceNOW
#


@ctmBridgeApp.route("/bridge/api/snow/validateChangeState", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.validateChangeState.yml')
def post_snow_validateChangeState():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:

        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "validateChangeState"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            pass
        else:
            ctmChangeID = snow.createSnowReq(data=ctmDataReq)

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")

        if len(ctmChangeID) > 1:
            ctmChangeStatus = snow.getSnowReqStatus(data=ctmChangeID)
            ctmResponseCode = snow.translateSnowReqStatus(data=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        # WCM response json as string in one line
        # ctmDataResp   = '"message":"The change ' + ctmChangeID + ' is in phase: ' + ctmChangeStatus + '"'
        ctmDataResp = '"changeID":"' + ctmChangeID + ' "'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: Validate WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: Validate WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: Validate WCM Workspace: "%s"', ctmWorkspace)
            logger.info('CTM: Validate WCM Response Code: "%s"',
                        ctmResponseCode)
            logger.info('CTM: Validate WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
        return responseFlask

# ./swagger/bridge.ctm.api.stateChanged.yml


@ctmBridgeApp.route("/bridge/api/snow/stateChanged", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.stateChanged.yml')
def post_snow_stateChanged():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = snow.getSnowReqStatus(data=ctmChangeID)
            ctmResponseCode = snow.translateSnowReqStatus(data=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")

        if _localDebug:
            logger.info('CTM: State Change WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: State Change WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: State Change WCM Workspace: "%s"', ctmWorkspace)

    # WCM response json as string in one line
        # Helix Smart IT Link
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
        return responseFlask

# ./swagger/bridge.ctm.api.getChangeStatus.yml


@ctmBridgeApp.route("/bridge/api/snow/getChangeStatus", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.getChangeStatus.yml')
def post_snow_getChangeStatus():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")

        if len(ctmChangeID) > 1:
            ctmChangeStatus = snow.getSnowReqStatus(data=ctmChangeID)
            ctmResponseCode = snow.translateSnowReqStatus(data=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

    # WCM response json as string in one line
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info(
                'CTM: Change Status WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Change Status WCM Change Request ID: "%s"', ctmChangeID)
            logger.info(
                'CTM: Change Status WCM Change Status: "%s"', ctmChangeStatus)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
            logger.info('CTM: Change Status WCM Workspace: "%s"', ctmWorkspace)
            logger.info(
                'CTM: Change Status WCM JSON Response: "%s": %s ', ctmWcmApi, ctmDataResp)
        return responseFlask


# Support Local
@ctmBridgeApp.route("/bridge/api/local/validateChangeState", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.validateChangeState.yml')
def post_local_validateChangeState():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:

        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "validateChangeState"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            pass
        else:
            ctmChangeID = "LOCAL0001"

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmChangeStatus = "Implementation In Progress"
        ctmResponseCode = 200

        if len(ctmChangeID) > 1:
            ctmResponseCode = 200

        # WCM response json as string in one line
        # ctmDataResp   = '"message":"The change ' + ctmChangeID + ' is in phase: ' + ctmChangeStatus + '"'
        ctmDataResp = '"changeID":"' + ctmChangeID + ' "'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: Validate WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: Validate WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: Validate WCM Workspace: "%s"', ctmWorkspace)
            logger.info('CTM: Validate WCM Response Code: "%s"',
                        ctmResponseCode)
            logger.info('CTM: Validate WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
        return responseFlask

# ./swagger/bridge.ctm.api.stateChanged.yml


@ctmBridgeApp.route("/bridge/api/local/stateChanged", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.stateChanged.yml')
def post_local_stateChanged():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = "LCL0001"
        else:
            ctmChangeStatus = "N/A"

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmResponseCode = 200

        if _localDebug:
            logger.info('CTM: State Change WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: State Change WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: State Change WCM Workspace: "%s"', ctmWorkspace)

    # WCM response json as string in one line
        # Helix Smart IT Link
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
        return responseFlask

# ./swagger/bridge.ctm.api.getChangeStatus.yml


@ctmBridgeApp.route("/bridge/api/local/getChangeStatus", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.getChangeStatus.yml')
def post_local_getChangeStatus():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = "Implementation In Progress"
        else:
            ctmChangeStatus = "N/A"

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmResponseCode = 200

    # WCM response json as string in one line
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info(
                'CTM: Change Status WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Change Status WCM Change Request ID: "%s"', ctmChangeID)
            logger.info(
                'CTM: Change Status WCM Change Status: "%s"', ctmChangeStatus)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
            logger.info('CTM: Change Status WCM Workspace: "%s"', ctmWorkspace)
            logger.info(
                'CTM: Change Status WCM JSON Response: "%s": %s ', ctmWcmApi, ctmDataResp)
        return responseFlask

# Support TrueSight Orchestrator for WCM


@ctmBridgeApp.route("/bridge/api/tso/validateChangeState", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.validateChangeState.yml')
def post_tso_validateChangeState():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:

        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "validateChangeState"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            pass
        else:
            ctmChangeID = tso.createTsoCrq(data=ctmDataReq)

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmChangeStatus = "Implementation In Progress"
        ctmResponseCode = 200

        if len(ctmChangeID) > 1:
            ctmResponseCode = 200

        # WCM response json as string in one line
        # ctmDataResp   = '"message":"The change ' + ctmChangeID + ' is in phase: ' + ctmChangeStatus + '"'
        ctmDataResp = '"changeID":"' + ctmChangeID + ' "'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: Validate WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Validate WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: Validate WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: Validate WCM Workspace: "%s"', ctmWorkspace)
            logger.info('CTM: Validate WCM Response Code: "%s"',
                        ctmResponseCode)
            logger.info('CTM: Validate WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
        return responseFlask

# ./swagger/bridge.ctm.api.stateChanged.yml


@ctmBridgeApp.route("/bridge/api/tso/stateChanged", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.stateChanged.yml')
def post_tso_stateChanged():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = tso.getTsoCrqStatus(data=ctmChangeID)
            ctmResponseCode = tso.translateCrqStatus(status=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmResponseCode = 200

        if _localDebug:
            logger.info('CTM: State Change WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: State Change WCM Change Request ID: "%s"', ctmChangeID)
            logger.info('CTM: State Change WCM Change Status: "%s"',
                        ctmChangeStatus)
            logger.info('CTM: State Change WCM Workspace: "%s"', ctmWorkspace)

    # WCM response json as string in one line
        # Helix Smart IT Link
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info('CTM: WCM JSON Response: "%s": %s ',
                        ctmWcmApi, ctmDataResp)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
        return responseFlask

# ./swagger/bridge.ctm.api.getChangeStatus.yml


@ctmBridgeApp.route("/bridge/api/tso/getChangeStatus", methods=['POST'])
@swag_from('./swagger/bridge.ctm.api.getChangeStatus.yml')
def post_tso_getChangeStatus():
    ctmDataReq = request.get_json()

    if not ctmDataReq:
        ctmDataResp = '"message":"WCM Integration Failure No input data provided"'
        responseFlask = make_response(ctmDataResp, 400)
        responseFlask.mimetype = "application/json"
        return responseFlask
    else:
        ctmDataReq = w3rkstatt.jsonTranslateValues(ctmDataReq)
        ctmWcmApi = "getChangeStatus"
        jCtmDataReq = json.loads(ctmDataReq)
        ctmChangeID = w3rkstatt.getJsonValue(
            path="$.changeID", data=jCtmDataReq)

        if _localDebug:
            logger.debug('CTM: WCM API Request: "%s": %s ',
                         ctmWcmApi, ctmDataReq)

        if len(ctmChangeID) > 1:
            ctmChangeStatus = tso.getTsoCrqStatus(data=ctmChangeID)
            ctmResponseCode = tso.translateCrqStatus(status=ctmChangeStatus)
        else:
            ctmChangeStatus = "N/A"
            ctmResponseCode = 400

        ctmRequestID = w3rkstatt.jsonExtractSimpleValue(
            ctmDataReq, "ctmRequestID")
        ctmWorkspace = w3rkstatt.jsonExtractSimpleValue(ctmDataReq, "name")
        ctmResponseCode = 200

    # WCM response json as string in one line
        ctmTicketLink = helix.itsm_smrtit + ctmChangeID
        ctmDataResp = '"message":"The change ' + ctmChangeID + \
            ' is in phase: ' + ctmChangeStatus + ' Link: ' + ctmTicketLink + '"'
        responseFlask = make_response(ctmDataResp, ctmResponseCode)
        responseFlask.mimetype = "application/json"

        if _localDebug:
            logger.info(
                'CTM: Change Status WCM Request ID: "%s"', ctmRequestID)
            logger.info(
                'CTM: Change Status WCM Change Request ID: "%s"', ctmChangeID)
            logger.info(
                'CTM: Change Status WCM Change Status: "%s"', ctmChangeStatus)
            logger.info('CTM: Change Status WCM Change Link: "%s"',
                        ctmTicketLink)
            logger.info('CTM: Change Status WCM Workspace: "%s"', ctmWorkspace)
            logger.info(
                'CTM: Change Status WCM JSON Response: "%s": %s ', ctmWcmApi, ctmDataResp)
        return responseFlask


def ctmBridge():
    ctmBridgeApp.run(debug=True, host=ctm_bridge_host, port=ctm_bridge_port)


if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logger.info('Flask: CTM WCM Bridge: "Start"')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: "%s" ', platform.system())
    logger.info('Log Level: "%s"', loglevel)
    logger.info('Epoch: %s', epoch)
    logger.info('Flask: Port: %s', ctm_bridge_port)
    logger.info('Flask: Index File: "%s"', ctm_bridge_html)
    logger.info('Flask: OpenAPI Template: "%s"', oApiTempFile)

    ctmBridge()

    logger.info('Flask: CTM WCM Bridge: "End"')
    logging.shutdown()

    print(f"Version: {_modVer}")
