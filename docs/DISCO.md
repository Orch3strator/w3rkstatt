# Discovery

Control-M discovery Python module for Werkstatt projects

## Core functions for integrating with solutions using Python

- Discover Control-M infrastructure and export data as json file

## Core Libraries and purpose

- **w3rkstatt** basic project functions
- **ctm** basic Control-M integration

## Dependencies

- [X] **W3rkstatt Libraries**
- [X] **Control-M**
- [X] **Control-M AAPI**

## Solutions leveraging the base tools

| Solution                  | API           | Python        |
| :-------------            | :---:         | :---:         |
| Werkstatt Tools           | ⬜            | ✅    |
| Control-M                 | ✅            | 🔶    |

- ✅ — Supported
- 🔶 — Partial support
- 🚧 — Under development
- ⬜ - N/A ️

**ToDO**:

- [x] Initial Core Development
- [x] *ctm* | [**core_ctm**](./CTM.md) | Setup Control-M environment and variables

**Info**:
The discovery script will utilize the Control-M REST API to collect inventory data and export given data to a local json file.
