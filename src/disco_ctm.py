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
import pandas as pd
from io import StringIO

import jsonpath_rw_ext
from jsonpath_ng.ext import parse

# Get configuration from bmcs_core.json
jCfgData   = w3rkstatt.getProjectConfig()
cfgFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.config_folder",data=jCfgData)
logFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.log_folder",data=jCfgData)
tmpFolder  = w3rkstatt.getJsonValue(path="$.DEFAULT.template_folder",data=jCfgData)
cryptoFile = w3rkstatt.getJsonValue(path="$.DEFAULT.crypto_file",data=jCfgData)

data_folder = w3rkstatt.getJsonValue(path="$.DEFAULT.data_folder",data=jCfgData)
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

def writeInfoFile(file,content):
    fileStatus = False
    fileContent = json.loads(content)
    fileJsonStatus = w3rkstatt.jsonValidator(data=content)

    if fileJsonStatus:
        fileName    = file
        filePath    = w3rkstatt.concatPath(path=data_folder,folder=fileName)
        fileRsp     = w3rkstatt.writeJsonFile(file=filePath,content=fileContent)  
        fileStatus  = w3rkstatt.getFileStatus(path=filePath)
    else:
        filePath = ""

        if _localQA: 
            logger.info('Info File: "%s" ', filePath)

    return filePath

def writeAgentInfoFile(ctmAgent,data):
    filename   = "ctm.agent." + ctmAgent + ".json"
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath    

def writeRemoteHostsInfoFile(ctmServer,data):
    filename   = "ctm.server.agents.remote." + ctmServer + ".json"
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath 

def writeServerInfoFile(ctmServer,data):
    filename   = "ctm.server." + ctmServer + ".json"
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath  

def writeHostGroupsInfoFile(ctmServer,data):
    filename   = "ctm.hostgroups." + ctmServer + ".json"
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath  

def writeInventoryInfoFile(data):
    filename = "ctm.inventory." + str(epoch).replace(".","") + ".json"
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath 
    
def writeJobTypesInfoFile(data):
    filename = "ctm.job.ai.types.r2d.json"
    data = w3rkstatt.dTranslate4Json(data=data)        
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath 

def writeJobTypesDraftInfoFile(data):
    filename = "ctm.job.ai.types.draft.json"
    data = w3rkstatt.dTranslate4Json(data=data)        
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath 

def writeSharedConnectionProfilesInfoFile(data):
    filename = "ctm.connection.profiles.shared.json"
    data = w3rkstatt.dTranslate4Json(data=data)        
    filePath = writeInfoFile(file=filename,content=data) 
    return filePath 

def getCentralConnectionProfiles(ctmApiClient,jobTypes):
    # Base Applications    
    sCtmAppTypes = jobTypes      
    jConnProfiles = ""         

    for appType in sCtmAppTypes:
        if _localDebug: 
            logger.debug(' - Action: %s : %s',"Get Connection Profile",appType)
        jProfiles = ctm.getCtmCentralConnectionProfile(ctmApiClient=ctmApiClient,ctmAppType=appType)
        jProfilesLen = len(jProfiles)
        if jProfilesLen > 0:
            logger.debug(' - Action: %s : %s',"Found Connection Profile",appType)
            jProfile = '"' + appType + '":'
            jProfile = jProfile + str(jProfiles)
            jConnProfiles = jProfile + "," + jConnProfiles
        else:
            if _localDebug: 
                jProfile = '"' + appType + '":None'
                jConnProfiles = jProfile + "," + jConnProfiles

                            
    jConnProfiles = str(jConnProfiles).rstrip(',')
    jConnProfilsWrapper = '{"apps":{' +  jConnProfiles + '}}'
    sConnProfile = w3rkstatt.dTranslate4Json(data=jConnProfilsWrapper)      
   
    return sConnProfile

