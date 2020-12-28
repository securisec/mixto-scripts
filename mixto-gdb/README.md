# mixto-gdb

Mixto plugin for GDB. Compitable with python 3. 

## Usage
To source `mixto-gdb.py` inside gdb, use `source /path/to/mixto-gdb.py`

This script does not have any dependencies, and tries to obtain information from two places:

- It will look for the following environment variables:
  - MIXTO_ENTRY_ID - *Required to be set*
  - MIXTO_HOST
  - MIXTO_API_KEY
- If either the `MIXTO_HOST` or `MIXTO_API_KEY` is not set, then it will look for these values in the `~/.mixto.json` file.

## Usage inside gdb
Simply run `mixto any gdb command` inside gdb and it will send the data to the mixto server. Ex:
```
(gdb) mixto info registers
```