# mixto_ctf_importer

A simple python script that connects to various CTF score boards and automatically creates all challenges as entries. 

## Supports
  [x] CTFd
  [] Redpwn CTF
  [] Mellivora

## Usage
```bash
❯❯ python mixto_ctf_importer.py -h
usage: ctfd.py [-h] --host HOST --session SESSION [--platform {ctfd,redpwn,mellivora}] [--workspace WORKSPACE]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           The hostname of the CTFd instance. Do not include /api/v1
  --session SESSION     A valid session cookie value from the CTFd instance
  --platform {ctfd,redpwn,mellivora}
                        The CTF scoring platform to use
  --workspace WORKSPACE
                        The workspace to add entries to. Defaults to mixto config
```