def getLocalConnectionProfiles(ctmApiClient,ctmServer,ctmAgent,ctmAppType):
    # Base Applications    
    sCtmAppTypes = ctmAppType      
    jConnProfiles = ""                    

    for appType in sCtmAppTypes:
        if _localDebug: 
            pass
        logger.debug(' - Action: %s : %s',"Get Connection Profile",appType)
        jProfiles = ctm.getCtmAgentConnectionProfile(ctmApiClient=ctmApiClient,ctmServer=ctmServer,ctmAgent=ctmAgent,ctmAppType=appType)
        jProfilesLen = len(jProfiles)
        if jProfilesLen > 0:
            logger.debug(' - Action: %s : %s',"Found Connection Profile",appType)
            jProfile = '"' + appType + '":'
            jProfile = jProfile + str(jProfiles)
            jConnProfiles = jProfile + "," + jConnProfiles
        else:
            if _localDebug: 
                jProfile = '"' + appType + '":None'
                jConnProfiles = jProfile + "," + jConnProfiles

    jConnProfiles = str(jConnProfiles).rstrip(',')
    jConnProfilsWrapper = '{"apps":{' +  jConnProfiles + '}}'
    sConnProfile = w3rkstatt.dTranslate4Json(data=jConnProfilsWrapper)       
   
    return sConnProfile

def getCentralConnectionProfilesAi(ctmApiClient,jobTypes):
    appTypes = jobTypes["jobtypes"]
    jConnProfiles = ""
    for appType in appTypes:
        job_type_name = appType["job_type_name"]
        job_type_id = appType["job_type_id"]
        appTypeAi = "ApplicationIntegrator:" + job_type_name
        if _localDebug: 
            logger.debug(' - Action: %s : %s',"Get Connection Profile",appTypeAi)
        jProfiles = ctm.getCtmCentralConnectionProfile(ctmApiClient=ctmApiClient,ctmAppType=appTypeAi)
        jProfilesLen = len(jProfiles)
        if jProfilesLen > 0:
            logger.debug(' - Action: %s : %s',"Found Connection Profile",job_type_id)
            jProfile = '"' + job_type_id + '":'
            jProfile = jProfile + str(jProfiles)
            jConnProfiles = jProfile + "," + jConnProfiles
        else:
            if _localDebug: 
                jProfile = '"' + job_type_id + '":None'
                jConnProfiles = jProfile + "," + jConnProfiles    
                                                            
    jConnProfiles = str(jConnProfiles).rstrip(',')
    jConnProfilsWrapper = '{"ai":{' +  jConnProfiles + '}}'
    sConnProfile = w3rkstatt.dTranslate4Json(data=jConnProfilsWrapper)      
   
    return sConnProfile

def getLocalConnectionProfilesAi(ctmApiClient,ctmServer,ctmAgent,ctmAppType):
    appTypes = ctmAppType["jobtypes"]
    jConnProfiles = ""
    for appType in appTypes:
        job_type_name = appType["job_type_name"]
        job_type_id = appType["job_type_id"]
        appTypeAi = "ApplicationIntegrator:" + job_type_name
        if _localDebug: 
            pass
        logger.debug(' - Action: %s : %s',"Get Connection Profile",appTypeAi)
        jProfiles = ctm.getCtmAgentConnectionProfile(ctmApiClient=ctmApiClient,ctmServer=ctmServer,ctmAgent=ctmAgent,ctmAppType=appTypeAi)
        jProfilesLen = len(jProfiles)
        if jProfilesLen > 0:
            logger.debug(' - Action: %s : %s',"Found Connection Profile",job_type_id)
            jProfile = '"' + job_type_id + '":'
            jProfile = jProfile + str(jProfiles)
            jConnProfiles = jProfile + "," + jConnProfiles
        else:
            if _localDebug: 
                jProfile = '"' + job_type_id + '":None'
                jConnProfiles = jProfile + "," + jConnProfiles    
                                                            
    jConnProfiles = str(jConnProfiles).rstrip(',')
    jConnProfilsWrapper = '{"ai":{' +  jConnProfiles + '}}'
    sConnProfile = w3rkstatt.dTranslate4Json(data=jConnProfilsWrapper)      
   
    return sConnProfile

