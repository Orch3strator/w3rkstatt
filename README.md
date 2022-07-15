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

Install dependencies, see [Setup documentation](docs/SETUP.md) for more details.

```bash
Linux
python3 -m pip install wheel requests urllib3 pyCryptodome pandas json2html jsonpath-ng jsonpath_rw_ext --user
python3 -m pip install git+https://github.com/dcompane/controlm_py.git --user
```

```bash
Windows
python -m pip install wheel requests urllib3 pyCryptodome pandas json2html jsonpath-ng jsonpath_rw_ext
python -m pip install git+https://github.com/dcompane/controlm_py.git
```

## Solutions leveraging the base tools

| Solution        | API | Python |
| :-------------- | :-: | :----: |
| Werkstatt Tools | ⬜  |   ✅   |
| BMC Control-M   | 🔶  |   ✅   |
| BMC Helix ITSM  | 🔶  |   ✅   |
| BMC TrueSight   | 🔶  |   ✅   |
| ServiceNOW      | 🔶  |   🚧   |
| E-Mail          | 🔶  |   ✅   |
| Shell Scripts   | ⬜  |   ⬜   |

- ✅ — Supported
- 🔶 — Partial support
- 🚧 — Under development
- ⬜ - N/A ️

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
_core_smtp_ | [**prepareEmail**](docs/SMTP.md) | Prepare HTML content, based on template
_core_smtp_ | [**sendEmailSmtpSSL**](docs/SMTP.md) | Send E-mail with SSL enabled

**Helix ITSM Application**:
Module | Method | Description
------------ | ------------- | -------------
_core_itsm_ | [**createChange**](docs/ITSM.md) | Create ITSM Change Request
_core_itsm_ | [**getChange**](docs/ITSM.md) | Get ITSM Change Request status
_core_itsm_ | [**extractChangeState**](docs/ITSM.md) | Translate ITSM Change Request details
_core_itsm_ | [**createIncident**](docs/ITSM.md) | Create ITSM Incident
_core_itsm_ | [**getIncident**](docs/ITSM.md) | Get ITSM Incident details
_core_itsm_ | [**getIncidentStatus**](docs/ITSM.md) | Get ITSM Incident status

**Helix ITSM Core**:
Module | Method | Description
------------ | ------------- | -------------
_core_itsm_ | [**authenticate**](docs/ITSM.md) | Login to Helix ITSM
_core_itsm_ | [**logout**](docs/ITSM.md) | Logout of Helix ITSM
_core_itsm_ | [**itsmFormGet**](docs/ITSM.md) | HTTP Get from Helix ITSM Form
_core_itsm_ | [**itsmFormPost**](docs/ITSM.md) | HTTP Post to Helix ITSM Form

**TrueSight Operations Manager Application**:
Module | Method | Description
------------ | ------------- | -------------
_core_tsim_ | [**getEventID**](docs/TSIM.md)| Extract TSIM Event mc_ueid
_core_tsim_ | [**createCI**](docs/TSIM.md) | Create TSIM CI
_core_tsim_ | [**searchCI**](docs/TSIM.md) | Search for TSIM CI
_core_tsim_ | [**searchCIAdvanced**](docs/TSIM.md) | Search for TSIM CI Advanced

**TrueSight Operations Manager Core**:
Module | Method | Description
------------ | ------------- | -------------
_core_tsim_ | [**authenticate**](docs/TSIM.md)| Login to TrueSight Presentation Server
_core_tsim_ | [**createEvent**](docs/TSIM.md) | Create TSIM Event
_core_tsim_ | [**updateEvent**](docs/TSIM.md) | Update TSIM Event
_core_tsim_ | [**searchEvent**](docs/TSIM.md) | Search for TSIM Event

**TrueSight Orchestrator Application**:
Module | Method | Description
------------ | ------------- | -------------
_core_tso_ | [**getTsoModules**](docs/TSO.md) | Get TrueSight Orchestrator Modules
_core_tso_ | [**getTsoAdapters**](docs/TSO.md) | Get TrueSight Orchestrator Adapters
_core_tso_ | [**executeTsoProcess**](docs/TSO.md) | Execute TrueSight Orchestrator

**TrueSight Orchestrator Core**:
Module | Method | Description
------------ | ------------- | -------------
_core_tso_ | [**authenticate**](docs/TSO.md) | Login to TrueSight Orchestrator
_core_tso_ | [**logout**](docs/TSO.md) | Logout of TrueSight Orchestrator
_core_tso_ | [**apiGet**](docs/TSO.md) | HTTP Get from TrueSight Orchestrator
_core_tso_ | [**apiPost**](docs/TSO.md) | HTTP Post to TrueSight Orchestrator

**Shell Scripts**:
Solution | Script | Description
------------ | ------------- | -------------
_ctm_ | [**remove_ctm_env.sh**](docs/SHELL.md) | Remove Control-M environments matching a pattern for ctm aapi

**Python Scripts**:
Solution | Script | Description
------------ | ------------- | -------------
_ctm_ | [**disco_ctm.py**](docs/DISCO.md) | Create inventory of Control-M environment and resources
