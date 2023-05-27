# Shell Scripts

Basic Bash Sehll scripts for Werkstatt projects

## Installation

Install Bash and dependent libraries

- [ ] **For All Users**
- [ ] **Add to system path**

## Dependencies

- [ ] **Bash Shell**

Shell Scripts

```bash
Linux
remove_ctm_env.sh
remove_ctm_env.sh -h
remove_ctm_env.sh -p [patten]
```

**Shell Scripts**:
Solution | Script | Description
------------ | ------------- | -------------
*ctm* | [**remove_ctm_env.sh**](../src/shell/remove_ctm_env.sh) | Remove Control-M environments matching a pattern for ctm aapi

## Control-M

During developement you might create a lot of environment. The provided script allow the deletion of ctm environments matching the search pattern.

Local log files will be written to identify the deleted environments:

- ctmenv.deleted.json
- ctmenv.final.json
- ctmenv.old.json
