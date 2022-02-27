import json
from pathlib import Path
from urllib.parse import urljoin
from typing import List
import requests
from pydantic import BaseModel

MIXTO_USER_AGENT = "mixto-ctf-importer"


class MixtoConfig(BaseModel):
    api_key: str
    categories: List[str]
    host: str
    workspace: str


class MixtoEntry(BaseModel):
    title: str
    category: str


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
