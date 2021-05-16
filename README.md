# Werkstatt Tools
Basic Python modules for Werkstatt projects


## Core functions for integrating with solutions using Python
- Basic transform and core functions
- Encryption of credential 
- External configuration in custom json file

## Core Library and purpose
- **general** base python functions for project support
- **security** encrypt the cleartext passwords

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
| BMC Control-M             | 🔶            | 🚧    | 
| BMC Helix ITSM            | 🔶            | 🚧    | 
| BMC TrueSight             | 🔶            | 🚧    | 
| ServiceNOW                | 🔶            | 🚧    | 
| E-Mail                    | 🔶            | 🚧    | 



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

All URIs are relative to */*

## Test 
**SMTP**:
Module | Method | Description
------------ | ------------- | -------------
*smtp* | [**prepareEmail**](docs/SMTP.md)     | Prepare HTML content, based on template
*smtp* | [**sendEmailSmtpSSL**](docs/SMTP.md) | Send E-mail with SSL enabled

**Helix ITSM Application**:
Module | Method | Description
------------ | ------------- | -------------
*itsm* | [**createChange**](docs/ITSM.md) | Create ITSM Change Request
*itsm* | [**getChange**](docs/ITSM.md) | Get ITSM Change Request status
*itsm* | [**extractChangeState**](docs/ITSM.md) | Translate ITSM Change Request details
*itsm* | [**createIncident**](docs/ITSM.md) | Create ITSM Incident
*itsm* | [**getIncident**](docs/ITSM.md) | Get ITSM Incident details
*itsm* | [**getIncidentStatus**](docs/ITSM.md) | Get ITSM Incident status

**Helix ITSM Core**:
Module | Method | Description
------------ | ------------- | -------------
*itsm* | [**itsmAuthenticate**](docs/ITSM.md) | Login to Helix ITSM
*itsm* | [**itsmLogout**](docs/ITSM.md) | Logout of Helix ITSM
*itsm* | [**itsmFormGet**](docs/ITSM.md) | HTTP Get from Helix ITSM Form
*itsm* | [**itsmFormPost**](docs/ITSM.md) | HTTP Post to Helix ITSM Form