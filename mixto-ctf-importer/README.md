# mixto_ctf_importer

A simple python script that connects to various CTF score boards and automatically creates all challenges as entries.

## Supports

[x] CTFd
[] Redpwn CTF
[] Mellivora
[x] PicoCTF

## Usage

```bash
❯❯ python mixto_ctf_importer.py -h
usage: mixto_ctf_importer.py [-h] --host HOST --platform {ctfd,pico} [--event-id EVENT_ID]
                             [--workspace WORKSPACE] [--cookies [COOKIES ...]]

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           The hostname of the CTFd instance. Do not include /api/v1
  --platform {ctfd,pico}
                        The CTF scoring platform to use
  --event-id EVENT_ID   The event id to use
  --workspace WORKSPACE
                        The workspace to add entries to. Defaults to mixto config
  --cookies [COOKIES ...]
                        Cookies. Example cookiename=cookievalue. Can add multiple.
```

Not all CTF scoring platforms are the same. For example, Pico requires an event id, white CTFd does not.

### Example

- CTFd

```
./mixto_ctf_importer.py --platform ctfd --host http://ctf.ctfd.com --cookies session=mysessioncookievalue
```

- Pico CTF

```
./mixto_ctf_importer.py --platform pico --host http://ctf.pico.com --cookies sessionid=mysessioncookievalue csrftoken=somecsrftoken
```
