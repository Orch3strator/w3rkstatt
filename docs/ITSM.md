# Werkstatt Tools
E-Mail Python module for Werkstatt projects

## Core functions for integrating with solutions using Python
- Create objects in Helix ITSM / ServiceNOW

## Core Libraries and purpose
- **w3rkstatt** basic project functions
- **itsm** basic Helix ITSM integration

## Dependencies
- [X] **Basic Libraries**
- [X] **Cryptodome**
- [X] **Helix ITSM**
- [X] **ServiceNOW**


## Solutions leveraging the base tools
| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         | 
| Werkstatt Tools           | ⬜            | ✅    | 
| Helix ITSM                | ✅            | 🔶    | 
| ServiceNOW                | ✅            | 🚧    | 



* ✅ — Supported
* 🔶 — Partial support
* 🚧 — Under development
* ⬜ - N/A ️


**ToDO**: 
- [x] Initial Core Development
- [ ] Add / Transfer ServiceNOW support


**Configuration**: 
- After the inital run of w3rkstatt.py a local crypto key file is being generated in the /configs folder with [hostname].bin
- After the inital run of w3rkstatt.py a local config file is being generated in the /configs folder with [hostname].json
- Update the credentials and other settings in the [hostname].json file
- Execute w3rkstatt.py to encrypt the passwords in [hostname].json
- All password in cleartext will be removed
- Update file level access for [hostname].bin to only authorized OS accounts. If the file [hostname].bin is being deleted, the encrypted passwords cannot be recovered 
- The account running the python scripts needs to have access to [hostname].json and [hostname].bin
- Update ITSM Server settings

**Helix ITSM**:
- Create Helux ITSM account with proper permissions
- Add application credentials to [hostname].json

**ServiceNOW**:
- Create ServiceNOW ITSM account with proper permissions
- Add application credentials to [hostname].json

## Module Information
**Mail Server Configuration**: 
- Folder: ~/.w3rkstatt/configs
- File: [hostname].json - custome config file


**Function**:
**Helix ITSM Application**:
Module | Method | Description
------------ | ------------- | -------------
*itsm* | [**createChange**] | Create ITSM Change Request
*itsm* | [**getChange**] | Get ITSM Change Request status
*itsm* | [**extractChangeState**] | Translate ITSM Change Request details
*itsm* | [**createIncident**]| Create ITSM Incident
*itsm* | [**getIncident**] | Get ITSM Incident details
*itsm* | [**getIncidentStatus**]| Get ITSM Incident status

**Helix ITSM Core**:
Module | Method | Description
------------ | ------------- | -------------
*itsm* | [**itsmAuthenticate**]| Login to Helix ITSM
*itsm* | [**itsmLogout**] | Logout of Helix ITSM
*itsm* | [**itsmFormGet**]| HTTP Get from Helix ITSM Form
*itsm* | [**itsmFormPost**]| HTTP Post to Helix ITSM Form


## Helix ITSM HTTP Body
Update the JSON content, utlize project default settings from [hostname].json
**Change Management**:
```bash
{
	"values": {
		"z1D_Action": "CREATE",
		"First Name": "",
		"Last Name": "",
		"Description": "",
		"Impact": "",
		"Urgency": "",
		"Status": "",
		"Status Reason": "",
		"Vendor Ticket Number": "",
		"ServiceCI": "",
		"Company3": "",
		"Support Organization": "",
		"Support Group Name": "",
		"Location Company": "",
		"Region": "",
		"Site Group": "",
		"Site": "",
		"Categorization Tier 1": "",
		"Categorization Tier 2": "",
		"Categorization Tier 3": "",
		"Product Cat Tier 1(2)": "",
		"Product Cat Tier 2 (2)": "",
		"Product Cat Tier 3 (2)": "",
		"Scheduled Start Date": "",
		"Scheduled End Date": "",
		"TemplateID": ""
	}
}
```

**Incident Management**:
```bash
{
	"values": {
		"z1D_Action": "CREATE",
		"First_Name": "",
		"Last_Name": "",
		"Description": "",
		"Impact": "",
		"Urgency": "",
		"Status": "",
		"Reported Source": "",
		"Service_Type": "",
		"ServiceCI": "",
		"Assigned Group": "",
		"Assigned Support Company": "",
		"Assigned Support Organization": "",
		"Categorization Tier 1": "",
		"Categorization Tier 2": "",
		"Categorization Tier 3": "",
		"Product Categorization Tier 1": "",
		"Product Categorization Tier 2": "",
		"Product Categorization Tier 3": "",
		"Product Name": "",
		"TemplateID": ""
	}
}
```