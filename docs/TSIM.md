# TrueSight Operations Manager

Event Management Python module for Werkstatt projects

## Core functions for integrating with solutions using Python

- Create objects in TrueSight Operations Manager

## Core Libraries and purpose

- **w3rkstatt** basic project functions
- **core_tsim** basic TrueSight Operations Manager integration

## Dependencies

- [X] **Basic Libraries**
- [X] **Cryptodome**
- [X] **TrueSight Operations Manager**

## Solutions leveraging the base tools

| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         |
| Werkstatt Tools           | ⬜            | ✅    |
| TrueSight OM              | ✅            | 🔶    |
| TrueSight PS              | ✅            | 🔶    |

- ✅ — Supported
- 🔶 — Partial support
- 🚧 — Under development
- ⬜ - N/A ️

**ToDO**:

- [x] Initial Core Development
- [ ] Add custom event format to .load of your main TSIM cell

**Configuration**:

- After the inital run of w3rkstatt.py a local crypto key file is being generated in the /configs folder with [hostname].bin
- After the inital run of w3rkstatt.py a local config file is being generated in the /configs folder with [hostname].json
- Update the credentials and other settings in the [hostname].json file
- Execute w3rkstatt.py to encrypt the passwords in [hostname].json
- All password in cleartext will be removed
- Update file level access for [hostname].bin to only authorized OS accounts. If the file [hostname].bin is being deleted, the encrypted passwords cannot be recovered
- The account running the python scripts needs to have access to [hostname].json and [hostname].bin
- Update TSIM / TSPS Server settings

**TrueSight Operations Manager**:

- Create TrueSight Operation Manager account with proper permissions
- Add application credentials to [hostname].json

## Module Information

**TSIM Configuration**:

- Folder: ~/.w3rkstatt/configs
- File: [hostname].json - custome config file

**Function**:
**TrueSight Operations Manager Application**:
Module | Method | Description
------------ | ------------- | -------------
*core_tsim* | [**getEventID**]| Extract TSIM Event mc_ueid
*core_tsim* | [**createCI**] | Create TSIM CI
*core_tsim* | [**searchCI**] | Search for TSIM CI
*core_tsim* | [**searchCIAdvanced**] | Search for TSIM CI Advanced

**TrueSight Operations Manager Core**:
Module | Method | Description
------------ | ------------- | -------------
*core_tsim* | [**authenticate**]| Login to TrueSight Presentation Server
*core_tsim* | [**createEvent**] | Create TSIM Event
*core_tsim* | [**updateEvent**] | Update TSIM Event
*core_tsim* | [**searchEvent**] | Search for TSIM Event

## TrueSight Operations Manager HTTP Body

Update the JSON content, utlize project default settings from [hostname].json
Sample TSIM Event payload

```bash
[{
 "eventSourceHostName": "host.local",
 "attributes": {
  "severity": "WARNING",
  "CLASS": "EVENT",
  "msg": "This event was created using the TSOM REST API",
  "cdmclass": "BMC_ComputerSystem",
  "componentalias": "BMC_ComputerSystem:host.local'",
  "instancename": "host.local",
  "itsm_product_name": "Control-M",
  "mc_host": "host.local",
  "mc_host_address": "a.b.c.d",
  "mc_location": "",
  "mc_object": "Job",
  "mc_object_class": "Control-M",
  "mc_origin": "Enterprise Manager",
  "mc_origin_class": "Control-M",
  "mc_tool_id": "epoch=1621631064.550844",
  "mc_tool": "Python Script",
  "mc_tool_rule": "uat.py",
  "mc_tool_uri": "git.io"
 }
}]
```

**TSIM Cell Control-M Event Class**:

