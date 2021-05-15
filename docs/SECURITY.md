# Werkstatt Tools
Security Python module for Werkstatt projects

## Core functions for integrating with solutions using Python
- Encryption of credential 

## Core Libraries and purpose
- **werkstatt_security** encrypt the cleartext passwords

## Dependencies
- [ ] **Basic Libraries**
- [ ] **Cryptodome**

## Solutions leveraging the base tools
| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         | 
| Werkstatt Tools           | ⬜            | ✅    | 

* ✅ — Supported
* 🔶 — Partial support
* 🚧 — Under development
* ⬜ - N/A ️


**ToDO**: 
- [x] Initial Core Development
- [ ] update custom json config file
- [ ] execute werkstatt_security.py
- [ ] secure [hostname].bin on OS level

**Configuration**: 
- After the inital run of werkstatt_general.py a local crypto key file is being generated in the /configs folder with [hostname].bin
- After the inital run of werkstatt_general.py a local config file is being generated in the /configs folder with [hostname].json
- Update the credentials and other settings in the [hostname].json file
- Execute werkstatt_security.py to encrypt the passwords in [hostname].json
- All password in cleartext will be removed
- Update file level access for [hostname].bin to only authorized OS accounts. If the file [hostname].bin is being deleted, the encrypted passwords cannot be recovered 
- The account running the python scripts needs to have access to [hostname].json and [hostname].bin

**Info**: 
Cryptodome is beind utilized for safekeeping of the credentials
- Folder: /configs
- File: [hostname].json - custome config file
- File: [hostname].bin - crypto key for security functions