def getHostGroups(ctmApiClient,ctmServer):
    # Get HostGroups
    sHostGroupList = '{"groups":[]}'
    jCtmHostGroups = ctm.getCtmHostGroups(ctmApiClient=ctmApiClient,ctmServer=ctmServer)
    iCtmHostGroups = len(jCtmHostGroups)
    lHostGroup = ""
    if iCtmHostGroups > 0:
        sjCtmHostGroups = str(jCtmHostGroups)
        j = 0
        for sHostGroupName in jCtmHostGroups:
            sCtmGroupId  = str(j).zfill(4)
            sHostGroupMembers = ""
            
            jHostGroupMembers = ctm.getCtmHostGroupMembers(ctmApiClient=ctmApiClient,ctmServer=ctmServer,ctmHostGroup=sHostGroupName)
            iHostGroupMembers = len(jHostGroupMembers)
            i = 0
            for sHostGroupMember in jHostGroupMembers:
                sHostGroupMember = str(sHostGroupMember).replace("host",str(i).zfill(4)) 
                
                sCtmAgentName = str(sHostGroupMember).split("'")[3]
                sCtmAgentId  = str(i).zfill(4)
                sCtmAgentGroup = sHostGroupName
                sCtmAgent = '{"id":"G' + sCtmGroupId + 'A' + sCtmAgentId + '","server":"' + ctmServer + '","group":"' + sCtmAgentGroup + '","agent":"' + sCtmAgentName + '"}' 

                sHostGroupMembers = sCtmAgent + "," + sHostGroupMembers 
                i = int(i + 1)
            j = int(j + 1)
            sHostGroupMembers =  w3rkstatt.dTranslate4Json(data=sHostGroupMembers[:-1])        
            lHostGroup = sHostGroupMembers + ',' + lHostGroup
        lHostGroup = lHostGroup[:-1]
        sHostGroupList = '{"groups":[' + lHostGroup+ ']}'

    jHostGroupList = json.loads(sHostGroupList)
    return jHostGroupList

def getAgentHostGroupsMembership(ctmHostGroups,ctmAgent="*"):
    jHostGroupList = ctmHostGroups 
    # Load Control-M Hostgroup into panda dataframe
    df = pd.json_normalize(jHostGroupList,record_path=['groups'])

    if df.empty:
        logger.error('Empty dataframe, no agent records')  
        jCtmAgents = {}
    else:
        dfCtmAgents = df.groupby('agent')['group'].apply(list).reset_index(name='groups')
        jCtmAgents = dfCtmAgents.to_json(orient ='records')

        # Get matching agent via panda dataframe
        if ctmAgent != "*":
            xCtmAgentGroups = df.loc[df['agent'] == ctmAgent]
            yCtmAgentGroups = xCtmAgentGroups.groupby('agent')['group'].apply(list).reset_index(name='groups')
            zCtmAgentGroups = yCtmAgentGroups.to_json(orient ='records')
            jCtmAgents = zCtmAgentGroups
    if _localDebug: 
        logger.debug('CTM Panda records:\n %s', jCtmAgents)  
    return jCtmAgents

