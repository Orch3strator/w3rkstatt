#!/usr/bin/env python3
#Filename: smtp.py

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

w3rkstatt Python E-Mail Tools 
Provide email functions for w3rkstatt related python scripts

Change Log
Date (YMD)    Name                  What
--------      ------------------    ------------------------
20210513      Volker Scheithauer    Tranfer Development from other projects


See also: https://realpython.com/python-send-email/
"""




import sys, getopt, platform, argparse
import os, json
import subprocess

# fix to bbe able to add global module

import w3rkstatt

import smtplib, ssl
from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from json2html import *


# Get configuration from bmcs_core.json

jCfgFile    = w3rkstatt.jCfgFile
jCfgData    = w3rkstatt.jCfgData
log_folder  = w3rkstatt.logFolder
data_folder = log_folder
sUuid       = w3rkstatt.sUuid


# SMTP Server Settigns
smtp_host      = w3rkstatt.getJsonValue(path="$.MAIL.host",data=jCfgData)
smtp_port      = w3rkstatt.getJsonValue(path="$.MAIL.port",data=jCfgData)
smtp_ssl       = w3rkstatt.getJsonValue(path="$.MAIL.ssl",data=jCfgData)
smtp_user      = w3rkstatt.getJsonValue(path="$.MAIL.user",data=jCfgData)
smtp_dsiplay_name = w3rkstatt.getJsonValue(path="$.MAIL.display",data=jCfgData)
smtp_pwd       = w3rkstatt.getJsonValue(path="$.MAIL.pwd",data=jCfgData)
template_name  = w3rkstatt.getJsonValue(path="$.MAIL.template",data=jCfgData)
template_file  = os.path.join(w3rkstatt.pFolder,"templates",template_name) 


# Assign module defaults
_localDebug = False
_localDebugAdv = True
_localInfo = True
_modVer = "0.01"
_timeFormat = '%d %b %Y %H:%M:%S,%f'

logger   = w3rkstatt.logging.getLogger(__name__) 
logFile  = w3rkstatt.logFile
loglevel = w3rkstatt.loglevel
epoch    = w3rkstatt.time.time()
parser   = argparse.ArgumentParser(prefix_chars=':')
sUuid    = w3rkstatt.sUuid

if __name__ == "__main__":
    w3rkstatt.logging.basicConfig(filename=logFile, filemode='a', level=w3rkstatt.logging.DEBUG , format='%(asctime)s - %(levelname)s # %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    
    sSysOutMsg = "E-Mail Internal ID=" + sUuid

    if _localInfo: 
        logger.info('BMCS: start e-mail management - %s', w3rkstatt.sUuid)
        logger.info('Version: %s ', _modVer)
        logger.info('System Platform: %s ', w3rkstatt.sPlatform)
        logger.info('Log Level: %s', loglevel)
        logger.info('Epoch: %s', epoch)
        logger.info('Host Name: %s', w3rkstatt.sHostname)
        logger.info('UUID: %s', w3rkstatt.sUuid)


    # Script Arguments
    xArgp = argparse.ArgumentParser(prog='sendmail.py', usage='%(prog)s [options]', description='BMC Software - E-Mail Integration Helper Tools', epilog='Enjoy the program.')
    xArgp.add_argument('--sender','-x', type=str, action='store', help='E-Mail Sender', nargs='?',required=False)
    xArgp.add_argument('--recipient','-r', type=str, action='store', help='E-Mail Recipient ', nargs='?',required=True)
    xArgp.add_argument('--subject','-s', type=str, action='store', help='E-Mail Subject Line ', nargs='?',required=True)
    xArgp.add_argument('--message','-m', type=str, action='store', help='E-Mail Message', nargs='?',required=False)
    xArgp.add_argument('--template','-t', type=str, action='store', help='E-Mail HTML Template', nargs='?',required=False)
    xArgp.add_argument('--data','-d', type=str, action='store', help='E-Mail HTML content data used with template', nargs='?',required=False)
    xArgps = xArgp.parse_args()



    email_from = smtp_user
    email_rcpt = ""
    email_subject = ""
    email_message = ""
    email_template = ""
    email_data = ""

    


    # Extract arguments
    if xArgps.sender is not None:
        email_from = xArgps.sender     

    if xArgps.recipient is not None:
        email_rcpt = xArgps.recipient  

    if xArgps.subject is not None:
        email_subject = xArgps.subject  

    if xArgps.message is not None:
        email_message = xArgps.message 

    if xArgps.template is not None:
        email_template = xArgps.template       

    if xArgps.data is not None:
        email_data = xArgps.data 


    if _localDebugAdv: 
        logger.debug('E-Mail From: "%s"', email_from)      
        logger.debug('E-Mail Recipient: "%s"', email_rcpt)
        logger.debug('E-Mail Subjcet: "%s"', email_subject)
        logger.debug('E-Mail HTML Template: "%s"', template_file)
        logger.debug('SMTP Server: "%s:%s"', smtp_host, smtp_port )   
        logger.debug('SMTP SSL: %s', smtp_ssl ) 
        logger.debug('SMTP User Name: %s', smtp_user ) 
 

    # Check if data is JSON format
    email_data_text = str(email_data)
    email_data = w3rkstatt.jsonTranslateValuesAdv(data=email_data_text)    
    email_data_status = w3rkstatt.jsonValidator(data=email_data)
    if email_data_status:
        email_msg_tbl  = json2html.convert(json = email_data )
    else:
        email_msg_tbl  = email_message


    # Fro HTML E-Mail
    email_logo_txt = "This message was sent by Orchestrator."
    email_template = w3rkstatt.readHtmlFile(file=template_file)

    # replace HTML content
    email_html_00 = email_template
    email_html_01 = email_html_00.replace("$$EMAIL_LOGO_TEXT$$",email_logo_txt)
    email_html_02 = email_html_01.replace("$$EMAIL_MESSAGE$$",email_msg_tbl)
    email_html_03 = email_html_02.replace("$$EMAIL_UUID$$",sUuid)
    email_new_html = email_html_03


    # For Text E-Mail
    email_format_text = """ Simple E-Mail Body"""

    email_message = MIMEMultipart("alternative")
    email_message["Subject"] = email_subject
    email_message["From"] = email_from
    email_message["To"] = email_rcpt

    email_part_text = MIMEText(email_format_text, "plain")
    email_part_html = MIMEText(email_new_html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    email_message.attach(email_part_text)
    email_message.attach(email_part_html)



    # SMTP with SSL/TLS enabled and authentication
    if smtp_ssl:
        logger.debug('SMTP Connection SSL: %s', smtp_ssl ) 
        smtp_pwd = w3rkstatt.decryptPwd(data=smtp_pwd)
        try:
            smtp_connection = smtplib.SMTP_SSL(smtp_host, smtp_port)
            smtp_connection.login(smtp_user, smtp_pwd)
            server_ehlo = smtp_connection.ehlo()
            server_rsp_id  = server_ehlo[0]
            server_rsp_msg = str(server_ehlo[1])
            logger.debug('SMTP Server EHLO: %s', server_rsp_msg ) 

            smtp_connection.sendmail(
                email_from, email_rcpt, email_message.as_string()
            )

        except Exception as e:
            logger.error('SMTP Error: %s', e ) 
        finally:            
            smtp_connection.quit()

    # SMTP with SSL/TLS disbaled, no authentication
    if not smtp_ssl:
        logger.debug('SMTP Connection SSL: %s', smtp_ssl ) 
        try:
            smtp_connection = smtplib.SMTP(smtp_host, smtp_port)
            server_ehlo = smtp_connection.ehlo()
            server_rsp_id  = server_ehlo[0]
            server_rsp_msg = str(server_ehlo[1])
            logger.debug('SMTP Server EHLO: %s', server_rsp_msg ) 

            smtp_connection.sendmail(
                email_from, email_rcpt, email_message.as_string()
            )

        except Exception as e:
            logger.error('SMTP Error: %s', e ) 
        finally:            
            smtp_connection.quit()

    w3rkstatt.logging.shutdown()

    print (f"Message: {sSysOutMsg}")
