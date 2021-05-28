# Werkstatt Tools
TrueSight Orchestrator Python module for Werkstatt projects

## Core functions for integrating with solutions using Python
- Create objects in TrueSight Orchestrator

## Core Libraries and purpose
- **w3rkstatt** basic project functions
- **tso** basic TrueSight Orchestrator integration

## Dependencies
- [X] **Basic Libraries**
- [X] **Cryptodome**
- [X] **TrueSight Orchestrator**



## Solutions leveraging the base tools
| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         | 
| Werkstatt Tools           | ⬜            | ✅    | 
| TrueSight Orchestrator     | ✅            | 🚧    | 




* ✅ — Supported
* 🔶 — Partial support
* 🚧 — Under development
* ⬜ - N/A ️


**ToDO**: 
- [x] Initial Core Development
- [ ] Add TrueSight Orchestrator functions


**Configuration**: 
- After the inital run of w3rkstatt.py a local crypto key file is being generated in the /configs folder with [hostname].bin
- After the inital run of w3rkstatt.py a local config file is being generated in the /configs folder with [hostname].json
- Update the credentials and other settings in the [hostname].json file
- Execute w3rkstatt.py to encrypt the passwords in [hostname].json
- All password in cleartext will be removed
- Update file level access for [hostname].bin to only authorized OS accounts. If the file [hostname].bin is being deleted, the encrypted passwords cannot be recovered 
- The account running the python scripts needs to have access to [hostname].json and [hostname].bin
- Update TSO Server settings

**TrueSight Orchestrator**:
- Create TrueSight Orchestrator account with proper permissions
- Add application credentials to [hostname].json


## Module Information
**TrueSight Orchestrator Configuration**: 
- Folder: ~/.w3rkstatt/configs
- File: [hostname].json - custome config file


**Function**:
**TrueSight Orchestrator Application**:
Module | Method | Description
------------ | ------------- | -------------
*core_tso* | [**getTsoModules**] | Get TrueSight Orchestrator Modules
*core_tso* | [**getTsoAdapters**] | Get TrueSight Orchestrator Adapters
*core_tso* | [**executeTsoProcess**] | Execute TrueSight Orchestrator


**TrueSight Orchestrator Core**:
Module | Method | Description
------------ | ------------- | -------------
*core_tso* | [**authenticate**]| Login to TrueSight Orchestrator
*core_tso* | [**logout**] | Logout of TrueSight Orchestrator
*core_tso* | [**apiGet**]| HTTP Get from TrueSight Orchestrator 
*core_tso* | [**apiPost**]| HTTP Post to TrueSight Orchestrator 


## TrueSight Orchestrator HTTP Body
Update the JSON content, utlize project default settings from [hostname].json


**TrueSight Orchestrator Workflow**:
```bash
{
	"inputParameters": [{
		"name": "data",
		"value": "test"
	}]
}
```

