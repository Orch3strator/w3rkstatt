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

Module | Method | Description
------------ | ------------- | ------------- | -------------
*smtp* | [**prepareEmail**] (docs/SMTP.md     | Prepare HTML content, based on template
*smtp* | [**sendEmailSmtpSSL**] (docs/SMTP.md | Send E-mail with SSL enabled