```bash
#--------------------------------------------------------------------
# File name: bmcs_ctm.baroc
# Version: 11.3.03
# located in %mcell_home%/etc/%cell%/kb/classes
# ToDo: add to .load, compile cell
# Copyright 1998-2020 BMC Software, Inc. All Rights Reserved
# Created by Orchestrator, BMC Software, Software Consultant
#--------------------------------------------------------------------

MC_EV_CLASS:
    CTMX_EVENT ISA EVENT
    DEFINES
    {
        mc_tool                     : default="CTM Enterprise Manager";
        mc_tool_class               : default = "CTM Event", dup_detect = yes;
        mc_host_address             : dup_detect=yes;
        mc_origin_key               : dup_detect=yes;
        mc_owner                    : STRING;
        mc_object                   : STRING;
        mc_object_class             : STRING;
        mc_ueid                     : STRING;
        mc_long_msg                 : STRING;
        msg                         : STRING;
        severity                    : SEVERITY, default=WARNING;        
        ctmUpdateType               : STRING; # Alert update type 'I' Insert - new alert 'U' Update existing alert
        ctmAlertId                  : STRING; # Alert id Unique alert identifier
        ctmDataCenter               : STRING; # Control-M server name
        ctmMemName                  : STRING; # Job member name
        ctmOrderId                  : STRING; # Job order id
        ctmSeverity                 : STRING; # Alert severity 'R' - regular 'U' - urgent 'V' - very urgent
        ctmTime                     : STRING; # representation = date; # Alert creation time (YYYYMMDDhhmmss)
        ctmStatus                   : STRING; # Alert status (Not_Noticed, Noticed or Handled)
        ctmNodeId                   : STRING; # Job node id
        ctmJobName                  : STRING; # Job name
        ctmMessage                  : STRING; # Alert message
        ctmApplication              : STRING; # Job application name
        ctmSubApplication           : STRING; # Job sub application name
        ctmAlertType                : STRING; # Alert type B - BIM alert type R or empty - regular alert type
        ctmClosedFromEM             : STRING; # Closed from Control-M/Enterprise Manager Y - yes N or empty - no
        ctmTicketNumber             : STRING; # Remedy ticket number
        ctmRunCounter               : STRING; # Job's run counter
        ctmUser                     : STRING; # Last updated by, user name
        ctmUpdateTime               : STRING; # representation = date; # Last time the alert was updated (YYYYMMDDhhmmss)
        ctmOwner                    : STRING; # The user who runs the job
        ctmNotes                    : STRING; # Alert notes
        ctmFolder                   : STRING; # Job folder
        ctmFolderID                 : STRING; # Job folder ID
        ctmJobID                    : STRING; # Job ID
        ctmJobHeld                  : STRING; # Job hold status
        xctmCallType                : STRING; # Alert update type 'I' Insert - new alert 'U' Update existing alert
        xctmSerial                  : STRING; # Serial number
        xctmCompType                : STRING; # Alert id Unique alert identifier
        xctmCompMachine             : STRING; # Control-M server name
        xctmCompName                : STRING; # Job member name
        xctmMessageId               : STRING; # Job order id
        xctmXSeverity               : STRING; # Alert severity '0' - Undefined '1' - Severe '2' - Error '3' - Warning
        xctmMessage                 : STRING; # representation = date; # Alert creation time (YYYYMMDDhhmmss)
        xctmXTime                   : STRING; # Alert status (Not_Noticed, Noticed or Handled)
        xctmXTimeOFLast             : STRING; # Job node id
        xctmCounter                 : STRING; # Job name
        xctmStatus                  : STRING; # Alert message
        xctmNote                    : STRING; # Job application name
        xctmKey1                    : STRING; # Job group name
        xctmKey2                    : STRING; # Alert type B - BIM alert type R or empty - regular alert type
        xctmKey3                    : STRING; # Closed from Control-M/Enterprise Manager Y - yes N or empty - no
        xctmKey4                    : STRING; # Remedy ticket number
        xctmKey5                    : STRING; # Job's run counter

    };
END


MC_EV_CLASS :
 CTMX_JOB ISA CTMX_EVENT;
END
```

**TSIM Cell Collector MRL**:

```bash
#--------------------------------------------------------------------
# File name: bmcs_ctm.mrl
# Version: 11.3.03
# windows_logs_collectors.mrl
# located in %mcell_home%/etc/%cell%/kb/collectors
# ToDo: add to .load, compile cell
# Created by Orchestrator, BMC Software, Software Consultant
# Copyright 1998-2020 BMC Software, Inc. All Rights Reserved
#--------------------------------------------------------------------

collector 'Hyper Automation':
{
        r['Service Administrators','Event Administrator','Service Operators - Senior','Event Supervisor','Service Operators','Event Operator','Service Managers - Senior','Service Managers']
        w['Service Administrators','Event Administrator','Service Operators - Senior','Event Supervisor','Service Operators','Event Operator','Service Managers - Senior','Service Managers']
        x['Service Administrators','Event Administrator','Service Operators - Senior','Event Supervisor','Service Operators','Event Operator','Service Managers - Senior','Service Managers']
}
END

collector 'Hyper Automation'.Workload:
CTMX_JOB 
where [
   $THIS.status == OPEN 
 ]
END

collector 'Hyper Automation'.Workload.*:
CTMX_JOB 
where [
   $THIS.status == OPEN 
 ]
 create $THIS.mc_object_owner
END

collector 'Hyper Automation'.Infrastructure:
CTMX_EVENT
where [
    $THIS.status == OPEN 
]
END

collector 'Hyper Automation'.Infrastructure.*:
CTMX_EVENT
where [
    $THIS.status == OPEN
]
create $THIS.mc_host
END

```
