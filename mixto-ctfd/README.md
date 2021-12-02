# mixto-ctfd

A simple python script that connects to a CTFd session and automatically creates all challenges as entries. 

```bash
❯❯ python ctfd.py -h
usage: ctfd.py [-h] --host HOST --session SESSION

optional arguments:
  -h, --help         show this help message and exit
  --host HOST        The hostname of the CTFd instance. Do not include /api/v1
  --session SESSION  A valid session cookie value from the CTFd instance
```
