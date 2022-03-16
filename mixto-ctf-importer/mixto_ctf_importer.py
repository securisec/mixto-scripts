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


if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="The hostname of the CTFd scoreboard. Do not include /api/v1",
    )
    parser.add_argument(
        "--platform",
        help="The CTF scoring platform to use",
        choices=["ctfd", "htb", "pico"],
        required=True,
    )
    parser.add_argument(
        "--workspace", help="The workspace to add entries to. Defaults to mixto config"
    )
    args = parser.parse_args()

    # placeholder for mixto entries
    entries: List[MixtoEntry] = []
    mixto = CreateMixtoEntries(
        workspace=args.workspace,
    )

    ctf_platform = args.platform
    if ctf_platform == "ctfd":
        if args.host is None:
            print("You must specify the host flag for CTFd")
            exit(1)
        c = CTFd(args.host, mixto.config)
        entries = c.process_challenges_to_entries()

    elif ctf_platform == "pico":
        c = PicoCTF("https://play.picoctf.org", mixto.config)
        entries = c.process_challenges_to_entries()

    elif ctf_platform == "htb":
        c = HtbCTF("https://ctf-api.hackthebox.com", mixto.config)
        entries = c.process_challenges_to_entries()

    else:
        print("Scoring server not implemented yet")
        exit(1)

    # sanity check
    if len(entries) == 0:
        print("No challenges found")
        exit(1)

    # batch create entries
    mixto.batch_create_entries(entries)
