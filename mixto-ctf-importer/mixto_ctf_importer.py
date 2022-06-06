"""
This script allows calling the CTFd API and automatically creating valid 
Mixto entries.
"""
import argparse
from typing import List
from lib.ctfd import CTFd
from lib.pico import PicoCTF
from lib.htb import HtbCTF

from lib.r_types import MixtoEntry
from lib.mixto import MixtoEntry, CreateMixtoEntries
from lib.custom import validate_custom_json
from lib.rctf import RCTF


if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser()
    # group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(
        "-p",
        "--platform",
        help="The CTF scoring platform to use",
        choices=["ctfd", "htb", "pico", "rctf"],
    )
    parser.add_argument(
        "--workspace", help="The workspace to add entries to. Defaults to mixto config"
    )
    parser.add_argument(
        "--json",
        help="The path to the json file containing the entries.",
        required=False,
    )
    args = parser.parse_args()

    # placeholder for mixto entries
    entries: List[MixtoEntry] = []
    mixto = CreateMixtoEntries(
        workspace=args.workspace,
    )

    if args.json:
        entries = validate_custom_json(mixto.config, args.json)
        mixto.batch_create_entries(entries)
        exit(0)

    ctf_platform = args.platform
    if ctf_platform == "ctfd":
        ctfdHost = input("CTFD host: ")
        c = CTFd(ctfdHost, mixto.config)
        entries = c.process_challenges_to_entries()

    elif ctf_platform == "rctf":
        c = RCTF(input("Host: "), mixto.config)
        entries = c.process_challenges_to_entries()

    elif ctf_platform == "pico":
        c = PicoCTF("https://play.picoctf.org", mixto.config)
        entries = c.process_challenges_to_entries()

    elif ctf_platform == "htb":
        c = HtbCTF("https://ctf-api.hackthebox.com", mixto.config)
        entries = c.process_challenges_to_entries()

    else:
        print("Scoring server not implemented yet. Use --json to specify a json file.")
        exit(1)

    # sanity check
    if len(entries) == 0:
        print("No challenges found")
        exit(1)

    # batch create entries
    mixto.batch_create_entries(entries)
