# Werkstatt Tools
Basic Python modules for Werkstatt projects


## Core functions for integrating with solutions using Python
- Basic transform and core functions
- Encryption of credential 
- External configuration in custom json file

## Core Library and purpose
- **w3rkstatt** base python functions for project support
- **w3rkstatt** encrypt the cleartext passwords

## Dependencies
- [ ] **Basic Libraries**
- [ ] **Cryptodome**


Install dependencies
```bash
Linux
python3 -m pip install pyCryptodome
python3 -m pip install pandas
python3 -m pip install wheel requests urllib3
python3 -m pip install json2html jsonpath-ng jsonpath_rw_ext
```
```bash
Windows
python -m pip install pyCryptodome
python -m pip install pandas
python -m pip install wheel requests urllib3
python -m pip install json2html jsonpath-ng jsonpath_rw_ext 
```

## Solutions leveraging the base tools
| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         | 
| Werkstatt Tools           | ⬜            | ✅    | 
| BMC Control-M             | 🔶            | ✅    | 
| BMC Helix ITSM            | 🔶            | ✅    | 
| BMC TrueSight             | 🔶            | ✅    | 
| ServiceNOW                | 🔶            | 🚧    | 
| E-Mail                    | 🔶            | ✅    | 



* ✅ — Supported
* 🔶 — Partial support
* 🚧 — Under development
* ⬜ - N/A ️

**ToDO**: 
- [x] Initial Core Development
- [ ] update CamelCase / snake_case
- [ ] automate this process

**Info**:
- Log files are being written to [home]/werkstatt/logs
- Werkstatt main log file is [home]/werkstatt/logs/integrations.log
- Configuration files are in [home]/werkstatt/configs
- Example files are in [project]/samples  

## Documentation of Modules

**SMTP**:
Module | Method | Description
------------ | ------------- | -------------
*core_smtp* | [**prepareEmail**](docs/SMTP.md)     | Prepare HTML content, based on template
*core_smtp* | [**sendEmailSmtpSSL**](docs/SMTP.md) | Send E-mail with SSL enabled

**Helix ITSM Application**:
Module | Method | Description
------------ | ------------- | -------------
*core_itsm* | [**createChange**](docs/ITSM.md) | Create ITSM Change Request
*core_itsm* | [**getChange**](docs/ITSM.md) | Get ITSM Change Request status
*core_itsm* | [**extractChangeState**](docs/ITSM.md) | Translate ITSM Change Request details
*core_itsm* | [**createIncident**](docs/ITSM.md) | Create ITSM Incident
*core_itsm* | [**getIncident**](docs/ITSM.md) | Get ITSM Incident details
*core_itsm* | [**getIncidentStatus**](docs/ITSM.md) | Get ITSM Incident status

**Helix ITSM Core**:
Module | Method | Description
------------ | ------------- | -------------
*core_itsm* | [**authenticate**](docs/ITSM.md) | Login to Helix ITSM
*core_itsm* | [**logout**](docs/ITSM.md) | Logout of Helix ITSM
*core_itsm* | [**itsmFormGet**](docs/ITSM.md) | HTTP Get from Helix ITSM Form
*core_itsm* | [**itsmFormPost**](docs/ITSM.md) | HTTP Post to Helix ITSM Form

**TrueSight Operations Manager Application**:
Module | Method | Description
------------ | ------------- | -------------
*core_tsim* | [**getEventID**](docs/TSIM.md)| Extract TSIM Event mc_ueid
*core_tsim* | [**createCI**](docs/TSIM.md) | Create TSIM CI
*core_tsim* | [**searchCI**](docs/TSIM.md) | Search for TSIM CI
*core_tsim* | [**searchCIAdvanced**](docs/TSIM.md) | Search for TSIM CI Advanced

**TrueSight Operations Manager Core**:
Module | Method | Description
------------ | ------------- | -------------
*core_tsim* | [**authenticate**](docs/TSIM.md)| Login to TrueSight Presentation Server
*core_tsim* | [**createEvent**](docs/TSIM.md) | Create TSIM Event
*core_tsim* | [**updateEvent**](docs/TSIM.md) | Update TSIM Event
*core_tsim* | [**searchEvent**](docs/TSIM.md) | Search for TSIM Event

**TrueSight Orchestrator Application**:
Module | Method | Description
------------ | ------------- | -------------
*core_tso* | [**getTsoModules**](docs/TSO.md) | Get TrueSight Orchestrator Modules
*core_tso* | [**getTsoAdapters**](docs/TSO.md) | Get TrueSight Orchestrator Adapters
*core_tso* | [**executeTsoProcess**](docs/TSO.md) | Execute TrueSight Orchestrator

**TrueSight Orchestrator Core**:
Module | Method | Description
------------ | ------------- | -------------
*core_tso* | [**authenticate**](docs/TSO.md) | Login to TrueSight Orchestrator
*core_tso* | [**logout**](docs/TSO.md) | Logout of TrueSight Orchestrator
*core_tso* | [**apiGet**](docs/TSO.md) | HTTP Get from TrueSight Orchestrator 
*core_tso* | [**apiPost**](docs/TSO.md) | HTTP Post to TrueSight Orchestrator 