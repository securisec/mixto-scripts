import gdb
from os import getenv
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from urllib.error import HTTPError
from pathlib import Path
from json import loads, dumps

MIXTO_ENTRY_ID = getenv("MIXTO_ENTRY_ID")
MIXTO_HOST = getenv("MIXTO_HOST")
MIXTO_API_KEY = getenv("MIXTO_API_KEY")
MIXTO_WORKSPACE = getenv("MIXTO_WORKSPACE")

class MissingRequired(Exception):
    pass


class BadResponse(Exception):
    pass


def _send_to_mixto(out: str, arg: str):
    if MIXTO_WORKSPACE is None:
        raise MissingRequired("Workspace is missing")

    if MIXTO_ENTRY_ID is None:
        raise MissingRequired("Entry ID is missing")

    if MIXTO_HOST is None:
        raise MissingRequired("Mixto host is missing")

    if MIXTO_API_KEY is None:
        raise MissingRequired("Mixto API key is missing")

    url = urljoin(MIXTO_HOST, "/api/entry/" + MIXTO_WORKSPACE + "/" + MIXTO_ENTRY_ID + "/commit")
    req = Request(
        method="POST",
        url=url,
        data=dumps(
            {"type": "tool", "title": "(GDB) - " + arg, "data": out, "meta": {}, "tags": ["gdb"]}
        ).encode(),
        headers={"x-api-key": MIXTO_API_KEY, "Content-Type": "application/json"},
    )
    try:
        res = urlopen(req)
        status = res.getcode()
        if status > 300:
            raise BadResponse(status, res)
        print("Sent!")
    except HTTPError as e:
        raise


try:
    if MIXTO_HOST is None or MIXTO_API_KEY is None:
        conf_path = str(Path().home() / ".mixto.json")
        try:
            with open(conf_path) as f:
                j = loads(f.read())
                MIXTO_HOST = j.get("host")
                MIXTO_API_KEY = j.get("api_key")
        except:
            print('Cannot find Mixto envars or config file')
except:
    raise MissingRequired("Cannot read Mixto config")


class MixtoGDB(gdb.Command):
    def __init__(self):
        super(MixtoGDB, self).__init__("mixto", gdb.COMMAND_USER)

    def invoke(self, arg, from_tty):
        try:
            output = gdb.execute(arg, from_tty, to_string=True)
            _send_to_mixto(output, arg)
        except gdb.error:
            print("Error in gdb")


MixtoGDB()
