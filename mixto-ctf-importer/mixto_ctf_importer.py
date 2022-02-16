"""
This script allows calling the CTFd API and automatically creating valid 
Mixto entries.
"""
import json
import argparse
from typing import List
from urllib.parse import urljoin
from pathlib import Path
import requests
from lib.ctfd import CTFd
from lib.pico import PicoCTF

from lib.r_types import MixtoConfig, MixtoEntry
from lib.helpers import ParseKwargs

MIXTO_USER_AGENT = "mixto-ctf-importer"


class CreateMixtoEntries:
    def __init__(self, workspace: str = None) -> None:
        self.config = self.read_mixto_conf()
        self.workspace = workspace if workspace is not None else self.config.workspace

    @property
    def mixto_url(self) -> str:
        return urljoin(self.config.host, f"/api/entry/{self.workspace}")

    def read_mixto_conf(self) -> MixtoConfig:
        """
        Reads the ~/.mixto.json file and returns a dictionary with the configuration.
        """
        config_path = Path.home() / ".mixto.json"
        if not config_path.exists():
            raise Exception("The configuration file does not exist.")
        with config_path.open() as config_file:
            return MixtoConfig(**json.load(config_file))

    def workspace_has_entries(self) -> bool:
        """
        Returns true if the workspace has entries.
        """
        url = urljoin(self.mixto_url, f"/api/workspace/{self.workspace}")
        res = requests.get(url, headers={"x-api-key": self.config.api_key})
        current_count = res.json().get("entries_count", 0)
        return current_count != 0

    def batch_create_entries(self, entries: List[MixtoEntry]) -> None:
        """
        Batch create entries
        """
        # check if workspace has entries
        if self.workspace_has_entries():
            self.confirm(
                f'The workspace "{self.workspace}" already has entries. Do you want to add to them?'
            )

        # confirm batch add entries
        self.confirm(f"Do you want to add {len(entries)} entries to {self.workspace}?")
        try:
            url = urljoin(self.mixto_url, f"/api/entry/{self.workspace}")
            res = requests.put(
                url,
                json=entries,
                headers={
                    "x-api-key": self.config.api_key,
                    "User-Agent": MIXTO_USER_AGENT,
                },
            )
            if res.status_code != 200:
                raise Exception(f"Failed to add entries: {res.status_code}")
            # print the number of entries created
            added = res.json()
            for entry in added:
                print(f"Added {entry['category']} {entry['title']}")
            print("Entries added: ", len(added))
        except Exception as e:
            raise Exception(f"Error when adding entries")

    def confirm(self, msg: str):
        """
        Asks the user to confirm an action.
        """
        print(msg)
        if not input("[Y/n] ").lower() == "y":
            print("Aborting...")
            exit(1)


if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="The hostname of the CTFd instance. Do not include /api/v1",
        required=True,
    )
    parser.add_argument(
        "--platform",
        help="The CTF scoring platform to use",
        choices=["ctfd", "pico"],
        required=True,
    )
    parser.add_argument(
        "--event-id", help="The event id to use", required=False, default=None
    )
    parser.add_argument(
        "--workspace", help="The workspace to add entries to. Defaults to mixto config"
    )
    parser.add_argument(
        "--cookies",
        help="Cookies. Example cookiename=cookievalue. Can add multiple.",
        nargs="*",
        action=ParseKwargs,
    )
    args = parser.parse_args()

    # placeholder for mixto entries
    entries: List[MixtoEntry] = []
    mixto = CreateMixtoEntries(
        workspace=args.workspace,
    )

    ctf_platform = args.platform
    if ctf_platform == "ctfd":
        c = CTFd(args.host, args.cookies, mixto.config)
        entries = c.process_challenges_to_entries()

    elif ctf_platform == "pico":
        c = PicoCTF(args.host, args.cookies, args.event_id, mixto.config)
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
