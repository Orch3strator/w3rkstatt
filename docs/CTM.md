# Werkstatt Tools
Control-M Python module for Werkstatt projects

## Core functions for integrating with solutions using Python
- Control-M Alert Management
- [Ensuring that folders and job chains are running as expected](https://community.bmc.com/s/news/aA33n000000Xb6XCAS/ensuring-that-folders-and-job-chains-are-running-as-expected "Control-M Alert Management")

## Core Libraries and purpose
- **w3rkstatt** basic project functions
- **ctm** basic Control-M integration

## Dependencies
- [X] **W3rkstatt Libraries**
- [X] **Control-M**
- [X] **Control-M AAPI**


## Solutions leveraging the base tools
| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         | 
| Werkstatt Tools           | ⬜            | ✅    | 
| Control-M                 | ✅            | 🔶    | 



* ✅ — Supported
* 🔶 — Partial support
* 🚧 — Under development
* ⬜ - N/A ️


**ToDO**: 
- [x] Initial Core Development
- [ ] Automate Control-M configuration 


**Configuration**: 
- After the inital run of w3rkstatt.py a local crypto key file is being generated in the /configs folder with [hostname].bin
- After the inital run of w3rkstatt.py a local config file is being generated in the /configs folder with [hostname].json
- Update the credentials and other settings in the [hostname].json file
- Execute w3rkstatt.py to encrypt the passwords in [hostname].json
- All password in cleartext will be removed
- Update file level access for [hostname].bin to only authorized OS accounts. If the file [hostname].bin is being deleted, the encrypted passwords cannot be recovered 
- The account running the python scripts needs to have access to [hostname].json and [hostname].bin
- Update ITSM Server settings

**Control-M**:
- Create Control-M account with proper permissions
- Add application credentials to [hostname].json
- Configure Control-M Alert notifications


## Module Information
**Control-M Configuration**: 
- Folder: ~/.w3rkstatt/configs
- File: [hostname].json - custome config file

## Control-M Alert Configuration
:one: &nbsp;Do not enable SNMP if you are not going to use it. 
:two: &nbsp;If any of the SNMP related parameters were changed in the CCM, make sure to cycle the Gateway(s) to make these changes take effect.
:three: &nbsp;Check the Gateway log files ($HOME/ctm_em/log/gtw_log*)

- :arrow_right: &nbsp;SNMPHost: Define the hostname of the SNMP server where the alerts are sent.
- :arrow_right: &nbsp;SNMPSendActive: Change the value to 1 to generate SNMP messages for Active Alerts.
- :arrow_right: &nbsp;SendSNMP: Change the value to 0 to send alerts to SNMP server only.
- :arrow_right: &nbsp;SendAlertNotesSnmp: Change the value to 1 if you want to send the NOTES field to the SNMP server.
- :arrow_right: &nbsp;XAlertsEnableSending: Change the value to 1 to enable xAlert sending.
- :arrow_right: &nbsp;XAlertsSnmpHosts: Define the hostname of the SNMP server where the xAlerts are sent.
- :arrow_right: &nbsp;XalertsSendSnmp: Change the value to 1 to send xAlerts to SNMP server only.

- :arrow_right: &nbsp;SendAlarmToScript: Define the full path name of the script that is activated when an alert is generated.
- :arrow_right: &nbsp;SendSNMP: Change the value to 1 to send alerts to a script only.
- :arrow_right: &nbsp;SendAlertNotesSnmp: Change the value to 1 if you want to send the NOTES field to a script.
- :arrow_right: &nbsp;SNMPSendActive: Change the value to 1 to generate SNMP messages to a script.
- :arrow_right: &nbsp;XAlertsEnableSending: Change the value to 1 to enable xAlert sending.
- :arrow_right: &nbsp;XAlertsSend2Script: Define the full path name of the script that is activated when an xAlert is generated.
- :arrow_right: &nbsp;XalertsSendSnmp: Change the value to 2 to send xAlerts to a script only.

**Alert Configuration**
```bash
SendAlarmToScript: D:\Programs\BMCS\Integrations\ctm_alerts.bat
SendSNMP: 1
SendAlertNotesSnmp: 1
SNMPSendActive: 1
XAlertsEnableSending: 1
XAlertsSend2Script: D:\Programs\BMCS\Integrations\ctm_alerts.bat
XalertsSendSnmp: 2
```

**Alert Configuration Script**
Update ctm_alerts.bat or ctm_alerts.sh top point to the right script. 

**Alert Log Files**
Check the CTM EM gateway log file for details on script call and the .w3rkstatt\logs\[hostname].log for script execution information

## Additonal Information
- [Control-M SNMP Trap](https://documents.bmc.com/supportu/9.0.20/help/Main_help/en-US/index.htm#45731.htm)
- [Sending alerts and xAlerts to an event management system](https://documents.bmc.com/supportu/9.0.20/help/Main_help/en-US/index.htm#45709.htm)
- [Sending Alerts and xAlerts to a script](https://documents.bmc.com/supportu/9.0.20/help/Main_help/en-US/index.htm#45710.htm)
- [Downloading and installing or upgrading the Control-M REST API](https://docs.bmc.com/docs/automation-api/monthly/installation-1007966461.html#Installation-download)
- [How to send alerts from Control-M/Enterprise Manager to a script?](https://community.bmc.com/s/article/How-to-send-alerts-from-Control-M-Enterprise-Manager-to-a-script)