def getCtmRemoteHosts(ctmApiClient,ctmServer):
    # Get Remote Hosts
    sRemoteHostsList = "{}"
    sRemoteHostList = ""
    jRemoteHosts = ctm.getCtmRemoteHosts(ctmApiClient=ctmApiClient,ctmServer=ctmServer)
    iRemoteHosts = len(jRemoteHosts)
    if iRemoteHosts > 1:  
        sRemoteHosts = str(jRemoteHosts)
        xRemoteHosts = w3rkstatt.dTranslate4Json(data=sRemoteHosts)    
        
        
        j = 0
        for xRemoteHost in jRemoteHosts:
            sCtmHostId  = str(j).zfill(4)
            jRemoteHostProperties = ctm.getRemoteHostProperties(ctmApiClient=ctmApiClient,ctmServer=ctmServer,ctmRemoteHost=xRemoteHost)

            jCtmAgents = jRemoteHostProperties["agents"]
            iCtmAgents = len(jCtmAgents)
            sRemoteHostAgentMembers = ""
            if iCtmAgents > 0:
                i = 0
                for sCtmAgent in jCtmAgents:
                    sCtmAgentName = sCtmAgent
                    sCtmAgentId  = str(i).zfill(4)                
                    sRemoteHostAgent = '{"id":"R' + sCtmHostId + 'A' + sCtmAgentId + '","server":"' + ctmServer + '","host":"' + xRemoteHost + '","agent":"' + sCtmAgentName + '"}' 
                    sRemoteHostAgentMembers = sRemoteHostAgent + "," + sRemoteHostAgentMembers   
                    sRemoteHostAgentMembers = str(sRemoteHostAgentMembers).rstrip(",")
                    i = int(i + 1)

            sRemoteHostList = sRemoteHostAgentMembers + "," + sRemoteHostList
            sRemoteHostList = str(sRemoteHostList).rstrip(",")
                
            j = int(j + 1)
          
        yRemoteHostList =  w3rkstatt.dTranslate4Json(data=sRemoteHostList)   
    else:
        yRemoteHostList = "{}"

    xRemoteHostFinal = '{"remote":[' + yRemoteHostList+ ']}' 
    sRemoteHostFinal = w3rkstatt.dTranslate4Json(data=xRemoteHostFinal)   
    jRemoteHostFinal = json.loads(sRemoteHostFinal)

    return jRemoteHostFinal

def getAgentRemoteHosts(ctmRemoteHosts,ctmAgent="*"):
    jRemoteHostList = ctmRemoteHosts 
    # Load Control-M Hostgroup into panda dataframe
    df = pd.json_normalize(jRemoteHostList,record_path=['remote'])

    if df.empty:
        logger.error('Empty dataframe, no remote hosts records')  
        jCtmAgents = {}
    else:
        dfCtmAgents = df.groupby('agent')['host'].apply(list).reset_index(name='host')
        jCtmAgents = dfCtmAgents.to_json(orient ='records')

        # Get matching agent via panda dataframe
        if ctmAgent != "*":
            xCtmAgentGroups = df.loc[df['agent'] == ctmAgent]
            yCtmAgentGroups = xCtmAgentGroups.groupby('agent')['host'].apply(list).reset_index(name='hosts')
            zCtmAgentGroups = yCtmAgentGroups.to_json(orient ='records')
            jCtmAgents = zCtmAgentGroups
    if _localDebug:  
        logger.debug('CTM Panda records:\n %s', jCtmAgents)  
    return jCtmAgents

