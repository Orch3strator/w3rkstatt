# Werkstatt Tools
E-Mail Python module for Werkstatt projects

## Core functions for integrating with solutions using Python
- Send E-mail in HTML format

## Core Libraries and purpose
- **w3rkstatt** basic project functions
- **smtp** basic SMTP e-mail functions

## Dependencies
- [X] **Basic Libraries**
- [X] **Cryptodome**
- [X] **SMTPLib**


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


**Configuration**: 
- After the inital run of w3rkstatt.py a local crypto key file is being generated in the /configs folder with [hostname].bin
- After the inital run of w3rkstatt.py a local config file is being generated in the /configs folder with [hostname].json
- Update the credentials and other settings in the [hostname].json file
- Execute w3rkstatt.py to encrypt the passwords in [hostname].json
- All password in cleartext will be removed
- Update file level access for [hostname].bin to only authorized OS accounts. If the file [hostname].bin is being deleted, the encrypted passwords cannot be recovered 
- The account running the python scripts needs to have access to [hostname].json and [hostname].bin
- Update SMTP Server settings

**Google**:
- Get an application password
- Add application password to [hostname].json

**Info**: 
- Folder: ~/.w3rkstatt/configs
- File: [hostname].json - custome config file


**Function**:
Module | Method | Description
------------ | ------------- | ------------- 
*smtp* | [**prepareEmail**]     | Prepare HTML content, bbased on template
*smtp* | [**sendEmailSmtpSSL**] | Send E-mail with SSL enabled


**Internals**:
| Key Word                  | Description           
| :-------------            | -------------        
| *EMAIL_LOGO_TEXT*         | Text above custom logo
| *EMAIL_MESSAGE*           | Email Messsage
| *EMAIL_DATA*              | Data in JSON format, will be converted to HTML Table
| *EMAIL_UUID*              | UUID to track activity in [hostname].log file

| Parameters                | Description           
| :-------------            | -------------   
| *Template*                | Templates in Folder: ~/.w3rkstatt/templates


**Templates**:
- Copy your HTML templates to ~/.w3rkstatt/templates
- Use the internal keywords for string replacement