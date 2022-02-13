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

from r_types import CTFdChallenge, CTFdResponse, MixtoConfig, MixtoEntry


class CreateMixtoEntries:
    def __init__(
        self, platform: str, ctf_url: str, ctf_session: str, workspace: str = None
    ) -> None:
        self.ctf_url = ctf_url
        self.ctf_session = ctf_session
        self.ctfPlatform = platform
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
            self.show_error("The configuration file does not exist.")
        with config_path.open() as config_file:
            return MixtoConfig(**json.load(config_file))

    def workspace_has_entries(self) -> bool:
        """
        Returns true if the workspace has entries.
        """
        url = urljoin(self.mixto_url, f"/api/workspace/{self.workspace}")
        res = requests.get(url, headers={"x-api-key": self.config.api_key})
        return res.json()["entries_count"] != 0

    def process_entries(self) -> List[MixtoEntry]:
        """
        Processes an array of challenges and returns an array of entries.
        """
        # check if workspace has entries
        if self.workspace_has_entries():
            self.confirm(
                f'The workspace "{self.workspace}" already has entries. Do you want to add to them?'
            )

        hold: List[MixtoEntry] = []
        challenges = self.get_challenges()
        for challenge in challenges:
            if challenge.category in self.config.categories:
                hold.append({"title": challenge.name, "category": challenge.category})
            else:
                hold.append({"title": challenge.name, "category": "other"})
        return hold

    def batch_create_entries(self) -> None:
        """
        Batch create entries
        """
        entries = self.process_entries()
        # confirm batch add entries
        self.confirm(f"Do you want to add {len(entries)} entries to {self.workspace}?")
        try:
            url = urljoin(self.mixto_url, f"/api/entry/{self.workspace}")
            r = requests.put(
                url, json=entries, headers={"x-api-key": self.config.api_key}
            )
            if r.status_code != 200:
                self.show_error(f"Failed to add entries: {r.status_code}")
            # print the number of entries created
            added = r.json()
            for entry in added:
                print(f"Added {entry['category']} {entry['title']}")
            print("Entries added: ", len(added))
        except Exception as e:
            self.show_error(f"Error when adding entries: {r.status_code}")

    def show_error(self, message: str):
        """
        Prints an error message and exits the program.
        """
        raise Exception(message)

    def confirm(self, msg: str):
        """
        Asks the user to confirm an action.
        """
        print(msg)
        if not input("[Y/n] ").lower() == "y":
            print("Aborting...")
            exit(1)

    def get_challenges(self) -> List[CTFdChallenge]:
        """
        Returns all challenges from the CTFd instance.
        """
        if self.ctfPlatform == "ctfd":
            return self.get_ctfd_challenges()
        else:
            self.show_error("The platform is not supported.")

    # methods to get challenges from various platforms

    def get_ctfd_challenges(self) -> List[CTFdChallenge]:
        """
        Returns all challenges from the CTFd instance.
        """
        url = urljoin(self.ctf_url, "/api/v1/challenges")
        try:
            r = requests.get(url, cookies={"session": self.ctf_session})
            return CTFdResponse(**r.json()).data
        except Exception as e:
            self.show_error(f"Failed to get challenges: {e}")


if __name__ == "__main__":
    # argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="The hostname of the CTFd instance. Do not include /api/v1",
        required=True,
    )
    parser.add_argument(
        "--session",
        help="A valid session cookie value from the CTFd instance",
        required=True,
    )
    parser.add_argument(
        "--platform",
        help="The CTF scoring platform to use",
        default="ctfd",
        choices=["ctfd", "redpwn", "mellivora"],
    )
    parser.add_argument(
        "--workspace", help="The workspace to add entries to. Defaults to mixto config"
    )
    args = parser.parse_args()

    m = CreateMixtoEntries(
        platform=args.platform,
        ctf_url=args.host,
        ctf_session=args.session,
        workspace=args.workspace,
    )
    m.batch_create_entries()