def getServerRemoteHosts(ctmRemoteHosts,ctmServer):
    # Load Control-M Hostgroup into panda dataframe
    jData = ctmRemoteHosts
    df = pd.json_normalize(jData,record_path=['remote'])

    if df.empty:
        logger.error('Empty dataframe, no remote hosts records')  
        dfList = []
    else:        
        dfEntries = df['host'].unique()
        dfList = dfEntries.tolist()
        if _localDebug:  
            logger.debug('CTM Panda records:\n %s', dfList) 

    values = json.dumps(dfList)
    if _localDebug:  
        logger.debug('CTM Panda records:\n %s', values)  

    return values


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

        # Get CTM Job Types and
        jCtmAiJobTypes      = ctm.getDeployedAiJobtypes(ctmApiClient=ctmApiClient,ctmAiJobDeployStatus="ready to deploy")
        jCtmAiJobTypesDraft = ctm.getDeployedAiJobtypes(ctmApiClient=ctmApiClient,ctmAiJobDeployStatus="draft")
        sCtmAppTypes        = ["Hadoop","Database","FileTransfer","Informatica","SAP","AWS","Azure"]

        # Count CTM AI job types
        iCtmAiJobTypes      = len(jCtmAiJobTypes['jobtypes'])
        iCtmAiJobTypesDraft = len(jCtmAiJobTypesDraft['jobtypes'])
        iCtmAppTypes        = len(sCtmAppTypes)
        sCtmAiJobTypes      = '{"r2d":"' + str(iCtmAiJobTypes) + '","draft":"' + str(iCtmAiJobTypesDraft) + '","apps":"' + str(iCtmAppTypes)  + '"}'

        # Get CTM Shared Connection Profiles
        jCtmCentralConnectionProfilesBase     = getCentralConnectionProfiles(ctmApiClient=ctmApiClient,jobTypes=sCtmAppTypes)
        jCtmCentralConnectionProfilesAi       = getCentralConnectionProfilesAi(ctmApiClient=ctmApiClient,jobTypes=jCtmAiJobTypes)
        jCtmCentralConnectionProfilesBaseTemp = str(jCtmCentralConnectionProfilesBase).lstrip('{')[:-1]
        jCtmCentralConnectionProfilesAiTemp   = str(jCtmCentralConnectionProfilesAi).lstrip('{')[:-1]
        jCtmCentralConnectionProfiles = '{"shared":{'  + jCtmCentralConnectionProfilesBaseTemp + ',' +  jCtmCentralConnectionProfilesAiTemp + '}}'


        # Write Control-M AI JobTypes File
        filePath    = writeJobTypesInfoFile(data=jCtmAiJobTypes)
        filePath    = writeJobTypesDraftInfoFile(data=jCtmAiJobTypesDraft)        
        filePath    = writeSharedConnectionProfilesInfoFile(data=jCtmCentralConnectionProfiles)
        

        for xCtmServer in jCtmServers:
            sCtmServerName = xCtmServer["name"]
            sCtmServerFQDN = xCtmServer["host"]
            logger.debug('CTM Server: %s', sCtmServerName)      

            # Get Control-M Server Parameters
            jCtmServerParameters = ctm.getCtmServerParams(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName)
            iCtmServerParameters = len(jCtmServerParameters)
            if iCtmServerParameters > 0:
                sCtmServerParameters = w3rkstatt.dTranslate4Json(data=jCtmServerParameters)
            else:
                # Mainframe has no data
                sCtmServerParameters = "[]"

            # Get Remote Hosts
            jCtmRemoteHosts = getCtmRemoteHosts(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName)
            sCtmRemoteHosts = w3rkstatt.dTranslate4Json(data=jCtmRemoteHosts)   
            filePath      = writeRemoteHostsInfoFile(ctmServer=sCtmServerName,data=sCtmRemoteHosts)

            jCtmServerRemoteHosts = json.loads(getServerRemoteHosts(ctmRemoteHosts=jCtmRemoteHosts,ctmServer=sCtmServerName))
            iCtmServerRemoteHosts = len(jCtmServerRemoteHosts)
            if iCtmServerRemoteHosts > 1:
                sServerRemoteHosts = str(jCtmServerRemoteHosts)
                sServerRemoteHosts = w3rkstatt.dTranslate4Json(data=sServerRemoteHosts) 
            else:
                sServerRemoteHosts = "[]"            
            
            
            # Get Control-M Agents
            jCtmAgents = getCtmAgents(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName)
            xCtmAgents = w3rkstatt.getJsonValue(path="$.agents",data=jCtmAgents)

            # Get Control-M Hostgroups
            jCtmHostGroups = getHostGroups(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName)
            sCtmHostGroups = w3rkstatt.dTranslate4Json(data=jCtmHostGroups)   
            filePath     = writeHostGroupsInfoFile(ctmServer=sCtmServerName,data=sCtmHostGroups)
            
            # Sample Debug data
            # xCtmAgents = [{'hostgroups': 'None', 'nodeid': 'vw-aus-ctm-wk01.adprod.bmc.com', 'operating_system': 'Microsoft Windows Server 2016  (Build 14393)', 'status': 'Available', 'version': '9.0.20.000'}]
            xCtmAgentsInfo = ""
            if "None" in xCtmAgents:
                iCtmAgents = 0
                xCtmAgentsInfo = {}
            else:
                iCtmAgents = len(xCtmAgents)

            if iCtmAgents > 0:
                iCtmAgent = 1
                for xAgent in xCtmAgents:
                    
                    sParam = w3rkstatt.dTranslate4Json(data=xAgent)
                    jParam = json.loads(sParam)
                    if _localDebug: 
                        logger.debug('CTM Agent "%s": %s', str(iCtmAgent), sParam)

                    sAgentName       = str(w3rkstatt.getJsonValue(path="$.nodeid",data=jParam))
                    sAgentStatus     = str(w3rkstatt.getJsonValue(path="$.status",data=jParam))
                    sAgentVersion    = str(w3rkstatt.getJsonValue(path="$.version",data=jParam))
                    sAgentOS         = str(w3rkstatt.getJsonValue(path="$.operating_system",data=jParam))
                    sConnProfile     = ""
                    logger.debug('CTM Agent "%s/%s" Status: %s = %s', iCtmAgent, iCtmAgents, sAgentName, sAgentStatus)

                    # Get CTM Agent Remote Hosts
                    jAgentRemoteHosts = json.loads(getAgentRemoteHosts(jCtmRemoteHosts,ctmAgent=sAgentName))
                    iAgentRemoteHosts = len(jAgentRemoteHosts)
                    if iAgentRemoteHosts == 1:
                        lAgentRemoteHosts = jAgentRemoteHosts[0]
                        sAgentRemoteHosts = str(w3rkstatt.getJsonValue(path="$.hosts",data=lAgentRemoteHosts))
                        sAgentRemoteHosts = w3rkstatt.dTranslate4Json(data=sAgentRemoteHosts) 
                    else:
                        sAgentRemoteHosts = "[]"

                    # Get CTM Agent Hostgroup Membership
                    jAgentHostGroupsMembership = json.loads(getAgentHostGroupsMembership(ctmHostGroups=jCtmHostGroups,ctmAgent=sAgentName))
                    iAgentHostGroupsMembership = len(jAgentHostGroupsMembership)
                    if iAgentHostGroupsMembership == 1:
                        lAgentHostGroupsMembership = jAgentHostGroupsMembership[0]   
                        sAgentHostGroupsMembership = str(w3rkstatt.getJsonValue(path="$.groups",data=lAgentHostGroupsMembership))
                        sAgentHostGroupsMembership = w3rkstatt.dTranslate4Json(data=sAgentHostGroupsMembership)             
                    else:
                        sAgentHostGroupsMembership = "[]"    

                    # Get Control-M agent info of active agent               
                    if sAgentStatus == "Available":     
                         # Get CTM Agent Parameters
                        logger.debug(' - Action: %s', "Get Parameters")
                        jCtmAgentParams = ctm.getCtmAgentParams(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName,ctmAgent=sAgentName)
                        dCtmAgentParams = ctm.simplifyCtmJson(data=jCtmAgentParams)
                       
                        jAgentInfo = '{"name":"' + sAgentName + '",'
                        jAgentInfo = jAgentInfo + '"nodeid":"' + sAgentName + '",'
                        jAgentInfo = jAgentInfo + '"status":"' + sAgentStatus + '",'
                        jAgentInfo = jAgentInfo + '"hostgroups":' + sAgentHostGroupsMembership + ','
                        jAgentInfo = jAgentInfo + '"remote":' + sAgentRemoteHosts + ','
                        jAgentInfo = jAgentInfo + '"version":"' + sAgentVersion + '",'
                        jAgentInfo = jAgentInfo + '"operating_system":"' + sAgentOS + '",'   
                        jAgentInfo = jAgentInfo + '"server_name":"' + sCtmServerName + '",'   
                        jAgentInfo = jAgentInfo + '"server_fqdn":"' + sCtmServerFQDN + '",'   
                        jAgentInfo = jAgentInfo + '"parameters":' + dCtmAgentParams + ','

                        # Get CTM Agent Connection Profiles
                        # Base Application and Application Integrator Job Type based connection profile
                        jCtmLocalConnectionProfilesAi   = getLocalConnectionProfilesAi(ctmApiClient,ctmServer=sCtmServerName,ctmAgent=sAgentName,ctmAppType=jCtmAiJobTypes)
                        jCtmLocalConnectionProfilesBase = getLocalConnectionProfiles(ctmApiClient=ctmApiClient,ctmServer=sCtmServerName,ctmAgent=sAgentName,ctmAppType=sCtmAppTypes)
                        jCtmLocalConnectionProfilesBaseTemp = str(jCtmLocalConnectionProfilesBase).lstrip('{')[:-1]
                        jCtmLocalConnectionProfilesAiTemp   = str(jCtmLocalConnectionProfilesAi).lstrip('{')[:-1]
                        jCtmLocalConnectionProfiles = '"profiles":{'  + jCtmLocalConnectionProfilesBaseTemp + ',' +  jCtmLocalConnectionProfilesAiTemp + '}'            

                        # Add to local CTM agent info
                        jAgentInfo = jAgentInfo + jCtmLocalConnectionProfiles + '}'
                        jAgentInfo = w3rkstatt.dTranslate4Json(data=jAgentInfo)              
                        
                                               
                    else:
                        jAgentInfo = '{"name":"' + sAgentName + '",'
                        jAgentInfo = jAgentInfo + '"nodeid":"' + sAgentName + '",'
                        jAgentInfo = jAgentInfo + '"status":"' + sAgentStatus + '",'
                        jAgentInfo = jAgentInfo + '"hostgroups":' + sAgentHostGroupsMembership + ','
                        jAgentInfo = jAgentInfo + '"remote":' + sAgentRemoteHosts + ','
                        jAgentInfo = jAgentInfo + '"version":"' + sAgentVersion + '",'
                        jAgentInfo = jAgentInfo + '"operating_system":"' + sAgentOS + '",'  
                        jAgentInfo = jAgentInfo + '"server_name":"' + sCtmServerName + '",'   
                        jAgentInfo = jAgentInfo + '"server_fqdn":"' + sCtmServerFQDN + '"}'  
                    if _localDebug: 
                        logger.debug('CTM Agent Info: %s', jAgentInfo)

                    if iCtmAgents == 1:
                        xCtmAgentsInfo = str(jAgentInfo).rstrip(',')
                    else:
                        xCtmAgentsInfo = str(jAgentInfo + ',' +xCtmAgentsInfo).rstrip(',')
                    # Internal Agent Counter
                    iCtmAgent = iCtmAgent + 1

                    # Write Status File for Agent
                    jAgentInfo = w3rkstatt.dTranslate4Json(data=jAgentInfo)   
                    filePath = writeAgentInfoFile(ctmAgent=sAgentName,data=jAgentInfo)
                
            xCtmAgentList = '{"server":"'  + sCtmServerName  + '","host":"'  + sCtmServerFQDN  +'","parameters":' + sCtmServerParameters + ',"runners":'  + str(iCtmAgents) + ',"remote":'  + str(sServerRemoteHosts)  + ',"agents":[' + str(xCtmAgentsInfo) + ']}'
            # Write Server Status File
            filePath = writeServerInfoFile(ctmServer=sCtmServerName,data=xCtmAgentList)
            
            if iCtmServers > 1:                
                yCtmAgentList = str(xCtmAgentList + ',' + yCtmAgentList).rstrip(',')
            else:
                yCtmAgentList = str(xCtmAgentList).rstrip(',')

        

        yCtmAgentList = yCtmAgentList
        zCtmAgentList = '{"inventory":{'+ '"servers":[' + yCtmAgentList + '],"profiles":' + jCtmCentralConnectionProfiles + ',"jobtypes":' + sCtmAiJobTypes + '}}'
        jCtmAgentList = w3rkstatt.dTranslate4Json(data=zCtmAgentList)

        # Write Inventory File
        filePath    = writeInventoryInfoFile(data=jCtmAgentList)

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

