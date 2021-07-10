#!/usr/bin/python
#Filename: disco_ctm.py

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
20210709      Volker Scheithauer    Inital Code

"""


# handle dev environment vs. production 
try:
    import w3rkstatt as w3rkstatt
    import core_ctm as ctm

except:
    # fix import issues for modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    from src import w3rkstatt as w3rkstatt
    from src import core_ctm as ctm

import time, logging
import sys, getopt, platform, argparse
import os, json
from collections import OrderedDict 

# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)

data_folder = logFolder
ctm_host    = w3rkstatt.getJsonValue(path="$.CTM.host",data=jCfgData)
ctm_port    = w3rkstatt.getJsonValue(path="$.CTM.port",data=jCfgData)

# Assign module defaults
_localDebug = False
_localDebugAdv = False
_localInfo = True
_localQA = False
_localQAlert = False
_localDebugITSM = False
_modVer = "0.0.1"
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
sUuid    = w3rkstatt.sUuid

def getCtmAgents(ctmApiClient,ctmServer):
    jCtmAgents = ctm.getCtmAgents(ctmApiClient,ctmServer)

    return jCtmAgents

def getCtmServers(ctmApiClient):
    jCtmServers = ctm.getCtmServers(ctmApiClient=ctmApiClient)
    if _localDebug:  
        logger.debug('CTM Servers: %s', jCtmServers)
    return jCtmServers    

def getCtmServersAdv(ctmApiClient):
    jCtmServers = ctm.getCtmServers(ctmApiClient=ctmApiClient)
    if _localDebug:  
        logger.debug('CTM Servers: %s', jCtmServers)
    iCtmServers = int(len(jCtmServers))
    yCtmServerList = ""
    for xCtmServer in jCtmServers:
            sCtmServerName    = xCtmServer["name"]
            sCtmServerHost    = xCtmServer["host"]
            sCtmServerState   = xCtmServer["state"]
            sCtmServerMsg     = xCtmServer["message"]
            sCtmServerVersion = xCtmServer["version"]
            jCtmServerParams  = ctm.getCtmServerParams(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName)

            # Prepare new JSON
            jParameters = '{'
            jParamEntries = '"name":"' + sCtmServerName + '",'
            jParamEntries = jParamEntries + '"host":"' + sCtmServerHost + '",'
            jParamEntries = jParamEntries + '"state":"' + sCtmServerState + '",'
            jParamEntries = jParamEntries + '"message":"' + sCtmServerMsg + '",'
            jParamEntries = jParamEntries + '"version":"' + sCtmServerVersion + '",'

            if len(jCtmServerParams) > 0:
                for key in jCtmServerParams:
                    
                    sParam = w3rkstatt.dTranslate4Json(data=key)
                    jParam = json.loads(sParam)
                    sParamName = w3rkstatt.getJsonValue(path="$.name",data=jParam).lower()
                    sParamVal  = w3rkstatt.getJsonValue(path="$.value",data=jParam)
                    # logger.debug('CTM Server: %s:%s', sParamName,sParamVal)

                    if len(sParamVal) > 0:
                        jParamEntry = '"' + sParamName + '":"' + sParamVal + '"'
                    else:
                        jParamEntry = '"' + sParamName + '":None'
                    jParamEntries = jParamEntry + "," + jParamEntries

            else:
                pass

            jParamEntries = jParamEntries[:-1]
            jParameters = '{' + str(jParamEntries) + '}'
            sParameters = w3rkstatt.dTranslate4Json(data=jParameters)
            jServerParameters = json.loads(sParameters)
            dParameters = OrderedDict(sorted(jServerParameters.items()))
            dParameters = json.dumps(dParameters)
            xCtmServerList = dParameters

            if iCtmServers > 1:                
                yCtmServerList = xCtmServerList + ',' + yCtmServerList                
            else:
                yCtmServerList = xCtmServerList  

    yCtmServerList = yCtmServerList[:-1]
    zCtmServerList = '[' + yCtmServerList + ']'
    jCtmServers    = w3rkstatt.dTranslate4Json(data=zCtmServerList)    
    if _localDebug:    
        logger.debug('CTM Server Parameters: %s', jCtmServers)

    return jCtmServers    

def discoCtm():
    # CTM Login
    try:
        ctmApiObj    = ctm.getCtmConnection()
        ctmApiClient = ctmApiObj.api_client
        _ctmActiveApi    = True
    except:
        _ctmActiveApi = False
        ctmApiClient = None
        logger.error('CTM Login Status: %s', _ctmActiveApi)


    if _ctmActiveApi:
        jCtmServers =  getCtmServers(ctmApiClient=ctmApiClient)
        jCtmAgentList = {}
        yCtmAgentList = ""
        iCtmServers = int(len(jCtmServers))

        for xCtmServer in jCtmServers:
            sCtmServerName = xCtmServer["name"]
            sCtmServerFQDN = xCtmServer["host"]
            logger.debug('CTM Server: %s', sCtmServerName)

            jCtmAgents = getCtmAgents(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName)
            xCtmAgents = w3rkstatt.getJsonValue(path="$.agents",data=jCtmAgents)
            if "None" in xCtmAgents:
                iCtmAgents = 0
            else:
                iCtmAgents = len(xCtmAgents)

            xCtmAgentList = '{"server":"'  + sCtmServerName  + '","host":"'  + sCtmServerFQDN  +'","runners":'  + str(iCtmAgents)  + ',"agents":' + str(xCtmAgents) + '}'
            if iCtmServers > 1:                
                yCtmAgentList = xCtmAgentList + ',' + yCtmAgentList
            else:
                yCtmAgentList = xCtmAgentList
        yCtmAgentList = yCtmAgentList[:-1]
        zCtmAgentList = '{"inventory":{'+ '"servers":[' + yCtmAgentList + ']}}'
        jCtmAgentList = w3rkstatt.dTranslate4Json(data=zCtmAgentList)

        if _localDebug:  
            logger.debug('CTM Servers: %s', jCtmServers)
        logger.debug('CTM Agents: %s', jCtmAgentList)


    # Close CTM AAPI connection
    if _ctmActiveApi:
        ctm.delCtmConnection(ctmApiObj)

if __name__ == "__main__":
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    
    sSysOutMsg = ""

    if _localInfo: 
        logger.info('CTM: start discovery - %s', w3rkstatt.sUuid)
        logger.info('Version: %s ', _modVer)
        logger.info('System Platform: %s ', w3rkstatt.sPlatform)
        logger.info('Log Level: %s', loglevel)
        logger.info('Epoch: %s', epoch)
        logger.info('Host Name: %s', w3rkstatt.sHostname)
        logger.info('UUID: %s', w3rkstatt.sUuid)

    discoCtm()

    logging.shutdown()

    print (f"Message: {sSysOutMsg}")

