#!/usr/bin/env python3
#Filename: w3rkstatt.py
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
20210513      Volker Scheithauer    Tranfer Development from other projects
20210513      Volker Scheithauer    Add Password Encryption
20220715      Volker Scheithauer    Add API Key Encryption

"""

import logging
import os
import json
import socket
import platform
import shutil
import errno
import uuid
import re
import time
import datetime
import urllib
import json
import sys
import random
from os.path import expanduser

from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from jsonpath_ng import jsonpath
from jsonpath_ng.ext import parse

try:
    # Cryptodome
    from base64 import b64encode, b64decode
    from Cryptodome.Cipher import AES
    from Cryptodome.Util.Padding import pad, unpad
    from Cryptodome.Random import get_random_bytes
except:
    # Crypto ?
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    from Crypto.Util.Padding import pad, unpad
    from Crypto.Random import get_random_bytes

_modVer = "2.0"
_timeFormat = '%d %b %Y %H:%M:%S,%f'
_localDebug = False
_SecureDebug = True


# Global functions

def getRandomNumber(l):
    '''
    Generate a random 10 digit number

    :param int l: random number lenght
    :return: the random number
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A
    '''
    minimum = pow(10, l-1)
    maximum = pow(10, l) - 1
    value = int(random.randint(minimum, maximum))
    return value


def getCurrentFolder():
    '''
    Get the current folder 

    :return: the current path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A
    '''
    path = str(os.path.dirname(os.path.abspath(__file__)))
    return path


def getParentFolder(folder):
    '''
    Get the parent folder of given path

    :param str folder: a given path
    :return: the parent path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    parentFolder = str(Path(folder).parent)
    return parentFolder


def getFiles(path, pattern):
    '''
    Get the all files in a given folder matching search pattern

    :param str path: a given path
    :param str pattern: a given search pattern
    :return: files
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    files = []
    with os.scandir(path) as listOfEntries:
        for entry in listOfEntries:
            if entry.is_file():
                if entry.name.endswith(pattern):
                    if _localDebug:
                        logger.debug('Core: File Name: %s', entry.name)
                    file = os.path.join(path, entry.name)
                    files.append(file)
    return files


def concatPath(path, folder):
    '''
    Concateneate path and folder

    :param str path: a given path
    :param str folder: a given folder name
    :return: path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    value = str(os.path.join(path, folder))
    return value


def getFileStatus(path):
    '''
    Check if file exists

    :param str path: a given file name, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    return os.path.isfile(path)


def getFolderStatus(path):
    '''
    Check if folder exists

    :param str path: a given folder, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    return os.path.exists(path)


def createFolder(path):
    '''
    Create folder, if it does not exist

    :param str path: a given folder, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: OSError
    :raises TypeError: N/A    
    '''
    sFolderStatus = getFolderStatus(path)
    if not sFolderStatus:
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def getFileName(path):
    '''
    Get file name from fully qualified file path

    :param str path: a given file, fully qualified
    :return: file name
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    fileName = str(os.path.basename(path))
    return fileName


def getFileJson(file):
    '''
    Read json file content

    :param str file: a given json formatted file, fully qualified
    :return: file name
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    with open(file) as f:
        data = json.load(f)
    return data


def getFilePathLocal(file):
    '''
    Get parent folder of file, fully qualified

    :param str file: a given file name, fully qualified
    :return: parent folder
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    return os.path.join(getCurrentFolder(), file)


def getFileDate(path):
    '''
    Get file date, fully qualified

    :param str path: a given file name, fully qualified
    :return: file date
    :rtype: datetime
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    try:
        fTime = os.path.getmtime(path)
    except OSError:
        fTime = 0
    fileTime = datetime.datetime.fromtimestamp(fTime)
    return fileTime


def getEpoch(timeVal, timeFormat):
    '''
    Get epoch from provided time 

    :param datetime timeVal: time
    :param str timeFormat: time format
    :return: epoch
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    epoch = int(time.mktime(time.strptime(timeVal, timeFormat)))
    return epoch


def getTime():
    '''
    Get time  

    :return: epoch
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    ts = datetime.datetime.now().timestamp()
    return ts


def getCurrentDate(timeFormat=""):
    '''
    Get current date  

    :param str timeFormat: time format
    :return: string
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if len(timeFormat) < 1:
        tf = _timeFormat
    else:
        tf = timeFormat

    ts = datetime.datetime.now()
    dt = ts.strftime(tf)
    return dt


def addTimeDelta(date, delta, timeFormat=""):
    '''
    Add delta to given date  

    :param str dt: date string
    :param str delta: time delta int
    :param str timeFormat: time format
    :return: string
    :rtype: int
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    if len(timeFormat) < 1:
        tf = _timeFormat
    else:
        tf = timeFormat
    #  '%Y-%m-%dT%H:%M:%S'
    epoch = getEpoch(timeVal=date, timeFormat=timeFormat)
    dtDY = int(time.strftime('%Y', time.localtime(epoch)))
    dtDM = int(time.strftime('%m', time.localtime(epoch)))
    dtDD = int(time.strftime('%d', time.localtime(epoch)))
    dtTH = int(time.strftime('%H', time.localtime(epoch)))
    dtTM = int(time.strftime('%M', time.localtime(epoch)))
    dtTS = int(time.strftime('%S', time.localtime(epoch)))
    dltDt = datetime.datetime(dtDY, dtDM, dtDD, dtTH, dtTM,
                              dtTS) + datetime.timedelta(days=delta)
    value = dltDt.strftime(tf)

    return value


def jsonValidator(data):
    '''
    Check if content is valid json

    :param str data: json content
    :return: status
    :rtype: boolean
    :raises ValueError: see log file
    :raises TypeError: N/A    
    '''
    try:
        json.loads(data)
        return True
    except ValueError as error:
        logger.error('Script: Invalid json: %s', error)
        return False


def readFile(file):
    '''
    Read file content

    :param str file: a given file name, fully qualified
    :return: content
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    lines = []
    i = 0
    with open(file, encoding='windows-1252') as fp:
        line = fp.readline()
        while line:
            i += 1
            lines.append(line)
            line = fp.readline()
    fp.close
    return lines


def readHtmlFile(file):
    '''
    Read file content

    :param str file: a given file name, fully qualified
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    lines = ""
    i = 0
    # with open(file, encoding='windows-1252') as fp:
    #         lines = fp.readlines()
    # fp.close

    with open(file, 'r', encoding='UTF-8') as file:
        lines = file.read().replace('\n', '')

    return lines


def writeJsonFile(file, content):
    '''
    Write file content

    :param str file: a given file name, fully qualified
    :param str content: file content
    :return: status
    :rtype: boolean
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    status = True
    try:
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
    except ValueError as error:
        status = False
        logger.error('Script: Invalid json: %s', error)

    return status


def getJsonValue(path, data):
    '''
    Extract data from json content using jsonPath

    :param str path: jsonPath expression
    :param dict data: json content
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    jpexp = parse(path)
    match = jpexp.find(data)
    try:
        value = match[0].value
    except:
        value = ""

    return value


def getJsonValues(path, data):
    '''
    Extract data from json content using jsonPath

    :param str path: jsonPath expression
    :param dict data: json content
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    jpexp = parse(path)
    values = [match.value for match in jpexp.find(data)]
    return values


def jsonTranslateValues(data):
    '''
    Replace predefined str in json content

    :param str data: jsonPath expression
    :return: content
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    sData = ""
    data = str(data)
    sData = str(data).replace("'", '"')

    isJsonData = jsonValidator(data=sData)
    if isJsonData:

        jData = json.loads(sData)
        if isinstance(jData, dict):
            for key in jData:
                if jData[key] is False:
                    jData[key] = 'false'
                if jData[key] is True:
                    jData[key] = 'true'
                if jData[key] is None:
                    jData[key] = 'null'

            # for (key, value) in jData.items():
            #     if value == "False":
            #         value = "false"
            #     elif value == "True":
            #         value = "true"
            #     elif value == "None":
            #         value = "null"
            #     jData[key] = value

        sData = str(jData).replace("'", '"')

        # data = data.replace('False', 'false')
        # data = data.replace('True', 'true')
        # data = data.replace('None', 'null')
        # data = data.replace("'",'"')
        # data = data.replace("\n",'')
    pass
    return sData


def jsonTranslateValuesAdv(data):
    '''
    Replace predefined str in json content

    :param str data: jsonPath expression
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    data = str(data)
    data = data.replace('False', 'false')
    data = data.replace('True', 'true')
    data = data.replace('None', 'null')
    data = data.replace("'", '"')
    data = data.replace("\\n", '')
    data = data.replace("\\t", '')
    data = data.replace("\n", '')
    data = data.replace("\\", '')
    return data


def jsonTranslateValues4Panda(data):
    '''
    Replace predefined str in json content

    :param str data: jsonPath expression
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    data = str(data)
    data = data.replace('False', "'false'")
    data = data.replace('True', "'true'")
    data = data.replace('None', "'null'")
    data = data.replace("'", '"')
    data = data.replace("\n", '')
    return data


def sTranslate4Json(data):
    '''
    Replace predefined str in json content

    :param str data: json string
    :return: content
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    sData = str(data)
    xData = sData.replace("None", "null")
    xData = xData.replace("True", "true")
    xData = xData.replace("False", "false")
    xData = xData.replace("True", "true")

    return xData


def dTranslate4Json(data):
    '''
    Replace predefined str in dict content

    :param str data: json string
    :return: content
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    sData = str(data)
    xData = sData.replace("None", "null")
    xData = xData.replace("True", "true")
    xData = xData.replace("False", "false")
    xData = xData.replace("'", '"')

    return xData


def extract(data, arr, key):
    '''
    Extract value from content

    :param str data: json content
    :param arrray arr: json content
    :param str key: jsonPath expression
    :return: content
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                extract(v, arr, key)
            elif k == key:
                arr.append(v)
    elif isinstance(data, list):
        for item in data:
            extract(item, arr, key)
    return arr


def jsonExtractValues(data, key):
    '''
    Extract data from json content

    :param str data: json content
    :param str key: string to search for
    :return: content
    :rtype: array
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    arr = []
    results = extract(data, arr, key)
    return results


def jsonExtractSimpleValue(data, key):
    '''
    Extract data from json content

    :param str data: json content
    :param str key: string to search for
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    value = ""
    try:
        data = json.loads(data)
        value = data[key]
    except ValueError as error:
        logger.error('Script: Invalid json: %s', error)
    else:
        value = data[key]

    return value


def jsonMergeObjects(*argv):
    '''
    Merge json content

    :param str *: json content
    :return: content
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    data_list = []
    json_data = {}
    for arg in argv:
        json_data = json.loads(str(arg))
        data_list.append(json_data)
    json_data = json.dumps(data_list)
    if _localDebug:
        logger.debug('Core: JSON Merge: %s', json_data)
    return json_data


def encodeUrl(data):
    '''
    Encode url

    :param str data: url
    :return: content
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    data = str(data)
    data = urllib.parse.quote(data)
    return data


def getHostIP(hostname):
    '''
    Get IP address for given hostname

    :param str hostname: hostname
    :return: ip address
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if _localDebug:
        logger.debug('Script: Get IP of Host Name: %s', hostname)

    try:
        ip = str(socket.gethostbyname(hostname))
        if _localDebug:
            logger.debug('Script: Host IP: %s', ip)
        return ip

    except socket.gaierror as exp:
        # Issues on MAC OS System Platform
        logger.error('Script: Get Host IP Socket Error: %s', exp)
        try:
            ip = socket.gethostbyname(hostname + '.local')
            if _localDebug:
                logger.debug('Script: Host IP with .local: %s', ip)
            return ip
        except:
            pass
    except:
        pass


def getHostName():
    '''
    Get hostname of current system

    :return: hostname
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    try:
        data = socket.gethostname()
        hostName = data
        return hostName
    except Exception as exp:
        logger.error('Script: Get Hostname Socket Error: %s', exp)
        return False


def getHostFqdn(hostname):
    '''
    Get full qualified domain name for given hostnamr

    :param str hostname: hostname
    :return: fqdn
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if _localDebug:
        logger.debug('Script: Host Name / IP: %s', hostname)

    try:
        data = str(socket.getfqdn(hostname))
        fqdn = data
        if _localDebug:
            logger.debug('Script: Host FQDN: %s', fqdn)
        return fqdn
    except Exception as exp:
        logger.error('Script: Get Host FQDN Socket Error: %s', exp)
        return False


def getHostDomain(hostname):
    '''
    Extract domain name for given hostname

    :param str hostname: hostname
    :return: domain
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    fqdn = getHostFqdn(hostname)
    domain = ".".join(fqdn.split('.')[1:])
    return domain


def getHostFromFQDN(fqdn):
    '''
    Extract hostname name for given full qualified hostname

    :param str hostname: full qualified hostname
    :return: hostname
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    hostname = fqdn.split('.')[0]
    return hostname


def getHostByIP(hostIP):
    '''
    Get hostname name for given ip address

    :param str hostname: full qualified hostname
    :return: ip address
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if _localDebug:
        logger.debug('Script: Host IP: %s', hostIP)
    try:
        data = socket.gethostbyaddr(hostIP)[0]
        hostName = data
        if _localDebug:
            logger.debug('Script: Host Name: %s', hostName)
        return hostName
    except Exception as exp:
        logger.error('Script: Socket Error: %s', exp)
        return False


def getHostAddressInfo(hostname, port):
    '''
    Extract hostname name for given full qualified hostname

    :param str hostname: The host parameter takes either an ip address or a host name.
    :param int port: The port number of the service. If zero, information is returned for all supported socket types
    :return: full qualified hostname
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if _localDebug:
        logger.debug('Script: Host Name: %s Port: %s', hostname, port)

    try:
        data = str(socket.getaddrinfo(hostname, port))
        fqdn = data
        if _localDebug:
            logger.debug('Script: Host Info: %s', fqdn)
        return fqdn
    except Exception as exp:
        logger.error('Script: Socket Error: %s', exp)
        return False


def getCryptoKeyFile():
    '''
    Get fully qualified file name to support encryption / decryption functions

    :return: file name
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    # Custom Crypto File
    # checkCustomCryptoFile(folder=pFolder)
    sCryptoFileName = sHostname + ".bin"
    sProjectryptoFileName = os.path.join(cfgFolder, sCryptoFileName)
    sCryptoKeyFileName = sProjectryptoFileName
    return sCryptoKeyFileName


def encrypt(data, sKeyFileName=""):
    '''
    Symmetrically encrypt data 

    :param str data: The data to symmetrically encrypt
    :param str sKeyFileName: file that contains the encryption key, if empty: use default base of 'sCryptoKeyFileName'
    :return: encrypted data 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    sPwd = data
    if len(sKeyFileName) < 1:
        sCryptoKeyFile = getCryptoKeyFile()
    else:
        sCryptoKeyFile = sKeyFileName

    key = getCryptoKey(sCryptoKeyFile)
    # cipher = AES.new(key.encode(), AES.MODE_CBC)
    cipher = AES.new(key, AES.MODE_CBC)
    value = b64encode(cipher.iv).decode('utf-8') + b64encode(
        cipher.encrypt(pad(sPwd.encode(),
                           AES.block_size))).decode('utf-8') + str(
                               len(b64encode(cipher.iv).decode('utf-8')))
    sPwd = "ENC[" + value + "]"

    return sPwd


def decrypt(data, sKeyFileName=""):
    '''
    Symmetrically decrypt data 

    :param str data: The data to symmetrically decrypt
    :param str sKeyFileName: file that contains the encryption key, if empty: use default base of 'sCryptoKeyFileName'
    :return: decrypted data 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    if "ENC[" in data:
        start = data.find('ENC[') + 4
        end = data.find(']', start)
        sPwd = data[start:end]
    else:
        sPwd = data

    if len(sKeyFileName) < 1:
        sCryptoKeyFile = getCryptoKeyFile()
    else:
        sCryptoKeyFile = sKeyFileName

    key = getCryptoKey(sCryptoKeyFile)
    cipher = AES.new(key, AES.MODE_CBC, b64decode(sPwd[0:int(sPwd[-2:]):1]))
    value = unpad(cipher.decrypt(b64decode(sPwd[int(sPwd[-2:]):len(sPwd):1])),
                  AES.block_size).decode('utf-8')

    return value


def getCryptoKey(sKeyFileName):
    '''
    Get symmetric crypto key 

    :param str sKeyFileName: file that contains the encryption key, if the file does not exist, create one.
    :return: decrypted data 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    if len(sKeyFileName) < 1:
        sCryptoKeyFile = sCryptoKeyFileName
    else:
        sCryptoKeyFile = sKeyFileName

    try:
        with open(sCryptoKeyFile, "rb") as keyfile:
            keySecret = keyfile.read()
    except FileNotFoundError as err:
        logger.error('Script: Crypto File Error: %s', err)
        keySecret = os.urandom(16)
        with open(sCryptoKeyFile, "wb") as keyfile:
            keyfile.write(keySecret)

    # value = key_data["AESCrypto"]
    value = keySecret
    if _localDebug:
        logger.debug('Script: Crypto File: "%s"', sCryptoKeyFile)
        logger.debug('Script: Crypto Secret: %s', keySecret)
    return value


def encryptPwd(data, sKeyFileName=""):
    '''
    Symmetrically encrypt password 

    :param str data: The password to symmetrically encrypt
    :return: encrypted password 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    value = encrypt(data=data, sKeyFileName=sKeyFileName)
    if _localDebug:
        logger.debug('Script: Encrypt Data: %s', value)
    return value


def decryptPwd(data, sKeyFileName=""):
    '''
    Symmetrically decrypt password 

    :param str data: The password to symmetrically decrypt
    :return: decrypted password 
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    value = decrypt(data=data, sKeyFileName=sKeyFileName)
    if _localDebug:
        logger.debug('Script: Encrypt Data: %s', value)
    return value


def convertCsv2Json(data, keepDuplicate=False, replaceEmpty=False):
    '''
    Convert panda with csv data to json 

    :param str data: panda with csv data
    :param str keepDuplicate: panda method of handling duplicate records
    :param boolean replaceEmpty: replace empty call with default value
    :return: data
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    df = convertCsv2Panda(data=data, keepDuplicate=keepDuplicate)
    if replaceEmpty:
        df.fillna("Not Defined", inplace=True)
    json_data = df.to_json(orient='records')
    return json_data


def convertCsv2Panda(data, keepDuplicate=False):
    '''
    Convert csv data to panda dataframe

    :param str data: data in csv format
    :return: data
    :rtype: panda dataframe
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    df = pd.read_csv(StringIO(data))
    df = df.drop_duplicates(keep=keepDuplicate)
    return df


def convertJson2Panda(data, keepDuplicate=False):
    '''
    Convert JSON data to panda dataframe

    :param str data: data in JSON format
    :return: data
    :rtype: panda dataframe
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    df = pd.read_json(StringIO(data), orient='records')
    df = df.drop_duplicates(keep=keepDuplicate)
    return df


def convertJson2Csv(data):
    df = convertJson2Panda(data=data)
    csvData = df.to_csv(index=False)
    return csvData


def copyFile(srcFile, dstFile, override=False):
    '''
    Copy file from src to dst

    :param str src: a given source file name, fully qualified
    :param str dst: a given target file name, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    srcFile = str(srcFile)
    dstFile = str(dstFile)
    sFileStatusSource = getFileStatus(srcFile)
    sFileStatusDest = getFileStatus(dstFile)

    if sFileStatusDest:
        if override:
            try:
                if sFileStatusSource:
                    shutil.copy(srcFile, dstFile)
            except OSError as err:
                logger.error('Script: File Copy Error: %s', err)
        else:
            logger.error('Script: File Exists: %s', dstFile)
    else:
        try:
            if sFileStatusSource:
                shutil.copy(srcFile, dstFile)
        except OSError as err:
            logger.error('Script: File Copy Error: %s', err)


def copyFolder(srcFolker, dstFolder, override=False):
    '''
    Copy folder from src to dst

    :param str src: a given source folder name, fully qualified
    :param str dst: a given target folder name, fully qualified
    :return: status
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    src = str(srcFolker)
    dst = str(dstFolder)
    sFolderStatusSource = getFolderStatus(src)
    createFolder(path=dst)
    if sFolderStatusSource:
        files = os.listdir(src)
        for file in files:
            srcname = os.path.join(src, file)
            dstname = os.path.join(dst, file)
            copyFile(srcname, dstname, override=override)


# Project Core Folder


def getProjectFolder():
    '''
    Get current project folder

    :param: 
    :return: path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    projectFolder = getCurrentFolder()

    return projectFolder


# User Home Folder


def getHomeFolder():
    '''
    Get user home folder

    :param: 
    :return: path
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    if platform.system() == "Windows":
        userHomeFolder = getCurrentFolder()
    else:
        userHomeFolder = expanduser("~")
    return userHomeFolder


# Security functions


def secureCredentials(data):
    '''
    Encrypt clear text passwords in config json file and update file

    :param json data: configuration 
    :return: data
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    jCfgData = data
    cfgFile = getJsonValue(path="$.DEFAULT.config_file", data=jCfgData)
    cryptoFile = getJsonValue(path="$.DEFAULT.crypto_file", data=jCfgData)

    # Crypto Support
    sCfgData = encryptPwds(file=cfgFile,
                           data=jCfgData,
                           sKeyFileName=cryptoFile)
    return sCfgData


def encryptPwds(file, data, sKeyFileName=""):
    '''
    Encrypt clear text passwords in config json file and update file

    :param str file: config file name
    :param json data: config data in json format
    :param str sKeyFileName: crypto key file name
    :return: data
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    pItemList = data.keys()
    sCfgData = data
    sCfgFile = file
    for pItem in pItemList:
        if _localDebug:
            logger.info('Crypto Process Credentials for: %s', pItem)
        securePwd = ""
        jSecPwd = ""
        aSecPwd = ""

        # unSecPwd = werkstatt.jsonExtractValues(jCfgData,pItem)[0]
        vPath = "$." + pItem + ".pwd"
        jPath = "$." + pItem + ".jks_pwd"

        unSecPwd = getJsonValue(path=vPath, data=sCfgData)
        ujSecPwd = getJsonValue(path=jPath, data=sCfgData)

        if len(unSecPwd) > 0:
            if "ENC[" in unSecPwd:
                start = unSecPwd.find('ENC[') + 4
                end = unSecPwd.find(']', start)
                sPwd = unSecPwd[start:end]

            else:
                sPwd = unSecPwd
                securePwd = encryptPwd(data=sPwd, sKeyFileName=sKeyFileName)
                logger.info('Crypto Encrypt Password for: "%s"', pItem)

                if _localDebug:
                    print(f"Encrypted user password for {pItem}: {securePwd}")

                sCfgData[pItem]["pwd"] = securePwd

        # Java Keystore passwords
        if len(ujSecPwd) > 0:
            if "ENC[" in ujSecPwd:
                start = ujSecPwd.find('ENC[') + 4
                end = ujSecPwd.find(']', start)
                sPwd = ujSecPwd[start:end]

            else:
                sPwd = ujSecPwd
                securePwd = encryptPwd(data=sPwd, sKeyFileName=sKeyFileName)
                logger.info('Crypto Encrypt JKS Password for: "%s"', pItem)
                if _localDebug:
                    print(
                        f"Encrypted user JKS password for {pItem}: {securePwd}"
                    )

                sCfgData[pItem]["jks_secure"] = securePwd
                sCfgData[pItem]["jks_pwd"] = securePwd


        if _localDebug:
            logger.debug('Core: Security Function: "%s" ', "Encrypt")
            logger.debug('Core: Security Solution: "%s" ', pItem)
            logger.debug('Core: unSecure Pwd: "%s" ', unSecPwd)
            logger.debug('Core: Secure Pwd: "%s"\n', securePwd)

    # update config json file
    logger.info('Crypto Update config file: "%s"', sCfgFile)
    writeJsonFile(file=sCfgFile, content=sCfgData)
    return sCfgData


def decryptPwds(data):
    '''
    Derypt passwords in config json file print 

    :param json data: config data in json format
    :return: path
    :rtype: 
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    pItemList = data.keys()
    sCfgData = data
    for pItem in pItemList:
        unSecPwd = ""

        # unSecPwd = werkstatt.jsonExtractValues(jCfgData,pItem)[0]
        vPath = "$." + pItem + ".pwd"
        sPwd = getJsonValue(path=vPath, data=sCfgData)
        if len(sPwd) > 0:
            unSecPwd = decryptPwd(data=sPwd)
            print(f"Decrypted Password for {pItem}: {unSecPwd}")

        if _localDebug:
            logger.debug('Core: Security Function: "%s" ', "Decrypt")
            logger.debug('Core: Security Solution: "%s" ', pItem)
            logger.debug('Core: unSecure Pwd: "%s" ', unSecPwd)
            logger.debug('Core: Secure Pwd: "%s"\n', sPwd)


def createProjectFolders(data):
    '''
    Create Project Folder Structure 

    :param:
    :return: project config
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    jLocalCfgData = data
    sHomeFolder = getHomeFolder()
    coreProjectFolder = os.path.join(sHomeFolder, ".w3rkstatt")
    coreProjecConfigFolder = os.path.join(coreProjectFolder, "configs")
    coreProjectLogFolder = os.path.join(coreProjectFolder, "logs")
    coreProjectDataFolder = os.path.join(coreProjectFolder, "data")
    coreProjectTemplatesFolder = os.path.join(coreProjectFolder, "templates")

    lFolders = coreProjecConfigFolder, coreProjectLogFolder, coreProjectDataFolder, coreProjectTemplatesFolder
    # Create Folders
    for sFolder in lFolders:
        if not getFolderStatus(sFolder):
            createFolder(sFolder)

    jLocalCfgData["DEFAULT"]["config_folder"] = coreProjecConfigFolder
    jLocalCfgData["DEFAULT"]["log_folder"] = coreProjectLogFolder
    jLocalCfgData["DEFAULT"]["data_folder"] = coreProjectDataFolder
    jLocalCfgData["DEFAULT"]["template_folder"] = coreProjectTemplatesFolder

    return jLocalCfgData


def createProjecConfig(data):
    '''
    Copy Project Files 

    :param:
    :return: project config
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''
    jLocalCfgData = data

    cfgFolder = getJsonValue(path="$.DEFAULT.config_folder",
                             data=jLocalCfgData)
    logFolder = getJsonValue(path="$.DEFAULT.log_folder", data=jLocalCfgData)
    datFolder = getJsonValue(path="$.DEFAULT.data_folder", data=jLocalCfgData)
    tmpFolder = getJsonValue(path="$.DEFAULT.template_folder",
                             data=jLocalCfgData)

    # Custom Crypto File
    sCryptoFileName = sHostname + ".bin"
    sProjectryptoFileName = os.path.join(cfgFolder, sCryptoFileName)
    sCfgFilesCryptoFileStatus = getFileStatus(sProjectryptoFileName)
    jLocalCfgData["DEFAULT"]["crypto_file"] = sProjectryptoFileName

    if not sCfgFilesCryptoFileStatus:
        keySecret = os.urandom(16)
        with open(sProjectryptoFileName, "wb") as keyfile:
            keyfile.write(keySecret)

    # Custom Config File
    sConfigFileName = sHostname + ".json"
    sProjectConfigFileName = os.path.join(cfgFolder, sConfigFileName)
    sCfgFilesConfigFileStatus = getFileStatus(sProjectConfigFileName)
    jLocalCfgData["DEFAULT"]["config_file"] = sProjectConfigFileName

    # Custom Log File
    sLogFile = sHostname + ".log"
    sLogFileName = os.path.join(logFolder, sLogFile)
    jLocalCfgData["DEFAULT"]["log_file"] = sLogFileName

    # Create custom config file
    if not sCfgFilesConfigFileStatus:
        writeJsonFile(file=sProjectConfigFileName, content=jLocalCfgData)
    else:
        jLocalCfgData = getFileJson(file=sProjectConfigFileName)

    # Copy all configs
    sLocalFolder = getCurrentFolder()
    sLocalCfgFolder = os.path.join(sLocalFolder, "config")
    copyFolder(srcFolker=sLocalCfgFolder, dstFolder=cfgFolder, override=False)

    # Copy all templates
    sLocalFolder = getCurrentFolder()
    sLocalCfgFolder = os.path.join(sLocalFolder, "templates")
    copyFolder(srcFolker=sLocalCfgFolder, dstFolder=tmpFolder, override=False)

    return jLocalCfgData


def getProjectDefaultConfigFileName():
    '''
    Get Project Default Config File Name

    :param:
    :return: project config file name
    :rtype: str
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    sLocalFolder = getCurrentFolder()
    sLocalCfgFileName = os.path.join(sLocalFolder, "templates",
                                     "integrations.json")
    return sLocalCfgFileName


def getProjectDefaultConfig(file):
    '''
    Get Project Default Config File Content

    :param file str:
    :return: default config
    :rtype: json
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    jCfgFile = file
    sLocalCfgFileContent = getFileJson(jCfgFile)
    return sLocalCfgFileContent


def getProjectConfig():
    '''
    Get Project Config 

    :param:
    :return: project config
    :rtype: dict
    :raises ValueError: N/A
    :raises TypeError: N/A    
    '''

    sHomeFolder = getHomeFolder()
    coreProjectFolder = os.path.join(sHomeFolder, ".w3rkstatt")
    coreProjecConfigFolder = os.path.join(coreProjectFolder, "configs")

    # Get Custom Config File & Content
    sConfigFileName = sHostname + ".json"
    sProjectConfigFileName = os.path.join(coreProjecConfigFolder,
                                          sConfigFileName)
    sCfgFilesConfigFileStatus = getFileStatus(sProjectConfigFileName)

    if sCfgFilesConfigFileStatus:
        sCfgFileContent = getFileJson(file=sProjectConfigFileName)
    else:
        sCfgFileContent = {}

    return sCfgFileContent


# Create a custom logger
pFolder = getProjectFolder()
hFolder = getHomeFolder()
sHostname = str(getHostName()).lower()
sPlatform = platform.system()
sUuid = str(uuid.uuid4())
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Setup log file
    logFile = os.path.join(pFolder, "w3rkstatt.log")
    logging.basicConfig(filename=logFile,
                        filemode='w',
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s # %(message)s',
                        datefmt='%d-%b-%y %H:%M:%S')
    logger.info('Werkstatt Python Core Script "Start"')
    logger.info('Version: %s ', _modVer)
    logger.info('System Platform: "%s" ', sPlatform)
    logger.info('System Name: "%s" ', sHostname)
    logger.info('Project Folder: "%s" ', pFolder)

    # Get Default Config
    jCfgFile = getProjectDefaultConfigFileName()
    jCfgData = getProjectDefaultConfig(file=jCfgFile)

    # Setup Project
    jUpdatedCfgfolders = createProjectFolders(data=jCfgData)
    jUpdatedCfgData = createProjecConfig(data=jUpdatedCfgfolders)

    loglevel = getJsonValue(path="$.DEFAULT.loglevel", data=jUpdatedCfgData)
    cfgFolder = getJsonValue(path="$.DEFAULT.config_folder",
                             data=jUpdatedCfgData)
    logFolder = getJsonValue(path="$.DEFAULT.log_folder", data=jUpdatedCfgData)
    datFolder = getJsonValue(path="$.DEFAULT.data_folder",
                             data=jUpdatedCfgData)
    tmpFolder = getJsonValue(path="$.DEFAULT.template_folder",
                             data=jUpdatedCfgData)
    cfgFile = getJsonValue(path="$.DEFAULT.config_file", data=jUpdatedCfgData)
    cryptoFile = getJsonValue(path="$.DEFAULT.crypto_file",
                              data=jUpdatedCfgData)

    logger.info('System Config JSON File: "%s" ', jCfgFile)
    logger.info('Log Folder: "%s" ', logFolder)
    logger.info('Data Folder: "%s" ', datFolder)
    logger.info('Template Folder: "%s" ', tmpFolder)
    logger.info('Config File: "%s" ', cfgFile)
    logger.info('Crypto Key File: "%s" ', cryptoFile)
    # Central config folder

    jSecureCfgData = secureCredentials(data=jUpdatedCfgData)
    if _SecureDebug:
        decryptPwds(data=jSecureCfgData)

    logger.info('Werkstatt Python Core Script "End"')
    logging.shutdown()
    print(f"Version: {_modVer}")
    print(f"Log File: {logFile}")
